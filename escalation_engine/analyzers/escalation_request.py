"""Context-aware classification of explicit customer escalation requests."""

import re
from typing import Any

from escalation_engine.analyzers.spelling import correct_spelling


_ACTIVE_REQUEST_PATTERNS = (
    # Direct English escalation requests.
    re.compile(r"\b(?:please|kindly)\s*,?\s*escalate\b"),
    re.compile(
        r"\b(?:can|could|would|will)\s+you\s*,?\s*"
        r"(?:please\s*,?\s*)?escalate\b"
    ),
    re.compile(
        r"\b(?:can|could|would)\s+(?:this(?:\s+(?:case|ticket|issue|request|"
        r"matter))?|it|the\s+(?:case|ticket|issue|request|matter))\s+be\s+"
        r"escalated\b"
    ),
    re.compile(
        r"\bwould\s+it\s+be\s+possible\s+to\s+escalate\b"
    ),
    re.compile(
        r"\b(?:i|we)\s+(?:want|need|would\s+like)\s+"
        r"(?:you\s+to\s+)?escalate\b"
    ),
    re.compile(
        r"\b(?:i|we)\s+(?:want|need|would\s+like)\s+"
        r"(?:this|it|the\s+(?:case|ticket|issue|request|matter))\s+"
        r"escalated\b"
    ),
    re.compile(
        r"\b(?:i|we)\s+(?:want|need|would\s+like)\s+(?:an?\s+)?"
        r"(?:(?:immediate|formal)\s+)?escalation\b"
    ),
    re.compile(
        r"\b(?:i\s+am|we\s+are)\s+asking\s+for\s+"
        r"(?:this(?:\s+(?:case|ticket|issue|request|matter))?|it|"
        r"the\s+(?:case|ticket|issue|request|matter))\s+"
        r"to\s+be\s+escalated\b"
    ),
    re.compile(
        r"\b(?:i\s+am|we\s+are)\s+requesting\s+(?:an?\s+)?"
        r"(?:(?:immediate|formal)\s+)?escalation\b"
    ),
    re.compile(
        r"\b(?:i|we)\s+request\s+(?:an?\s+)?"
        r"(?:(?:immediate|formal)\s+)?escalation\b"
    ),
    re.compile(
        r"\b(?:i|we)\s+(?:requested|have\s+requested|ve\s+requested)\s+"
        r"(?:an?\s+)?(?:(?:immediate|formal)\s+)?escalation\b"
    ),
    re.compile(
        r"\b(?:i|we)\s+(?:asked|have\s+asked|ve\s+asked)\s+"
        r"(?:you\s+)?to\s+escalate\b"
    ),
    re.compile(
        r"\b(?:this|it|the\s+(?:case|ticket|issue|request|matter))\s+"
        r"(?:needs|has)\s+to\s+be\s+escalated\b"
    ),
    re.compile(r"(?:^|[.!?;]\s*)escalate\b"),
    # English requests for hierarchy without the word "escalate".
    re.compile(
        r"\b(?:i|we)\s+(?:want|need|would\s+like)\s+to\s+"
        r"(?:speak|talk)\s+(?:directly\s+)?(?:with|to)\b"
    ),
    re.compile(
        r"\b(?:can|could|may)\s+i\s+(?:speak|talk)\s+"
        r"(?:directly\s+)?(?:with|to)\b"
    ),
    re.compile(
        r"\b(?:i|we)\s+(?:want|need|would\s+like)\s+(?:a|your|the)\s+"
        r"(?:manager|supervisor|team\s+lead|director|executive)\b"
    ),
    re.compile(
        r"\b(?:i|we)\s+(?:request|demand)\s+(?:a|your|the)\s+"
        r"(?:manager|supervisor|team\s+lead|director|executive)\b"
    ),
    re.compile(
        r"\b(?:please\s+)?(?:have|get)\s+(?:a|your|the)\s+"
        r"(?:manager|supervisor|team\s+lead|director|executive)\s+"
        r"(?:call|contact|email)\b"
    ),
    re.compile(
        r"\b(?:i|we)\s+(?:want|need|would\s+like|am\s+asking\s+for|"
        r"are\s+asking\s+for)\s+(?:someone|somebody|a\s+person)\s+with\s+"
        r"(?:decision\s+making\s+)?authority\b"
    ),
    re.compile(
        r"\b(?:please\s+)?take\s+(?:this|it|the\s+(?:case|issue|matter))\s+"
        r"(?:to\s+(?:a|the)\s+higher\s+level|higher)\b"
    ),
    # Direct Spanish escalation requests (text is accent-normalized).
    re.compile(
        r"\bpor\s+favor\s*,?\s*(?:escala|escale|escalelo|escalela|"
        r"escalen|escalenlo|escalenla|escalar)\b"
    ),
    re.compile(
        r"\b(?:puedes|puede|pueden|podrias|podria|podrian)\s+"
        r"(?:por\s+favor\s*,?\s*)?(?:escalar|escala|escalarlo|escalarla|"
        r"escalelo|escalela|escalenlo|escalenla)\b"
    ),
    re.compile(
        r"\b(?:se\s+puede|podria\s+esto|podria\s+el\s+caso)\s+"
        r"(?:ser\s+)?escalad(?:o|a)|\bse\s+puede\s+escalar\b"
    ),
    re.compile(
        r"\b(?:quiero|necesito|quisiera|queremos|necesitamos|quisieramos)\s+"
        r"(?:que\s+)?(?:(?:esto|lo|la|el\s+caso|este\s+caso|"
        r"la\s+solicitud|esta\s+solicitud|este\s+asunto)\s+)?"
        r"(?:se\s+)?(?:escale|escalen|escalado|escalada|escalar)\b"
    ),
    re.compile(
        r"\b(?:quiero|necesito|quisiera|queremos|necesitamos)\s+"
        r"(?:una\s+)?escalacion\b"
    ),
    re.compile(
        r"\b(?:solicito|solicitamos|estoy\s+solicitando|"
        r"estamos\s+solicitando)\s+(?:una\s+)?escalacion\b"
    ),
    re.compile(
        r"\b(?:solicite|solicitamos|he\s+solicitado|hemos\s+solicitado)\s+"
        r"(?:una\s+)?escalacion\b"
    ),
    re.compile(
        r"\b(?:pedi|pedimos|he\s+pedido|hemos\s+pedido)\s+"
        r"(?:que\s+)?(?:lo\s+|la\s+|esto\s+|el\s+caso\s+)?"
        r"(?:escalen|escale|se\s+escale)\b"
    ),
    re.compile(r"(?:^|[.!?;]\s*)(?:escala|escale|escalen)\b"),
    # Spanish requests for hierarchy without the word "escalar".
    re.compile(
        r"\b(?:quiero|necesito|quisiera|queremos|necesitamos)\s+"
        r"hablar\s+(?:directamente\s+)?con\b"
    ),
    re.compile(
        r"\b(?:puedo|podria|podriamos)\s+hablar\s+"
        r"(?:directamente\s+)?con\b"
    ),
    re.compile(
        r"\b(?:quiero|necesito|queremos|necesitamos)\s+(?:un|una|a\s+un|"
        r"a\s+una|su)\s+(?:gerente|supervisor|supervisora|jefe|jefa|"
        r"director|directora)\b"
    ),
    re.compile(
        r"\b(?:exijo|exigimos|solicito|solicitamos)\s+(?:hablar\s+con\s+)?"
        r"(?:un|una|su)?\s*(?:gerente|supervisor|supervisora|jefe|jefa|"
        r"director|directora)\b"
    ),
    re.compile(
        r"\b(?:que|por\s+favor)\s+(?:me|nos)\s+"
        r"(?:llame|llamen|contacte|contacten)\s+(?:un|una|su)?\s*"
        r"(?:gerente|supervisor|supervisora|jefe|jefa|director|directora)\b"
    ),
    re.compile(
        r"\b(?:quiero|necesito|queremos|necesitamos)\s+(?:hablar\s+con\s+)?"
        r"alguien\s+con\s+(?:autoridad|poder\s+de\s+decision)\b"
    ),
    re.compile(
        r"\b(?:por\s+favor\s+)?(?:lleva|lleve|lleven)\s+(?:esto|el\s+caso|"
        r"este\s+caso)\s+a\s+(?:un|el)\s+nivel\s+superior\b"
    ),
)

