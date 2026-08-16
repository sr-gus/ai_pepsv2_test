# Guía interna de desarrollo

Esta guía resume lo necesario para trabajar en el motor sin tener que conocer
todo el historial del repositorio. No sustituye la documentación funcional ni
la documentación de despliegue.

## Preparación local

Requisitos:

- Python compatible con Azure Functions v4.
- Azure Functions Core Tools para ejecutar el endpoint localmente.

En PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:ENGINEER_EMAILS="eng1@example.com,eng2@example.com"
func start
```

La Function queda expuesta en la ruta `threadEscalationEngine`. El nivel de
autenticación configurado es `FUNCTION`.

## Flujo de procesamiento

```text
function_app.py
  -> request/validation.py
  -> service.py
     -> sentimental.py
     -> keyword.py
     -> frequency.py
  -> scoring/aggregation.py
  -> scoring/decision.py
  -> notification.py
```

`service.py` ejecuta los tres analizadores y conserva sus resultados en la
respuesta. La agregación calcula el score final, la decisión selecciona el
tier y la notificación traduce esa decisión a un objeto para el sistema que
consume la Function.

## Contrato del payload

Se admiten las dos envolturas siguientes:

```json
{"thread": []}
```

```json
{"body": {"thread": []}}
```

Cada mensaje usa como contrato canónico:

```json
{
  "subject": "Urgent billing issue",
  "bodyPreview": "I need help immediately.",
  "body": {
    "contentType": "html",
    "content": "<div>I need help immediately.</div>"
  },
  "receivedDateTime": "2026-07-12T20:30:00Z",
  "from": {
    "emailAddress": {
      "address": "customer@example.com"
    }
  },
  "headers": {
    "Auto-Submitted": "no"
  }
}
```

Reglas que todos los analizadores deben respetar:

- Las fechas se obtienen mediante `thread/extractors.py`; no se deben parsear
  de forma independiente en cada analizador.
- El texto nuevo se obtiene mediante `get_message_content`. La prioridad es
  `uniqueBody`, `body` y finalmente `bodyPreview`; no se debe analizar
  `body.content` directamente porque contiene el historial citado completo.
- La limpieza compartida convierte HTML a texto y elimina marcadores comunes
  de respuestas citadas y firmas. Cada analizador decide qué mensajes consume,
  pero no vuelve a implementar esta limpieza.
- El rol se obtiene mediante `get_message_role` en `thread/selectors.py`.
- Un correo presente en `ENGINEER_EMAILS` es un ingeniero; cualquier otro
  remitente se considera cliente.
- Las respuestas automáticas se detectan mediante `is_automatic_message` y se
  excluyen antes del análisis. Los headers con `Auto-Submitted: no` no se deben
  considerar automáticos.
- No se deben volver a introducir heurísticas basadas en palabras como
  `support`, `agent` o `microsoft`.
- Los campos opcionales deben leerse mediante los extractores compartidos para
  evitar errores cuando sean nulos o tengan un tipo inesperado.

## Contrato de un analizador

Un analizador debe ser una función asíncrona que reciba el thread sin modificar
y devuelva, como mínimo:

```python
{
    "name": "analyzer_name",
    "score": 0.0,       # entre 0.0 y 1.0
    "label": "label",
    "flags": [],
    "details": {},
}
```

Cuando se agregue una nueva señal:

1. Implementar o modificar el analizador correspondiente.
2. Declarar pesos, boosts o thresholds en `escalation_engine/config.py`.
3. Actualizar `scoring/aggregation.py` solamente si cambia la composición del
   score.
4. Agregar pruebas con resultados observables, no únicamente pruebas de que la
   función no lanza excepciones.

### Actualización del vocabulario

Las listas de keywords y frases viven en `escalation_engine/config.py`. Al
actualizarlas:

- Preferir frases que expresen riesgo o impacto real sobre términos genéricos
  como `subscription`, `tenant`, `request` o `cancel`.
- El asunto solo aporta evidencia en el primer mensaje. En un thread existente
  se siguen reportando sus coincidencias, pero no afectan el trigger ni el
  score porque normalmente conserva el problema original aunque ya se resolvio.
- Varias señales independientes entre tópicos deben aportar más confianza que
  acumular muchos sinónimos dentro de un solo tópico.
- Evitar duplicar la misma keyword en varios tópicos, porque cada coincidencia
  contribuye al score total.
- Preferir `patterns` para duraciones o cantidades variables y reservar
  `critical_patterns` para lenguaje que por si solo justifica el trigger.
- Incluir variantes en inglés y español cuando existan en conversaciones
  reales.
- Usar ejemplos anonimizados en las pruebas; nunca copiar nombres, correos,
  IDs de suscripción o contenido completo de clientes.
- Agregar un caso neutral o resuelto para vigilar falsos positivos.

Los thresholds no representan severidad por sí solos: representan cuántas
señales distintas deben aparecer para activar un tópico. Una keyword, frase o
patrón normal vale 1. Repetir la misma señal o encontrar una keyword dentro de
una frase más específica no suma evidencia adicional. Las entradas críticas
valen al menos 2, por lo que una expresión inequívoca puede activar un tópico.

Calibración actual:

- `urgent_request`: 1, porque una declaración explícita de urgencia es suficiente.
- Los demás tópicos: 2. Sus términos genéricos requieren dos señales
  distintas; una frase o patrón crítico puede alcanzar el umbral por sí solo.

### Solicitudes explícitas de escalación

El routing distingue la intención de escalar del score de riesgo:

- Una solicitud activa a manager, supervisor, leadership, alguien con
  autoridad o Tier 2 se clasifica como `hierarchical` y fuerza Tier 2.
- Una solicitud activa sin target se clasifica como `generic` y fuerza Tier 2.
- Escalar a billing, engineering, product, platform, security, subscriptions,
  support u otro equipo especializado se clasifica como `specialist_handoff`.
  No aplica override: el score agregado conserva la decisión.
- Condicionales, negaciones, agradecimientos, solicitudes ya completadas,
  subjects heredados y contenido citado no aplican override.

El override nunca modifica `aggregation.score`. La decisión y notificación
incluyen `decisionSource`, `routingOverride`, `routingConfidence` y la
clasificación completa en `escalationRequest`. Esto permite distinguir un Tier
2 solicitado por el cliente de uno alcanzado por score.

Al ampliar este clasificador, agregar como mínimo una prueba positiva, un
handoff especializado y ejemplos condicional, negado e histórico. Los targets
deben estar gramaticalmente ligados a la petición; no basta con que aparezca la
palabra `manager` o el nombre de un equipo en la misma oración.

## Verificaciones antes de compartir cambios

```powershell
python -m compileall escalation_engine tests function_app.py
python -m unittest discover -s tests -v
git diff --check
git status --short
```

Todo cambio de contrato, timestamp, remitente o scoring debe incluir al menos
una prueba de regresión. No agregar datos reales de clientes, correos privados,
claves de Function ni archivos `local.settings.json` al repositorio.

## Trabajo con Git

- `develop` es la rama de integración.
- Crear ramas cortas desde `develop`, normalmente `feat/...` o `fix/...`.
- Mantener cada commit enfocado en una sola intención.
- Antes de integrar, actualizar la rama con el estado reciente de `develop` y
  ejecutar las verificaciones locales.
- `master` debe recibir cambios desde `develop` únicamente cuando el conjunto
  esté listo para liberarse.

## Replays y regresiones de analizadores

Los tres analizadores pueden revisarse incrementalmente con los fixtures:

```powershell
python -m tests.inspect_keyword_timeline --case 1 --pause
python -m tests.inspect_frequency_timeline --case 1 --pause
python -m tests.inspect_sentiment_timeline --case 1 --pause
```

Para usar uno de los datasets adicionales, agregar `--fixture` y conservar
`--case` o `--all` como selector:

```powershell
python -m tests.inspect_keyword_timeline `
  --fixture tests\azure_billing_escalation_threads_short.json `
  --case 7 `
  --pause
```

