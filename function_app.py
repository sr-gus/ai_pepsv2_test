import json
import logging

import azure.functions as func

from escalation_engine.service import process_thread_escalation

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

logger = logging.getLogger(__name__)


@app.route(route="threadEscalationEngine")
async def thread_escalation_engine(req: func.HttpRequest) -> func.HttpResponse:
    logger.info("Thread escalation request received.")

    try:
        req_body = req.get_json()
    except ValueError:
        logger.warning("Request validation failed. Invalid JSON payload.")

        return func.HttpResponse(
            json.dumps({"error": "Invalid JSON payload"}),
            status_code=400,
            mimetype="application/json"
        )

    try:
        response_body, status_code = await process_thread_escalation(req_body)

        return func.HttpResponse(
            json.dumps(response_body),
            status_code=status_code,
            mimetype="application/json"
        )

    except Exception as exc:
        logger.exception("Unexpected error in thread escalation endpoint.")

        return func.HttpResponse(
            json.dumps({
                "error": "Internal server error",
                "details": str(exc)
            }),
            status_code=500,
            mimetype="application/json"
        )