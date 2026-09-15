import asyncio
import os
import unittest
from unittest.mock import AsyncMock, patch

from escalation_engine.service import process_thread_escalation
from escalation_engine.thread.extractors import get_case_number
from escalation_engine.thread.selectors import ENGINEER_EMAILS_ENV_VAR


def message(
    *,
    subject="Case update - TrackingID#0001234567890123",
    sender="customer@example.com",
    name="Example Customer",
    received="2026-09-13T10:00:00Z",
    body="Please escalate this case.",
):
    return {
        "subject": subject,
        "bodyPreview": body,
        "receivedDateTime": received,
        "from": {"emailAddress": {"address": sender, "name": name}},
    }


class CaseNumberExtractionTests(unittest.TestCase):
    def test_numeric_ids_have_variable_length_and_preserve_leading_zeros(self):
        for case_number in ("7", "000123", "0001234567890123", "1" * 20):
            with self.subTest(case_number=case_number):
                self.assertEqual(
                    get_case_number({
                        "subject": f"RE: Billing - TrackingID#{case_number}"
                    }),
                    case_number,
                )

    def test_marker_is_case_insensitive_and_allows_surrounding_punctuation(self):
        self.assertEqual(
            get_case_number({"subject": "RE: [trackingid#00123] update"}),
            "00123",
        )

    def test_invalid_subjects_do_not_produce_a_partial_or_invented_id(self):
        for subject in (
            None, 123, {}, [], "", "Case 123", "TrackingID#", "TrackingID#abc",
            "TrackingID#123abc", "TrackingID#123_456", "TrackingID# 123",
            "OtherTrackingID#123", "TrackingID#１２３",
        ):
            with self.subTest(subject=subject):
                self.assertIsNone(get_case_number({"subject": subject}))


