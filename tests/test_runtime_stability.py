import asyncio
import os
import unittest
from datetime import datetime
from unittest.mock import patch

from escalation_engine.analyzers.frequency import analyze_frequency
from escalation_engine.service import process_thread_escalation
from escalation_engine.thread.selectors import (
    get_latest_message,
    get_message_role,
)


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

    def test_nested_power_automate_payload_completes(self):
        payload = {
            "body": {
                "thread": [
                    {
                        "subject": "Question",
                        "bodyPreview": "Can you help me?",
                        "receivedDateTime": "2026-07-12T20:30:00Z",
                        "from": {
                            "emailAddress": {
                                "address": "customer@example.com"
                            }
                        }
                    }
                ]
            }
        }

        body, status = self.run_service(payload)

        self.assertEqual(status, 200)
        self.assertEqual(body["messageCount"], 1)

    def test_sender_role_uses_configured_email_case_insensitively(self):
        message = {
            "from": {
                "emailAddress": {
                    "address": "Engineer@Example.com"
                }
            }
        }

        with patch.dict(
            os.environ,
            {"ENGINEER_EMAILS": "engineer@example.com"},
            clear=False
        ):
            self.assertEqual(get_message_role(message), "engineer")

    def test_sender_role_does_not_use_legacy_name_heuristics(self):
        message = {
            "from": {
                "emailAddress": {
                    "address": "support-agent@example.com"
                }
            }
        }

        with patch.dict(os.environ, {"ENGINEER_EMAILS": ""}, clear=False):
            self.assertEqual(get_message_role(message), "customer")

    def test_frequency_uses_shared_sender_roles(self):
        messages = [
            {
                "subject": "Customer question",
                "receivedDateTime": "2026-07-12T10:00:00Z",
                "from": {
                    "emailAddress": {
                        "address": "customer@example.com"
                    }
                }
            },
            {
                "subject": "Engineer response",
                "receivedDateTime": "2026-07-12T11:00:00Z",
                "from": {
                    "emailAddress": {
                        "address": "engineer@example.com"
                    }
                }
            }
        ]

        with patch.dict(
            os.environ,
            {"ENGINEER_EMAILS": "engineer@example.com"},
            clear=False
        ):
            result = asyncio.run(
                analyze_frequency(messages, now=datetime(2026, 7, 12, 12, 0))
            )

        self.assertEqual(result["details"]["customerMessages"], 1)
        self.assertEqual(result["details"]["engineerMessages"], 1)
        self.assertEqual(result["details"]["unansweredCustomerMessages"], 0)

    def test_frequency_ignores_auto_reply_headers(self):
        messages = [
            {
                "subject": "Re: case",
                "receivedDateTime": "2026-07-12T10:00:00Z",
                "headers": {"Auto-Submitted": "auto-replied"},
                "from": {
                    "emailAddress": {
                        "address": "customer@example.com"
                    }
                }
            }
        ]

        result = asyncio.run(
            analyze_frequency(messages, now=datetime(2026, 7, 12, 12, 0))
        )

        self.assertEqual(result["details"]["spamMessagesIgnored"], 1)
        self.assertEqual(result["details"]["customerMessages"], 0)


if __name__ == "__main__":
    unittest.main()
