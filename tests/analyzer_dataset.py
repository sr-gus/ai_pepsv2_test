"""Shared fixture helpers for incremental analyzer regression tests."""

import json
from datetime import datetime
from pathlib import Path

from escalation_engine.thread.extractors import parse_received_datetime


FIXTURE_PATH = Path(__file__).with_name("azure_billing_escalation_threads.json")


def load_fixture():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


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
