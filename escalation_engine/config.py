ESCALATION_CONFIG = {
    "topics": {
        "billing_issue": {
            "keywords": ["invoice", "billing", "charge", "refund"],
            "threshold": 3
        },
        "technical_failure": {
            "keywords": ["error", "failure", "bug", "issue", "down"],
            "threshold": 2
        },
        "urgent_request": {
            "keywords": ["urgent", "asap", "immediately", "critical"],
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