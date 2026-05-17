import azure.functions as func
import logging
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="threadEscalationEngine")
def threadEscalationEngine(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Processing thread escalation request")

    # 1. Validate JSON
    try:
        req_body = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON payload"}),
            status_code=400,
            mimetype="application/json"
        )

    # 2. Validate root object
    if not isinstance(req_body, dict):
        return func.HttpResponse(
            json.dumps({"error": "Request body must be a JSON object"}),
            status_code=400,
            mimetype="application/json"
        )

    # 3. Validate "thread" exists
    thread = req_body.get("thread")
    if thread is None:
        return func.HttpResponse(
            json.dumps({"error": "Missing 'thread' field"}),
            status_code=400,
            mimetype="application/json"
        )

    # 4. Validate thread type
    if not isinstance(thread, list):
        return func.HttpResponse(
            json.dumps({"error": "'thread' must be an array"}),
            status_code=400,
            mimetype="application/json"
        )

    # 5. Validate thread content
    if len(thread) == 0:
        return func.HttpResponse(
            json.dumps({"error": "Thread is empty"}),
            status_code=400,
            mimetype="application/json"
        )

    # 6. Extract basic info safely
    messages = []

    for msg in thread:
        if not isinstance(msg, dict):
            continue

        messages.append({
            "subject": msg.get("subject"),
            "preview": msg.get("bodyPreview"),
            "from": (
                msg.get("from", {})
                   .get("emailAddress", {})
                   .get("address")
            ),
            "received": msg.get("receivedDateTime")
        })

    # 7. OUTPUT (simple test response for now)
    response = {
        "messageCount": len(messages),
        "firstMessage": messages[0],
        "note": "Thread received successfully"
    }

    return func.HttpResponse(
        json.dumps(response),
        status_code=200,
        mimetype="application/json"
    )