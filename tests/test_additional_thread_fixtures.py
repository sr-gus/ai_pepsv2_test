"""Quality and contextual-regression checks for additional thread fixtures."""

import asyncio
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from escalation_engine.analyzers.keyword import analyze_keywords
from escalation_engine.thread.extractors import (
    get_message_content,
    parse_received_datetime,
)
from escalation_engine.thread.selectors import (
    ENGINEER_EMAILS_ENV_VAR,
    ENGINEER_ROLE,
    get_message_role,
    is_automatic_message,
)
from tests.analyzer_dataset import (
    get_fixture_engineer_emails,
    get_request_thread,
    load_fixture,
    sort_messages,
)
from tests.fixture_constants import FIXTURE_ENGINEER_EMAIL


TEST_DIRECTORY = Path(__file__).parent
EXPECTATIONS_PATH = TEST_DIRECTORY / "additional_thread_expectations.json"
FIXTURE_NAMES = (
    "azure_billing_escalation_threads_short.json",
    "azure_billing_escalation_threads_mixed.json",
    "azure_billing_escalation_threads_long.json",
)
ESCALATION_FIELDS = (
    "status",
    "kind",
    "requestedTarget",
    "tier2Override",
)


def load_expectations():
    with EXPECTATIONS_PATH.open(encoding="utf-8") as expectations_file:
        return json.load(expectations_file)


class AdditionalFixtureQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expectations = load_expectations()

    def test_all_profiles_have_eight_outlook_shaped_threads(self):
        self.assertEqual(set(self.expectations), set(FIXTURE_NAMES))

        for fixture_name in FIXTURE_NAMES:
            fixture = load_fixture(TEST_DIRECTORY / fixture_name)
            self.assertEqual(len(fixture), 8, fixture_name)

            for request in fixture:
                self.assertEqual(request["method"], "POST")
                self.assertIn("threadEscalationEngine", request["uri"])
                self.assertIsInstance(request["body"]["thread"], list)
                self.assertGreaterEqual(len(request["body"]["thread"]), 3)

    def test_messages_are_chronological_and_have_graph_fields(self):
        for fixture_name in FIXTURE_NAMES:
            fixture = load_fixture(TEST_DIRECTORY / fixture_name)

            for request in fixture:
                thread = get_request_thread(request)
                received = [parse_received_datetime(message) for message in thread]
                self.assertTrue(all(received), fixture_name)
                self.assertEqual(received, sorted(received), fixture_name)

                for message in thread:
                    self.assertTrue(message["id"])
                    self.assertTrue(message["conversationId"])
                    self.assertEqual(message["body"]["contentType"], "html")
                    self.assertTrue(message["from"]["emailAddress"]["address"])
                    self.assertTrue(message["toRecipients"])

    def test_extracted_body_lengths_match_authored_expectations(self):
        for fixture_name, case_expectations in self.expectations.items():
            fixture = load_fixture(TEST_DIRECTORY / fixture_name)
            engineer_emails = get_fixture_engineer_emails(fixture)

            self.assertEqual(
                engineer_emails,
                {FIXTURE_ENGINEER_EMAIL},
                fixture_name,
            )

            with patch.dict(
                os.environ,
                {ENGINEER_EMAILS_ENV_VAR: ",".join(engineer_emails)},
                clear=False,
            ):
                for request, case_expected in zip(fixture, case_expectations):
                    expected_events = case_expected["customerEvents"]
                    actual_events = []

                    for message in get_request_thread(request):
                        if (
                            get_message_role(message) == ENGINEER_ROLE
                            or is_automatic_message(message)
                        ):
                            continue

                        content = get_message_content(message)
                        actual_events.append(
                            {
                                "authoredCharacters": len(content.text),
                                "authoredWords": len(content.text.split()),
                            }
                        )

                    for actual, expected_event in zip(
                        actual_events,
                        expected_events,
                    ):
                        self.assertEqual(
                            actual["authoredCharacters"],
                            expected_event["authoredCharacters"],
                            case_expected["key"],
                        )
                        self.assertEqual(
                            actual["authoredWords"],
                            expected_event["authoredWords"],
                            case_expected["key"],
                        )

    def test_profiles_create_materially_different_length_distributions(self):
        ranges = {}

        for fixture_name, case_expectations in self.expectations.items():
            word_counts = [
                event["authoredWords"]
                for case in case_expectations
                for event in case["customerEvents"]
            ]
            ranges[fixture_name] = {
                "minimum": min(word_counts),
                "maximum": max(word_counts),
                "average": sum(word_counts) / len(word_counts),
            }

        short = ranges[FIXTURE_NAMES[0]]
        mixed = ranges[FIXTURE_NAMES[1]]
        long = ranges[FIXTURE_NAMES[2]]
        self.assertLessEqual(short["maximum"], 12)
        self.assertLess(short["average"], mixed["average"])
        self.assertLess(mixed["average"], long["average"])
        self.assertGreaterEqual(long["maximum"], 90)


class AdditionalFixtureKeywordContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expectations = load_expectations()

    def test_escalation_context_matches_reviewed_expectations(self):
        asyncio.run(self._assert_all_contexts())

    async def _assert_all_contexts(self):
        mismatches = []

        for fixture_name, case_expectations in self.expectations.items():
            fixture = load_fixture(TEST_DIRECTORY / fixture_name)
            engineer_emails = get_fixture_engineer_emails(fixture)

            with patch.dict(
                os.environ,
                {ENGINEER_EMAILS_ENV_VAR: ",".join(sorted(engineer_emails))},
                clear=False,
            ):
                for request, case_expected in zip(fixture, case_expectations):
                    accumulated_thread = []
                    customer_event = 0

                    for message in sort_messages(get_request_thread(request)):
                        accumulated_thread.append(message)

                        if is_automatic_message(message):
                            continue

                        if get_message_role(message) == ENGINEER_ROLE:
                            continue

                        customer_event += 1
                        result = await analyze_keywords(accumulated_thread)
                        actual = result["details"]["escalationRequest"]
                        expected_event = case_expected["customerEvents"][
                            customer_event - 1
                        ]

                        for field in ESCALATION_FIELDS:
                            if actual[field] != expected_event[field]:
                                mismatches.append(
                                    f"{fixture_name} case={case_expected['case']} "
                                    f"key={case_expected['key']} "
                                    f"customer_event={customer_event} field={field}: "
                                    f"actual={actual[field]!r} "
                                    f"expected={expected_event[field]!r}"
                                )

        if mismatches:
            self.fail("\n" + "\n".join(mismatches))


if __name__ == "__main__":
    unittest.main()
