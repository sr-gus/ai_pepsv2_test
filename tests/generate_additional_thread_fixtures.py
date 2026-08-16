"""Generate additional deterministic Outlook-shaped thread fixtures.

The generated payloads deliberately vary the newly-authored message length.
They also contain realistic quoted replies so content extraction is exercised
under the same conditions as a Power Automate/Graph payload.
"""

from __future__ import annotations

import base64
import hashlib
import html
import json
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path


OUTPUT_DIRECTORY = Path(__file__).parent
FUNCTION_URI = (
    "https://<your-function-app>.azurewebsites.net/"
    "api/threadEscalationEngine?code=<function-key>"
)


def clean(value: str) -> str:
    return textwrap.dedent(value).strip()


def expected(
    status: str = "none",
    kind: str | None = None,
    target: str | None = None,
    tier2_override: bool = False,
) -> dict:
    return {
        "status": status,
        "kind": kind,
        "requestedTarget": target,
        "tier2Override": tier2_override,
    }


def customer(text: str, at_hours: float, escalation=None, **options) -> dict:
    return {
        "role": "customer",
        "text": clean(text),
        "atHours": at_hours,
        "expectedEscalation": escalation or expected(),
        **options,
    }


def engineer(text: str, at_hours: float, **options) -> dict:
    return {
        "role": "engineer",
        "text": clean(text),
        "atHours": at_hours,
        **options,
    }


def automatic(text: str, at_hours: float, **options) -> dict:
    return {
        "role": "automatic",
        "text": clean(text),
        "atHours": at_hours,
        **options,
    }


SHORT_SCENARIOS = [
    {
        "key": "short_generic_escalation",
        "language": "en",
        "subject": "Card verification loop - TrackingID#2701010001000001",
        "customer": ("Maya Reed", "maya.reed@contoso-retail.com"),
        "engineer": ("Owen Price", "owen.price@microsoft.com"),
        "intent": "A terse generic escalation must force Tier 2.",
        "messages": [
            customer("My card keeps failing verification.", 0),
            engineer("I am checking the payment profile now.", 1),
            customer("Any update?", 25),
            engineer("The validation job is still pending.", 27),
            customer(
                "Escalate this.",
                50,
                expected("active", "generic", tier2_override=True),
            ),
        ],
    },
    {
        "key": "short_manager_request",
        "language": "en",
        "subject": "Missing corrected invoice - TrackingID#2701010001000002",
        "customer": ("Eli Warren", "eli.warren@fabrikam-foods.com"),
        "engineer": ("Nina Shah", "nina.shah@microsoft.com"),
        "intent": "A short manager request without the word escalate is hierarchical.",
        "messages": [
            customer("The corrected invoice is missing.", 0),
            engineer("I requested a new invoice document.", 2),
            customer("Still nothing.", 30),
            customer(
                "I need your manager.",
                54,
                expected("active", "hierarchical", "manager", True),
            ),
        ],
    },
    {
        "key": "short_specialist_handoff",
        "language": "en",
        "subject": "Usage meter mismatch - TrackingID#2701010001000003",
        "customer": ("Jon Bell", "jon.bell@northwind-labs.com"),
        "engineer": ("Sara Kim", "sara.kim@microsoft.com"),
        "intent": "Engineering handoff is active but remains score-based.",
        "messages": [
            customer("The meter total looks wrong.", 0),
            engineer("Please share the resource ID.", 0.5),
            customer("Sent.", 1),
            engineer("I reproduced the mismatch.", 5),
            customer(
                "Please escalate this to engineering.",
                7,
                expected("active", "specialist_handoff", "engineering_team"),
            ),
        ],
    },
    {
        "key": "short_conditional",
        "language": "en",
        "subject": "Credit not visible - TrackingID#2701010001000004",
        "customer": ("Ana Costa", "ana.costa@adatum-energy.com"),
        "engineer": ("Luis Mora", "luis.mora@microsoft.com"),
        "intent": "A future escalation threat must not override routing.",
        "messages": [
            customer("Our credit disappeared.", 0),
            engineer("I am refreshing the benefit record.", 3),
            customer(
                "If it is not back today, I will escalate.",
                8,
                expected("conditional"),
            ),
        ],
    },
    {
        "key": "short_manager_false_positive",
        "language": "en",
        "subject": "Need receipt copy - TrackingID#2701010001000005",
        "customer": ("Ben Holt", "ben.holt@wingtip-toys.com"),
        "engineer": ("Iris Long", "iris.long@microsoft.com"),
        "intent": "Mentioning the customer's manager is not an escalation request.",
        "messages": [
            customer("Please resend the receipt.", 0),
            engineer("Attached is the receipt copy.", 0.25),
            customer("Thanks. My manager needed it.", 0.5),
        ],
    },
    {
        "key": "short_spanish_generic",
        "language": "es",
        "subject": "Cobro duplicado - TrackingID#2701010001000006",
        "customer": ("Lucía Vega", "lucia.vega@proseware.mx"),
        "engineer": ("Diego Luna", "diego.luna@microsoft.com"),
        "intent": "A concise Spanish generic escalation must force Tier 2.",
        "messages": [
            customer("Me cobraron dos veces.", 0),
            engineer("Estoy revisando ambas transacciones.", 2),
            customer("¿Alguna novedad?", 28),
            engineer("Aún estoy validando el segundo cargo.", 31),
            customer(
                "Necesito una escalación.",
                52,
                expected("active", "generic", tier2_override=True),
            ),
        ],
    },
    {
        "key": "short_spanish_specialist",
        "language": "es",
        "subject": "Impuesto incorrecto - TrackingID#2701010001000007",
        "customer": ("Iván Soto", "ivan.soto@cohovineyard.mx"),
        "engineer": ("Elena Ruiz", "elena.ruiz@microsoft.com"),
        "intent": "A Spanish billing handoff is not a severity override.",
        "messages": [
            customer("El impuesto no corresponde.", 0),
            engineer("Validaré el domicilio fiscal.", 4),
            customer(
                "Por favor, escálenlo con facturación.",
                25,
                expected("active", "specialist_handoff", "billing_team"),
            ),
        ],
    },
    {
        "key": "short_quoted_risk",
        "language": "en",
        "subject": "Refund status - TrackingID#2701010001000008",
        "customer": ("Noah Day", "noah.day@tailspin-farm.com"),
        "engineer": ("Amy Cole", "amy.cole@microsoft.com"),
        "intent": "A calm reply must ignore escalation language in quoted history.",
        "messages": [
            customer(
                "Please escalate this refund to your manager now.",
                0,
                expected("active", "hierarchical", "manager", True),
            ),
            engineer("I obtained approval and submitted the refund.", 5),
            customer("Perfect, thank you.", 8),
        ],
    },
]


