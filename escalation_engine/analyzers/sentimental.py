import logging
from typing import Any

from escalation_engine.thread.conditioning import (
    build_sentiment_transcript,
)

logger = logging.getLogger(__name__)


async def analyze_sentimental(raw_thread: list[Any]) -> dict[str, Any]:
    """
    Placeholder sentimental analysis.

    This analyzer conditions the full accumulated thread for the future model.
    """
    conditioned = build_sentiment_transcript(raw_thread)

    logger.info(
        "Starting sentimental analysis. analyzed_message_count=%s "
        "conditioned_turn_count=%s ignored_automatic_message_count=%s",
        conditioned.analyzed_messages,
        conditioned.included_turns,
        conditioned.ignored_automatic_messages,
    )

    full_text = conditioned.text

    # Placeholder:
    # Later this full_text can be sent to a real sentiment model.
    _ = full_text

    data = {"text": full_text}

    body = str.encode(json.dumps(data))

    url = 'https://bertcustomsentimentanalys-zexox.eastus.inference.ml.azure.com/score'
    # Replace this with the primary/secondary key, AMLToken, or Microsoft Entra ID token for the endpoint
    api_key = '2yrniPgXNBsRJZdRvuganlWrOdYPpZNC7rZqjoVoSjYMSKWZ94oGJQQJ99CIAAAAAAAAAAAAINFRAZMLtdb4'
    if not api_key:
        raise Exception("A key should be provided to invoke the endpoint")


    headers = {'Content-Type':'application/json', 'Accept': 'application/json', 'Authorization':('Bearer '+ api_key)}

    req = urllib.request.Request(url, body, headers)

    try:
        response = urllib.request.urlopen(req)

        result = response.read()
        print(result)
    except urllib.error.HTTPError as error:
        print("The request failed with status code: " + str(error.code))

        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(error.read().decode("utf8", 'ignore'))

"""
    result = {
        "name": "sentimental",
        "score": 0.82,
        "label": "negative",
        "confidence": 0.9,
        "flags": ["frustration_detected"],
        "details": {
            "analyzedMessages": conditioned.analyzed_messages,
            "ignoredAutomaticMessages": (
                conditioned.ignored_automatic_messages
            ),
            "conditionedTurns": conditioned.included_turns,
            "textSources": conditioned.text_sources,
        }
    }

    logger.info(
        "Completed sentimental analysis. score=%s label=%s flags=%s",
        result["score"],
        result["label"],
        result["flags"]
    )
"""
    logger.info("Completed Sentimental analysis: "+str(result))
    
    return result