_HIERARCHICAL_TARGETS = (
    (
        "manager",
        re.compile(
            r"\b(?:(?:to|with)\s+(?:a|your|the)?\s*(?:manager|management)|"
            r"(?:want|need|request|demand)\s+(?:a|your|the)\s+manager|"
            r"(?:have|get)\s+(?:a|your|the)\s+manager|"
            r"(?:con|a|al)\s+(?:un|una|su|el|la)?\s*(?:gerente|gerencia)|"
            r"(?:quiero|necesito)\s+(?:un|una|a\s+un|a\s+una|su)\s+"
            r"gerente)\b"
        )
    ),
    (
        "supervisor",
        re.compile(
            r"\b(?:(?:to|with)\s+(?:a|your|the)?\s*supervisor|"
            r"(?:want|need|request|demand)\s+(?:a|your|the)\s+supervisor|"
            r"(?:con|a|al)\s+(?:un|una|su|el|la)?\s*"
            r"(?:supervisor|supervisora|supervision)|"
            r"(?:quiero|necesito|queremos|necesitamos)\s+(?:un|una|su)\s+"
            r"(?:supervisor|supervisora))\b"
        )
    ),
    (
        "team_lead",
        re.compile(
            r"\b(?:(?:to|with)\s+(?:a|your|the)?\s*"
            r"(?:team\s+lead|leadership)|(?:con|a|al)\s+"
            r"(?:un|una|su|el|la)?\s*(?:lider|liderazgo|jefe|jefa)|"
            r"(?:request|demand)\s+(?:a|your|the)\s+team\s+lead)\b"
        )
    ),
    (
        "director_or_executive",
        re.compile(
            r"\b(?:(?:to|with)\s+(?:a|your|the)?\s*(?:director|executive|"
            r"executive\s+team|senior\s+leadership)|(?:con|a|al)\s+"
            r"(?:un|una|su|el|la)?\s*(?:director|directora|direccion)|"
            r"(?:request|demand)\s+(?:a|your|the)\s+(?:director|executive))\b"
        )
    ),
    (
        "decision_maker",
        re.compile(
            r"\b(?:(?:to|with|want|need)\s+(?:a|the)?\s*(?:decision\s+"
            r"maker|someone\s+with\s+authority|person\s+with\s+authority)|"
            r"(?:want|need)\s+(?:someone|a\s+person)\s+with\s+"
            r"decision\s+making\s+authority|(?:con|a|necesito|quiero)\s+"
            r"(?:hablar\s+con\s+)?alguien\s+con\s+(?:autoridad|"
            r"poder\s+de\s+decision))\b"
        )
    ),
    (
        "tier_2_support",
        re.compile(
            r"\b(?:to|with|request|need|want)\s+(?:the\s+)?(?:tier\s*2|"
            r"tier\s+two|level\s*2|level\s+two|l2|second\s+line)\b|"
            r"\b(?:a|al|con)\s+(?:soporte\s+)?(?:nivel\s*2|segundo\s+nivel)\b"
        )
    ),
    (
        "higher_level",
        re.compile(
            r"\b(?:to|at|request|need|want)\s+(?:a|the)?\s*(?:higher|next)\s+"
            r"level\b|\b(?:a|al|solicito|necesito|quiero)\s+(?:un|el)?\s*"
            r"nivel\s+(?:superior|siguiente)\b"
        )
    ),
)

