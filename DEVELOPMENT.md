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
