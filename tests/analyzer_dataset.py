"""Shared fixture helpers for incremental analyzer regression tests."""

import json
import sys
from datetime import datetime
from pathlib import Path

from escalation_engine.thread.extractors import parse_received_datetime


FIXTURE_PATH = Path(__file__).with_name("azure_billing_escalation_threads.json")


def configure_utf8_output():
    """Keep Spanish fixture text readable in redirected Windows terminals."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def load_fixture(fixture_path=None):
    path = Path(fixture_path) if fixture_path else FIXTURE_PATH

    with path.open(encoding="utf-8-sig") as fixture_file:
        fixture = json.load(fixture_file)

    if not isinstance(fixture, list):
        raise ValueError("The fixture must contain a JSON array of requests")

    return fixture


def get_request_thread(request):
    nested_body = request.get("body")

    if isinstance(nested_body, dict) and isinstance(
        nested_body.get("thread"),
        list
    ):
        return nested_body["thread"]

    if isinstance(request.get("thread"), list):
        return request["thread"]

    raise ValueError("The request must contain thread or body.thread")


def sort_messages(messages):
    return sorted(
        messages,
        key=lambda message: parse_received_datetime(message) or datetime.min
    )


def get_fixture_engineer_emails(fixture):
    return {
        message.get("from", {}).get("emailAddress", {}).get("address", "")
        for request in fixture
        for message in get_request_thread(request)
        if message.get("from", {})
        .get("emailAddress", {})
        .get("address", "")
        .endswith("@microsoft.com")
    }
