import asyncio
import os
import unittest
from datetime import datetime
from unittest.mock import patch

from escalation_engine.analyzers.frequency import analyze_frequency
from escalation_engine.analyzers.keyword import analyze_keywords
from escalation_engine.analyzers.sentimental import analyze_sentimental
from escalation_engine.thread.extractors import get_message_content
from escalation_engine.thread.selectors import (
    get_customer_messages,
    is_automatic_message,
)


def message(
    *,
    subject="RE: Example case",
    preview="",
    body=None,
    unique_body=None,
    received="2026-08-10T18:40:00Z",
    headers=None,
):
    value = {
        "subject": subject,
        "bodyPreview": preview,
        "receivedDateTime": received,
        "from": {
            "emailAddress": {
                "address": "customer@example.com"
            }
        }
    }

    if body is not None:
        value["body"] = body

    if unique_body is not None:
        value["uniqueBody"] = unique_body

    if headers is not None:
        value["headers"] = headers

    return value


class MessageContentExtractionTests(unittest.TestCase):
    def test_outlook_html_keeps_only_the_new_reply(self):
        value = message(
            preview=(
                "Hola estoy muy enojado!!!!\r\n"
                "________________________________\r\nFrom: Engineer"
            ),
            body={
                "contentType": "html",
                "content": (
                    "<html><head><style>p { color: red; }</style></head><body>"
                    "<div>Hola estoy muy enojado!!!!</div>"
                    "<div id=\"appendonsend\"></div><hr>"
                    "<div id=\"divRplyFwdMsg\">From: Engineer</div>"
                    "<div>Please escalate this data breach.</div>"
                    "</body></html>"
                )
            }
        )

        content = get_message_content(value)

        self.assertEqual(content.text, "Hola estoy muy enojado!!!!")
        self.assertEqual(content.source, "body")
        self.assertTrue(content.quoted_content_removed)
        self.assertNotIn("data breach", content.text)

    def test_unique_body_is_preferred_when_power_automate_provides_it(self):
        value = message(
            preview="Please escalate this data breach.",
            body={
                "contentType": "html",
                "content": "<div>Please escalate this data breach.</div>"
            },
            unique_body={
                "contentType": "html",
                "content": "<div>Thank you, everything is resolved.</div>"
            }
        )

        content = get_message_content(value)

        self.assertEqual(content.text, "Thank you, everything is resolved.")
        self.assertEqual(content.source, "uniqueBody")

    def test_body_preview_is_cleaned_as_a_legacy_fallback(self):
        value = message(
            preview=(
                "This is the current reply.\n"
                "________________________________\n"
                "From: Engineer\nSent: Monday\n"
                "Please escalate the previous message."
            )
        )

        content = get_message_content(value)

        self.assertEqual(content.text, "This is the current reply.")
        self.assertEqual(content.source, "bodyPreview")
        self.assertTrue(content.quoted_content_removed)

    def test_plain_text_body_removes_standard_quoted_headers(self):
        value = message(
            body={
                "contentType": "text",
                "content": (
                    "Current response\n\n"
                    "From: Engineer <engineer@example.com>\n"
                    "Sent: Monday\nTo: Customer\nSubject: Case\n"
                    "Old message"
                )
            }
        )

        content = get_message_content(value)

        self.assertEqual(content.text, "Current response")
        self.assertTrue(content.quoted_content_removed)

    def test_html_signature_is_not_analyzed_as_customer_language(self):
        value = message(
            body={
                "contentType": "html",
                "content": (
                    "<div>Thanks for the update.</div>"
                    "<div id=\"Signature\">Urgent Security Escalation Team</div>"
                )
            }
        )

        content = get_message_content(value)

        self.assertEqual(content.text, "Thanks for the update.")
        self.assertTrue(content.signature_removed)