MIXED_SCENARIOS = [
    {
        "key": "mixed_progressive_frustration",
        "language": "en",
        "subject": "EA commitment applied to wrong enrollment - TrackingID#2702020002000001",
        "customer": ("Rachel Flynn", "rachel.flynn@litware-finance.com"),
        "engineer": ("Tom Becker", "tom.becker@microsoft.com"),
        "intent": "General escalation risk grows over messages without an explicit request.",
        "messages": [
            customer(
                "Our commitment appears under the retired enrollment instead of the new billing account. Can you verify the mapping?",
                0,
            ),
            engineer(
                "I can see the old enrollment reference. I will compare the transfer records and confirm whether a backend correction is required.",
                3,
            ),
            customer("Checking in because finance closes the month tomorrow. Do you have a timeline?", 27),
            engineer("The transfer record is with the commerce operations queue. I expect their review within two business days.", 31),
            customer(
                "Two more business days passed and there is still no timeline or correction. The committed spend is being reported in the wrong entity and our controller is asking why this remains unresolved.",
                82,
            ),
        ],
    },
    {
        "key": "mixed_generic_polite",
        "language": "en",
        "subject": "Refund exception review - TrackingID#2702020002000002",
        "customer": ("Paul Ng", "paul.ng@blueyonder-air.com"),
        "engineer": ("Mina Fox", "mina.fox@microsoft.com"),
        "intent": "A polite passive generic request still overrides to Tier 2.",
        "messages": [
            customer(
                "We purchased the reservation under the wrong tenant this morning. No workloads have used it, so I am requesting a refund exception.",
                0,
            ),
            engineer(
                "The standard self-service exchange window is closed for this offer. I am checking whether the unused purchase qualifies for a manual review.",
                4,
            ),
            customer(
                "Thank you for checking. Given that the reservation is untouched and the amount is significant, could this case be escalated?",
                28,
                expected("active", "generic", tier2_override=True),
            ),
        ],
    },
    {
        "key": "mixed_security_handoff",
        "language": "en",
        "subject": "Unknown marketplace purchase - TrackingID#2702020002000003",
        "customer": ("Kim Wells", "kim.wells@citypower.example"),
        "engineer": ("Raj Patel", "raj.patel@microsoft.com"),
        "intent": "A security-team handoff is specialist routing, not a hierarchy request.",
        "messages": [
            customer(
                "An unfamiliar marketplace purchase appeared on our invoice. The purchaser field points to an account we disabled last month.",
                0,
            ),
            engineer(
                "I have placed the invoice item under review. Please confirm whether the object ID belonged to an employee or service principal.",
                2,
            ),
            customer(
                "It belonged to a former contractor and should no longer have access. Please escalate this to the security team so they can validate whether the credential was reused.",
                6,
                expected("active", "specialist_handoff", "security_team"),
            ),
        ],
    },
    {
        "key": "mixed_hierarchy_without_escalate",
        "language": "en",
        "subject": "Subscription reactivation delayed - TrackingID#2702020002000004",
        "customer": ("Derek Moss", "derek.moss@graphicdesign.example"),
        "engineer": ("June Park", "june.park@microsoft.com"),
        "intent": "A request to speak with a supervisor forces Tier 2.",
        "messages": [
            customer("Payment cleared yesterday, but our production subscription is still disabled.", 0),
            engineer("The balance is cleared. I have started a manual entitlement refresh.", 1),
            automatic("I am currently out of the office and will return tomorrow.", 9),
            customer(
                "The refresh did not restore access and our overnight processing is blocked. I would like to speak with a supervisor who can authorize the next recovery step.",
                18,
                expected("active", "hierarchical", "supervisor", True),
            ),
        ],
    },
    {
        "key": "mixed_historical_escalation",
        "language": "en",
        "subject": "Tax exemption review - TrackingID#2702020002000005",
        "customer": ("Olivia Stone", "olivia.stone@humongous-insurance.com"),
        "engineer": ("Leo Grant", "leo.grant@microsoft.com"),
        "intent": "Acknowledging a completed escalation is historical only.",
        "messages": [
            customer(
                "Our exemption certificate was accepted in the portal, but sales tax still appears on the latest invoice.",
                0,
            ),
            engineer(
                "The certificate is valid. I escalated the effective-date mismatch to the tax operations team and they corrected the account record.",
                8,
            ),
            customer(
                "Thanks for escalating it. The corrected invoice is now visible and the tax line has been removed.",
                11,
                expected("historical"),
            ),
        ],
    },
    {
        "key": "mixed_spanish_manager",
        "language": "es",
        "subject": "Suscripción cancelada sigue facturando - TrackingID#2702020002000006",
        "customer": ("Sofía Reyes", "sofia.reyes@treyresearch.mx"),
        "engineer": ("Hugo Díaz", "hugo.diaz@microsoft.com"),
        "intent": "A Spanish manager request buried after context forces Tier 2.",
        "messages": [
            customer(
                "Cancelamos la suscripción el mes pasado, pero el nuevo estado de cuenta todavía incluye consumo posterior a la fecha de cancelación.",
                0,
            ),
            engineer(
                "La suscripción está cancelada. Revisaré si los cargos corresponden a uso procesado con retraso o a un error de cierre.",
                5,
            ),
            customer(
                "Ya envié la fecha exacta y los identificadores de los recursos dos veces. Necesito hablar con su gerente porque seguimos recibiendo la misma explicación sin una corrección.",
                54,
                expected("active", "hierarchical", "manager", True),
            ),
        ],
    },
    {
        "key": "mixed_spanish_conditional",
        "language": "es",
        "subject": "Saldo de patrocinio sin aplicar - TrackingID#2702020002000007",
        "customer": ("Mateo Gil", "mateo.gil@nonprofit-example.org"),
        "engineer": ("Clara Nieto", "clara.nieto@microsoft.com"),
        "intent": "A Spanish conditional threat is recorded without override.",
        "messages": [
            customer(
                "El portal muestra saldo disponible, pero la factura cobró el consumo completo a nuestra tarjeta.",
                0,
            ),
            engineer(
                "La oferta está activa. Estoy verificando por qué el beneficio no se aplicó al perfil de facturación.",
                6,
            ),
            customer(
                "Necesitamos cerrar el mes esta semana. Si no recibimos una corrección antes del viernes, vamos a escalar el caso.",
                29,
                expected("conditional"),
            ),
        ],
    },
    {
        "key": "mixed_negated_escalation",
        "language": "en",
        "subject": "Budget alert delivery - TrackingID#2702020002000008",
        "customer": ("Wes Ford", "wes.ford@wideworldimporters.com"),
        "engineer": ("Ada Young", "ada.young@microsoft.com"),
        "intent": "Explicitly declining escalation must not trigger routing.",
        "messages": [
            customer(
                "Our budget alerts reach the owner but not the finance distribution list. Could you check the action-group configuration?",
                0,
            ),
            engineer(
                "The distribution list was configured as an ARM role receiver, which only resolves individual role assignments. I changed it to an email receiver.",
                2,
            ),
            customer(
                "That fixed it. We do not need to escalate this; both test alerts reached finance successfully.",
                3,
                expected("negated"),
            ),
        ],
    },
]