Los archivos `short`, `mixed` y `long` contienen 8 threads cada uno. Mantienen
la forma `[{uri, method, body: {thread: [...]}}]`, mensajes Graph/Outlook con
HTML, fechas ordenadas, respuestas del ingeniero y contenido citado. El
archivo `tests/additional_thread_expectations.json` registra la intención,
longitudes y clasificación contextual esperada por evento de cliente, pero no
fija scores. Se regeneran de forma determinista con:

```powershell
python -m tests.generate_additional_thread_fixtures
```

`tests/test_additional_thread_fixtures.py` valida el contrato, la extracción
del body nuevo, las distribuciones de longitud y el contexto de escalación.

Para payloads exportados de Power Automate, reemplazar `--case 1` por
`--payload <archivo.json>` y proporcionar `--engineer-email` cuando el correo
del ingeniero no esté configurado en el ambiente.

Regresiones disponibles:

- Keyword fija score, label, tópicos y resolución para los 100 eventos de
  cliente de los 25 casos.
- Frequency fija score, label, flags, mensajes pendientes y horas sin
  respuesta para los mismos 100 eventos. También prueba escenarios sintéticos
  de ráfagas, delays de 24/72 horas, auto-replies y tendencias.
- Sentiment valida desde ahora el replay, filtrado, fuentes de texto y contrato
  de salida. Su regresión de calidad queda omitida mientras continúe siendo un
  placeholder; se activa al llenar `EXPECTED_SENTIMENT_TIMELINES` en
  `tests/test_sentiment_dataset_regression.py`.

Observaciones de frequency, sin cambios en su implementación:

- En el instante en que llega un correo nuevo del cliente, `ghostedHours` es
  normalmente 0. Detectar silencios de 24/72 horas requiere una ejecución
  posterior o programada; un flujo disparado exclusivamente por correos no
  despierta durante el silencio.
- El replay debe pasar como `now` la fecha del evento. Usar el reloj actual al
  reproducir fixtures antiguos genera delays críticos artificiales.
- `ghostedHours` se calcula desde el mensaje pendiente más reciente. Un nuevo
  follow-up reinicia ese reloj aunque el primer mensaje continúe sin respuesta.
- 88 de los 100 eventos del fixture producen exactamente el baseline 0.05,
  neutral y sin flags. El fixture por sí solo ofrece poca cobertura de ráfagas
  o delays, por lo que se agregaron casos sintéticos.
- `multiple_unanswered_messages` afecta el score, pero no tiene boost en la
  agregación final; solamente `rapid_followup` recibe un boost adicional.

## Estado conocido

- El analizador sentimental todavía es un placeholder y devuelve un score
  negativo fijo.
- La validación actual comprueba solamente la estructura mínima del request.
- El analizador de frecuencia y el de keywords ya comparten la clasificación
  de remitentes.
- Keyword, sentiment y frequency comparten la extracción de contenido nuevo y
  el filtro de respuestas automáticas.
- Todavía no hay pipeline de CI ni versiones de dependencias fijadas.

Si un cambio requiere alterar el formato del payload o la semántica de un
score, acordarlo con el equipo antes de implementarlo, porque afecta a Power
Automate y a cualquier consumidor de la respuesta.