_SPECIALIST_TARGETS = (
    (
        "billing_team",
        re.compile(
            r"\b(?:(?:to|with)\s+(?:the\s+)?(?:billing|billing\s+team|"
            r"billing\s+department|billing\s+specialist)|"
            r"(?:al|a\s+la|con(?:\s+(?:el|la))?)\s+(?:equipo\s+de\s+"
            r"facturacion|departamento\s+de\s+facturacion|facturacion|"
            r"cobranza))\b"
        )
    ),
    (
        "engineering_team",
        re.compile(
            r"\b(?:(?:to|with)\s+(?:the\s+)?(?:engineering|"
            r"engineering\s+team|engineers?|technical\s+team)|"
            r"(?:al|a\s+la|con(?:\s+(?:el|la))?)\s+(?:equipo\s+de\s+"
            r"ingenieria|ingenieria|equipo\s+tecnico))\b"
        )
    ),
    (
        "product_team",
        re.compile(
            r"\b(?:(?:to|with)\s+(?:the\s+)?(?:product|product\s+team)|"
            r"(?:al|a\s+la|con(?:\s+el)?)\s+(?:equipo\s+de\s+)?producto)\b"
        )
    ),
    (
        "platform_team",
        re.compile(
            r"\b(?:(?:to|with)\s+(?:the\s+)?(?:platform|platform\s+team|"
            r"backend|backend\s+team|service\s+team)|"
            r"(?:al|a\s+la|con(?:\s+el)?)\s+"
            r"(?:equipo\s+de\s+plataforma|equipo\s+de\s+backend))\b"
        )
    ),
    (
        "security_team",
        re.compile(
            r"\b(?:(?:to|with)\s+(?:the\s+)?(?:security\s+team|"
            r"security\s+specialist|security)|(?:al|a\s+la|"
            r"con(?:\s+(?:el|la))?)\s+(?:equipo\s+de\s+seguridad|"
            r"seguridad))\b"
        )
    ),
    (
        "subscription_team",
        re.compile(
            r"\b(?:(?:to|with)\s+(?:the\s+)?(?:subscription\s+team|"
            r"subscriptions?|account|account\s+team|account\s+specialist)|"
            r"(?:al|a\s+la|con(?:\s+el)?)\s+(?:equipo\s+de\s+suscripciones|"
            r"equipo\s+de\s+cuentas))\b"
        )
    ),
    (
        "support_team",
        re.compile(
            r"\b(?:(?:to|with)\s+(?:the\s+)?(?:support|support\s+team|"
            r"specialist\s+team)|(?:al|a\s+la|con(?:\s+el)?)\s+(?:soporte|equipo\s+"
            r"de\s+soporte|equipo\s+especializado))\b"
        )
    ),
    (
        "other_team",
        re.compile(
            r"\b(?:to|with)\s+(?:the\s+)?(?:another|appropriate|correct|"
            r"relevant)\s+(?:team|department|group|queue)\b|"
            r"\b(?:al|a\s+la|con\s+el)\s+(?:otro\s+(?:equipo|departamento|"
            r"area)|equipo\s+correcto|equipo\s+adecuado|equipo\s+"
            r"correspondiente)\b|\b(?:to|with)\s+(?:the\s+)?[a-z0-9]+"
            r"(?:\s+[a-z0-9]+){0,2}\s+(?:team|department|group|queue)\b|"
            r"\b(?:al|a\s+la|con(?:\s+el)?)\s+(?:equipo|departamento|area)\s+"
            r"de\s+[a-z0-9]+(?:\s+[a-z0-9]+){0,2}\b"
        )
    ),
)