LONG_SCENARIOS = [
    {
        "key": "long_calm_technical",
        "language": "en",
        "subject": "Cost analysis export differs from invoice - TrackingID#2703030003000001",
        "customer": ("Grace Liu", "grace.liu@alpine-ski.example"),
        "engineer": ("Marco Hill", "marco.hill@microsoft.com"),
        "intent": "Long technical detail must remain low risk when language is calm.",
        "messages": [
            customer(
                """
                We are reconciling the July invoice against our daily Cost Management export. The invoice total is 18,421.73 USD, while the sum of the amortized-cost rows for the same billing period is 18,097.21 USD. I filtered to the same billing profile, excluded purchases and refunds, and converted all timestamps to UTC before grouping. The remaining difference appears mostly under bandwidth and support charges. Could you confirm whether those charge types are intentionally absent from the amortized export, or whether I should use a different cost field for invoice reconciliation? There is no production impact; we are trying to document the correct accounting method before month-end.
                """,
                0,
            ),
            engineer(
                """
                Your comparison method is mostly correct. The amortized-cost export spreads reservation purchases and can omit certain invoice-level adjustments that are not resource usage. I will map the difference by charge type and send you the exact query needed to reproduce the invoiced total. In the meantime, please keep the invoice currency rather than converting the rows through the pricing-currency column, because those can differ for some agreements.
                """,
                5,
            ),
            customer(
                """
                That makes sense. I reran the query using invoice currency and added the pricing-model and charge-type columns. The difference is now down to the support plan and a small tax adjustment, which matches your explanation. When you have the sample query, please send it so we can add it to our internal runbook. This is not time-sensitive anymore, and the invoice can proceed through approval while we document the reconciliation steps.
                """,
                28,
            ),
        ],
    },
    {
        "key": "long_manager_at_end",
        "language": "en",
        "subject": "Production reservation exchange blocked - TrackingID#2703030003000002",
        "customer": ("Martin Webb", "martin.webb@fourthcoffee.example"),
        "engineer": ("Priya Nair", "priya.nair@microsoft.com"),
        "intent": "A hierarchy request at the end of a long message must be detected.",
        "messages": [
            customer(
                """
                Last Thursday we exchanged twelve D-series reservations after the sizing review recommended moving the workload to E-series. The portal accepted eleven exchanges, but the final reservation remains in a failed state even though it is still charging against the original scope. We supplied the purchase order, reservation order ID, target SKU, region, and screenshots of the portal error in the initial request. The workload migration is complete, so the unused reservation is now creating avoidable daily cost. Please review why this single item behaves differently from the other eleven and tell us whether the exchange must be completed through a backend operation.
                """,
                0,
            ),
            engineer(
                """
                I confirmed that the failed item has a stale exchange operation attached to it. I sent the reservation order and correlation ID to commerce operations so they can clear the pending state. Their normal handling time is two business days, and I will update you as soon as the operation is released.
                """,
                4,
            ),
            customer(
                """
                We are now on the fourth business day and the reservation still shows the same pending operation. Yesterday we were told the queue had accepted the request, but nobody could provide an owner, a completion estimate, or a workaround. We have already moved the production workload and are paying for capacity that cannot be applied, which makes every additional day more expensive. The technical details and correlation ID have been available since the case opened, so another request for the same information will not move this forward. Please escalate this to your manager and have someone with decision-making authority confirm the recovery plan today.
                """,
                101,
                expected("active", "hierarchical", "manager", True),
            ),
        ],
    },
    {
        "key": "long_specialist_at_end",
        "language": "en",
        "subject": "Storage transaction spike after lifecycle change - TrackingID#2703030003000003",
        "customer": ("Helen Ward", "helen.ward@consolidatedmessenger.example"),
        "engineer": ("Alex Wu", "alex.wu@microsoft.com"),
        "intent": "A long specialist request must not be confused with hierarchy.",
        "messages": [
            customer(
                """
                We changed the lifecycle policy on three archive storage accounts on August 2. The stored capacity stayed nearly flat, but transaction charges increased by roughly six times during the following forty-eight hours. We checked the diagnostic logs and can see repeated list and set-tier operations, although no application deployment occurred during that period. The policy contains one rule for blobs older than 180 days and another rule that deletes snapshots after 30 days. We need help determining whether reevaluation of the policy can generate this transaction pattern or whether another service is touching the accounts.
                """,
                0,
            ),
            engineer(
                """
                The billing meter confirms that the increase is primarily list operations. Lifecycle evaluation can perform internal scans, but I need the storage diagnostics team to correlate the request IDs with the policy run. Please send one affected account name and a six-hour UTC window so I can prepare the trace request.
                """,
                6,
            ),
            customer(
                """
                I added the account name, policy JSON, and the UTC window to the secure upload. The trace should focus on 03:00 through 09:00 on August 3, when the list-operation meter rose most sharply. We are not asking for a management escalation at this stage; we need the source of the requests identified before changing a policy that applies to retained customer records. Please escalate the technical investigation to the storage engineering team and keep the current case owner copied so the billing and diagnostic findings stay together.
                """,
                10,
                expected("active", "specialist_handoff", "other_team"),
            ),
        ],
    },
    {
        "key": "long_conditional_relationship_risk",
        "language": "en",
        "subject": "Enterprise invoice allocation unresolved - TrackingID#2703030003000004",
        "customer": ("Victor Ames", "victor.ames@contoso-pharma.example"),
        "engineer": ("Rita Singh", "rita.singh@microsoft.com"),
        "intent": "Strong relationship-risk language with a conditional escalation remains score-based.",
        "messages": [
            customer(
                """
                Since the billing profile migration, three invoice sections have been assigned to the wrong legal entities. We provided the intended ownership matrix before the migration and again when the first incorrect invoice appeared. The current structure prevents our regional teams from approving their charges and forces corporate finance to reallocate several hundred line items manually. We can tolerate a temporary reporting discrepancy, but we need a documented correction plan before the next invoice is generated.
                """,
                0,
            ),
            engineer(
                """
                I compared the matrix with the current invoice-section owners and found that the migration imported the previous department identifiers. I submitted a batch correction to billing operations. They must validate the legal-entity mapping before applying it, and I requested completion before the next billing cut.
                """,
                7,
            ),
            customer(
                """
                Another week has passed without a confirmed owner or completion date. This is the third billing cycle affected, and our auditors have now recorded the allocation failure as a control exception. We selected the enterprise agreement partly because consolidated billing was supposed to reduce manual reconciliation, yet this case has added work every month and nobody will commit to a timeline. If the ownership matrix is not corrected before Friday, we will escalate this through our account team and reconsider whether the current agreement is workable for the renewal.
                """,
                176,
                expected("conditional"),
            ),
        ],
    },
    {
        "key": "long_historical_and_quoted",
        "language": "en",
        "subject": "Marketplace refund completed - TrackingID#2703030003000005",
        "customer": ("Amber Cole", "amber.cole@schoolofart.example"),
        "engineer": ("Neil Cox", "neil.cox@microsoft.com"),
        "intent": "Resolution text must ignore both historical and quoted active requests.",
        "messages": [
            customer(
                """
                The marketplace plan was purchased by a test account during a proof of concept and was never deployed to a production resource. We disabled renewal as soon as finance noticed it, but the annual charge had already posted. The publisher confirmed in writing that they do not object to a refund and attached their authorization. Because the amount consumes most of the department's remaining annual software budget, please escalate this case to your manager for an exception review.
                """,
                0,
                expected("active", "hierarchical", "manager", True),
            ),
            engineer(
                """
                The publisher authorization was sufficient for an exception. My manager approved the request and the marketplace operations team issued the credit memo. It may take up to twenty-four hours for the adjusted balance to appear in Cost Management and the invoice portal.
                """,
                30,
            ),
            customer(
                """
                Thank you for escalating the exception and keeping us informed. The credit memo is now visible, the invoice balance matches the amount approved by the publisher, and finance has released the remaining budget for the department. No additional review is required from our side. You can close the support request after confirming that the marketplace subscription itself remains disabled, since we do not intend to reactivate it.
                """,
                52,
                expected("historical"),
            ),
        ],
    },
    {
        "key": "long_spanish_hierarchy",
        "language": "es",
        "subject": "Créditos consumidos por recurso eliminado - TrackingID#2703030003000006",
        "customer": ("Carolina Paredes", "carolina.paredes@empresa-ejemplo.mx"),
        "engineer": ("Andrés Peña", "andres.pena@microsoft.com"),
        "intent": "A long Spanish hierarchy request must force Tier 2.",
        "messages": [
            customer(
                """
                Eliminamos el clúster de pruebas el 3 de agosto y el grupo de recursos ya no aparece en el portal. Sin embargo, el reporte de costos sigue mostrando cargos diarios asociados con discos administrados y direcciones IP que pensábamos que se borrarían junto con el clúster. Revisamos las suscripciones una por una y no encontramos esos recursos con los nombres que aparecen en la exportación. Necesitamos identificar dónde permanecen antes de que se termine el saldo del patrocinio, pero por ahora solo buscamos una explicación técnica y los pasos correctos para localizarlos.
                """,
                0,
            ),
            engineer(
                """
                Los identificadores indican que dos discos y una IP quedaron en un grupo administrado diferente al que se eliminó. Estoy verificando si pertenecen a nodos que fueron reemplazados antes de borrar el clúster. Enviaré la ruta exacta de cada recurso y confirmaré si existe alguna dependencia antes de recomendar su eliminación.
                """,
                5,
            ),
            customer(
                """
                Han pasado seis días desde esa respuesta y todavía no recibimos las rutas ni una confirmación de dependencias. Mientras tanto, los cargos continúan y el crédito restante bajó lo suficiente como para poner en riesgo las cargas de producción que sí deben permanecer activas. Ya compartimos la exportación completa, los identificadores y las fechas en dos ocasiones, así que volver a pedir la misma información no es una solución. Por favor, escale este caso con su supervisora y solicite que alguien con autoridad nos dé hoy un plan y una fecha de resolución.
                """,
                149,
                expected("active", "hierarchical", "supervisor", True),
            ),
        ],
    },
    {
        "key": "long_spanish_specialist",
        "language": "es",
        "subject": "Uso no reconocido en cuenta de almacenamiento - TrackingID#2703030003000007",
        "customer": ("Jorge Cano", "jorge.cano@datos-ejemplo.mx"),
        "engineer": ("Teresa Ríos", "teresa.rios@microsoft.com"),
        "intent": "A Spanish specialist request remains score-based even in a long email.",
        "messages": [
            customer(
                """
                Detectamos un incremento de operaciones de lectura en una cuenta que normalmente solo recibe respaldos nocturnos. El cambio comenzó el lunes a las 02:00 UTC y no coincide con ninguna implementación de nuestro equipo. Las métricas muestran solicitudes desde varias direcciones y el costo diario ya es cuatro veces mayor al promedio. Rotamos las claves de acceso y detuvimos el trabajo de respaldo, pero las operaciones continuaron durante casi una hora. Queremos confirmar si se trata de un proceso interno de la plataforma o de credenciales que todavía estén activas en otro servicio.
                """,
                0,
            ),
            engineer(
                """
                Revisé los registros disponibles y las solicitudes usan autenticación de identidad administrada, no las claves que rotaron. Para conocer el recurso que posee esa identidad necesitamos correlacionar el identificador del token con los registros de la plataforma. Por favor, carguen de forma segura tres identificadores de solicitud y el intervalo exacto donde siguieron viendo tráfico.
                """,
                3,
            ),
            customer(
                """
                Ya cargamos cinco identificadores, el intervalo en UTC y una captura de las métricas. También incluimos el identificador de la suscripción para evitar otra ronda de preguntas. El acceso se detuvo, pero necesitamos saber qué identidad lo originó antes de volver a habilitar los respaldos. Por favor, escalen la investigación al equipo de seguridad; no estamos solicitando intervención de un gerente, sino una revisión especializada de los registros y recomendaciones para evitar que vuelva a ocurrir.
                """,
                9,
                expected("active", "specialist_handoff", "security_team"),
            ),
        ],
    },
    {
        "key": "long_request_in_signature",
        "language": "en",
        "subject": "Billing profile address updated - TrackingID#2703030003000008",
        "customer": ("Sam King", "sam.king@lucernepublishing.example"),
        "engineer": ("Faye Ross", "faye.ross@microsoft.com"),
        "intent": "Escalation words in a signature must not affect a calm long reply.",
        "messages": [
            customer(
                """
                We moved offices and updated the sold-to address in the billing account last week. The profile page shows the new street and postal code, but the downloadable invoice still shows the previous address. Our accounts-payable team can process this month's invoice as long as the tax registration and legal entity remain unchanged. Could you confirm whether invoice documents take effect only in the next billing cycle, and whether we need to regenerate the current document after the profile update?
                """,
                0,
            ),
            engineer(
                """
                Address changes apply to documents generated after the update and do not rewrite an invoice that has already been finalized. I requested a regenerated informational copy for your records, while the legally issued original will remain unchanged. The next invoice will use the new sold-to address automatically.
                """,
                4,
            ),
            customer(
                """
                Understood. That behavior is acceptable because the legal entity and tax registration are correct, and accounts payable has confirmed that they can use the original document. Please send the informational copy when it is available, but there is no deadline and no further action is needed for this month's payment. We will verify the address on the next invoice and reopen the case only if it still shows the old office.
                """,
                7,
                signature="Sam King\nDirector, Customer Escalation Management",
            ),
        ],
    },
]


