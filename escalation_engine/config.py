ESCALATION_CONFIG = {
    "topics": {
        "billing_issue": {
            "keywords": [
                "invoice", "billing", "bill", "charge", "charges", "charged",
                "refund", "payment", "factura", "cobro", "cargo", "reembolso",
                "pago"
            ],
            "phrases": [
                "payment failed", "billing issue", "refund request",
                "cargo incorrecto", "problema de facturacion"
            ],
            "threshold": 3
        },
        "technical_failure": {
            "keywords": [
                "error", "failure", "failed", "bug", "issue", "down",
                "outage", "broken", "falla", "fallo", "problema", "caido",
                "caida"
            ],
            "phrases": [
                "not working", "cannot access", "can't access", "cant access",
                "cannot login", "can't login", "cant login", "service down",
                "no funciona", "no puedo acceder", "no puedo entrar",
                "sistema caido"
            ],
            "threshold": 2
        },
        "urgent_request": {
            "keywords": [
                "urgent", "asap", "immediately", "critical", "urgente",
                "critico", "inmediato", "inmediatamente", "prioridad"
            ],
            "phrases": [
                "as soon as possible", "high priority", "critical issue",
                "necesito ayuda urgente", "lo antes posible", "alta prioridad"
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
