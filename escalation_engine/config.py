ESCALATION_CONFIG = {
    "topics": {
        "billing_issue": {
            "keywords": [
                "invoice", "billing", "bill", "charge", "charges", "charged",
                "refund", "payment", "overcharged", "overbilling", "factura",
                "cobro", "cargo", "reembolso", "pago"
            ],
            "phrases": [
                "payment failed", "billing issue", "refund request",
                "excessive billing", "unrecognized charge",
                "unrecognized recurring charge", "unexpected charge",
                "did not recognize this charge", "past due notice",
                "paying full price", "billing adjustment",
                "card was declined", "payment method declined",
                "payment is past due", "unpaid invoice",
                "invoice appears unpaid", "outstanding balance",
                "incorrect invoice", "wrong invoice", "missing invoice",
                "credit not applied", "refund not received",
                "refund is pending", "unable to update payment method",
                "cannot update payment method", "tax is incorrect",
                "cargo incorrecto", "cobro no reconocido",
                "facturacion excesiva",
                "problema de facturacion", "tarjeta rechazada",
                "pago vencido", "factura sin pagar", "saldo pendiente",
                "factura incorrecta",
                "reembolso no recibido", "no puedo actualizar el pago"
            ],
            "critical_phrases": [
                "unauthorized charge", "charged without authorization",
                "charged after cancellation", "duplicate charge",
                "cargo no autorizado", "cobro duplicado"
            ],
            "threshold": 3
        },
        "technical_failure": {
            "keywords": [
                "error", "failure", "failed", "bug", "issue", "down",
                "outage", "broken", "blocked", "inaccessible", "falla",
                "fallo", "problema", "bloqueado", "caido", "caida"
            ],
            "phrases": [
                "not working", "cannot access", "can't access", "cant access",
                "cannot login", "can't login", "cant login", "service down",
                "unable to cancel", "unable to create", "no access",
                "access denied", "login is failing",
                "login is constantly failing", "sign in issue",
                "authentication issue", "permission issue",
                "account level block", "preventing subscription creation",
                "blocked on additional testing", "cannot move forward",
                "authorization failed", "insufficient permissions",
                "insufficient privileges", "subscription not visible",
                "cannot see the subscription", "no subscriptions found",
                "wrong directory", "cannot switch directory",
                "no funciona", "no puedo acceder", "no puedo entrar",
                "no puedo cancelar", "no puedo crear", "acceso denegado",
                "fallo de inicio de sesion", "bloqueo de cuenta",
                "permisos insuficientes", "suscripcion no visible",
                "no encuentro la suscripcion", "directorio incorrecto",
                "sistema caido"
            ],
            "threshold": 3
        },
        "urgent_request": {
            "keywords": [
                "urgent", "asap", "immediately", "critical", "urgente",
                "escalate", "escalated", "escalation", "pressure",
                "critico", "inmediato", "inmediatamente", "prioridad"
            ],
            "phrases": [
                "as soon as possible", "high priority", "critical issue",
                "significant pressure", "business impact",
                "still waiting for feedback", "has not responded",
                "no response", "drive this toward a resolution",
                "necesito ayuda urgente", "lo antes posible", "alta prioridad",
                "impacto a clientes"
            ],
            "critical_phrases": [
                "critical impact", "production is down",
                "services are disrupted", "go live is blocked",
                "customer impact", "revenue impact",
                "produccion esta caida", "servicios interrumpidos",
                "impacto financiero"
            ],
            "threshold": 1
        },
        "security_concern": {
            "keywords": [
                "unauthorized", "unrecognized", "fraud", "fraudulent",
                "suspicious", "impersonating", "compromise", "compromised",
                "abuse", "fraude", "fraudulento", "sospechoso"
            ],
            "phrases": [
                "without authorization",
                "did not create this tenant", "did not authorize",
                "no association with this tenant",
                "unrelated to our business", "security incident",
                "bad actor", "suspicious resources",
                "unknown subscription", "resources i did not create",
                "unfamiliar sign in", "no autorizado",
                "recursos sospechosos", "no cree este tenant",
                "suscripcion desconocida"
            ],
            "critical_phrases": [
                "unauthorized use", "account compromise", "account takeover",
                "identity theft", "data breach", "credentials were stolen",
                "uso no autorizado", "actividad fraudulenta",
                "robo de identidad", "cuenta comprometida",
                "credenciales robadas"
            ],
            "threshold": 2
        },
        "business_impact": {
            "keywords": [
                "standstill", "downtime", "deadline", "rebuilding",
                "detenido", "inactividad"
            ],
            "phrases": [
                "at a standstill", "blocked on additional testing",
                "paying full price", "impacting our project",
                "impacting us", "cannot move forward",
                "rebuilding from scratch",
                "deadline will be missed", "unable to meet the deadline",
                "workloads are stopped",
                "proyecto detenido", "bloqueado para continuar",
                "pagando precio completo", "no cumpliremos la fecha limite"
            ],
            "critical_phrases": [
                "production impact", "project migration is blocked",
                "service interruption", "data is at risk",
                "resources are offline", "impacto en produccion",
                "interrupcion del servicio", "datos en riesgo",
                "recursos fuera de linea"
            ],
            "threshold": 2
        },
        "subscription_state": {
            "keywords": [
                "disabled", "suspended", "expired", "deactivated", "warned",
                "reactivate", "reactivation", "paused", "offline",
                "deshabilitada", "suspendida", "expirada", "reactivar",
                "pausados"
            ],
            "phrases": [
                "subscription was suspended", "subscription has expired",
                "subscription was deactivated",
                "credit has expired", "credit is exhausted",
                "spending limit reached", "reached the spending limit",
                "past due balance", "outstanding payment",
                "cannot reactivate", "reactivation failed",
                "resources are read only",
                "credito agotado", "limite de gasto alcanzado",
                "saldo vencido", "no puedo reactivar",
                "reactivacion fallida",
                "recursos de solo lectura"
            ],
            "critical_phrases": [
                "subscription is disabled", "subscription still disabled",
                "services are paused", "subscription was deleted",
                "resources went offline", "account will be deleted",
                "suscripcion deshabilitada", "suscripcion suspendida",
                "servicios pausados"
            ],
            "threshold": 2
        },
        "quota_capacity": {
            "keywords": [
                "quota", "capacity", "limit", "quotaexceeded",
                "cuota", "capacidad", "limite"
            ],
            "phrases": [
                "quota exceeded", "quota limit exceeded", "limit reached",
                "maximum allowed", "no available quota",
                "insufficient quota", "capacity unavailable",
                "no available capacity", "sku not available",
                "quota increase denied", "cannot increase quota",
                "subscription policy limit", "cuota excedida",
                "limite de cuota excedido", "sin cuota disponible",
                "capacidad no disponible", "limite alcanzado",
                "aumento de cuota rechazado"
            ],
            "threshold": 3
        },
        "transfer_ownership": {
            "keywords": [
                "stuck", "rejected", "orphaned", "atascada", "rechazada",
                "huerfana"
            ],
            "phrases": [
                "transfer failed", "transfer is stuck",
                "unable to transfer the subscription",
                "cannot accept the transfer", "transfer request expired",
                "billing owner left the organization", "no billing owner",
                "transfer policy blocked", "destination tenant rejected",
                "transferencia fallida", "transferencia atascada",
                "no puedo aceptar la transferencia",
                "propietario dejo la organizacion",
                "sin propietario de facturacion"
            ],
            "critical_phrases": [
                "lost access after the transfer",
                "role assignments were removed",
                "subscription disappeared after transfer",
                "perdi acceso despues de la transferencia"
            ],
            "threshold": 2
        },
        "support_breakdown": {
            "keywords": [
                "unresolved", "ignored", "overdue", "repeatedly",
                "abandoned", "ignorado", "atrasado",
                "repetidamente", "abandonado"
            ],
            "phrases": [
                "still no response", "no response from support",
                "still no update", "waiting for days",
                "promised callback", "missed callback",
                "multiple support requests", "issue keeps happening",
                "problem keeps happening", "not been resolved",
                "no progress", "same issue again", "nadie responde",
                "sigo sin respuesta", "sigo sin actualizacion",
                "esperando desde hace dias", "llamada prometida",
                "sin avances", "el problema continua"
            ],
            "critical_phrases": [
                "waiting for weeks", "case closed without resolution",
                "closed without resolution", "bounced between teams",
                "conflicting information", "esperando desde hace semanas",
                "caso cerrado sin solucion", "enviado entre varios equipos",
                "informacion contradictoria"
            ],
            "threshold": 2
        }
    },
    "weights": {
        "sentimental": 0.4,
        "keyword": 0.3,
        "frequency": 0.3
    },
    "boosts": {
        "keyword_trigger": 0.05,
        "rapid_followup": 0.05,
        "frustration_detected": 0.05
    },
    "tiers": {
        "tier_1_min_score": 0.5,
        "tier_2_min_score": 0.75
    },
    "notifications": {
        "exit": {
            "shouldNotify": False,
            "severity": "none",
            "target": None,
            "title": "No escalation required",
            "summary": "Thread did not reach the minimum escalation score.",
            "recommendedAction": "No action required"
        },
        "tier_1": {
            "shouldNotify": True,
            "severity": "medium",
            "target": "support",
            "title": "Tier 1 escalation",
            "summary": "Thread reached moderate escalation risk.",
            "recommendedAction": "Review by support engineer"
        },
        "tier_2": {
            "shouldNotify": True,
            "severity": "high",
            "target": "supervisor",
            "title": "Tier 2 escalation required",
            "summary": "Thread reached high escalation risk.",
            "recommendedAction": "Review by engineer and supervisor"
        }
    }
}