FIXTURE_GROUPS = {
    "short": SHORT_SCENARIOS,
    "mixed": MIXED_SCENARIOS,
    "long": LONG_SCENARIOS,
}


def stable_token(*parts: str, length: int = 44) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).digest()
    encoded = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return encoded[:length]


def graph_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def compact(value: str) -> str:
    return " ".join(value.split())


def paragraphs(value: str) -> str:
    return "".join(
        f'<div class="elementToProof">{html.escape(paragraph)}</div>'
        for paragraph in value.split("\n\n")
    )


def make_html_body(message: dict, previous: dict | None, sent: datetime) -> str:
    current = paragraphs(message["text"])
    signature = ""

    if message.get("signature"):
        signature = (
            '<div id="Signature">'
            + html.escape(message["signature"]).replace("\n", "<br>")
            + "</div>"
        )

    quoted = ""

    if previous:
        quoted = (
            '<div id="appendonsend"></div><hr tabindex="-1">'
            '<div id="divRplyFwdMsg" dir="ltr">'
            f"<b>From:</b> {html.escape(previous['senderName'])} "
            f"&lt;{html.escape(previous['senderAddress'])}&gt;<br>"
            f"<b>Sent:</b> {graph_datetime(sent)}<br>"
            f"<b>Subject:</b> RE: generated fixture"
            "</div>"
            f'<div class="quotedMessage">{paragraphs(previous["text"])}</div>'
        )

    return (
        '<html><head><meta charset="utf-8"></head><body dir="ltr">'
        f"{current}{signature}{quoted}</body></html>"
    )


