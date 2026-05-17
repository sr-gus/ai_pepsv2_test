import azure.functions as func
import logging
import json
import asyncio

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# =========================================
# ANALYSIS FUNCTIONS (STANDARD FORMAT)
# =========================================

async def analyze_sentimental(thread):
    return {
        "name": "sentimental",
        "score": 0.82,
        "label": "negative",
        "confidence": 0.9,
        "flags": ["frustration_detected"],
        "details": {}
    }


async def analyze_keywords(thread):
    return {
        "name": "keyword",
        "score": 0.7,
        "label": "high_keyword_density",
        "flags": ["keyword_trigger"],
        "details": {
            "keywords": ["billing", "error"],
            "matches": 5
        }
    }


async def analyze_frequency(thread):
    return {
        "name": "frequency",
        "score": 0.6,
        "label": "increasing",
        "flags": ["rapid_followup"],
        "details": {
            "messagesPerDay": len(thread),
            "ghostedHours": 24
        }
    }


# =========================================
# AGGREGATION (DETERMINANT LOGIC)
# =========================================

def aggregate_results(sentimental, keyword, frequency):
    weights = {
        "sentimental": 0.4,
        "keyword": 0.3,
        "frequency": 0.3
    }

    base_score = (
        sentimental["score"] * weights["sentimental"] +
        keyword["score"] * weights["keyword"] +
        frequency["score"] * weights["frequency"]
    )

    # Apply rule-based boosts
    boosts = 0

    if "keyword_trigger" in keyword.get("flags", []):
        boosts += 0.05

    if "rapid_followup" in frequency.get("flags", []):
        boosts += 0.05

    if "frustration_detected" in sentimental.get("flags", []):
        boosts += 0.05

    final_score = min(base_score + boosts, 1.0)

    return {
        "score": round(final_score, 2),
        "baseScore": round(base_score, 2),
        "boost": round(boosts, 2),
        "signals": [sentimental, keyword, frequency]
    }


# =========================================
# FINAL DECISION (TIER LOGIC)
# =========================================

def decide_escalation(aggregate):
    score = aggregate["score"]

    explanation = []

    for signal in aggregate["signals"]:
        if signal.get("flags"):
            explanation.extend(signal["flags"])

    if score < 0.5:
        return {
            "tier": None,
            "action": "exit",
            "reason": "Low escalation score",
            "confidence": score,
            "explanation": explanation
        }

    elif score < 0.75:
        return {
            "tier": "Tier 1",
            "action": "Only Support Engineer",
            "reason": "Moderate escalation risk",
            "confidence": score,
            "explanation": explanation
        }

    else:
        return {
            "tier": "Tier 2",
            "action": "Engineer, TA, Manager",
            "reason": "High escalation risk",
            "confidence": score,
            "explanation": explanation
        }


# =========================================
# MAIN FUNCTION
# =========================================

@app.route(route="threadEscalationEngine")
async def threadEscalationEngine(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing thread escalation request")

    # ----------------------------
    # 1. VALIDATION
    # ----------------------------
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON payload"}),
            status_code=400,
            mimetype="application/json"
        )

    thread = req_body.get("thread")

    if not isinstance(thread, list) or len(thread) == 0:
        return func.HttpResponse(
            json.dumps({"error": "'thread' must be a non-empty array"}),
            status_code=400,
            mimetype="application/json"
        )

    # ----------------------------
    # 2. NORMALIZATION
    # ----------------------------
    messages = []

    for msg in thread:
        if not isinstance(msg, dict):
            continue

        messages.append({
            "subject": msg.get("subject"),
            "preview": msg.get("bodyPreview"),
            "from": msg.get("from", {}).get("emailAddress", {}).get("address"),
            "received": msg.get("receivedDateTime")
        })

    # ----------------------------
    # 3. PARALLEL ANALYSIS
    # ----------------------------
    try:
        sentimental, keyword, frequency = await asyncio.wait_for(
            asyncio.gather(
                analyze_sentimental(messages),
                analyze_keywords(messages),
                analyze_frequency(messages)
            ),
            timeout=10
        )
    except asyncio.TimeoutError:
        return func.HttpResponse(
            json.dumps({"error": "Analysis timeout"}),
            status_code=504,
            mimetype="application/json"
        )

    # ----------------------------
    # 4. AGGREGATION
    # ----------------------------
    aggregate = aggregate_results(sentimental, keyword, frequency)

    # ----------------------------
    # 5. DECISION
    # ----------------------------
    decision = decide_escalation(aggregate)

    # ----------------------------
    # 6. FINAL RESPONSE
    # ----------------------------
    response = {
        "messageCount": len(messages),
        "analysis": {
            "sentimental": sentimental,
            "keyword": keyword,
            "frequency": frequency
        },
        "aggregation": aggregate,
        "decision": decision
    }

    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )