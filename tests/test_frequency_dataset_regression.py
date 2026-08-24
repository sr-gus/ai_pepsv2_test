import asyncio
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from escalation_engine.analyzers.frequency import analyze_frequency
from escalation_engine.thread.extractors import parse_received_datetime
from escalation_engine.thread.selectors import (
    CUSTOMER_ROLE,
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


DEFAULT_CUSTOMER_EVENT = (0.05, "neutral", (), 1, 0.0)
EXPECTED_CUSTOMER_EVENT_COUNTS = {
    1: 4,
    2: 5,
    3: 5,
    4: 4,
    5: 5,
    6: 5,
    7: 5,
    8: 5,
    9: 5,
    10: 5,
    11: 5,
    12: 5,
    13: 5,
    14: 4,
    15: 5,
    16: 3,
    17: 3,
    18: 3,
    19: 2,
    20: 3,
    21: 2,
    22: 3,
    23: 3,
    24: 3,
    25: 3,
}
EXPECTED_CUSTOMER_EVENT_OVERRIDES = {
    (2, 5): (0.05, "decreasing", (), 1, 0.0),
    (3, 5): (0.05, "decreasing", (), 1, 0.0),
    (5, 5): (0.05, "decreasing", (), 1, 0.0),
    (
        6,
        4,
    ): (0.10, "neutral", ("multiple_unanswered_messages",), 2, 0.0),
    (7, 5): (0.05, "decreasing", (), 1, 0.0),
    (8, 5): (0.20, "increasing", (), 1, 0.0),
    (9, 5): (0.05, "decreasing", (), 1, 0.0),
    (10, 5): (0.05, "decreasing", (), 1, 0.0),
    (11, 5): (0.05, "decreasing", (), 1, 0.0),
    (12, 5): (0.05, "decreasing", (), 1, 0.0),
    (13, 5): (0.20, "increasing", (), 1, 0.0),
    (15, 5): (0.05, "decreasing", (), 1, 0.0),
}


class FrequencyDatasetRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_fixture()
        cls.engineer_emails = get_fixture_engineer_emails(cls.fixture)

    def test_all_customer_events_match_reviewed_frequency_baseline(self):
        """Lock frequency output at the instant each customer email arrives."""
        total_customer_events = 0

        with patch.dict(
            os.environ,
            {ENGINEER_EMAILS_ENV_VAR: ",".join(self.engineer_emails)},
            clear=False
        ):
            for case_number, request in enumerate(self.fixture, start=1):
                accumulated_thread = []
                customer_event = 0
                engineer_messages = 0

                for message in sort_messages(get_request_thread(request)):
                    accumulated_thread.append(message)

                    if is_automatic_message(message):
                        continue

                    if get_message_role(message) == ENGINEER_ROLE:
                        engineer_messages += 1
                        continue

                    customer_event += 1
                    total_customer_events += 1
                    result = asyncio.run(analyze_frequency(
                        list(accumulated_thread),
                        now=parse_received_datetime(message)
                    ))
                    details = result["details"]
                    actual = (
                        result["score"],
                        result["label"],
                        tuple(result["flags"]),
                        details["unansweredCustomerMessages"],
                        details["ghostedHours"],
                    )
                    expected = EXPECTED_CUSTOMER_EVENT_OVERRIDES.get(
                        (case_number, customer_event),
                        DEFAULT_CUSTOMER_EVENT
                    )

                    with self.subTest(
                        case=case_number,
                        customer_event=customer_event
                    ):
                        self.assertEqual(actual, expected)
                        self.assertEqual(
                            details["customerMessages"],
                            customer_event
                        )
                        self.assertEqual(
                            details["engineerMessages"],
                            engineer_messages
                        )

                with self.subTest(case=case_number, check="event_count"):
                    self.assertEqual(
                        customer_event,
                        EXPECTED_CUSTOMER_EVENT_COUNTS[case_number]
                    )

        self.assertEqual(total_customer_events, 100)

    def test_full_thread_matches_the_last_incremental_message(self):
        with patch.dict(
            os.environ,
            {ENGINEER_EMAILS_ENV_VAR: ",".join(self.engineer_emails)},
            clear=False
        ):
            for case_number, request in enumerate(self.fixture, start=1):
                messages = sort_messages(get_request_thread(request))
                accumulated_thread = []
                incremental_result = None
                last_event_time = None

                for message in messages:
                    accumulated_thread.append(message)
                    last_event_time = parse_received_datetime(message)
                    incremental_result = asyncio.run(analyze_frequency(
                        list(accumulated_thread),
                        now=last_event_time
                    ))

                full_result = asyncio.run(analyze_frequency(
                    messages,
                    now=last_event_time
                ))

                with self.subTest(case=case_number):
                    self.assertIsNotNone(incremental_result)
                    self.assertEqual(incremental_result, full_result)


class FrequencyBehaviorTests(unittest.TestCase):
    BASE_TIME = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)

    @classmethod
    def message(cls, hour_offset, sender, *, automatic=False):
        message = {
            "subject": "Case update",
            "bodyPreview": "Update",
            "receivedDateTime": (
                cls.BASE_TIME + timedelta(hours=hour_offset)
            ).isoformat(),
            "from": {
                "emailAddress": {
                    "address": sender
                }
            },
        }

        if automatic:
            message["headers"] = {"Auto-Submitted": "auto-replied"}

        return message

    def analyze(self, messages, now_offset):
        with patch.dict(
            os.environ,
            {ENGINEER_EMAILS_ENV_VAR: "engineer@example.com"},
            clear=False
        ):
            return asyncio.run(analyze_frequency(
                messages,
                now=self.BASE_TIME + timedelta(hours=now_offset)
            ))

    def test_three_quick_customer_messages_trigger_rapid_followup(self):
        messages = [
            self.message(0, "customer@example.com"),
            self.message(0.5, "customer@example.com"),
            self.message(1, "customer@example.com"),
        ]
        result = self.analyze(messages, 1)

        self.assertEqual(result["score"], 0.30)
        self.assertEqual(
            result["flags"],
            ["multiple_unanswered_messages", "rapid_followup"]
        )
        self.assertEqual(
            result["details"]["unansweredCustomerMessages"],
            3
        )

    def test_long_and_critical_unanswered_delays_cross_thresholds(self):
        message = self.message(0, "customer@example.com")
        long_delay = self.analyze([message], 25)
        critical_delay = self.analyze([message], 73)

        self.assertEqual(long_delay["score"], 0.17)
        self.assertEqual(long_delay["label"], "increasing")
        self.assertIn("long_response_delay", long_delay["flags"])
        self.assertEqual(critical_delay["score"], 0.40)
        self.assertIn("critical_response_delay", critical_delay["flags"])

    def test_engineer_reply_clears_unanswered_state(self):
        messages = [
            self.message(0, "customer@example.com"),
            self.message(1, "engineer@example.com"),
        ]
        result = self.analyze(messages, 25)

        self.assertEqual(result["score"], 0.0)
        self.assertEqual(result["details"]["unansweredCustomerMessages"], 0)
        self.assertEqual(result["details"]["ghostedHours"], 0.0)

    def test_automatic_reply_does_not_clear_customer_wait(self):
        messages = [
            self.message(0, "customer@example.com"),
            self.message(1, "engineer@example.com", automatic=True),
        ]
        result = self.analyze(messages, 25)

        self.assertEqual(result["details"]["unansweredCustomerMessages"], 1)
        self.assertEqual(result["details"]["spamMessagesIgnored"], 1)
        self.assertIn("auto_reply_detected", result["flags"])
        self.assertIn("long_response_delay", result["flags"])

    def test_ghosted_time_uses_the_latest_unanswered_customer_message(self):
        messages = [
            self.message(0, "customer@example.com"),
            self.message(24, "customer@example.com"),
        ]
        result = self.analyze(messages, 30)

        self.assertEqual(result["details"]["unansweredCustomerMessages"], 2)
        self.assertEqual(result["details"]["ghostedHours"], 6.0)
        self.assertNotIn("long_response_delay", result["flags"])

    def test_worsening_response_times_add_trend_risk(self):
        messages = [
            self.message(0, "customer@example.com"),
            self.message(0.5, "engineer@example.com"),
            self.message(2, "customer@example.com"),
            self.message(2.5, "engineer@example.com"),
            self.message(4, "customer@example.com"),
            self.message(6, "engineer@example.com"),
            self.message(7, "customer@example.com"),
            self.message(10, "engineer@example.com"),
        ]
        result = self.analyze(messages, 10)

        self.assertEqual(result["label"], "increasing")
        self.assertEqual(result["score"], 0.15)

    def test_improving_response_times_do_not_add_score(self):
        messages = [
            self.message(0, "customer@example.com"),
            self.message(3, "engineer@example.com"),
            self.message(4, "customer@example.com"),
            self.message(6, "engineer@example.com"),
            self.message(7, "customer@example.com"),
            self.message(7.5, "engineer@example.com"),
            self.message(8, "customer@example.com"),
            self.message(8.5, "engineer@example.com"),
        ]
        result = self.analyze(messages, 8.5)

        self.assertEqual(result["label"], "decreasing")
        self.assertEqual(result["score"], 0.0)


if __name__ == "__main__":
    unittest.main()
