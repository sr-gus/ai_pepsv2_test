import azure.functions as func
import logging
import json
import asyncio
import re
from datetime import datetime

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# =========================================
# KEYWORD CONFIGURATION
# =========================================

TOPIC_CONFIG = {
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
}

# =========================================
# HELPERS
# =========================================

def normalize_text(thread):
    """
    Full-thread normalizer.
    Useful for sentiment/frequency/other future analyses.
    """
    text = " ".join(
        ((msg.get("subject") or "") + " " + (msg.get("preview") or ""))
        for msg in thread
    )

    return re.sub(r"[^\w\s]", " ", text.lower())


def get_latest_message(thread):
    """
    Returns the newest message in the normalized thread list.
    Expects items shaped like:
    {
        "subject": ...,
        "preview": ...,
        "from": ...,
        "received": ...
    }
    """
    valid_messages = [
        msg for msg in thread
        if isinstance(msg, dict) and msg.get("received")
    ]

    if not valid_messages:
        return thread[-1] if thread else {}

    def parse_dt(value):
        if not value:
            return datetime.min
        try:
            # Handles values like: 2026-05-17T10:00:00Z
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return datetime.min

    return max(valid_messages, key=lambda m: parse_dt(m.get("received")))


# =========================================
# ANALYSIS FUNCTIONS (STANDARD FORMAT)
# =========================================

async def analyze_sentimental(thread):
    """
    Placeholder sentimental analysis.
    Can later use normalize_text(thread) or the full thread directly.
    """
    return {
        "name": "sentimental",
        "score": 0.82,
        "label": "negative",
        "confidence": 0.9,
        "flags": ["frustration_detected"],
        "details": {}
    }


async def analyze_keywords(thread):
    """
    Topic-based keyword analysis.
    Uses ONLY the newest message in the thread.
    If at least one topic exceeds its threshold, keyword_trigger is raised.
    """
    latest_msg = get_latest_message(thread)

    # Analyze only newest message
    text = (
        (latest_msg.get("subject") or "") + " " +
        (latest_msg.get("preview") or "")
    )

    text = re.sub(r"[^\w\s]", " ", text.lower())
    words = text.split()

    topic_results = []
    triggered_topics = []
    total_matches = 0

    for topic, config in TOPIC_CONFIG.items():
        keyword_matches = 0

        for keyword in config["keywords"]:
            keyword_matches += sum(1 for w in words if w == keyword.lower())

        threshold = config["threshold"]
        triggered = keyword_matches >= threshold

        topic_result = {
            "topic": topic,
            "matches": keyword_matches,
            "threshold": threshold,
            "triggered": triggered
        }

        topic_results.append(topic_result)
        total_matches += keyword_matches

        if triggered:
            triggered_topics.append(topic)

    # OR-condition trigger: if at least one topic triggered
    overall_trigger = len(triggered_topics) > 0

    # Score based only on latest message density
    word_count = max(len(words), 1)
    raw_score = total_matches / word_count
    score = min(raw_score * 5, 1.0)

    # Label
    if overall_trigger:
        label = "triggered"
    elif score > 0.5:
        label = "moderate_signal"
    else:
        label = "low_signal"

    # Flags
    flags = []

    if overall_trigger:
        flags.append("keyword_trigger")

    if total_matches > 5:
        flags.append("high_keyword_density")

    return {
        "name": "keyword",
        "score": round(score, 2),
        "label": label,
        "flags": flags,
        "details": {
            "analyzedMessage": {
                "received": latest_msg.get("received"),
                "subject": latest_msg.get("subject"),
                "preview": latest_msg.get("preview")
            },
            "topics": topic_results,
            "triggeredTopics": triggered_topics,
            "totalMatches": total_matches,
            "wordCount": len(words)
        }
    }


async def analyze_frequency(thread):
    """
    Placeholder frequency analysis.
    Can later use received timestamps across full thread.
    """
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
            "action": "Engineer, Supervisor",
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

    if len(messages) == 0:
        return func.HttpResponse(
            json.dumps({"error": "Thread contains no valid messages"}),
            status_code=400,
            mimetype="application/json"
        )

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
    except Exception as e:
        logging.exception("Unexpected error during analysis")
        return func.HttpResponse(
            json.dumps({
                "error": "Internal analysis failure",
                "details": str(e)
            }),
            status_code=500,
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