_CONDITIONAL_PATTERNS = (
    re.compile(
        r"\b(?:if|unless|in\s+case)\b[^.!?;]{0,160}\b"
        r"escalat(?:e|ed|ing|ion)\b"
    ),
    re.compile(
        r"\bescalat(?:e|ed|ing|ion)\b[^.!?;]{0,100}\b"
        r"(?:if|unless)\b"
    ),
    re.compile(
        r"\b(?:si|a\s+menos\s+que|en\s+caso\s+de\s+que)\b"
        r"[^.!?;]{0,160}\bescal(?:ar|e|en|ado|ada|acion)\b"
    ),
    re.compile(
        r"\bescal(?:ar|e|en|ado|ada|acion)\b[^.!?;]{0,100}\bsi\b"
    ),
    re.compile(
        r"\b(?:otherwise|i\s+(?:may|might|will|would|could|have\s+to)|"
        r"we\s+(?:may|might|will|would|could|have\s+to)|"
        r"considering)\b[^.!?;]{0,100}\bescalat(?:e|ed|ing|ion)\b"
    ),
    re.compile(
        r"\b(?:de\s+lo\s+contrario|podria|podriamos|voy\s+a|vamos\s+a|"
        r"tendre\s+que|tendremos\s+que|estoy\s+considerando)\b"
        r"[^.!?;]{0,100}\bescal(?:ar|e|en|ado|ada|acion)\b"
    ),
)

