import asyncio
import unittest

from escalation_engine.analyzers.keyword import analyze_keywords


class KeywordVocabularyTests(unittest.TestCase):
    def analyze(self, preview, subject="Case update"):
        result = asyncio.run(
            analyze_keywords([
                {
                    "subject": subject,
                    "bodyPreview": preview,
                    "receivedDateTime": "2026-08-09T12:00:00Z",
                    "from": {
                        "emailAddress": {
                            "address": "customer@example.com"
                        }
                    }
                }
            ])
        )

        return result

    def topic(self, result, topic_name):
        return next(
            topic
            for topic in result["details"]["topics"]
            if topic["topic"] == topic_name
        )

    def test_unrecognized_billing_and_unauthorized_activity(self):
        result = self.analyze(
            "I found an unrecognized recurring charge that I did not authorize."
        )

        billing = self.topic(result, "billing_issue")

        self.assertIn("charge", billing["uniqueMatches"])
        self.assertIn("unrecognized recurring charge", billing["uniqueMatches"])
        self.assertIn("security_concern", result["details"]["triggeredTopics"])

    def test_access_blocker_language(self):
        result = self.analyze(
            "My login is constantly failing and I am blocked on additional testing."
        )

        self.assertIn("technical_failure", result["details"]["triggeredTopics"])

    def test_business_impact_language(self):
        result = self.analyze(
            "Our project migration is at a standstill and we are paying full price."
        )

        self.assertIn("business_impact", result["details"]["triggeredTopics"])

    def test_spanish_security_and_billing_language(self):
        result = self.analyze(
            "Detectamos un cobro no reconocido y posible uso no autorizado."
        )

        billing = self.topic(result, "billing_issue")

        self.assertIn("cobro", billing["uniqueMatches"])
        self.assertIn("cobro no reconocido", billing["uniqueMatches"])
        self.assertIn("security_concern", result["details"]["triggeredTopics"])

    def test_resolution_language_with_generic_subject_does_not_trigger(self):
        result = self.analyze(
            "Everything is working as expected. Please close the ticket."
        )

        self.assertEqual(result["details"]["triggeredTopics"], [])

    def test_disabled_subscription_state(self):
        result = self.analyze(
            "Our subscription is disabled because the spending limit was reached."
        )

        self.assertIn("subscription_state", result["details"]["triggeredTopics"])

    def test_payment_failure_vocabulary(self):
        result = self.analyze(
            "Our card was declined and the invoice appears unpaid."
        )

        self.assertIn("billing_issue", result["details"]["triggeredTopics"])

    def test_quota_capacity_vocabulary(self):
        result = self.analyze(
            "Deployment failed with quota exceeded and no available capacity."
        )

        self.assertIn("quota_capacity", result["details"]["triggeredTopics"])

    def test_failed_ownership_transfer_vocabulary(self):
        result = self.analyze(
            "The transfer failed and we lost access after the transfer."
        )

        self.assertIn("transfer_ownership", result["details"]["triggeredTopics"])

    def test_support_breakdown_vocabulary(self):
        result = self.analyze(
            "There is still no response and the case was closed without resolution."
        )

        self.assertIn("support_breakdown", result["details"]["triggeredTopics"])

    def test_completed_transfer_is_neutral(self):
        result = self.analyze(
            "The billing ownership transfer completed successfully and access is working."
        )

        self.assertEqual(result["details"]["triggeredTopics"], [])

    def test_normal_quota_request_is_neutral(self):
        result = self.analyze(
            "We submitted a quota increase request for planned growth."
        )

        self.assertEqual(result["details"]["triggeredTopics"], [])

    def test_single_generic_technical_signal_stays_below_threshold(self):
        result = self.analyze("There is an issue with the operation.")

        technical = self.topic(result, "technical_failure")

        self.assertEqual(technical["weightedMatches"], 1)
        self.assertFalse(technical["triggered"])

    def test_common_quota_pair_stays_below_threshold(self):
        result = self.analyze("The deployment returned quota exceeded.")

        quota = self.topic(result, "quota_capacity")

        self.assertEqual(quota["weightedMatches"], 2)
        self.assertFalse(quota["triggered"])

    def test_explicit_urgency_triggers_with_one_signal(self):
        result = self.analyze("This is urgent.")

        urgent = self.topic(result, "urgent_request")

        self.assertEqual(urgent["weightedMatches"], 1)
        self.assertTrue(urgent["triggered"])

    def test_critical_security_phrase_has_double_weight(self):
        result = self.analyze("We confirmed a data breach.")

        security = self.topic(result, "security_concern")

        self.assertEqual(security["weightedMatches"], 2)
        self.assertTrue(security["triggered"])
        self.assertEqual(
            security["criticalPhraseMatches"][0]["weightMultiplier"],
            2
        )


if __name__ == "__main__":
    unittest.main()
