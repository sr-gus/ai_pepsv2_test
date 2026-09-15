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


async def analyze_sentimental(
    raw_thread: list[Any],
) -> dict[str, Any]:
    """
    Analyze sentiment using the Azure ML endpoint.
    """

    conditioned = build_sentiment_transcript(raw_thread)

    logger.info(
        "Starting sentimental analysis. "
        "analyzed_message_count=%s "
        "conditioned_turn_count=%s "
        "ignored_automatic_message_count=%s",
        conditioned.analyzed_messages,
        conditioned.included_turns,
        conditioned.ignored_automatic_messages,
    )

    full_text = conditioned.text

    data = {
        "text": full_text
    }

    body = json.dumps(data).encode("utf-8")

    url = (
        "https://bertcustomsentimentanalys-zexox."
        "eastus.inference.ml.azure.com/score"
    )

    api_key = "2yrniPgXNBsRJZdRvuganlWrOdYPpZNC7rZqjoVoSjYMSKWZ94oGJQQJ99CIAAAAAAAAAAAAINFRAZMLtdb4"

    if not api_key:
        raise RuntimeError(
            "A key should be provided to invoke the endpoint"
        )

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

    def call_endpoint() -> bytes:
        try:
            with urllib.request.urlopen(
                request,
                timeout=8,
            ) as response:
                return response.read()

        except urllib.error.HTTPError as error:
            error_body = error.read().decode(
                "utf-8",
                errors="ignore",
            )

            logger.error(
                "Azure ML request failed. "
                "status_code=%s headers=%s body=%s",
                error.code,
                error.info(),
                error_body,
            )

            raise

        except urllib.error.URLError as error:
            logger.error(
                "Azure ML connection failed. reason=%s",
                error.reason,
            )

            raise

    raw_result = await asyncio.to_thread(call_endpoint)

    decoded_result = raw_result.decode("utf-8")
    result = json.loads(decoded_result)

    logger.info(
        "Completed sentimental analysis. "
        "success=%s score=%s chunks_analyzed=%s",
        result.get("success"),
        result.get("score"),
        result.get("chunks_analyzed"),
    )

    return result