class AnalyzerContentIntegrationTests(unittest.TestCase):
    def analyze_keywords(self, messages):
        with patch.dict(os.environ, {"ENGINEER_EMAILS": ""}, clear=False):
            return asyncio.run(analyze_keywords(messages))

    def test_keyword_uses_long_body_content_beyond_the_truncated_preview(self):
        value = message(
            preview="Here is the first part of the context.",
            body={
                "contentType": "html",
                "content": (
                    "<div>Here is the first part of the context. "
                    "Additional technical details follow. "
                    "I need this fixed NOW because we are losing revenue."
                    "</div><div id=\"appendonsend\"></div>"
                    "<div>Old reply</div>"
                )
            }
        )

        result = self.analyze_keywords([value])

        self.assertEqual(
            result["details"]["analyzedMessage"]["textSource"],
            "body"
        )
        self.assertIn("urgent_request", result["details"]["triggeredTopics"])
        self.assertIn("business_impact", result["details"]["triggeredTopics"])

    def test_keyword_does_not_reuse_risk_language_from_quoted_history(self):
        value = message(
            preview="Thanks for the update.",
            body={
                "contentType": "html",
                "content": (
                    "<div>Thanks for the update.</div>"
                    "<div id=\"appendonsend\"></div><hr>"
                    "<div>Please escalate this confirmed data breach.</div>"
                )
            }
        )

        result = self.analyze_keywords([value])

        self.assertEqual(result["details"]["triggeredTopics"], [])
        self.assertEqual(result["score"], 0.0)
        self.assertTrue(
            result["details"]["analyzedMessage"]["quotedContentRemoved"]
        )

    def test_automatic_reply_is_ignored_by_keyword_and_sentiment(self):
        customer_message = message(
            subject="Urgent request",
            preview="This is urgent.",
            received="2026-08-10T18:39:00Z"
        )
        automatic_reply = message(
            preview="I am currently out of the office.",
            body={
                "contentType": "html",
                "content": (
                    "<div>I am currently out of the office and will return "
                    "next week. If this is urgent, contact someone else.</div>"
                )
            },
            received="2026-08-10T18:44:00Z"
        )
        thread = [customer_message, automatic_reply]

        keyword = self.analyze_keywords(thread)
        sentiment = asyncio.run(analyze_sentimental(thread))

        self.assertEqual(
            keyword["details"]["analyzedMessage"]["received"],
            customer_message["receivedDateTime"]
        )
        self.assertEqual(keyword["details"]["customerMessageCount"], 1)
        self.assertEqual(keyword["details"]["ignoredAutomaticMessageCount"], 1)
        self.assertEqual(sentiment["details"]["analyzedMessages"], 1)
        self.assertEqual(sentiment["details"]["ignoredAutomaticMessages"], 1)

    def test_frequency_uses_the_shared_body_auto_reply_filter(self):
        automatic_reply = message(
            preview="I am currently out of the office.",
            received="2026-08-10T18:44:00Z"
        )

        result = asyncio.run(analyze_frequency(
            [automatic_reply],
            now=datetime(2026, 8, 10, 20, 0)
        ))

        self.assertEqual(result["details"]["spamMessagesIgnored"], 1)
        self.assertEqual(result["details"]["customerMessages"], 0)


class AutomaticMessageDetectionTests(unittest.TestCase):
    def test_out_of_office_body_from_real_payload_shape_is_automatic(self):
        value = message(
            preview=(
                "I am currently out of the office and will return on [Date]. "
                "I will have limited access to my email during this time."
            )
        )

        self.assertTrue(is_automatic_message(value))
        self.assertEqual(get_customer_messages([value]), [])

    def test_auto_submitted_no_is_not_an_automatic_reply(self):
        value = message(
            preview="Normal customer response",
            headers={"Auto-Submitted": "no"}
        )

        self.assertFalse(is_automatic_message(value))

    def test_graph_internet_message_headers_are_supported(self):
        value = message(preview="Automated acknowledgement")
        value["internetMessageHeaders"] = [
            {"name": "Auto-Submitted", "value": "auto-replied"}
        ]

        self.assertTrue(is_automatic_message(value))


if __name__ == "__main__":
    unittest.main()
