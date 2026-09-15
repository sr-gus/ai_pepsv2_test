"""Escalation keyword configuration.

Expanded from the existing configuration to improve coverage of natural
English/Spanish wording while preserving the existing scoring weights,
thresholds, boosts, tiers, and notification behavior.
"""


ESCALATION_CONFIG = {
    'topics': {
        'billing_issue': {
            'keywords': [
                'bill',
                'billed',
                'charge',
                'charges',
                'charged',
                'payment',
                'overcharged',
                'overbilling',
                'factura',
                'cobro',
                'cargo',
                'reembolso',
                'pago',
                'billing',
                'invoice',
                'invoices',
                'refund',
                'refunded',
                'declined',
                'balance',
                'credit',
                'credits',
                'tax',
                'facturacion',
                'devolucion'
            ],
            'phrases': [
                'payment failed',
                'billing issue',
                'refund request',
                'excessive billing',
                'unrecognized charge',
                'unexpected charge',
                'did not recognize this charge',
                'past due notice',
                'billing adjustment',
                'card was declined',
                'payment method declined',
                'payment is past due',
                'unpaid invoice',
                'invoice appears unpaid',
                'outstanding balance',
                'incorrect invoice',
                'wrong invoice',
                'missing invoice',
                'reverse these charges',
                'no credit applied',
                'credit never applied',
                'full pay as you go rates',
                'credit not applied',
                'refund not received',
                'refund is pending',
                'unable to update payment method',
                'cannot update payment method',
                'tax is incorrect',
                'cargo incorrecto',
                'cobro no reconocido',
                'facturacion excesiva',
                'problema de facturacion',
                'tarjeta rechazada',
                'pago vencido',
                'factura sin pagar',
                'saldo pendiente',
                'factura incorrecta',
                'reembolso no recibido',
                'no puedo actualizar el pago',
                'charged twice',
                'charged multiple times',
                'charged too much',
                'wrong amount charged',
                'incorrect amount charged',
                'billing discrepancy',
                'invoice discrepancy',
                'unexpected invoice',
                'duplicate invoice',
                'duplicate payment',
                'refund still pending',
                'refund has not arrived',
                'refund never arrived',
                'refund has not been received',
                'payment keeps failing',
                'payment is failing',
                'payment was declined',
                'billing is incorrect',
                'billing amount is wrong',
                'incorrect billing amount',
                'credit is missing',
                'credit was not applied',
                'charged after canceling',
                'cobrado dos veces',
                'cobro duplicado',
                'monto incorrecto',
                'factura duplicada',
                'reembolso pendiente',
                'reembolso no ha llegado',
                'pago rechazado',
                'credito no aplicado'
            ],
            'patterns': [
                {
                    'value': 'invoice',
                    'pattern': '\\binvoices?\\b'
                },
                {
                    'value': 'refund',
                    'pattern': '\\brefund(?:ed|s|ing)?\\b'
                },
                {
                    'value': 'refund still not posted',
                    'pattern': '\\b(?:still\\s+no\\s+refund\\s+has\\s+posted|refund\\s+(?:has\\s+not|hasn\\s+t)\\s+posted)\\b'
                },
                {
                    'value': 'billing terminology',
                    'pattern': '\\bbill(?:ing|ed|s)?\\b'
                },
                {
                    'value': 'charge terminology',
                    'pattern': '\\bcharg(?:e|ed|es|ing)\\b'
                },
                {
                    'value': 'duplicate charge',
                    'pattern': '\\b(?:charged|billed)\\b[^.!?]{0,60}\\b(?:twice|multiple\\s+times|duplicate(?:d)?)\\b'
                },
                {
                    'value': 'payment declined',
                    'pattern': '\\b(?:card|payment|transaction)\\b[^.!?]{0,40}\\b(?:declined|rejected|failed)\\b'
                },
                {
                    'value': 'refund not received',
                    'pattern': '\\brefund\\b[^.!?]{0,60}\\b(?:not\\s+received|never\\s+received|missing|pending|not\\s+arrived|hasn\\s+t\\s+arrived)\\b'
                }
            ],
            'critical_phrases': [
                'unauthorized charge',
                'charged without authorization',
                'charged after cancellation',
                'duplicate charge',
                'unrecognized recurring charge',
                'cargo no autorizado',
                'cobro duplicado',
                'cobro recurrente no reconocido',
                'unauthorized billing',
                'unauthorized recurring charge',
                'recurring charge after cancellation',
                'billing continued after cancellation',
                'charged for a cancelled service',
                'charged for a canceled service',
                'cobro despues de cancelar',
                'facturacion despues de cancelar'
            ],
            'critical_patterns': [
                {
                    'value': 'billing continued after cancellation',
                    'pattern': '\\b(?:billed|charged)\\s+for\\b[^.!?]{0,70}\\b(?:cancelled|canceled)\\b'
                },
                {
                    'value': 'charged for deleted resources',
                    'pattern': '\\bdeleted\\b[^.!?]{0,180}\\bcharged\\b'
                },
                {
                    'value': 'material invoice discrepancy',
                    'pattern': '\\binvoice\\b[^.!?]{0,100}\\b(?:higher|discrepancy|does\\s+not\\s+match|doesn\\s+t\\s+match|different)\\b'
                }
            ],
            'threshold': 2
        },
        'technical_failure': {
            'keywords': [
                'failure',
                'failed',
                'bug',
                'outage',
                'broken',
                'blocked',
                'inaccessible',
                'falla',
                'fallo',
                'problema',
                'bloqueado',
                'caido',
                'caida',
                'failing',
                'error',
                'errors',
                'unavailable',
                'unavailability',
                'disruption',
                'disruptions',
                'disrupted',
                'degraded',
                'degradation',
                'crash',
                'crashed',
                'crashing',
                'timeout',
                'timeouts',
                'malfunction',
                'malfunctioning',
                'interruption',
                'interrupted',
                'indisponible',
                'interrupcion',
                'interrumpido',
                'degradado',
                'errores'
            ],
            'phrases': [
                'not working',
                'cannot access',
                "can't access",
                'cant access',
                'cannot login',
                "can't login",
                'cant login',
                'service down',
                'unable to cancel',
                'unable to create',
                'no access',
                'access denied',
                'login is failing',
                'login is constantly failing',
                'sign in issue',
                'authentication issue',
                'permission issue',
                'account level block',
                'preventing subscription creation',
                'authorization failed',
                'insufficient permissions',
                'insufficient privileges',
                'subscription not visible',
                'cannot see the subscription',
                'no subscriptions found',
                'error message',
                'system error',
                'portal error',
                'api error',
                'returned an error',
                'error code',
                'retry failed',
                'get this unblocked',
                'this is down',
                'wrong directory',
                'cannot switch directory',
                'no funciona',
                'no puedo acceder',
                'no puedo entrar',
                'no puedo cancelar',
                'no puedo crear',
                'acceso denegado',
                'fallo de inicio de sesion',
                'bloqueo de cuenta',
                'permisos insuficientes',
                'suscripcion no visible',
                'no encuentro la suscripcion',
                'directorio incorrecto',
                'sistema caido',
                'service unavailable',
                'application unavailable',
                'app unavailable',
                'system unavailable',
                'portal unavailable',
                'environment unavailable',
                'production environment unavailable',
                'production environment is down',
                'production environment is disrupted',
                'production environment is affected',
                'affecting the production environment',
                'affecting my production environment',
                'causing disruptions',
                'causing disruption',
                'production issue',
                'production failure',
                'production outage',
                'service interruption',
                'service disruption',
                'system disruption',
                'application keeps failing',
                'service keeps failing',
                'system keeps failing',
                'keeps timing out',
                'request keeps timing out',
                'portal keeps failing',
                'entorno de produccion caido',
                'entorno de produccion afectado',
                'entorno de produccion interrumpido',
                'servicio no disponible',
                'sistema no disponible',
                'interrupcion del servicio'
            ],
            'patterns': [
                {
                    'value': 'payment submission failure',
                    'pattern': '\\bsomething\\s+is\\s+wrong\\s+with\\s+how\\b[^.!?]{0,70}\\b(?:submitting|processing|sending)\\b'
                },
                {
                    'value': 'generic failure morphology',
                    'pattern': '\\b(?:fail(?:ed|ing|ure|ures)?|error(?:s)?|crash(?:ed|es|ing)?|timeout(?:s)?)\\b'
                },
                {
                    'value': 'production disruption',
                    'pattern': '\\b(?:disruption|disruptions|disrupted|interruption|interrupted)\\b[^.!?]{0,80}\\b(?:production|production\\s+environment)\\b'
                },
                {
                    'value': 'production disruption reversed',
                    'pattern': '\\b(?:production|production\\s+environment)\\b[^.!?]{0,80}\\b(?:disruption|disruptions|disrupted|interruption|interrupted|unavailable|degraded)\\b'
                },
                {
                    'value': 'resource unavailable',
                    'pattern': '\\b(?:service|application|app|portal|system|database|environment|workload)\\b[^.!?]{0,60}\\b(?:unavailable|inaccessible|offline|down|degraded)\\b'
                },
                {
                    'value': 'cannot use resource',
                    'pattern': '\\b(?:cannot|can\\s+t|unable\\s+to)\\s+(?:access|open|use|reach|connect\\s+to)\\b[^.!?]{0,80}\\b(?:service|application|app|portal|system|database|environment|resource|subscription)\\b'
                }
            ],
            'critical_phrases': [
                'production app is down',
                'business critical outage',
                'completely preventable outage',
                'preventable outage',
                'aplicacion en produccion caida',
                'interrupcion critica del negocio',
                'production environment is down',
                'production outage',
                'critical production outage',
                'critical production failure',
                'production services are down',
                'production services unavailable',
                'production system is down',
                'production disruption affecting customers',
                'entorno de produccion no disponible',
                'caida de produccion'
            ],
            'critical_patterns': [
                {
                    'value': 'named service is down',
                    'pattern': '\\b(?:platform|application|app|service|services|database|environment|environments|system|workload|production)\\b[^.!?]{0,80}\\b(?:completely\\s+)?down\\b'
                },
                {
                    'value': 'production system unavailable',
                    'pattern': '\\b(?:production|prod)\\b[^.!?]{0,60}\\b(?:service|application|app|system|environment|workload)?\\b[^.!?]{0,40}\\b(?:down|offline|unavailable|inaccessible)\\b'
                }
            ],
            'threshold': 2
        },
        'urgent_request': {
            'keywords': [
                'urgent',
                'asap',
                'immediately',
                'urgente',
                'escalate',
                'inmediato',
                'inmediatamente',
                'urgently',
                'escalated',
                'escalation',
                'prioritario',
                'prioritaria'
            ],
            'phrases': [
                'as soon as possible',
                'high priority',
                'critical issue',
                'business critical',
                'please escalate',
                'escalate this',
                'want this escalated',
                'need this escalated',
                'need this reviewed',
                'can i appeal',
                'need this fixed now',
                'requesting immediate escalation',
                'immediate escalation',
                'severity 1 case',
                'drive this toward a resolution',
                'need a firm answer',
                'please reactivate',
                'please push hard',
                'necesito ayuda urgente',
                'lo antes posible',
                'alta prioridad',
                'impacto a clientes',
                'quiero que lo escalen',
                'necesito que lo escalen',
                'need this solved urgently',
                'need this resolved urgently',
                'need this fixed urgently',
                'need this addressed urgently',
                'please resolve urgently',
                'please fix urgently',
                'please address urgently',
                'requires urgent attention',
                'requires immediate attention',
                'needs immediate attention',
                'need immediate assistance',
                'need urgent assistance',
                'need urgent help',
                'please treat this as urgent',
                'please prioritize this',
                'this is time sensitive',
                'this is time-sensitive',
                'need a resolution immediately',
                'need a resolution urgently',
                'need this handled immediately',
                'need this handled urgently',
                'i need an urgent resolution',
                'we need an urgent resolution',
                'necesito una solucion urgente',
                'necesito una resolucion urgente',
                'necesito que se resuelva urgentemente',
                'requiere atencion inmediata',
                'por favor prioricen esto'
            ],
            'patterns': [
                {
                    'value': 'same-day action request',
                    'pattern': '\\b(?:i\\s+)?need\\s+(?:this|it)\\s+(?:approved|resolved|fixed|reviewed)\\s+(?:by\\s+)?today\\b'
                },
                {
                    'value': 'manager contact request',
                    'pattern': '\\b(?:i|we)\\s+(?:want|need)\\s+(?:(?:to\\s+)?(?:speak|talk)\\s+with\\s+(?:a|your)\\s+manager|a\\s+manager\\s+to\\s+(?:call|contact)\\s+(?:me|us))\\b'
                },
                {
                    'value': 'action required before payment due',
                    'pattern': '\\bneed\\s+this\\s+(?:resolved|fixed|reviewed|refunded)\\s+before\\s+(?:it|the\\s+(?:invoice|payment|bill))\\s+(?:is|s)\\s+due\\b'
                },
                {
                    'value': 'urgent resolution request',
                    'pattern': '\\b(?:i|we)\\s+need\\b[^.!?]{0,45}\\b(?:solved|resolved|fixed|addressed|handled)\\b[^.!?]{0,30}\\b(?:urgently|immediately|asap)\\b'
                },
                {
                    'value': 'urgent action request',
                    'pattern': '\\b(?:please\\s+)?(?:resolve|fix|address|handle|review)\\b[^.!?]{0,30}\\b(?:urgently|immediately|asap)\\b'
                },
                {
                    'value': 'explicit escalation request',
                    'pattern': '\\b(?:please\\s+)?(?:escalate|escalating)\\s+(?:this|the\\s+(?:case|issue|request))\\b'
                }
            ],
            'critical_phrases': [
                'critical impact',
                'production is down',
                'services are disrupted',
                'go live is blocked',
                'customer impact',
                'revenue impact',
                'produccion esta caida',
                'servicios interrumpidos',
                'impacto financiero',
                'production environment is down',
                'production outage',
                'production services are unavailable',
                'critical customer impact',
                'major customer impact',
                'active revenue impact',
                'operations are blocked',
                'business operations are blocked',
                'entorno de produccion caido',
                'impacto critico al cliente'
            ],
            'threshold': 1
        },
        'security_concern': {
            'keywords': [
                'unauthorized',
                'unrecognized',
                'fraud',
                'fraudulent',
                'suspicious',
                'impersonating',
                'compromise',
                'compromised',
                'abuse',
                'fraude',
                'fraudulento',
                'sospechoso',
                'hacked',
                'hacker',
                'breach',
                'breached',
                'phishing',
                'malicious',
                'malware',
                'stolen',
                'exposed',
                'leaked',
                'intrusion',
                'intruder',
                'hackeado',
                'vulnerado',
                'filtracion',
                'malicioso',
                'robadas'
            ],
            'phrases': [
                'without authorization',
                'did not create this tenant',
                'did not authorize',
                'no association with this tenant',
                'unrelated to our business',
                'security incident',
                'bad actor',
                'suspicious resources',
                'unknown subscription',
                'resources i did not create',
                'unfamiliar sign in',
                'no autorizado',
                'recursos sospechosos',
                'no cree este tenant',
                'suscripcion desconocida',
                'suspicious sign in',
                'suspicious login',
                'unknown login',
                'unauthorized login',
                'unauthorized sign in',
                'someone accessed my account',
                'someone accessed our account',
                'credentials compromised',
                'credentials exposed',
                'possible compromise',
                'possible breach',
                'account was hacked',
                'account may be compromised',
                'tenant i do not recognize',
                'subscription i do not recognize',
                'resource i did not create',
                'resources we did not create',
                'actividad sospechosa',
                'inicio de sesion sospechoso',
                'acceso no autorizado',
                'cuenta hackeada',
                'posible compromiso'
            ],
            'critical_phrases': [
                'unauthorized use',
                'account compromise',
                'account takeover',
                'identity theft',
                'data breach',
                'credentials were stolen',
                'uso no autorizado',
                'actividad fraudulenta',
                'robo de identidad',
                'cuenta comprometida',
                'credenciales robadas',
                'active compromise',
                'security breach',
                'customer data exposed',
                'sensitive data exposed',
                'data was leaked',
                'malicious activity',
                'phishing attack',
                'credentials compromised',
                'credentials exposed',
                'active unauthorized access',
                'brecha de seguridad',
                'datos expuestos',
                'actividad maliciosa'
            ],
            'threshold': 2,
            'patterns': [
                {
                    'value': 'unrecognized account activity',
                    'pattern': '\\b(?:i|we)\\s+(?:do\\s+not|don\\s+t|did\\s+not|didn\\s+t)\\s+(?:recognize|create|authorize)\\b[^.!?]{0,80}\\b(?:login|sign\\s+in|tenant|subscription|resource|resources|activity)\\b'
                },
                {
                    'value': 'possible account compromise',
                    'pattern': '\\b(?:account|credentials?|identity)\\b[^.!?]{0,60}\\b(?:compromised|hacked|stolen|exposed|breached)\\b'
                }
            ]
        },
        'business_impact': {
            'keywords': [
                'standstill',
                'downtime',
                'deadline',
                'rebuilding',
                'detenido',
                'inactividad',
                'disruption',
                'disruptions',
                'interruption',
                'impact',
                'impacting',
                'affected',
                'affecting',
                'delay',
                'delayed',
                'revenue',
                'blocked',
                'interrupcion',
                'impacto',
                'afectado',
                'afectando',
                'retraso'
            ],
            'phrases': [
                'at a standstill',
                'blocked on additional testing',
                'paying full price',
                'impacting our project',
                'impacting us',
                'cannot move forward',
                'rebuilding from scratch',
                'deadline will be missed',
                'unable to meet the deadline',
                'workloads are stopped',
                'cash flow',
                'live acquisition',
                'delayed our close',
                'put real strain',
                'material cost increase',
                'finance is asking questions',
                'production workload',
                'committed spend',
                'wrong term',
                'tight budget',
                'cannot keep floating',
                "can't keep floating",
                'before we can process payment',
                'problems with our ap department',
                'acquisition closing',
                'legal is asking',
                'month end close',
                'finance needs this reconciled',
                'out of pocket',
                'fixed budget',
                'a lot of money for me',
                'proyecto detenido',
                'bloqueado para continuar',
                'pagando precio completo',
                'no cumpliremos la fecha limite',
                'flujo de efectivo',
                'cierre financiero',
                'impacting production',
                'affecting production',
                'disrupting production',
                'production disruption',
                'production environment affected',
                'production environment disrupted',
                'production environment impact',
                'customer facing impact',
                'customer-facing impact',
                'customer facing outage',
                'customers are affected',
                'users are affected',
                'affecting customers',
                'impacting customers',
                'affecting users',
                'business operations affected',
                'business operations are affected',
                'unable to operate',
                'operations are blocked',
                'operations are stopped',
                'critical workload affected',
                'critical workloads affected',
                'impacting a live environment',
                'affecting a live environment',
                'causing business disruption',
                'causing production disruption',
                'deadline is at risk',
                'launch is at risk',
                'migration is at risk',
                'revenue is being affected',
                'revenue is impacted',
                'afectando produccion',
                'impactando produccion',
                'clientes afectados',
                'operaciones bloqueadas',
                'ingresos afectados'
            ],
            'critical_phrases': [
                'production impact',
                'project migration is blocked',
                'service interruption',
                'data is at risk',
                'resources are offline',
                'client critical workloads',
                'losing revenue',
                'revenue loss',
                'business critical outage',
                'affecting live client work',
                'lost critical time',
                'regulatory exposure',
                'mission critical workloads',
                'cannot afford',
                "can't afford",
                'cannot absorb',
                'impacto en produccion',
                'interrupcion del servicio',
                'datos en riesgo',
                'recursos fuera de linea',
                'production environment is impacted',
                'production environment is disrupted',
                'production environment unavailable',
                'customer facing production outage',
                'customers cannot access the service',
                'users cannot access the service',
                'business operations are stopped',
                'business operations are blocked',
                'active revenue loss',
                'losing customers',
                'critical workload is down',
                'critical workloads are down',
                'impacto critico en produccion',
                'clientes sin servicio',
                'perdida de ingresos'
            ],
            'patterns': [
                {
                    'value': 'missing resource blocks work',
                    'pattern': '\\b(?:zero|no)\\s+[^.!?]{0,50}\\bto\\s+(?:even\\s+)?(?:start|begin|continue|complete)\\b'
                },
                {
                    'value': 'production environment impacted',
                    'pattern': '\\b(?:causing|creating|resulting\\s+in)?\\s*(?:disruption|disruptions|impact|issues?)\\b[^.!?]{0,80}\\b(?:production|production\\s+environment|live\\s+environment)\\b'
                },
                {
                    'value': 'production impact reversed',
                    'pattern': '\\b(?:production|production\\s+environment|live\\s+environment)\\b[^.!?]{0,80}\\b(?:affected|impacted|disrupted|degraded|blocked|unavailable)\\b'
                },
                {
                    'value': 'customer impact',
                    'pattern': '\\b(?:customers?|clients?|users?)\\b[^.!?]{0,70}\\b(?:affected|impacted|blocked|unable|disrupted|experiencing)\\b'
                },
                {
                    'value': 'deadline at risk',
                    'pattern': '\\b(?:deadline|launch|migration|go\\s*live|deployment)\\b[^.!?]{0,60}\\b(?:at\\s+risk|blocked|delayed|missed|slipping)\\b'
                }
            ],
            'critical_patterns': [
                {
                    'value': 'material cash-flow strain',
                    'pattern': '\\bput\\s+real\\s+strain\\s+on\\b.{0,40}\\bcash\\s+flow\\b'
                },
                {
                    'value': 'material business delay',
                    'pattern': '\\b(?:nearly\\s+)?delayed\\s+our\\s+(?:close|launch|migration)\\b'
                },
                {
                    'value': 'time lost during business event',
                    'pattern': '\\bcost\\s+us\\s+(?:nearly\\s+)?(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten)\\s+(?:business\\s+)?(?:days?|weeks?|months?)\\b'
                },
                {
                    'value': 'customer environments unavailable',
                    'pattern': '\\ball\\s+(?:of\\s+)?our\\s+[^.!?]{0,45}\\b(?:environments|services|workloads)\\s+(?:are\\s+)?(?:now\\s+)?(?:inaccessible|offline|down)\\b'
                },
                {
                    'value': 'client-facing services unavailable',
                    'pattern': '\\b(?:suspended|blocked|lost)\\s+access\\s+to\\s+(?:our\\s+)?client[-\\s]facing\\s+services\\b'
                },
                {
                    'value': 'legal closing blocked',
                    'pattern': '\\bblocking\\s+(?:a\\s+)?(?:legal|acquisition)\\s+closing(?:\\s+date)?\\b'
                },
                {
                    'value': 'customer-facing production outage',
                    'pattern': '\\b(?:platform|application|app|service|database)\\b[^.!?]{0,80}\\b(?:completely\\s+)?down\\s+for\\s+customers\\b'
                },
                {
                    'value': 'continuous monetary loss',
                    'pattern': '\\bevery\\s+(?:minute|hour|day)\\b[^.!?]{0,60}\\b(?:real\\s+money|revenue|financial\\s+loss)\\b'
                },
                {
                    'value': 'material out-of-pocket amount',
                    'pattern': '\\b(?:usd\\s+)?[\\d,]+(?:\\.\\d+)?\\s+out\\s+of\\s+pocket\\b'
                },
                {
                    'value': 'material unexpected monetary hit',
                    'pattern': '\\b(?:usd\\s+)?[\\d,]+(?:\\.\\d+)?\\s+is\\s+(?:a\\s+)?(?:huge|major|significant)\\s+unexpected\\s+(?:hit|expense|cost)\\b'
                },
                {
                    'value': 'time-bound financial close',
                    'pattern': '\\bfinance\\s+needs\\b[^.!?]{0,80}\\bbefore\\s+(?:the\\s+)?month\\s+end\\s+close\\b[^.!?]{0,35}\\bin\\s+(?:\\d+|one|two|three|four|five)\\s+(?:business\\s+)?days?\\b'
                },
                {
                    'value': 'material production disruption',
                    'pattern': '\\b(?:production|live)\\b[^.!?]{0,70}\\b(?:environment|service|application|system|workload)?\\b[^.!?]{0,50}\\b(?:down|offline|unavailable|blocked|disrupted)\\b'
                },
                {
                    'value': 'customers unable to use service',
                    'pattern': '\\b(?:customers?|clients?|users?)\\b[^.!?]{0,70}\\b(?:cannot|can\\s+t|unable\\s+to)\\b[^.!?]{0,40}\\b(?:access|use|reach|connect)\\b'
                }
            ],
            'threshold': 2
        },
        'subscription_state': {
            'keywords': [
                'disabled',
                'suspended',
                'expired',
                'deactivated',
                'warned',
                'reactivate',
                'paused',
                'offline',
                'deshabilitada',
                'suspendida',
                'expirada',
                'reactivar',
                'pausados',
                'inactive',
                'terminated',
                'locked',
                'cancelled',
                'canceled',
                'desactivada',
                'inactiva',
                'cancelada',
                'bloqueada'
            ],
            'phrases': [
                'subscription was suspended',
                'subscription has expired',
                'subscription was deactivated',
                'credit has expired',
                'credit is exhausted',
                'spending limit reached',
                'reached the spending limit',
                'past due balance',
                'outstanding payment',
                'cannot reactivate',
                'reactivation failed',
                'resources are read only',
                'credito agotado',
                'limite de gasto alcanzado',
                'saldo vencido',
                'no puedo reactivar',
                'reactivacion fallida',
                'recursos de solo lectura',
                'subscription is suspended',
                'subscription is inactive',
                'subscription is deactivated',
                'subscription is locked',
                'subscription cannot be used',
                'subscription disabled unexpectedly',
                'account is disabled',
                'account was disabled',
                'account is suspended',
                'resources unavailable after suspension',
                'resources stopped working',
                'subscription shows disabled',
                'subscription shows suspended',
                'suscripcion inactiva',
                'suscripcion desactivada',
                'cuenta suspendida',
                'cuenta deshabilitada'
            ],
            'critical_phrases': [
                'subscription is disabled',
                'subscription still disabled',
                'subscription was suspended',
                'suspended access',
                'services are paused',
                'subscription was deleted',
                'resources went offline',
                'account will be deleted',
                'suscripcion deshabilitada',
                'suscripcion suspendida',
                'servicios pausados',
                'account is disabled',
                'account was disabled',
                'account is suspended',
                'subscription access revoked',
                'all resources went offline',
                'all services are paused',
                'subscription terminated unexpectedly',
                'acceso a la suscripcion revocado'
            ],
            'critical_patterns': [
                {
                    'value': 'subscription suspension',
                    'pattern': '\\bsubscription\\s+was\\s+(?:just\\s+)?suspended\\b'
                },
                {
                    'value': 'subscription disabled or suspended',
                    'pattern': '\\bsubscription\\b[^.!?]{0,50}\\b(?:disabled|suspended|deactivated|terminated|locked)\\b'
                }
            ],
            'threshold': 2
        },
        'quota_capacity': {
            'keywords': [
                'quota',
                'capacity',
                'quotaexceeded',
                'cuota',
                'capacidad',
                'quotas',
                'limits',
                'limit',
                'exhausted',
                'availability',
                'cuotas',
                'limites',
                'agotada',
                'agotado'
            ],
            'phrases': [
                'quota exceeded',
                'quota limit exceeded',
                'limit reached',
                'maximum allowed',
                'no available quota',
                'insufficient quota',
                'capacity unavailable',
                'no available capacity',
                'sku not available',
                'quota increase denied',
                'cannot increase quota',
                'subscription policy limit',
                'cuota excedida',
                'limite de cuota excedido',
                'sin cuota disponible',
                'capacidad no disponible',
                'limite alcanzado',
                'aumento de cuota rechazado',
                'quota reached',
                'quota has been reached',
                'quota request denied',
                'quota request rejected',
                'quota increase rejected',
                'capacity exhausted',
                'capacity is exhausted',
                'region has no capacity',
                'regional capacity issue',
                'sku capacity unavailable',
                'cannot deploy due to quota',
                'deployment blocked by quota',
                'quota prevents deployment',
                'capacity prevents deployment',
                'not enough capacity',
                'not enough quota',
                'insufficient capacity',
                'resource limit reached',
                'cuota agotada',
                'sin capacidad suficiente',
                'despliegue bloqueado por cuota'
            ],
            'threshold': 2,
            'patterns': [
                {
                    'value': 'quota blocks deployment',
                    'pattern': '\\b(?:quota|capacity|limit)\\b[^.!?]{0,80}\\b(?:block(?:ed|ing)?|prevent(?:s|ed|ing)?|fail(?:ed|ing)?)\\b[^.!?]{0,60}\\b(?:deploy|deployment|provision|provisioning|create|creation)\\b'
                },
                {
                    'value': 'capacity unavailable in region',
                    'pattern': '\\b(?:capacity|sku)\\b[^.!?]{0,60}\\b(?:unavailable|not\\s+available|exhausted)\\b[^.!?]{0,60}\\b(?:region|zone|location)?\\b'
                }
            ]
        },
        'transfer_ownership': {
            'keywords': [
                'stuck',
                'orphaned',
                'atascada',
                'huerfana',
                'transfer',
                'transferred',
                'transferring',
                'ownership',
                'owner',
                'pending',
                'transferencia',
                'propietario',
                'titularidad'
            ],
            'phrases': [
                'transfer failed',
                'transfer is stuck',
                'unable to transfer the subscription',
                'cannot accept the transfer',
                'transfer request expired',
                'billing owner left the organization',
                'no billing owner',
                'transfer policy blocked',
                'destination tenant rejected',
                'transferencia fallida',
                'transferencia atascada',
                'no puedo aceptar la transferencia',
                'propietario dejo la organizacion',
                'sin propietario de facturacion',
                'transfer is pending',
                'transfer still pending',
                'transfer did not complete',
                'transfer cannot be completed',
                'transfer cannot be accepted',
                'unable to accept transfer',
                'ownership transfer failed',
                'ownership transfer is stuck',
                'cannot change billing owner',
                'cannot change ownership',
                'new owner cannot accept',
                'previous owner left the company',
                'owner no longer works here',
                'transferencia pendiente',
                'transferencia no se completo',
                'no puedo cambiar el propietario'
            ],
            'critical_phrases': [
                'lost access after the transfer',
                'role assignments were removed',
                'subscription disappeared after transfer',
                'perdi acceso despues de la transferencia',
                'lost access during transfer',
                'lost access after ownership transfer',
                'subscription inaccessible after transfer',
                'resources inaccessible after transfer',
                'roles removed after transfer',
                'acceso perdido despues de la transferencia'
            ],
            'threshold': 2,
            'patterns': [
                {
                    'value': 'transfer failed or stuck',
                    'pattern': '\\b(?:transfer|ownership\\s+transfer)\\b[^.!?]{0,60}\\b(?:failed|stuck|pending|expired|rejected|blocked|not\\s+completed)\\b'
                }
            ]
        },
        'support_breakdown': {
            'keywords': [
                'unresolved',
                'ignored',
                'overdue',
                'repeatedly',
                'abandoned',
                'finally',
                'chasing',
                'silence',
                'denials',
                'ignorado',
                'atrasado',
                'repetidamente',
                'abandonado',
                'waiting',
                'pending',
                'delayed',
                'unanswered',
                'followup',
                'followups',
                'callback',
                'callbacks',
                'stalled',
                'delay',
                'esperando',
                'pendiente',
                'retrasado',
                'retrasada',
                'sinrespuesta'
            ],
            'phrases': [
                'still no response',
                'no response from support',
                'still no update',
                'waiting for days',
                'promised callback',
                'missed callback',
                'multiple support requests',
                'issue keeps happening',
                'problem keeps happening',
                'not been resolved',
                'no progress',
                'same issue again',
                'no real answer',
                'heard nothing',
                'still nothing',
                'far longer',
                'multiple follow ups',
                'no clear reason',
                'keep getting rejected',
                'keeps getting rejected',
                'no clear explanation',
                'following up again',
                'first time anyone has told me',
                'nobody flagged',
                'zero indication',
                'never considered',
                'any news',
                'still frustrated',
                'no warning',
                'should not have taken',
                "shouldn't have taken",
                'caused a lot of stress',
                'should not have had to',
                "shouldn't have had to",
                'feedback actually goes somewhere',
                'end up back here',
                "haven't heard anything",
                'have not heard anything',
                "haven't heard back",
                'have not heard back',
                'zero notice',
                'not acceptable',
                'any update',
                "that's ridiculous",
                'that is ridiculous',
                'nobody mentioned',
                'nobody told me',
                'never disclosed',
                'still inaccessible',
                'not another status update',
                'any progress',
                "email updates aren't cutting it",
                'nadie responde',
                'sigo sin respuesta',
                'sigo sin actualizacion',
                'esperando desde hace dias',
                'llamada prometida',
                'sin avances',
                'el problema continua',
                'sin respuesta real',
                'sin previo aviso',
                'no response',
                'no update',
                'still waiting',
                'waiting for an update',
                'waiting for a response',
                'no one has responded',
                'nobody has responded',
                'no one has replied',
                'nobody has replied',
                'support has not responded',
                'support stopped responding',
                'support is not responding',
                'case is still open',
                'case remains unresolved',
                'case is still unresolved',
                'issue remains unresolved',
                'still waiting for resolution',
                'still waiting for support',
                'sent multiple follow ups',
                'sent several follow ups',
                'followed up multiple times',
                'no eta',
                'no estimated time',
                'no estimated resolution time',
                'keeps being delayed',
                'keeps getting delayed',
                'nothing has changed',
                'no meaningful update',
                'no useful update',
                'no action has been taken',
                'still waiting on this',
                'still chasing this',
                'another follow up',
                'sin respuesta',
                'sin actualizacion',
                'sigo esperando',
                'caso sigue abierto',
                'caso sigue sin resolverse',
                'sin fecha de resolucion'
            ],
            'critical_phrases': [
                'waiting for weeks',
                'case closed without resolution',
                'closed without resolution',
                'bounced between teams',
                'conflicting information',
                'no resolution',
                'no timeline',
                'no firm timeline',
                'without a timeline',
                'not resolved',
                'esperando desde hace semanas',
                'sin resolucion',
                'sin fecha estimada',
                'sin plazo',
                'no se ha resuelto',
                'caso cerrado sin solucion',
                'enviado entre varios equipos',
                'informacion contradictoria',
                'weeks without a response',
                'weeks without an update',
                'support stopped responding',
                'no owner for this case',
                'case has no owner',
                'repeatedly closed without resolution',
                'multiple teams with no resolution',
                'no path to resolution',
                'sin respuesta durante semanas',
                'semanas sin actualizacion'
            ],
            'patterns': [
                {
                    'value': 'extended unresolved duration',
                    'pattern': '\\b(?:open|waiting|waited|chasing)\\s+(?:for\\s+)?(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\\s+(?:business\\s+)?(?:days?|weeks?|months?)\\b'
                },
                {
                    'value': 'ongoing issue duration',
                    'pattern': '\\b(?:this|it)\\s+(?:has|s)\\s+been\\s+going\\s+on\\s+(?:for\\s+)?(?:(?:over|almost|nearly|more\\s+than)\\s+)?(?:a|an|\\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\\s+(?:business\\s+)?(?:days?|weeks?|months?)\\b'
                },
                {
                    'value': 'silence duration',
                    'pattern': '\\b(?:i|we)\\s+(?:have\\s+not|haven\\s+t)\\s+heard\\s+back\\s+(?:for|in)\\s+(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\\s+(?:business\\s+)?(?:days?|weeks?|months?)\\b'
                },
                {
                    'value': 'additional unresolved wait',
                    'pattern': '\\bafter\\s+(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten)\\s+more\\s+(?:business\\s+)?(?:days?|weeks?)\\b'
                },
                {
                    'value': 'reported issue duration',
                    'pattern': '\\bgoing\\s+on\\s+(?:(?:over|almost|nearly|more\\s+than)\\s+)?(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\\s+(?:business\\s+)?(?:days?|weeks?|months?)\\s+since\\b'
                },
                {
                    'value': 'active disruption duration',
                    'pattern': '\\b(?:inaccessible|offline|down|suspended|blocked|without\\s+access)\\b[^.!?]{0,70}\\bfor\\s+(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten)\\s+(?:business\\s+)?(?:days?|weeks?)\\b'
                },
                {
                    'value': 'elapsed handling duration',
                    'pattern': '\\b(?:it|this)\\s+(?:has|s)\\s+(?:now\\s+)?been\\s+(?:(?:almost|nearly|over|more\\s+than)\\s+)?(?:a|an|\\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\\s+(?:business\\s+)?(?:days?|weeks?|months?)\\b'
                },
                {
                    'value': 'elapsed handling hours',
                    'pattern': '\\b(?:it|this)\\s+(?:has|s)\\s+been\\s+(?:over|more\\s+than|at\\s+least)\\s+(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|twenty\\s+four)\\s+hours\\b'
                },
                {
                    'value': 'excessive handling duration',
                    'pattern': '\\b(?:should\\s+not\\s+have\\s+|shouldn\\s+t\\s+have\\s+|has\\s+|have\\s+)?(?:taken|took|take)\\s+(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\\s+(?:business\\s+)?(?:days?|weeks?|months?)\\b'
                },
                {
                    'value': 'prolonged disruption or chasing',
                    'pattern': '\\b(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\\s+(?:business\\s+)?(?:days?|weeks?|months?)\\s+(?:of\\s+)?(?:chasing|waiting|silence|outage|delay|follow\\s+ups?)\\b'
                },
                {
                    'value': 'repeated failed handling attempts',
                    'pattern': '\\b(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten|first|second|third|fourth|fifth|multiple|several)\\s+(?:separate\\s+)?(?:denials|rejected\\s+attempts|attempts|attempt|follow\\s+ups|requests)\\b'
                },
                {
                    'value': 'repeated submission attempts',
                    'pattern': '\\b(?:submitted|tried|attempted|applied)\\b[^.!?]{0,80}\\b(?:\\d+|two|three|four|five|six|seven|eight|nine|ten)\\s+times\\b'
                },
                {
                    'value': 'repeated denial',
                    'pattern': '\\b(?:denied|rejected)\\s+for\\s+the\\s+(?:second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\\s+time\\b'
                },
                {
                    'value': 'time spent pursuing issue',
                    'pattern': '\\b(?:i|we)\\s+(?:have|ve)\\s+(?:now\\s+)?spent\\s+(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\\s+(?:business\\s+)?(?:days?|weeks?|months?)\\s+on\\s+this\\b'
                },
                {
                    'value': 'aged original request ignored',
                    'pattern': '\\boriginal\\s+(?:request|message)\\b[^.!?]{0,50}\\b(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\\s+(?:business\\s+)?(?:days?|weeks?|months?)\\s+ago\\b'
                },
                {
                    'value': 'warning was absent',
                    'pattern': '\\bwithout\\s+(?:any\\s+)?(?:real\\s+)?(?:warning|notice)\\b'
                },
                {
                    'value': 'delayed access to accountable owner',
                    'pattern': '\\b(?:\\d+|one|two|three|four|five|six|seven|eight|nine|ten)\\s+(?:days?|weeks?|months?)\\s+to\\s+(?:get|reach)\\s+(?:to\\s+)?someone\\b'
                },
                {
                    'value': 'no response or update',
                    'pattern': '\\b(?:still\\s+)?(?:no|without\\s+an?)\\s+(?:response|reply|update|answer)\\b'
                },
                {
                    'value': 'support not responding',
                    'pattern': '\\bsupport\\b[^.!?]{0,60}\\b(?:not\\s+responding|has\\s+not\\s+responded|hasn\\s+t\\s+responded|stopped\\s+responding)\\b'
                },
                {
                    'value': 'case remains unresolved',
                    'pattern': '\\b(?:case|issue|problem|request)\\b[^.!?]{0,60}\\b(?:still|remains?)\\b[^.!?]{0,25}\\b(?:open|unresolved|pending)\\b'
                }
            ],
            'critical_patterns': [
                {
                    'value': 'multi-day active disruption',
                    'pattern': '\\bday\\s+(?:\\d+|two|three|four|five|six|seven|eight|nine|ten)\\s+of\\s+(?:a\\s+)?(?:completely\\s+)?(?:preventable\\s+)?(?:outage|delay|disruption|failure)\\b'
                },
                {
                    'value': 'multi-day silence',
                    'pattern': '\\bday\\s+(?:\\d+|two|three|four|five|six|seven|eight|nine|ten)\\s+with\\s+(?:no\\s+)?(?:answer|response|update)\\b'
                }
            ],
            'threshold': 2
        },
        'customer_relationship_risk': {
            'keywords': [
                'trust',
                'confidence',
                'renewal',
                'renew',
                'competitor',
                'switching',
                'complaint',
                'relationship',
                'confianza',
                'renovacion',
                'queja'
            ],
            'phrases': [
                'confidence in this process',
                'primary cloud provider',
                'billing reliability',
                'without a backup plan',
                "not the experience i'd expect",
                'not the experience i would expect',
                'confianza en este proceso',
                'proveedor principal',
                'sin un plan de respaldo',
                'considering another provider',
                'considering switching providers',
                'considering switching',
                'switch providers',
                'move to another provider',
                'looking at other providers',
                'looking at alternatives',
                'evaluating other providers',
                'renewal is at risk',
                'renewal at risk',
                'may not renew',
                'might not renew',
                'do not plan to renew',
                'cannot rely on this service',
                'can no longer rely on this service',
                'losing confidence in this service',
                'losing trust in this process',
                'damaging our relationship',
                'hurting our relationship',
                'considerando otro proveedor',
                'considerando cambiar de proveedor',
                'renovacion en riesgo',
                'perdiendo confianza'
            ],
            'critical_phrases': [
                'damage is done',
                'damaged our trust',
                'lost our trust',
                'lost my trust',
                'lost confidence',
                'seriously reconsidering',
                'cautious about trusting',
                'formal complaint',
                'dano nuestra confianza',
                'perdimos la confianza',
                'reconsiderando seriamente',
                'switching providers',
                'moving to another provider',
                'terminating our relationship',
                'ending our relationship',
                'we will not renew',
                'i will not renew',
                'canceling our renewal',
                'cancelling our renewal',
                'moving our business elsewhere',
                'taking our business elsewhere',
                'formal executive complaint',
                'cambiando de proveedor',
                'no vamos a renovar',
                'terminando nuestra relacion'
            ],
            'critical_patterns': [
                {
                    'value': 'reconsidering vendor relationship',
                    'pattern': '\\b(?:reconsidering|reconsider)\\s+(?:whether\\s+)?(?:renewing|relying|using|our\\s+relationship)\\b'
                },
                {
                    'value': 'reviewing primary-provider status',
                    'pattern': '\\breviewing\\s+whether\\s+.{0,30}\\bremains\\s+our\\s+(?:primary|preferred)\\b'
                },
                {
                    'value': 'material loss of trust',
                    'pattern': '\\b(?:damaged|lost|shaken|eroded)\\s+(?:our|my|the)?\\s*(?:trust|confidence)\\b'
                },
                {
                    'value': 'reconsidering vendor reliance',
                    'pattern': '\\bmade\\s+us\\s+(?:seriously\\s+)?reconsider\\s+(?:renewing|relying|using)\\b'
                },
                {
                    'value': 'provider switching intent',
                    'pattern': '\\b(?:switch(?:ing)?|move|moving)\\b[^.!?]{0,50}\\b(?:provider|vendor|platform|service|business)\\b'
                },
                {
                    'value': 'renewal at risk',
                    'pattern': '\\b(?:may|might|will|do\\s+not|don\\s+t|not\\s+going\\s+to)\\b[^.!?]{0,35}\\brenew\\b'
                }
            ],
            'threshold': 2
        }
    },
    'weights': {
        'sentimental': 0.4,
        'keyword': 0.3,
        'frequency': 0.3
    },
    'boosts': {
        'keyword_trigger': 0.05,
        'rapid_followup': 0.05,
        'frustration_detected': 0.05
    },
    'tiers': {
        'tier_1_min_score': 0.5,
        'tier_2_min_score': 0.75
    },
    'notifications': {
        'missing_tracking_id': {
            'shouldNotify': False,
            'severity': 'none',
            'target': None,
            'title': 'Analysis skipped: missing TrackingID',
            'summary': 'No thread subject contains a valid numeric TrackingID.',
            'recommendedAction': 'No action required'
        },
        'exit': {
            'shouldNotify': False,
            'severity': 'none',
            'target': None,
            'title': 'No escalation required',
            'summary': 'Thread did not reach the minimum escalation score.',
            'recommendedAction': 'No action required'
        },
        'tier_1': {
            'shouldNotify': True,
            'severity': 'medium',
            'target': 'support',
            'title': 'Tier 1 escalation',
            'summary': 'Thread reached moderate escalation risk.',
            'recommendedAction': 'Review by support engineer'
        },
        'tier_2': {
            'shouldNotify': True,
            'severity': 'high',
            'target': 'supervisor',
            'title': 'Tier 2 escalation required',
            'summary': 'Thread reached high escalation risk.',
            'recommendedAction': 'Review by engineer and supervisor'
        },
        'explicit_escalation': {
            'shouldNotify': True,
            'severity': 'high',
            'target': 'supervisor',
            'title': 'Customer-requested Tier 2 escalation',
            'summary': 'Customer explicitly requested escalation; routing was applied independently of the aggregate score.',
            'recommendedAction': "Review by engineer and supervisor and acknowledge the customer's escalation request."
        }
    }
}
