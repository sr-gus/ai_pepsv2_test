import asyncio
import logging
from typing import Any

from escalation_engine.analyzers.frequency import analyze_frequency
from escalation_engine.analyzers.keyword import analyze_keywords
from escalation_engine.analyzers.sentimental import analyze_sentimental
from escalation_engine.notification import build_notification
from escalation_engine.request.validation import extract_thread, validate_request_body
from escalation_engine.scoring.aggregation import aggregate_results
from escalation_engine.scoring.decision import decide_escalation
from escalation_engine.thread.extractors import (
    get_case_number,
    get_sender_address,
    get_sender_name,
)
from escalation_engine.thread.selectors import (
    get_latest_engineer_message,
    get_latest_tracked_message,
    get_valid_messages,
)

logger = logging.getLogger(__name__)


async def process_thread_escalation(
    req_body: dict[str, Any]
) -> tuple[dict[str, Any], int]:
    is_valid, error_message = validate_request_body(req_body)

    if not is_valid:
        logger.warning("Request validation failed. error=%s", error_message)

        return {
            "error": error_message
        }, 400

    raw_thread = extract_thread(req_body)

    if raw_thread is None:
        logger.error("Request validation passed but thread extraction failed.")

        return {
            "error": "Unable to extract thread"
        }, 400

    valid_messages = get_valid_messages(raw_thread)

    logger.info(
        "Request validation completed. raw_thread_count=%s valid_message_count=%s",
        len(raw_thread),
        len(valid_messages)
    )

    case_number = get_case_number(get_latest_tracked_message(valid_messages))

    if case_number is None:
        logger.info("Analysis skipped: no numeric TrackingID in thread subjects.")
        decision = {
            "tier": None,
            "action": "exit",
            "reason": "Missing TrackingID in thread subjects",
            "confidence": None,
            "routingConfidence": None,
            "decisionSource": "missing_tracking_id",
            "routingOverride": False,
            "escalationRequest": None,
            "explanation": []
        }
        return {
            "messageCount": len(valid_messages),
            "analysis": {},
            "aggregation": {},
            "decision": decision,
            "notification": build_notification(decision)
        }, 200

    try:
        logger.info("Starting parallel analysis.")

        sentimental, keyword, frequency = await asyncio.wait_for(
            asyncio.gather(
                analyze_sentimental(raw_thread),
                analyze_keywords(raw_thread),
                analyze_frequency(raw_thread)
            ),
            timeout=10
        )

        logger.info("Parallel analysis completed.")

    except asyncio.TimeoutError:
        logger.error("Analysis timeout after 10 seconds.")

        return {
            "error": "Analysis timeout"
        }, 504

    except Exception as exc:
        logger.exception("Unexpected error during analysis.")

        return {
            "error": "Internal analysis failure",
            "details": str(exc)
        }, 500

    aggregate = aggregate_results(sentimental, keyword, frequency)
    decision = decide_escalation(aggregate)
    engineer_message = get_latest_engineer_message(valid_messages)
    notification = build_notification(
        decision,
        case_number=case_number,
        engineer_name=get_sender_name(engineer_message),
        engineer_email=get_sender_address(engineer_message),
    )

    response = {
        "messageCount": len(valid_messages),
        "analysis": {
            "sentimental": sentimental,
            "keyword": keyword,
            "frequency": frequency
        },
        "aggregation": aggregate,
        "decision": decision,
        "notification": notification
    }

    logger.info(
        "Thread escalation request completed. message_count=%s final_score=%s tier=%s action=%s should_notify=%s severity=%s target=%s",
        len(valid_messages),
        aggregate["score"],
        decision["tier"],
        decision["action"],
        notification["shouldNotify"],
        notification["severity"],
        notification["target"]
    )

    return response, 200