_NEGATED_PATTERNS = (
    re.compile(
        r"\b(?:don\s+t|do\s+not|not|never|no\s+need\s+to|avoid|without)\b"
        r"[^.!?;]{0,80}\bescalat(?:e|ed|ing|ion)\b"
    ),
    re.compile(r"\bno\s+escalation\s+(?:is\s+)?(?:needed|required)\b"),
    re.compile(
        r"\b(?:no\s+quiero|no\s+necesito|no\s+hace\s+falta|"
        r"sin\s+necesidad\s+de)\b[^.!?;]{0,80}\b"
        r"escal(?:ar|e|en|ado|ada|acion)\b"
    ),
    re.compile(
        r"\bno\s+(?:lo\s+|la\s+|esto\s+)?(?:escalar|escale|escalen)\b"
    ),
)

_MENTION_ONLY_PATTERNS = (
    re.compile(r"\bnot\s+just\s+escalate\s+internally\b"),
    re.compile(
        r"\b(?:you\s+(?:said|say|keep\s+saying)|they\s+(?:said|say))\b"
        r"[^.!?;]{0,80}\bescalat(?:e|ed|ing)\b"
    ),
)

_HISTORICAL_PATTERNS = (
    re.compile(
        r"\b(?:thank\s+you|thanks|appreciate)\b[^.!?;]{0,100}\b"
        r"escalat(?:ed|ing|ion)\b"
    ),
    re.compile(
        r"\b(?:already|previously)\b[^.!?;]{0,50}\b"
        r"escalat(?:ed|ing|ion)\b"
    ),
    re.compile(
        r"\b(?:was|were|has\s+been|have\s+been)\s+escalated\b"
    ),
    re.compile(r"\byou\s+escalated\b"),
    re.compile(
        r"\b(?:gracias|agradezco)\b[^.!?;]{0,100}\b"
        r"escal(?:ar|ado|ada|acion)\b"
    ),
    re.compile(
        r"\b(?:ya\s+fue|fue|ha\s+sido|se\s+habia)\s+"
        r"escalad(?:o|a)\b"
    ),
)

_ESCALATION_MENTION_PATTERN = re.compile(
    r"\b(?:escalat(?:e|ed|ing|ion)|escal(?:ar|e|en|ado|ada|acion))\b"
)


def classify_escalation_request(text: str) -> dict[str, Any]:
    """Classify active, contextual escalation language in normalized text."""
    matching_text, corrections = correct_spelling(text)
    result = _classify_escalation_request(matching_text)
    result['matchType'] = 'orthographic' if corrections else 'exact'
    result['spellingCorrections'] = corrections
    if corrections:
        result['originalText'] = text
        result['matchingText'] = matching_text
    return result


