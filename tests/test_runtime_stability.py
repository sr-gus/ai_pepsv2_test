import asyncio
import unittest

from escalation_engine.service import process_thread_escalation
from escalation_engine.thread.selectors import get_latest_message


class RuntimeStabilityTests(unittest.TestCase):
    def run_service(self, payload):
        return asyncio.run(process_thread_escalation(payload))

    def test_documented_payload_completes(self):
        payload = {
            "thread": [
                {
                    "subject": "Urgent billing issue",
                    "bodyPreview": "I need help with this charge immediately.",
                    "receivedDateTime": "2026-07-12T20:30:00Z",
                    "from": {
                        "emailAddress": {
                            "address": "customer@example.com"
                        }
                    }
                }
            ]
        }

        body, status = self.run_service(payload)

        self.assertEqual(status, 200)
        self.assertEqual(body["messageCount"], 1)
        self.assertIn("frequency", body["analysis"])

    def test_nullable_sender_and_non_string_text_do_not_crash(self):
        payload = {
            "thread": [
                {
                    "subject": 123,
                    "bodyPreview": None,
                    "from": None,
                    "receivedDateTime": "2026-07-12T20:30:00Z"
                }
            ]
        }

        body, status = self.run_service(payload)

        self.assertEqual(status, 200)
        self.assertEqual(body["messageCount"], 1)

    def test_mixed_timezone_timestamps_select_latest_message(self):
        messages = [
            {
                "subject": "aware",
                "receivedDateTime": "2026-01-01T00:00:00Z"
            },
            {
                "subject": "naive",
                "receivedDateTime": "2026-01-02T00:00:00"
            }
        ]

        latest = get_latest_message(messages)

        self.assertEqual(latest["subject"], "naive")

    def test_invalid_timestamp_is_ignored(self):
        payload = {
            "thread": [
                {
                    "subject": "Question",
                    "bodyPreview": "Hello",
                    "receivedDateTime": "not-a-date"
                }
            ]
        }

        body, status = self.run_service(payload)

        self.assertEqual(status, 200)
        self.assertEqual(
            body["analysis"]["frequency"]["details"]["messagesWithTimestamp"],
            0
        )


if __name__ == "__main__":
    unittest.main()
