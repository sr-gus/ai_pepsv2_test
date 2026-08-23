"""Inspect keyword-analysis results as customer messages arrive over time."""

import argparse
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from escalation_engine.analyzers.keyword import analyze_keywords
from escalation_engine.thread.extractors import (
    get_message_content,
    parse_received_datetime,
)
from escalation_engine.thread.selectors import (
    CUSTOMER_ROLE,
    ENGINEER_EMAILS_ENV_VAR,
    ENGINEER_ROLE,
    get_message_role,
    is_automatic_message,
)
from tests.analyzer_dataset import (
    configure_utf8_output,
    get_fixture_engineer_emails,
)


FIXTURE_PATH = Path(__file__).with_name("azure_billing_escalation_threads.json")
AUTOMATIC_ROLE = "automatic"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Replay the generated email threads and show keyword-analysis "
            "evidence after each customer message."
        )
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--case",
        type=int,
        default=1,
        help="One-based fixture case number to inspect (default: 1)."
    )
    selection.add_argument(
        "--all",
        action="store_true",
        help="Inspect every fixture case."
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument(
        "--fixture",
        type=Path,
        help=(
            "Read a JSON array of generated requests from this fixture "
            "instead of the default dataset."
        )
    )
    source.add_argument(
        "--payload",
        type=Path,
        help=(
            "Inspect a JSON payload exported from Power Automate instead of "
            "the generated fixture."
        )
    )
    parser.add_argument(
        "--engineer-email",
        action="append",
        default=[],
        help=(
            "Engineer sender address for role classification. Repeat this "
            "option for multiple engineers."
        )
    )
    parser.add_argument(
        "--only-triggered",
        action="store_true",
        help=(
            "Show only customer events that trigger a topic; engineer "
            "messages are hidden in this compact mode."
        )
    )
    parser.add_argument(
        "--pause",
        action="store_true",
        help="Wait for Enter after each displayed email."
    )

    return parser.parse_args()


def load_fixture(fixture_path=None):
    path = fixture_path or FIXTURE_PATH

    with path.open(encoding="utf-8-sig") as fixture_file:
        fixture = json.load(fixture_file)

    if not isinstance(fixture, list):
        raise SystemExit("--fixture must contain a JSON array of requests")

    return fixture


def load_payload(payload_path):
    with payload_path.open(encoding="utf-8-sig") as payload_file:
        payload = json.load(payload_file)

    if not isinstance(payload, dict):
        raise SystemExit("--payload must contain one JSON request object")

    return payload


def get_request_thread(request):
    nested_body = request.get("body")

    if isinstance(nested_body, dict) and isinstance(nested_body.get("thread"), list):
        return nested_body["thread"]

    if isinstance(request.get("thread"), list):
        return request["thread"]

    raise SystemExit("The payload must contain thread or body.thread")


def configure_engineers(engineer_emails):
    if engineer_emails:
        os.environ[ENGINEER_EMAILS_ENV_VAR] = ",".join(
            sorted(engineer_emails)
        )


def sort_messages(messages):
    return sorted(
        messages,
        key=lambda message: parse_received_datetime(message) or datetime.min
    )


def normalized_display_text(value):
    return " ".join(value.split())


def print_message_header(
    case_number,
    step_number,
    role,
    role_event,
    message
):
    role_labels = {
        CUSTOMER_ROLE: "CUSTOMER",
        ENGINEER_ROLE: "ENGINEER",
        AUTOMATIC_ROLE: "AUTOMATIC"
    }
    role_label = role_labels[role]
    content = get_message_content(message)

    print()
    print(
        f"Case {case_number:02d} | step {step_number} | "
        f"{role_label} message {role_event}"
    )
    print(f"Body: {normalized_display_text(content.text) or '-'}")


def print_customer_event(
    case_number,
    step_number,
    customer_event,
    message,
    result
):
    triggered_topics = result["details"]["triggeredTopics"]

    print_message_header(
        case_number,
        step_number,
        CUSTOMER_ROLE,
        customer_event,
        message
    )
    print(
        f"Result: score={result['score']:.2f} "
        f"label={result['label']} "
        f"triggered={','.join(triggered_topics) or '-'}"
    )
    escalation_request = result["details"]["escalationRequest"]

    if escalation_request["status"] != "none":
        print(
            "Escalation request: "
            f"status={escalation_request['status']} "
            f"kind={escalation_request['kind'] or '-'} "
            f"target={escalation_request['requestedTarget'] or '-'} "
            f"routing_override={escalation_request['routingOverride'] or '-'}"
        )

        if escalation_request["evidence"]:
            print(
                "Escalation evidence: "
                + " | ".join(escalation_request["evidence"])
            )

    evidence_topics = [
        topic
        for topic in result["details"]["topics"]
        if topic["weightedMatches"] > 0
    ]

    if not evidence_topics:
        print("Evidence: none")
        return

    print("Evidence:")

    for topic in evidence_topics:
        marker = "TRIGGER" if topic["triggered"] else "signal"
        evidence = ", ".join(topic["uniqueMatches"]) or "-"
        print(
            f"  [{marker}] {topic['topic']} "
            f"{topic['weightedMatches']}/{topic['threshold']}: {evidence}"
        )


def print_engineer_response(
    case_number,
    step_number,
    engineer_message,
    message
):
    print_message_header(
        case_number,
        step_number,
        ENGINEER_ROLE,
        engineer_message,
        message
    )
    print("Result: keyword not run (engineer response)")


def print_automatic_response(
    case_number,
    step_number,
    automatic_message,
    message
):
    print_message_header(
        case_number,
        step_number,
        AUTOMATIC_ROLE,
        automatic_message,
        message
    )
    print("Result: ignored (automatic response)")


async def inspect_case(case_number, request, args):
    accumulated_thread = []
    customer_event = 0
    engineer_message = 0
    automatic_message = 0
    displayed_messages = 0

    for step_number, message in enumerate(
        sort_messages(get_request_thread(request)),
        start=1
    ):
        accumulated_thread.append(message)

        if is_automatic_message(message):
            automatic_message += 1

            if not args.only_triggered:
                displayed_messages += 1
                print_automatic_response(
                    case_number,
                    step_number,
                    automatic_message,
                    message
                )

                if args.pause:
                    input("Press Enter for the next email...")

            continue

        role = get_message_role(message)

        if role == ENGINEER_ROLE:
            engineer_message += 1

            if not args.only_triggered:
                displayed_messages += 1
                print_engineer_response(
                    case_number,
                    step_number,
                    engineer_message,
                    message
                )

                if args.pause:
                    input("Press Enter for the next email...")

            continue

        customer_event += 1
        result = await analyze_keywords(list(accumulated_thread))

        if args.only_triggered and not result["details"]["triggeredTopics"]:
            continue

        displayed_messages += 1
        print_customer_event(
            case_number,
            step_number,
            customer_event,
            message,
            result
        )

        if args.pause:
            input("Press Enter for the next email...")

    return (
        customer_event,
        engineer_message,
        automatic_message,
        displayed_messages
    )


async def async_main(args):
    if args.payload:
        selected_cases = [(1, load_payload(args.payload))]
        configure_engineers(args.engineer_email)
    else:
        fixture = load_fixture(args.fixture)
        configure_engineers(
            get_fixture_engineer_emails(fixture) | set(args.engineer_email)
        )

        if args.all:
            selected_cases = list(enumerate(fixture, start=1))
        else:
            if args.case < 1 or args.case > len(fixture):
                raise SystemExit(
                    f"--case must be between 1 and {len(fixture)}"
                )

            selected_cases = [(args.case, fixture[args.case - 1])]

    total_customer_events = 0
    total_engineer_messages = 0
    total_automatic_messages = 0
    total_displayed_messages = 0

    for case_number, request in selected_cases:
        (
            customer_events,
            engineer_messages,
            automatic_messages,
            displayed_messages
        ) = await inspect_case(case_number, request, args)
        total_customer_events += customer_events
        total_engineer_messages += engineer_messages
        total_automatic_messages += automatic_messages
        total_displayed_messages += displayed_messages

    print()
    print(
        f"Summary: cases={len(selected_cases)} "
        f"customer_events={total_customer_events} "
        f"engineer_messages={total_engineer_messages} "
        f"automatic_messages={total_automatic_messages} "
        f"displayed_messages={total_displayed_messages}"
    )


def main():
    configure_utf8_output()
    asyncio.run(async_main(parse_args()))


if __name__ == "__main__":
    main()
