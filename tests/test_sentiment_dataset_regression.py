import asyncio
import os
import unittest
from unittest.mock import patch

from escalation_engine.analyzers.sentimental import analyze_sentimental
from escalation_engine.thread.selectors import (
    CUSTOMER_ROLE,
    ENGINEER_EMAILS_ENV_VAR,
    get_message_role,
    is_automatic_message,
)
from tests.analyzer_dataset import (
    get_fixture_engineer_emails,
    get_request_thread,
    load_fixture,
    sort_messages,
)


# Populate this mapping after the sentiment implementation has been reviewed.
# Each customer event must contain:
#     (score, label, confidence, ("flag_one", "flag_two"))
# The quality-regression test below will activate automatically once all 25
# cases have entries.
EXPECTED_SENTIMENT_TIMELINES = {}


class SentimentDatasetRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = load_fixture()
        cls.engineer_emails = get_fixture_engineer_emails(cls.fixture)

    def test_each_customer_event_is_ready_for_incremental_sentiment_analysis(self):
        """Validate replay, filtering, extraction coverage, and output schema."""
        total_customer_events = 0

        with patch.dict(
            os.environ,
            {ENGINEER_EMAILS_ENV_VAR: ",".join(self.engineer_emails)},
            clear=False
        ):
            for case_number, request in enumerate(self.fixture, start=1):
                accumulated_thread = []
                expected_analyzed_messages = 0
                expected_automatic_messages = 0
                customer_event = 0

                for message in sort_messages(get_request_thread(request)):
                    accumulated_thread.append(message)

                    if is_automatic_message(message):
                        expected_automatic_messages += 1
                        continue

                    expected_analyzed_messages += 1

                    if get_message_role(message) != CUSTOMER_ROLE:
                        continue

                    customer_event += 1
                    total_customer_events += 1
                    result = asyncio.run(analyze_sentimental(
                        list(accumulated_thread)
                    ))
                    details = result["details"]

                    with self.subTest(
                        case=case_number,
                        customer_event=customer_event
                    ):
                        self.assertEqual(result["name"], "sentimental")
                        self.assertGreaterEqual(result["score"], 0.0)
                        self.assertLessEqual(result["score"], 1.0)
                        self.assertGreaterEqual(result["confidence"], 0.0)
                        self.assertLessEqual(result["confidence"], 1.0)
                        self.assertIsInstance(result["label"], str)
                        self.assertIsInstance(result["flags"], list)
                        self.assertEqual(
                            details["analyzedMessages"],
                            expected_analyzed_messages
                        )
                        self.assertEqual(
                            details["ignoredAutomaticMessages"],
                            expected_automatic_messages
                        )
                        self.assertEqual(
                            sum(details["textSources"].values()),
                            expected_analyzed_messages
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

                for message in messages:
                    accumulated_thread.append(message)
                    incremental_result = asyncio.run(analyze_sentimental(
                        list(accumulated_thread)
                    ))

                full_result = asyncio.run(analyze_sentimental(messages))

                with self.subTest(case=case_number):
                    self.assertIsNotNone(incremental_result)
                    self.assertEqual(incremental_result, full_result)

    def test_quality_matches_reviewed_sentiment_baseline_when_enabled(self):
        """Strict future baseline; intentionally skipped for the placeholder."""
        if not EXPECTED_SENTIMENT_TIMELINES:
            self.skipTest(
                "Sentiment is still a placeholder. Populate "
                "EXPECTED_SENTIMENT_TIMELINES after manual review."
            )

        self.assertEqual(
            set(EXPECTED_SENTIMENT_TIMELINES),
            set(range(1, len(self.fixture) + 1))
        )

        with patch.dict(
            os.environ,
            {ENGINEER_EMAILS_ENV_VAR: ",".join(self.engineer_emails)},
            clear=False
        ):
            for case_number, request in enumerate(self.fixture, start=1):
                expected_timeline = EXPECTED_SENTIMENT_TIMELINES[case_number]
                actual_timeline = []
                accumulated_thread = []

                for message in sort_messages(get_request_thread(request)):
                    accumulated_thread.append(message)

                    if (
                        is_automatic_message(message)
                        or get_message_role(message) != CUSTOMER_ROLE
                    ):
                        continue

                    result = asyncio.run(analyze_sentimental(
                        list(accumulated_thread)
                    ))
                    actual_timeline.append((
                        result["score"],
                        result["label"],
                        result["confidence"],
                        tuple(result["flags"]),
                    ))

                with self.subTest(case=case_number):
                    self.assertEqual(actual_timeline, expected_timeline)


if __name__ == "__main__":
    unittest.main()
