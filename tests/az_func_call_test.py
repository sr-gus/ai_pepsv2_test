import asyncio
import json
import os
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from escalation_engine.service import process_thread_escalation


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOTENV_PATH = PROJECT_ROOT / ".env"


def get_azure_function_endpoint() -> str:
    """Read the endpoint from the process environment or the local .env."""
    environment_value = os.getenv("AZURE_FUNCTION_ENDPOINT", "").strip()

    if environment_value:
        return environment_value

    if not DOTENV_PATH.exists():
        return ""

    for raw_line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        name, separator, value = line.partition("=")

        if separator and name.strip() == "AZURE_FUNCTION_ENDPOINT":
            return value.strip().strip('"').strip("'")

    return ""


AZURE_FUNCTION_ENDPOINT = get_azure_function_endpoint()

REQUEST_TIMEOUT_SECONDS = 30


def build_power_automate_payload() -> dict:
    """Build a stable request with the wrapper used by Power Automate."""
    received = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    return {
        "body": {
            "thread": [
                {
                    "subject": "Case update",
                    "body": {
                        "contentType": "html",
                        "content": "<p>Please escalate this case.</p>"
                    },
                    "receivedDateTime": received,
                    "from": {
                        "emailAddress": {
                            "address": "smoke-test-customer@example.invalid"
                        }
                    }
                }
            ]
        }
    }


def call_deployed_function(payload: dict) -> tuple[int, str, dict]:
    request = Request(
        AZURE_FUNCTION_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        response = urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS)
    except HTTPError as exc:
        response = exc
    except URLError as exc:
        raise AssertionError(
            f"Unable to call the deployed Azure Function: {exc}"
        ) from exc

    with response:
        status_code = response.status
        content_type = response.headers.get("Content-Type", "")
        raw_body = response.read().decode("utf-8")

    try:
        response_body = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            "The deployed Azure Function did not return JSON. "
            f"status={status_code} body={raw_body!r}"
        ) from exc

    return status_code, content_type, response_body


@unittest.skipUnless(
    AZURE_FUNCTION_ENDPOINT.strip(),
    "Set AZURE_FUNCTION_ENDPOINT in .env to run remote tests."
)
class AzureFunctionRemoteTests(unittest.TestCase):
    def test_deployed_function_smoke_contract(self):
        status, content_type, body = call_deployed_function(
            build_power_automate_payload()
        )

        self.assertEqual(status, 200, body)
        self.assertIn("application/json", content_type.lower())
        self.assertEqual(body["messageCount"], 1)
        self.assertEqual(
            set(body),
            {
                "messageCount",
                "analysis",
                "aggregation",
                "decision",
                "notification"
            }
        )
        self.assertEqual(
            set(body["analysis"]),
            {"sentimental", "keyword", "frequency"}
        )
        self.assertEqual(body["decision"]["tier"], "Tier 2")
        self.assertTrue(body["decision"]["routingOverride"])
        self.assertTrue(body["notification"]["shouldNotify"])
        self.assertEqual(
            body["notification"]["tier"],
            body["decision"]["tier"]
        )

    def test_deployed_response_matches_direct_code_execution(self):
        payload = build_power_automate_payload()

        expected_body, expected_status = asyncio.run(
            process_thread_escalation(payload)
        )
        actual_status, _, actual_body = call_deployed_function(payload)

        self.assertEqual(actual_status, expected_status, actual_body)
        self.assertEqual(actual_body, expected_body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
