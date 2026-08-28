import asyncio
import os
import unittest
from unittest.mock import patch

from escalation_engine.analyzers.sentimental import analyze_sentimental
from escalation_engine.thread.conditioning import build_sentiment_transcript
from escalation_engine.thread.selectors import ENGINEER_EMAILS_ENV_VAR


ENGINEER_EMAIL = "engineer@example.com"


def message(
    sender,
    content,
    received,
    *,
    subject="Subject that must not reach the model",
    headers=None,
):
    value = {
        "subject": subject,
        "receivedDateTime": received,
        "from": {"emailAddress": {"address": sender}},
        "body": {"contentType": "html", "content": content},
    }

    if headers is not None:
        value["headers"] = headers

    return value


class SentimentConditioningTests(unittest.TestCase):
    def condition(self, thread):
        with patch.dict(
            os.environ,
            {ENGINEER_EMAILS_ENV_VAR: ENGINEER_EMAIL},
            clear=False,
        ):
            return build_sentiment_transcript(thread)

    def test_builds_training_format_in_chronological_order(self):
        initial_customer = message(
            "customer@example.com",
            "<div>The portal still shows the wrong charge.</div>",
            "2026-08-10T10:00:00Z",
        )
        support_reply = message(
            ENGINEER_EMAIL,
            "<div>I am reviewing the billing history.</div>",
            "2026-08-10T11:00:00Z",
        )
        customer_followup = message(
            "customer@example.com",
            "<div>This is now affecting our deadline.</div>",
            "2026-08-10T12:00:00Z",
        )

        result = self.condition([
            customer_followup,
            initial_customer,
            support_reply,
        ])

        self.assertEqual(
            result.text,
            "Customer: The portal still shows the wrong charge.\n"
            "Support: I am reviewing the billing history.\n"
            "Customer: This is now affecting our deadline.",
        )
        self.assertEqual(result.analyzed_messages, 3)
        self.assertEqual(result.included_turns, 3)
        self.assertEqual(result.ignored_automatic_messages, 0)
        self.assertEqual(result.text_sources, {"body": 3})
        self.assertNotIn("Subject that must not reach the model", result.text)

    def test_removes_quoted_history_and_flattens_message_paragraphs(self):
        customer = message(
            "customer@example.com",
            (
                "<div>Current paragraph.</div><div>Second paragraph.</div>"
                "<div id=\"appendonsend\"></div>"
                "<div>Please escalate the old quoted message.</div>"
            ),
            "2026-08-10T10:00:00Z",
        )

        result = self.condition([customer])

        self.assertEqual(
            result.text,
            "Customer: Current paragraph. Second paragraph.",
        )
        self.assertNotIn("old quoted message", result.text)

    def test_ignores_automatic_and_empty_messages(self):
        customer = message(
            "customer@example.com",
            "<div>We need an update.</div>",
            "2026-08-10T10:00:00Z",
        )
        automatic = message(
            ENGINEER_EMAIL,
            "<div>I am currently out of the office.</div>",
            "2026-08-10T10:05:00Z",
            subject="Automatic reply",
        )
        empty_support = message(
            ENGINEER_EMAIL,
            "<div>   </div>",
            "2026-08-10T10:10:00Z",
        )

        result = self.condition([customer, automatic, empty_support])

        self.assertEqual(result.text, "Customer: We need an update.")
        self.assertEqual(result.analyzed_messages, 2)
        self.assertEqual(result.included_turns, 1)
        self.assertEqual(result.ignored_automatic_messages, 1)
        self.assertEqual(result.text_sources, {"body": 1, "none": 1})

    def test_sentiment_analyzer_reports_conditioning_coverage(self):
        customer = message(
            "customer@example.com",
            "<div>We need an update.</div>",
            "2026-08-10T10:00:00Z",
        )

        with patch.dict(
            os.environ,
            {ENGINEER_EMAILS_ENV_VAR: ENGINEER_EMAIL},
            clear=False,
        ):
            result = asyncio.run(analyze_sentimental([customer]))

        self.assertEqual(result["score"], 0.82)
        self.assertEqual(result["details"]["conditionedTurns"], 1)
        self.assertEqual(result["details"]["analyzedMessages"], 1)


if __name__ == "__main__":
    unittest.main()