class NotificationContextIntegrationTests(unittest.TestCase):
    def setUp(self):
        environment = patch.dict(os.environ, {
            ENGINEER_EMAILS_ENV_VAR: (
                "engineer@example.com,second.engineer@example.com"
            )
        })
        environment.start()
        self.addCleanup(environment.stop)

    @staticmethod
    def run_service(thread, *, nested=False):
        payload = {"thread": thread}
        if nested:
            payload = {"body": payload}
        return asyncio.run(process_thread_escalation(payload))

    def test_missing_tracking_id_skips_all_analyzers_even_for_explicit_requests(self):
        for nested in (False, True):
            for subject in (None, 123, "Case update", "TrackingID#123abc"):
                analyzers = {
                    "analyze_sentimental": AsyncMock(),
                    "analyze_keywords": AsyncMock(),
                    "analyze_frequency": AsyncMock(),
                }
                with self.subTest(nested=nested, subject=subject), patch.multiple(
                    "escalation_engine.service", **analyzers
                ):
                    body, status = self.run_service([
                        None,
                        message(
                            subject=subject,
                            body="TrackingID#12345. Please escalate to a manager!",
                        ),
                    ], nested=nested)

                    self.assertEqual(status, 200)
                    self.assertEqual(body["messageCount"], 1)
                    self.assertEqual(body["analysis"], {})
                    self.assertEqual(body["aggregation"], {})
                    self.assertEqual(body["decision"]["action"], "exit")
                    self.assertIsNone(body["decision"]["tier"])
                    notification = body["notification"]
                    self.assertFalse(notification["shouldNotify"])
                    self.assertIsNone(notification["caseNumber"])
                    self.assertIsNone(notification["confidence"])
                    self.assertEqual(
                        notification["decisionSource"], "missing_tracking_id"
                    )
                    self.assertIn("skipped", notification["title"])
                    for analyzer in analyzers.values():
                        analyzer.assert_not_called()

    def test_valid_id_keeps_analysis_and_exposes_latest_engineer_metadata(self):
        # Deliberately unordered input; customer and auto-replies are more recent.
        thread = [
            message(
                sender="SECOND.Engineer@example.com",
                name="  Example Engineer Two  ",
                received="2026-09-13T12:00:00Z",
                body="I am reviewing your case.",
            ),
            message(received="2026-09-13T14:00:00Z"),
            message(
                sender="engineer@example.com", name="Example Engineer One",
                received="2026-09-13T11:00:00Z",
                body="I am reviewing your case.",
            ),
            {
                **message(
                    sender="engineer@example.com", name="Automatic Reply",
                    received="2026-09-13T15:00:00Z",
                ),
                "internetMessageHeaders": [
                    {"name": "Auto-Submitted", "value": "auto-replied"}
                ],
            },
        ]
        for nested in (False, True):
            with self.subTest(nested=nested):
                body, status = self.run_service(thread, nested=nested)
                self.assertEqual(status, 200)
                self.assertEqual(
                    set(body["analysis"]), {"sentimental", "keyword", "frequency"}
                )
                notification = body["notification"]
                self.assertEqual(notification["caseNumber"], "0001234567890123")
                self.assertEqual(notification["engineerName"], "Example Engineer Two")
                self.assertEqual(
                    notification["engineerEmail"], "SECOND.Engineer@example.com"
                )
                self.assertTrue(notification["shouldNotify"])
                self.assertEqual(notification["tier"], "Tier 2")
                self.assertEqual(
                    notification["decisionSource"], "explicit_escalation_request"
                )

    def test_id_can_come_from_an_earlier_subject_in_the_thread(self):
        body, status = self.run_service([
            message(received="2026-09-13T10:00:00Z"),
            message(subject="New subject", received="2026-09-13T12:00:00Z"),
        ])
        self.assertEqual(status, 200)
        self.assertEqual(body["notification"]["caseNumber"], "0001234567890123")
        self.assertIn("keyword", body["analysis"])

    def test_latest_tracked_subject_wins_by_timestamp(self):
        body, status = self.run_service([
            message(subject="RE: TrackingID#222", received="2026-09-13T11:00:00Z"),
            message(subject="RE: TrackingID#111", received="2026-09-13T10:00:00Z"),
        ])
        self.assertEqual(status, 200)
        self.assertEqual(body["notification"]["caseNumber"], "222")

    def test_missing_timestamps_use_last_matching_message_for_each_field(self):
        body, status = self.run_service([
            message(sender="engineer@example.com", name="First", received=None),
            message(
                sender="second.engineer@example.com", name="Second",
                subject="RE: TrackingID#222", received="not-a-date",
            ),
            message(subject=None, received=None),
        ])
        self.assertEqual(status, 200)
        self.assertEqual(body["notification"]["caseNumber"], "222")
        self.assertEqual(body["notification"]["engineerName"], "Second")

    def test_missing_or_invalid_engineer_name_retains_email_separately(self):
        for name in (None, "", "  ", 123, {}, []):
            with self.subTest(name=name):
                body, status = self.run_service([
                    message(sender="engineer@example.com", name=name),
                    message(received="2026-09-13T12:00:00Z"),
                ])
                self.assertEqual(status, 200)
                self.assertIsNone(body["notification"]["engineerName"])
                self.assertEqual(
                    body["notification"]["engineerEmail"], "engineer@example.com"
                )

    def test_engineer_is_not_inferred_from_customer_name_or_recipients(self):
        value = message(sender="support-agent@example.com", name="Support Engineer")
        value["toRecipients"] = [{"emailAddress": {
            "address": "engineer@example.com", "name": "Recipient Engineer"
        }}]
        for thread in (
            [value],
            [message(sender=None, name="Example Engineer")],
            [{**message(), "from": None}],
            [{**message(), "from": {"emailAddress": None}}],
        ):
            with self.subTest(thread=thread):
                body, status = self.run_service(thread)
                self.assertEqual(status, 200)
                self.assertIsNone(body["notification"]["engineerName"])
                self.assertIsNone(body["notification"]["engineerEmail"])

    def test_structurally_invalid_requests_still_return_400(self):
        for payload in (None, [], {}, {"thread": []}, {"thread": [None]}):
            with self.subTest(payload=payload):
                body, status = asyncio.run(process_thread_escalation(payload))
                self.assertEqual(status, 400)
                self.assertIn("error", body)


if __name__ == "__main__":
    unittest.main()
