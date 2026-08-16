ESCALATION_CONFIG = {
    "topics": {
        "billing_issue": {
            "keywords": [
                "bill", "billed", "charge", "charges", "charged",
                "payment", "overcharged", "overbilling", "factura",
                "cobro", "cargo", "reembolso", "pago"
            ],
            "phrases": [
                "payment failed", "billing issue", "refund request",
                "excessive billing", "unrecognized charge",
                "unexpected charge",
                "did not recognize this charge", "past due notice",
                "billing adjustment",
                "card was declined", "payment method declined",
                "payment is past due", "unpaid invoice",
                "invoice appears unpaid", "outstanding balance",
                "incorrect invoice", "wrong invoice", "missing invoice",
                "reverse these charges", "no credit applied",
                "credit never applied", "full pay as you go rates",
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
            "patterns": [
                {
                    "value": "invoice",
                    "pattern": r"\binvoices?\b"
                },
                {
                    "value": "refund",
                    "pattern": r"\brefund(?:ed|s|ing)?\b"
                },
                {
                    "value": "refund still not posted",
                    "pattern": r"\b(?:still\s+no\s+refund\s+has\s+posted|refund\s+(?:has\s+not|hasn\s+t)\s+posted)\b"
                }
            ],
            "critical_phrases": [
                "unauthorized charge", "charged without authorization",
                "charged after cancellation", "duplicate charge",
                "unrecognized recurring charge",
                "cargo no autorizado", "cobro duplicado",
                "cobro recurrente no reconocido"
            ],
            "critical_patterns": [
                {
                    "value": "billing continued after cancellation",
                    "pattern": r"\b(?:billed|charged)\s+for\b[^.!?]{0,70}\b(?:cancelled|canceled)\b"
                },
                {
                    "value": "charged for deleted resources",
                    "pattern": r"\bdeleted\b[^.!?]{0,180}\bcharged\b"
                },
                {
                    "value": "material invoice discrepancy",
                    "pattern": r"\binvoice\b[^.!?]{0,100}\b(?:higher|discrepancy|does\s+not\s+match|doesn\s+t\s+match|different)\b"
                }
            ],
            "threshold": 2
        },
        "technical_failure": {
            "keywords": [
                "failure", "failed", "bug",
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
                "authorization failed", "insufficient permissions",
                "insufficient privileges", "subscription not visible",
                "cannot see the subscription", "no subscriptions found",
                "error message", "system error", "portal error",
                "api error", "returned an error", "error code",
                "retry failed", "get this unblocked",
                "this is down",
                "wrong directory", "cannot switch directory",
                "no funciona", "no puedo acceder", "no puedo entrar",
                "no puedo cancelar", "no puedo crear", "acceso denegado",
                "fallo de inicio de sesion", "bloqueo de cuenta",
                "permisos insuficientes", "suscripcion no visible",
                "no encuentro la suscripcion", "directorio incorrecto",
                "sistema caido"
            ],
            "patterns": [
                {
                    "value": "payment submission failure",
                    "pattern": r"\bsomething\s+is\s+wrong\s+with\s+how\b[^.!?]{0,70}\b(?:submitting|processing|sending)\b"
                }
            ],
            "critical_phrases": [
                "production app is down", "business critical outage",
                "completely preventable outage", "preventable outage",
                "aplicacion en produccion caida",
                "interrupcion critica del negocio"
            ],
            "critical_patterns": [
                {
                    "value": "named service is down",
                    "pattern": r"\b(?:platform|application|app|service|services|database|environment|environments|system|workload|production)\b[^.!?]{0,80}\b(?:completely\s+)?down\b"
                }
            ],
            "threshold": 2
        },
        "urgent_request": {
            "keywords": [
                "urgent", "asap", "immediately", "urgente", "escalate",
                "inmediato", "inmediatamente"
            ],
            "phrases": [
                "as soon as possible", "high priority", "critical issue",
                "business critical", "please escalate", "escalate this",
                "want this escalated", "need this escalated",
                "need this reviewed", "can i appeal",
                "need this fixed now", "requesting immediate escalation",
                "immediate escalation", "severity 1 case",
                "drive this toward a resolution", "need a firm answer",
                "please reactivate", "please push hard",
                "necesito ayuda urgente", "lo antes posible", "alta prioridad",
                "impacto a clientes", "quiero que lo escalen",
                "necesito que lo escalen"
            ],
            "patterns": [
                {
                    "value": "same-day action request",
                    "pattern": r"\b(?:i\s+)?need\s+(?:this|it)\s+(?:approved|resolved|fixed|reviewed)\s+(?:by\s+)?today\b"
                },
                {
                    "value": "manager contact request",
                    "pattern": r"\b(?:i|we)\s+(?:want|need)\s+(?:(?:to\s+)?(?:speak|talk)\s+with\s+(?:a|your)\s+manager|a\s+manager\s+to\s+(?:call|contact)\s+(?:me|us))\b"
                },
                {
                    "value": "action required before payment due",
                    "pattern": r"\bneed\s+this\s+(?:resolved|fixed|reviewed|refunded)\s+before\s+(?:it|the\s+(?:invoice|payment|bill))\s+(?:is|s)\s+due\b"
                }
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
                "cash flow", "live acquisition", "delayed our close",
                "put real strain", "material cost increase",
                "finance is asking questions", "production workload",
                "committed spend", "wrong term", "tight budget",
                "cannot keep floating", "can't keep floating",
                "before we can process payment",
                "problems with our ap department",
                "acquisition closing", "legal is asking",
                "month end close", "finance needs this reconciled",
                "out of pocket", "fixed budget", "a lot of money for me",
                "proyecto detenido", "bloqueado para continuar",
                "pagando precio completo", "no cumpliremos la fecha limite",
                "flujo de efectivo", "cierre financiero"
            ],
            "critical_phrases": [
                "production impact", "project migration is blocked",
                "service interruption", "data is at risk",
                "resources are offline", "client critical workloads",
                "losing revenue", "revenue loss", "business critical outage",
                "affecting live client work",
                "lost critical time", "regulatory exposure",
                "mission critical workloads", "cannot afford",
                "can't afford", "cannot absorb",
                "impacto en produccion",
                "interrupcion del servicio", "datos en riesgo",
                "recursos fuera de linea"
            ],
            "patterns": [
                {
                    "value": "missing resource blocks work",
                    "pattern": r"\b(?:zero|no)\s+[^.!?]{0,50}\bto\s+(?:even\s+)?(?:start|begin|continue|complete)\b"
                }
            ],
            "critical_patterns": [
                {
                    "value": "material cash-flow strain",
                    "pattern": r"\bput\s+real\s+strain\s+on\b.{0,40}\bcash\s+flow\b"
                },
                {
                    "value": "material business delay",
                    "pattern": r"\b(?:nearly\s+)?delayed\s+our\s+(?:close|launch|migration)\b"
                },
                {
                    "value": "time lost during business event",
                    "pattern": r"\bcost\s+us\s+(?:nearly\s+)?(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:business\s+)?(?:days?|weeks?|months?)\b"
                },
                {
                    "value": "customer environments unavailable",
                    "pattern": r"\ball\s+(?:of\s+)?our\s+[^.!?]{0,45}\b(?:environments|services|workloads)\s+(?:are\s+)?(?:now\s+)?(?:inaccessible|offline|down)\b"
                },
                {
                    "value": "client-facing services unavailable",
                    "pattern": r"\b(?:suspended|blocked|lost)\s+access\s+to\s+(?:our\s+)?client[-\s]facing\s+services\b"
                },
                {
                    "value": "legal closing blocked",
                    "pattern": r"\bblocking\s+(?:a\s+)?(?:legal|acquisition)\s+closing(?:\s+date)?\b"
                },
                {
                    "value": "customer-facing production outage",
                    "pattern": r"\b(?:platform|application|app|service|database)\b[^.!?]{0,80}\b(?:completely\s+)?down\s+for\s+customers\b"
                },
                {
                    "value": "continuous monetary loss",
                    "pattern": r"\bevery\s+(?:minute|hour|day)\b[^.!?]{0,60}\b(?:real\s+money|revenue|financial\s+loss)\b"
                },
                {
                    "value": "material out-of-pocket amount",
                    "pattern": r"\b(?:usd\s+)?[\d,]+(?:\.\d+)?\s+out\s+of\s+pocket\b"
                },
                {
                    "value": "material unexpected monetary hit",
                    "pattern": r"\b(?:usd\s+)?[\d,]+(?:\.\d+)?\s+is\s+(?:a\s+)?(?:huge|major|significant)\s+unexpected\s+(?:hit|expense|cost)\b"
                },
                {
                    "value": "time-bound financial close",
                    "pattern": r"\bfinance\s+needs\b[^.!?]{0,80}\bbefore\s+(?:the\s+)?month\s+end\s+close\b[^.!?]{0,35}\bin\s+(?:\d+|one|two|three|four|five)\s+(?:business\s+)?days?\b"
                }
            ],
            "threshold": 2
        },
        "subscription_state": {
            "keywords": [
                "disabled", "suspended", "expired", "deactivated", "warned",
                "reactivate", "paused", "offline", "deshabilitada",
                "suspendida", "expirada", "reactivar", "pausados"
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
                "subscription was suspended", "suspended access",
                "services are paused", "subscription was deleted",
                "resources went offline", "account will be deleted",
                "suscripcion deshabilitada", "suscripcion suspendida",
                "servicios pausados"
            ],
            "critical_patterns": [
                {
                    "value": "subscription suspension",
                    "pattern": r"\bsubscription\s+was\s+(?:just\s+)?suspended\b"
                }
            ],
            "threshold": 2
        },
        "quota_capacity": {
            "keywords": [
                "quota", "capacity", "quotaexceeded", "cuota", "capacidad"
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
            "threshold": 2
        },
        "transfer_ownership": {
            "keywords": [
                "stuck", "orphaned", "atascada", "huerfana"
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
                "abandoned", "finally", "chasing", "silence", "denials",
                "ignorado", "atrasado",
                "repetidamente", "abandonado"
            ],
            "phrases": [
                "still no response", "no response from support",
                "still no update", "waiting for days",
                "promised callback", "missed callback",
                "multiple support requests", "issue keeps happening",
                "problem keeps happening", "not been resolved",
                "no progress", "same issue again", "no real answer",
                "heard nothing", "still nothing", "far longer",
                "multiple follow ups", "no clear reason",
                "keep getting rejected", "keeps getting rejected",
                "no clear explanation", "following up again",
                "first time anyone has told me", "nobody flagged",
                "zero indication", "never considered", "any news",
                "still frustrated", "no warning", "should not have taken",
                "shouldn't have taken", "caused a lot of stress",
                "should not have had to", "shouldn't have had to",
                "feedback actually goes somewhere", "end up back here",
                "haven't heard anything", "have not heard anything",
                "haven't heard back", "have not heard back",
                "zero notice", "not acceptable",
                "any update", "that's ridiculous", "that is ridiculous",
                "nobody mentioned", "nobody told me", "never disclosed",
                "still inaccessible", "not another status update",
                "any progress", "email updates aren't cutting it",
                "nadie responde",
                "sigo sin respuesta", "sigo sin actualizacion",
                "esperando desde hace dias", "llamada prometida",
                "sin avances", "el problema continua", "sin respuesta real",
                "sin previo aviso"
            ],
            "critical_phrases": [
                "waiting for weeks", "case closed without resolution",
                "closed without resolution", "bounced between teams",
                "conflicting information", "no resolution", "no timeline",
                "no firm timeline", "without a timeline", "not resolved",
                "esperando desde hace semanas", "sin resolucion",
                "sin fecha estimada", "sin plazo", "no se ha resuelto",
                "caso cerrado sin solucion", "enviado entre varios equipos",
                "informacion contradictoria"
            ],
            "patterns": [
                {
                    "value": "extended unresolved duration",
                    "pattern": r"\b(?:open|waiting|waited|chasing)\s+(?:for\s+)?(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:business\s+)?(?:days?|weeks?|months?)\b"
                },
                {
                    "value": "ongoing issue duration",
                    "pattern": r"\b(?:this|it)\s+(?:has|s)\s+been\s+going\s+on\s+(?:for\s+)?(?:(?:over|almost|nearly|more\s+than)\s+)?(?:a|an|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:business\s+)?(?:days?|weeks?|months?)\b"
                },
                {
                    "value": "silence duration",
                    "pattern": r"\b(?:i|we)\s+(?:have\s+not|haven\s+t)\s+heard\s+back\s+(?:for|in)\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:business\s+)?(?:days?|weeks?|months?)\b"
                },
                {
                    "value": "additional unresolved wait",
                    "pattern": r"\bafter\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+more\s+(?:business\s+)?(?:days?|weeks?)\b"
                },
                {
                    "value": "reported issue duration",
                    "pattern": r"\bgoing\s+on\s+(?:(?:over|almost|nearly|more\s+than)\s+)?(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:business\s+)?(?:days?|weeks?|months?)\s+since\b"
                },
                {
                    "value": "active disruption duration",
                    "pattern": r"\b(?:inaccessible|offline|down|suspended|blocked|without\s+access)\b[^.!?]{0,70}\bfor\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:business\s+)?(?:days?|weeks?)\b"
                },
                {
                    "value": "elapsed handling duration",
                    "pattern": r"\b(?:it|this)\s+(?:has|s)\s+(?:now\s+)?been\s+(?:(?:almost|nearly|over|more\s+than)\s+)?(?:a|an|\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:business\s+)?(?:days?|weeks?|months?)\b"
                },
                {
                    "value": "elapsed handling hours",
                    "pattern": r"\b(?:it|this)\s+(?:has|s)\s+been\s+(?:over|more\s+than|at\s+least)\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty\s+four)\s+hours\b"
                },
                {
                    "value": "excessive handling duration",
                    "pattern": r"\b(?:should\s+not\s+have\s+|shouldn\s+t\s+have\s+|has\s+|have\s+)?(?:taken|took|take)\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:business\s+)?(?:days?|weeks?|months?)\b"
                },
                {
                    "value": "prolonged disruption or chasing",
                    "pattern": r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:business\s+)?(?:days?|weeks?|months?)\s+(?:of\s+)?(?:chasing|waiting|silence|outage|delay|follow\s+ups?)\b"
                },
                {
                    "value": "repeated failed handling attempts",
                    "pattern": r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|first|second|third|fourth|fifth|multiple|several)\s+(?:separate\s+)?(?:denials|rejected\s+attempts|attempts|attempt|follow\s+ups|requests)\b"
                },
                {
                    "value": "repeated submission attempts",
                    "pattern": r"\b(?:submitted|tried|attempted|applied)\b[^.!?]{0,80}\b(?:\d+|two|three|four|five|six|seven|eight|nine|ten)\s+times\b"
                },
                {
                    "value": "repeated denial",
                    "pattern": r"\b(?:denied|rejected)\s+for\s+the\s+(?:second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\s+time\b"
                },
                {
                    "value": "time spent pursuing issue",
                    "pattern": r"\b(?:i|we)\s+(?:have|ve)\s+(?:now\s+)?spent\s+(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:business\s+)?(?:days?|weeks?|months?)\s+on\s+this\b"
                },
                {
                    "value": "aged original request ignored",
                    "pattern": r"\boriginal\s+(?:request|message)\b[^.!?]{0,50}\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s+(?:business\s+)?(?:days?|weeks?|months?)\s+ago\b"
                },
                {
                    "value": "warning was absent",
                    "pattern": r"\bwithout\s+(?:any\s+)?(?:real\s+)?(?:warning|notice)\b"
                },
                {
                    "value": "delayed access to accountable owner",
                    "pattern": r"\b(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:days?|weeks?|months?)\s+to\s+(?:get|reach)\s+(?:to\s+)?someone\b"
                }
            ],
            "critical_patterns": [
                {
                    "value": "multi-day active disruption",
                    "pattern": r"\bday\s+(?:\d+|two|three|four|five|six|seven|eight|nine|ten)\s+of\s+(?:a\s+)?(?:completely\s+)?(?:preventable\s+)?(?:outage|delay|disruption|failure)\b"
                },
                {
                    "value": "multi-day silence",
                    "pattern": r"\bday\s+(?:\d+|two|three|four|five|six|seven|eight|nine|ten)\s+with\s+(?:no\s+)?(?:answer|response|update)\b"
                }
            ],
            "threshold": 2
        },
        "customer_relationship_risk": {
            "keywords": [],
            "phrases": [
                "confidence in this process", "primary cloud provider",
                "billing reliability", "without a backup plan",
                "not the experience i'd expect",
                "not the experience i would expect",
                "confianza en este proceso", "proveedor principal",
                "sin un plan de respaldo"
            ],
            "critical_phrases": [
                "damage is done", "damaged our trust", "lost our trust",
                "lost my trust", "lost confidence", "seriously reconsidering",
                "cautious about trusting", "formal complaint",
                "dano nuestra confianza",
                "perdimos la confianza", "reconsiderando seriamente"
            ],
            "critical_patterns": [
                {
                    "value": "reconsidering vendor relationship",
                    "pattern": r"\b(?:reconsidering|reconsider)\s+(?:whether\s+)?(?:renewing|relying|using|our\s+relationship)\b"
                },
                {
                    "value": "reviewing primary-provider status",
                    "pattern": r"\breviewing\s+whether\s+.{0,30}\bremains\s+our\s+(?:primary|preferred)\b"
                },
                {
                    "value": "material loss of trust",
                    "pattern": r"\b(?:damaged|lost|shaken|eroded)\s+(?:our|my|the)?\s*(?:trust|confidence)\b"
                },
                {
                    "value": "reconsidering vendor reliance",
                    "pattern": r"\bmade\s+us\s+(?:seriously\s+)?reconsider\s+(?:renewing|relying|using)\b"
                }
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
        },
        "explicit_escalation": {
            "shouldNotify": True,
            "severity": "high",
            "target": "supervisor",
            "title": "Customer-requested Tier 2 escalation",
            "summary": (
                "Customer explicitly requested escalation; routing was "
                "applied independently of the aggregate score."
            ),
            "recommendedAction": (
                "Review by engineer and supervisor and acknowledge the "
                "customer's escalation request."
            )
        }
    }
}
