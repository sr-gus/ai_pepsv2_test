import asyncio
import json
import logging
import urllib.error
import urllib.request
from typing import Any

from escalation_engine.thread.conditioning import (
    build_sentiment_transcript,
)

logger = logging.getLogger(__name__)

ENDPOINT_URL = (
    "https://bertcustomsentimentanalys-zexox."
    "eastus.inference.ml.azure.com/score"
)

# Temporal: después mover a una variable de entorno.
API_KEY = "2yrniPgXNBsRJZdRvuganlWrOdYPpZNC7rZqjoVoSjYMSKWZ94oGJQQJ99CIAAAAAAAAAAAAINFRAZMLtdb4"

REQUEST_TIMEOUT_SECONDS = 30


async def analyze_sentimental(
    raw_thread: list[Any],
) -> dict[str, Any]:
    """
    Builds the conditioned transcript and sends it to the sentiment endpoint.
    """

    if not isinstance(raw_thread, list):
        raise TypeError("raw_thread must be a list")

    conditioned = build_sentiment_transcript(raw_thread)

    full_text = getattr(conditioned, "text", "")
    analyzed_messages = getattr(conditioned, "analyzed_messages", 0)
    ignored_automatic_messages = getattr(
        conditioned,
        "automatic_messages",
        0,
    )
    included_turns = getattr(conditioned, "included_turns", 0)
    text_sources = getattr(conditioned, "text_sources", [])

    logger.info(
        (
            "Starting sentiment analysis: "
            "analyzed_messages=%s "
            "ignored_automatic_messages=%s "
            "included_turns=%s"
        ),
        analyzed_messages,
        ignored_automatic_messages,
        included_turns,
    )

    if not isinstance(full_text, str) or not full_text.strip():
        logger.warning(
            "Sentiment analysis skipped because the conditioned "
            "transcript is empty."
        )

        return {
            "name": "sentimental",
            "score": 0.0,
            "label": "neutral",
            "confidence": 0.0,
            "flags": [],
            "details": {
                "analyzedMessages": analyzed_messages,
                "ignoredAutomaticMessages": ignored_automatic_messages,
                "conditionedTurns": included_turns,
                "textSources": text_sources,
                "reason": "Conditioned transcript is empty",
            },
            "modelResponse": None,
        }

    if not API_KEY or API_KEY == "PASTE_YOUR_API_KEY_HERE":
        raise RuntimeError("The sentiment API key has not been configured")

    payload = {
        "text": full_text,
    }

    try:
        model_response = await asyncio.to_thread(
            _invoke_sentiment_endpoint,
            ENDPOINT_URL,
            API_KEY,
            payload,
        )
    except Exception:
        logger.exception("Sentiment analysis failed")
        raise

    normalized = _normalize_model_response(model_response)

    result = {
        "name": "sentimental",
        "score": normalized["score"],
        "label": normalized["label"],
        "confidence": normalized["confidence"],
        "flags": normalized["flags"],
        "details": {
            "analyzedMessages": analyzed_messages,
            "ignoredAutomaticMessages": ignored_automatic_messages,
            "conditionedTurns": included_turns,
            "textSources": text_sources,
        },
        "modelResponse": model_response,
    }

    logger.info(
        (
            "Completed sentiment analysis: "
            "score=%s label=%s confidence=%s flags=%s"
        ),
        result["score"],
        result["label"],
        result["confidence"],
        result["flags"],
    )

    return result


def _invoke_sentiment_endpoint(
    url: str,
    api_key: str,
    payload: dict[str, Any],
) -> Any:
    """
    Executes the blocking HTTP request.

    This function is called through asyncio.to_thread so urlopen does not
    block the event loop.
    """

    if not url:
        raise RuntimeError("The sentiment endpoint URL is empty")

    body = json.dumps(payload).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    request = urllib.request.Request(
        url=url,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=REQUEST_TIMEOUT_SECONDS,
        ) as response:
            status_code = response.getcode()
            response_body = response.read().decode(
                "utf-8",
                errors="replace",
            )

        if not response_body.strip():
            raise RuntimeError(
                "Sentiment endpoint returned an empty response. "
                f"HTTP status: {status_code}"
            )

        try:
            return json.loads(response_body)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Sentiment endpoint returned invalid JSON. "
                f"HTTP status: {status_code}. "
                f"Response: {_truncate(response_body)}"
            ) from error

    except urllib.error.HTTPError as error:
        error_body = error.read().decode(
            "utf-8",
            errors="replace",
        )

        request_id = (
            error.headers.get("x-ms-request-id")
            or error.headers.get("x-request-id")
            or error.headers.get("request-id")
        )

        logger.error(
            (
                "Sentiment endpoint returned an HTTP error: "
                "status=%s reason=%s request_id=%s response=%s"
            ),
            error.code,
            error.reason,
            request_id,
            _truncate(error_body),
        )

        raise RuntimeError(
            "Sentiment endpoint request failed with "
            f"HTTP {error.code}: {_truncate(error_body)}"
        ) from error

    except urllib.error.URLError as error:
        logger.error(
            "Could not connect to sentiment endpoint: %s",
            error.reason,
        )

        raise RuntimeError(
            "Could not connect to sentiment endpoint: "
            f"{error.reason}"
        ) from error

    except TimeoutError as error:
        logger.error(
            "Sentiment endpoint timed out after %s seconds",
            REQUEST_TIMEOUT_SECONDS,
        )

        raise RuntimeError(
            "Sentiment endpoint request timed out after "
            f"{REQUEST_TIMEOUT_SECONDS} seconds"
        ) from error


def _normalize_model_response(
    model_response: Any,
) -> dict[str, Any]:
    """
    Normalizes common response structures returned by inference endpoints.
    """

    candidate = model_response

    if isinstance(candidate, list):
        if not candidate:
            candidate = {}
        else:
            candidate = candidate[0]

    if isinstance(candidate, dict):
        if isinstance(candidate.get("result"), dict):
            candidate = candidate["result"]

        elif isinstance(candidate.get("prediction"), dict):
            candidate = candidate["prediction"]

        elif isinstance(candidate.get("predictions"), list):
            predictions = candidate["predictions"]
            candidate = predictions[0] if predictions else {}

    if not isinstance(candidate, dict):
        logger.warning(
            "Unexpected sentiment response type: %s",
            type(model_response).__name__,
        )
        candidate = {}

    label = str(
        candidate.get("label", "unknown")
    ).strip().lower()

    score = _safe_float(
        candidate.get("score"),
        default=0.0,
    )

    confidence 