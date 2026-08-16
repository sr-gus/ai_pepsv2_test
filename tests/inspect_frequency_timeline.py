"""Replay frequency analysis as an email thread develops."""

import argparse
import asyncio
import json
import os
from pathlib import Path

from escalation_engine.analyzers.frequency import analyze_frequency
from escalation_engine.thread.extractors import (
    get_message_content,
    get_received_datetime,
    parse_received_datetime,
)
from escalation_engine.thread.selectors import (
    CUSTOMER_ROLE,
    ENGINEER_ROLE,
    get_message_role,
    is_automatic_message,
)
from tests.analyzer_dataset import (
    configure_utf8_output,
    get_fixture_engineer_emails,
    get_request_thread,
    load_fixture,
    sort_messages,
)


AUTOMATIC_ROLE = "automatic"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Replay generated or exported email threads through frequency "
            "analysis after every incoming message."
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
        help="Inspect one exported Power Automate JSON payload."
    )
    parser.add_argument(
        "--engineer-email",
        action="append",
        default=[],
        help=(
            "Engineer sender address for role classification. Repeat for "
            "multiple engineers."
        )
    )
    parser.add_argument(
        "--pause",
        action="store_true",
        help="Wait for Enter after each displayed email."
    )

    return parser.parse_args()


def load_payload(payload_path):
    with payload_path.open(encoding="utf-8-sig") as payload_file:
        payload = json.load(payload_file)

    if not isinstance(payload, dict):
        raise SystemExit("--payload must contain one JSON request object")

    return payload


def configure_engineers(engineer_emails):
    os.environ["ENGINEER_EMAILS"] = ",".join(sorted(engineer_emails))


def display_text(value):
    return " ".join(value.split())


def print_event(case_number, step_number, role, role_event, message, result):
    role_labels = {
        CUSTOMER_ROLE: "CUSTOMER",
        ENGINEER_ROLE: "ENGINEER",
        AUTOMATIC_ROLE: "AUTOMATIC",
    }
    content = get_message_content(message)
    details = result["details"]

    print()
    print(
        f"Case {case_number:02d} | step {step_number} | "
        f"{role_labels[role]} message {role_event}"
    )
    print(f"Received: {get_received_datetime(message) or '-'}")
    print(f"Body: {display_text(content.text) or '-'}")
    print(
        f"Result: score={result['score']:.2f} "
        f"label={result['label']} "
        f"flags={','.join(result['flags']) or '-'}"
    )
    print(
        "Metrics: "
        f"customer={details['customerMessages']} "
        f"engineer={details['engineerMessages']} "
        f"unanswered={details['unansweredCustomerMessages']} "
        f"ghosted_hours={details['ghostedHours']:.1f} "
        f"messages_per_day={details['messagesPerDay']:.2f} "
        f"automatic_ignored={details['spamMessagesIgnored']}"
    )


async def inspect_case(case_number, request, args):
    accumulated_thread = []
    role_counts = {
        CUSTOMER_ROLE: 0,
        ENGINEER_ROLE: 0,
        AUTOMATIC_ROLE: 0,
    }

    for step_number, message in enumerate(
        sort_messages(get_request_thread(request)),
        start=1
    ):
        accumulated_thread.append(message)

        if is_automatic_message(message):
            role = AUTOMATIC_ROLE
        else:
            role = get_message_role(message)

        role_counts[role] += 1
        result = await analyze_frequency(
            list(accumulated_thread),
            now=parse_received_datetime(message)
        )
        print_event(
            case_number,
            step_number,
            role,
            role_counts[role],
            message,
            result
        )

        if args.pause:
            input("Press Enter for the next email...")

    return role_counts


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

    totals = {
        CUSTOMER_ROLE: 0,
        ENGINEER_ROLE: 0,
        AUTOMATIC_ROLE: 0,
    }

    for case_number, request in selected_cases:
        role_counts = await inspect_case(case_number, request, args)

        for role, count in role_counts.items():
            totals[role] += count

    print()
    print(
        f"Summary: cases={len(selected_cases)} "
        f"customer_events={totals[CUSTOMER_ROLE]} "
        f"engineer_messages={totals[ENGINEER_ROLE]} "
        f"automatic_messages={totals[AUTOMATIC_ROLE]}"
    )


def main():
    configure_utf8_output()
    asyncio.run(async_main(parse_args()))


if __name__ == "__main__":
    main()