def _classify_escalation_request(text: str) -> dict[str, Any]:
    active_matches = []
    rejected_matches = []

    for pattern in _ACTIVE_REQUEST_PATTERNS:
        for match in pattern.finditer(text):
            context = _sentence_context(text, *match.span())
            status = _context_status(context, match.group(0))
            evidence = _clean_evidence(context)

            if status == "active":
                active_matches.append((match.start(), evidence, context))
            else:
                rejected_matches.append((match.start(), status, evidence))

    if active_matches:
        active_matches.sort(key=lambda item: item[0])
        evidence = _unique(item[1] for item in active_matches)
        contexts = [item[2] for item in active_matches]
        hierarchical_target = _find_target(
            contexts,
            _HIERARCHICAL_TARGETS
        )

        if hierarchical_target:
            return _result(
                detected=True,
                status="active",
                kind="hierarchical",
                target=hierarchical_target,
                tier2_override=True,
                evidence=evidence
            )

        specialist_target = _find_target(contexts, _SPECIALIST_TARGETS)

        if specialist_target:
            return _result(
                detected=True,
                status="active",
                kind="specialist_handoff",
                target=specialist_target,
                tier2_override=False,
                evidence=evidence
            )

        return _result(
            detected=True,
            status="active",
            kind="generic",
            target=None,
            tier2_override=True,
            evidence=evidence
        )

    contextual_match = _first_contextual_match(text)

    if contextual_match:
        status, evidence = contextual_match

        return _result(
            detected=False,
            status=status,
            kind=None,
            target=None,
            tier2_override=False,
            evidence=[evidence]
        )

    if rejected_matches:
        rejected_matches.sort(key=lambda item: item[0])
        status = rejected_matches[0][1]

        return _result(
            detected=False,
            status=status,
            kind=None,
            target=None,
            tier2_override=False,
            evidence=_unique(item[2] for item in rejected_matches)
        )

    if _ESCALATION_MENTION_PATTERN.search(text):
        return _result(
            detected=False,
            status="mentioned",
            kind=None,
            target=None,
            tier2_override=False,
            evidence=[]
        )

    return _result(
        detected=False,
        status="none",
        kind=None,
        target=None,
        tier2_override=False,
        evidence=[]
    )


def _result(
    *,
    detected: bool,
    status: str,
    kind: str | None,
    target: str | None,
    tier2_override: bool,
    evidence: list[str]
) -> dict[str, Any]:
    return {
        "detected": detected,
        "status": status,
        "kind": kind,
        "requestedTarget": target,
        "tier2Override": tier2_override,
        "routingOverride": "Tier 2" if tier2_override else None,
        "evidence": evidence,
    }


def _sentence_context(text: str, start: int, end: int) -> str:
    left_boundaries = [text.rfind(separator, 0, start) for separator in ".!?;"]
    left = max(left_boundaries) + 1
    right_candidates = [
        position
        for separator in ".!?;"
        if (position := text.find(separator, end)) >= 0
    ]
    right = min(right_candidates) if right_candidates else len(text)

    return text[left:right].strip()


def _context_status(context: str, matched_text: str) -> str:
    match_start = context.find(matched_text.strip())
    prefix = context[:max(match_start, 0)]
    suffix = context[max(match_start, 0) + len(matched_text.strip()):]

    # Hierarchy requests can omit "escalate", including Spanish "no necesito
    # un supervisor". Keep their direct negation when recovering a typo.
    if re.search(r"\b(?:no|not|never|nunca)\s*$", prefix):
        return "negated"

    if any(pattern.search(context) for pattern in _NEGATED_PATTERNS):
        return "negated"

    if any(pattern.search(context) for pattern in _HISTORICAL_PATTERNS):
        return "historical"

    if any(pattern.search(context) for pattern in _CONDITIONAL_PATTERNS):
        return "conditional"

    if re.search(
        r"\b(?:if|unless|si|a\s+menos\s+que)\b[^.!?;]{0,120}$",
        prefix
    ):
        return "conditional"

    if re.match(r"^\s*(?:if|unless|si)\b", suffix):
        return "conditional"

    return "active"


def _first_contextual_match(text: str) -> tuple[str, str] | None:
    candidates = []

    for status, patterns in (
        ("mentioned", _MENTION_ONLY_PATTERNS),
        ("negated", _NEGATED_PATTERNS),
        ("historical", _HISTORICAL_PATTERNS),
        ("conditional", _CONDITIONAL_PATTERNS),
    ):
        for pattern in patterns:
            for match in pattern.finditer(text):
                candidates.append((match.start(), status, match.group(0)))

    if not candidates:
        return None

    _, status, evidence = min(candidates, key=lambda item: item[0])
    return status, _clean_evidence(evidence)


def _find_target(contexts, target_patterns) -> str | None:
    matches = []

    for context in contexts:
        for target, pattern in target_patterns:
            match = pattern.search(context)

            if match:
                matches.append((match.start(), target))

    return min(matches, default=(0, None), key=lambda item: item[0])[1]


def _clean_evidence(value: str) -> str:
    return " ".join(value.split())


def _unique(values) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