def make_message(
    scenario: dict,
    scenario_index: int,
    message: dict,
    message_index: int,
    base_time: datetime,
    previous: dict | None,
) -> tuple[dict, dict]:
    role = message["role"]
    sent = base_time + timedelta(hours=message["atHours"])
    customer_name, customer_address = scenario["customer"]
    engineer_name, engineer_address = scenario["engineer"]

    if role == "engineer":
        sender_name, sender_address = engineer_name, engineer_address
        recipient_name, recipient_address = customer_name, customer_address
    elif role == "automatic":
        sender_name = customer_name
        sender_address = customer_address
        recipient_name, recipient_address = engineer_name, engineer_address
    else:
        sender_name, sender_address = customer_name, customer_address
        recipient_name, recipient_address = engineer_name, engineer_address

    seed = f"{scenario['key']}:{message_index}"
    item_id = "AAMkAG" + stable_token(seed, "item", length=90)
    change_key = stable_token(seed, "change", length=24)
    subject = scenario["subject"] if message_index == 1 else f"RE: {scenario['subject']}"
    sender_info = {"name": sender_name, "address": sender_address}
    headers = []

    if role == "automatic":
        subject = f"Automatic reply: {scenario['subject']}"
        headers = [
            {"name": "Auto-Submitted", "value": "auto-replied"},
            {"name": "Precedence", "value": "auto_reply"},
        ]

    graph_message = {
        "@odata.etag": f'W/"{change_key}"',
        "id": item_id,
        "createdDateTime": graph_datetime(sent),
        "lastModifiedDateTime": graph_datetime(sent + timedelta(minutes=1)),
        "changeKey": change_key,
        "categories": [],
        "receivedDateTime": graph_datetime(sent + timedelta(minutes=1)),
        "sentDateTime": graph_datetime(sent),
        "hasAttachments": False,
        "internetMessageId": f"<{stable_token(seed, 'internet')}@fixture.example>",
        "subject": subject,
        "bodyPreview": compact(message["text"])[:255],
        "importance": message.get("importance", "normal"),
        "parentFolderId": "AAMkAG" + stable_token(seed, "folder", length=64),
        "conversationId": "AAQkAG" + stable_token(scenario["key"], "conversation", length=78),
        "conversationIndex": stable_token(scenario["key"], str(message_index), length=32),
        "isDeliveryReceiptRequested": None,
        "isReadReceiptRequested": False,
        "isRead": True,
        "isDraft": False,
        "webLink": f"https://outlook.office365.com/owa/?ItemID={item_id}",
        "inferenceClassification": "focused",
        "body": {
            "contentType": "html",
            "content": make_html_body(message, previous, sent),
        },
        "sender": {"emailAddress": sender_info},
        "from": {"emailAddress": sender_info},
        "toRecipients": [
            {
                "emailAddress": {
                    "name": recipient_name,
                    "address": recipient_address,
                }
            }
        ],
        "ccRecipients": [],
        "bccRecipients": [],
        "replyTo": [],
        "flag": {"flagStatus": "notFlagged"},
    }

    if headers:
        graph_message["internetMessageHeaders"] = headers

    previous_value = {
        "text": message["text"],
        "senderName": sender_name,
        "senderAddress": sender_address,
    }
    return graph_message, previous_value


def make_request(scenario: dict, scenario_index: int) -> tuple[dict, dict]:
    base_time = datetime(2026, 9, 1 + scenario_index, 9, tzinfo=timezone.utc)
    graph_messages = []
    previous = None
    customer_expectations = []

    for message_index, message in enumerate(scenario["messages"], start=1):
        graph_message, previous = make_message(
            scenario,
            scenario_index,
            message,
            message_index,
            base_time,
            previous,
        )
        graph_messages.append(graph_message)

        if message["role"] == "customer":
            expectation = dict(message["expectedEscalation"])
            expectation.update(
                {
                    "customerEvent": len(customer_expectations) + 1,
                    "messageStep": message_index,
                    "authoredCharacters": len(message["text"]),
                    "authoredWords": len(message["text"].split()),
                }
            )
            customer_expectations.append(expectation)

    request = {
        "uri": FUNCTION_URI,
        "method": "POST",
        "body": {"thread": graph_messages},
    }
    metadata = {
        "key": scenario["key"],
        "subject": scenario["subject"],
        "language": scenario["language"],
        "intent": scenario["intent"],
        "messageCount": len(graph_messages),
        "customerEvents": customer_expectations,
    }
    return request, metadata


def generate() -> None:
    all_expectations = {}

    for profile, scenarios in FIXTURE_GROUPS.items():
        requests = []
        expectations = []

        for scenario_index, scenario in enumerate(scenarios, start=1):
            request, metadata = make_request(scenario, scenario_index)
            requests.append(request)
            metadata["case"] = scenario_index
            expectations.append(metadata)

        filename = f"azure_billing_escalation_threads_{profile}.json"
        output_path = OUTPUT_DIRECTORY / filename
        output_path.write_text(
            json.dumps(requests, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        all_expectations[filename] = expectations

    expectations_path = OUTPUT_DIRECTORY / "additional_thread_expectations.json"
    expectations_path.write_text(
        json.dumps(all_expectations, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    generate()
