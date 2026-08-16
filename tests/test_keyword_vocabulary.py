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

    def analyze_thread(self, messages):
        return asyncio.run(analyze_keywords(messages))

    def test_unrecognized_billing_and_unauthorized_activity(self):
        result = self.analyze(
            "I found an unrecognized recurring charge that I did not authorize."
        )

        billing = self.topic(result, "billing_issue")

        self.assertIn("unrecognized recurring charge", billing["uniqueMatches"])
        self.assertIn(
            "charge",
            [match["value"] for match in billing["keywordMatches"]]
        )
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

        self.assertIn("cobro no reconocido", billing["uniqueMatches"])
        self.assertIn(
            "cobro",
            [match["value"] for match in billing["keywordMatches"]]
        )
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

    def test_single_generic_issue_is_not_a_technical_failure(self):
        result = self.analyze("There is an issue with the operation.")

        technical = self.topic(result, "technical_failure")

        self.assertEqual(technical["weightedMatches"], 0)
        self.assertFalse(technical["triggered"])

    def test_common_quota_pair_stays_below_threshold(self):
        result = self.analyze("The deployment returned quota exceeded.")

        quota = self.topic(result, "quota_capacity")

        self.assertEqual(quota["weightedMatches"], 1)
        self.assertFalse(quota["triggered"])

    def test_overlapping_keyword_and_phrase_count_as_one_signal(self):
        result = self.analyze("There is a duplicate charge.")

        billing = self.topic(result, "billing_issue")

        self.assertEqual(billing["weightedMatches"], 2)
        self.assertEqual(billing["uniqueMatches"], ["duplicate charge"])
        self.assertTrue(billing["triggered"])

    def test_repeating_a_generic_word_does_not_cross_threshold(self):
        result = self.analyze("Failure, failure, failure.")

        technical = self.topic(result, "technical_failure")

        self.assertEqual(technical["matches"], 3)
        self.assertEqual(technical["weightedMatches"], 1)
        self.assertFalse(technical["triggered"])

    def test_no_timeline_is_support_breakdown(self):
        result = self.analyze(
            "This has been open for two weeks with no resolution and no timeline."
        )

        support = self.topic(result, "support_breakdown")

        self.assertIn("no timeline", support["uniqueMatches"])
        self.assertTrue(support["triggered"])

    def test_positive_timeline_language_is_neutral(self):
        result = self.analyze(
            "Great, that timeline works fine for us. Thanks for the quick answer."
        )

        self.assertEqual(result["details"]["triggeredTopics"], [])
        self.assertEqual(result["score"], 0.0)

    def test_stale_reply_subject_does_not_trigger_resolved_message(self):
        result = self.analyze(
            "The subscription is active now and everything is working.",
            subject="RE: Production subscription still disabled"
        )

        self.assertEqual(result["details"]["triggeredTopics"], [])
        self.assertEqual(result["score"], 0.0)
        self.assertTrue(
            result["details"]["analyzedMessage"]["subjectEvidenceIgnored"]
        )

    def test_subject_is_ignored_on_existing_thread_without_reply_prefix(self):
        result = self.analyze_thread([
            {
                "subject": "Production subscription disabled",
                "bodyPreview": "Please help.",
                "receivedDateTime": "2026-08-09T11:00:00Z"
            },
            {
                "subject": "Production subscription disabled",
                "bodyPreview": "It is active now. Thank you for the fast help.",
                "receivedDateTime": "2026-08-09T12:00:00Z"
            }
        ])

        self.assertEqual(result["details"]["triggeredTopics"], [])
        self.assertEqual(result["score"], 0.0)

    def test_fresh_subject_can_supply_high_precision_evidence(self):
        result = self.analyze(
            "Please help with the case.",
            subject="URGENT: production subscription is disabled"
        )

        self.assertIn("urgent_request", result["details"]["triggeredTopics"])
        self.assertIn("subscription_state", result["details"]["triggeredTopics"])

    def test_negated_urgency_does_not_trigger(self):
        result = self.analyze("This is not urgent; tomorrow is fine.")

        self.assertEqual(result["details"]["triggeredTopics"], [])

    def test_negated_and_ruled_out_risks_do_not_trigger(self):
        result = self.analyze(
            "The issue was resolved and there was no outage. "
            "An account compromise was ruled out."
        )

        self.assertEqual(result["details"]["triggeredTopics"], [])
        self.assertEqual(result["score"], 0.0)

    def test_acknowledging_a_completed_escalation_is_not_an_urgent_request(self):
        result = self.analyze(
            "I appreciate the escalation. The matter is resolved now."
        )

        urgent = self.topic(result, "urgent_request")

        self.assertEqual(urgent["weightedMatches"], 0)
        self.assertFalse(urgent["triggered"])

    def test_resolved_refund_does_not_count_as_current_billing_evidence(self):
        result = self.analyze(
            "The refund has posted and everything looks correct now.",
            subject="RE: Refund request denied"
        )

        self.assertEqual(result["details"]["triggeredTopics"], [])
        self.assertEqual(result["score"], 0.0)

    def test_message_length_does_not_dilute_explicit_urgency(self):
        short = self.analyze("This is urgent.")
        long = self.analyze(
            "This is urgent. " + "Here is additional context for the team. " * 20
        )

        self.assertEqual(short["score"], long["score"])

    def test_duration_and_repeated_attempt_patterns_generalize(self):
        result = self.analyze(
            "This should not have taken 12 days and multiple follow-ups."
        )

        support = self.topic(result, "support_breakdown")

        self.assertTrue(support["triggered"])
        self.assertGreaterEqual(len(support["patternMatches"]), 2)

    def test_elapsed_week_without_response_triggers_support_breakdown(self):
        result = self.analyze(
            "It's been almost a week and I haven't heard anything further."
        )

        support = self.topic(result, "support_breakdown")

        self.assertTrue(support["triggered"])
        self.assertIn("elapsed handling duration", support["uniqueMatches"])
        self.assertIn("haven t heard anything", support["uniqueMatches"])

    def test_elapsed_time_alone_stays_below_threshold(self):
        result = self.analyze(
            "It's been almost a week since launch and everything works well."
        )

        support = self.topic(result, "support_breakdown")

        self.assertEqual(support["weightedMatches"], 1)
        self.assertFalse(support["triggered"])

    def test_material_cost_and_production_language_triggers_business_impact(self):
        result = self.analyze(
            "This is a material cost increase on a production workload."
        )

        self.assertIn("business_impact", result["details"]["triggeredTopics"])

    def test_review_request_and_explicit_rejection_are_detected(self):
        result = self.analyze(
            "We had zero notice and that is not acceptable. "
            "I need this reviewed by someone accountable."
        )

        self.assertIn("urgent_request", result["details"]["triggeredTopics"])
        self.assertIn("support_breakdown", result["details"]["triggeredTopics"])

    def test_update_request_with_delay_and_committed_spend_triggers(self):
        result = self.analyze(
            "Any update? It's been 3 days and our committed spend is in "
            "the wrong term."
        )

        self.assertIn("business_impact", result["details"]["triggeredTopics"])
        self.assertIn("support_breakdown", result["details"]["triggeredTopics"])

    def test_routine_update_request_alone_does_not_trigger(self):
        result = self.analyze("Any update on the routine request?")

        support = self.topic(result, "support_breakdown")

        self.assertEqual(support["weightedMatches"], 1)
        self.assertFalse(support["triggered"])

    def test_appeal_and_missing_disclosure_language_triggers(self):
        result = self.analyze(
            "That's ridiculous. Nobody mentioned this policy. Can I appeal it?"
        )

        self.assertIn("urgent_request", result["details"]["triggeredTopics"])
        self.assertIn("support_breakdown", result["details"]["triggeredTopics"])

    def test_refund_limit_is_not_quota_capacity(self):
        result = self.analyze(
            "Nobody mentioned an annual refund limit when I asked for help."
        )

        quota = self.topic(result, "quota_capacity")

        self.assertEqual(quota["weightedMatches"], 0)

    def test_data_entry_error_is_not_a_technical_failure(self):
        result = self.analyze("This was a data entry error on our side.")

        technical = self.topic(result, "technical_failure")

        self.assertEqual(technical["weightedMatches"], 0)

    def test_revenue_loss_and_immediate_fix_request_are_critical(self):
        result = self.analyze(
            "It's been over 24 hours and resources are still inaccessible. "
            "We are losing revenue every hour this is down. "
            "I need this fixed NOW, not another status update."
        )

        for topic in (
            "technical_failure",
            "urgent_request",
            "business_impact",
            "support_breakdown"
        ):
            self.assertIn(topic, result["details"]["triggeredTopics"])

    def test_business_critical_outage_is_failure_and_impact(self):
        result = self.analyze(
            "This is a business-critical outage and I need an answer today."
        )

        self.assertIn("technical_failure", result["details"]["triggeredTopics"])
        self.assertIn("urgent_request", result["details"]["triggeredTopics"])
        self.assertIn("business_impact", result["details"]["triggeredTopics"])

    def test_formal_complaint_and_multi_day_outage_are_detected(self):
        result = self.analyze(
            "This is day 4 of a preventable outage. I am requesting immediate "
            "escalation and filing a formal complaint."
        )

        self.assertIn("technical_failure", result["details"]["triggeredTopics"])
        self.assertIn("urgent_request", result["details"]["triggeredTopics"])
        self.assertIn("support_breakdown", result["details"]["triggeredTopics"])
        self.assertIn(
            "customer_relationship_risk",
            result["details"]["triggeredTopics"]
        )

    def test_relationship_risk_language_triggers(self):
        result = self.analyze(
            "This incident has made us seriously reconsider relying on this vendor."
        )

        self.assertIn(
            "customer_relationship_risk",
            result["details"]["triggeredTopics"]
        )

    def test_spanish_accents_are_normalized(self):
        result = self.analyze(
            "Tenemos un problema de facturación y un cobro no reconocido."
        )

        self.assertIn("billing_issue", result["details"]["triggeredTopics"])

    def test_spanish_resolution_language_suppresses_old_problem(self):
        result = self.analyze(
            "El problema de facturación ya fue resuelto y el reembolso fue aprobado.",
            subject="RE: Problema de facturación"
        )

        self.assertEqual(result["details"]["triggeredTopics"], [])
        self.assertEqual(result["score"], 0.0)

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

    def test_repeated_rejections_and_missing_reason_trigger_support_breakdown(self):
        result = self.analyze(
            "I've submitted my verification documents 3 times, I keep "
            "getting rejected, and there is no clear reason."
        )

        self.assertIn("support_breakdown", result["details"]["triggeredTopics"])

    def test_same_day_approval_and_blocked_start_are_detected(self):
        result = self.analyze(
            "My deadline is in 2 days and I have zero credit to even start "
            "the assignment. I need this approved today."
        )

        self.assertIn("urgent_request", result["details"]["triggeredTopics"])
        self.assertIn("business_impact", result["details"]["triggeredTopics"])

    def test_resolved_thank_you_suppresses_historical_support_trigger(self):
        result = self.analyze(
            "Thank you for finally getting it done, but this should not have "
            "taken 10 days and three rejected attempts."
        )
        support = self.topic(result, "support_breakdown")

        self.assertTrue(
            result["details"]["analyzedMessage"]["resolutionAcknowledged"]
        )
        self.assertGreaterEqual(support["rawWeightedMatches"], 2)
        self.assertEqual(support["weightedMatches"], 0)
        self.assertTrue(support["suppressedByResolution"])
        self.assertNotIn(
            "support_breakdown",
            result["details"]["triggeredTopics"]
        )

    def test_active_request_for_resolution_is_not_a_resolution_acknowledgement(self):
        result = self.analyze(
            "Any update? This is a huge unexpected hit and I need this "
            "resolved before the invoice is due."
        )

        self.assertFalse(
            result["details"]["analyzedMessage"]["resolutionAcknowledged"]
        )

    def test_resolved_payment_does_not_hide_an_active_subscription_outage(self):
        result = self.analyze(
            "Our subscription was disabled for a payment issue that we "
            "resolved two days ago, but the subscription is still disabled "
            "and our "
            "production app is down. This is urgent."
        )

        self.assertFalse(
            result["details"]["analyzedMessage"]["resolutionAcknowledged"]
        )
        self.assertIn(
            "technical_failure",
            result["details"]["triggeredTopics"]
        )
        subscription = self.topic(result, "subscription_state")
        self.assertGreaterEqual(subscription["weightedMatches"], 1)
        self.assertEqual(
            subscription["weightedMatches"],
            subscription["rawWeightedMatches"]
        )
        self.assertFalse(subscription["suppressedByResolution"])

    def test_active_again_is_a_resolution_acknowledgement(self):
        result = self.analyze(
            "Subscription is finally active again. The outage damaged our "
            "trust in the service."
        )

        self.assertTrue(
            result["details"]["analyzedMessage"]["resolutionAcknowledged"]
        )
        self.assertNotIn(
            "technical_failure",
            result["details"]["triggeredTopics"]
        )

    def test_routine_invoice_structure_question_is_neutral(self):
        result = self.analyze(
            "We have three subscriptions under one billing profile. Do we "
            "get one consolidated invoice or a separate invoice for each?"
        )

        self.assertEqual(result["details"]["triggeredTopics"], [])

    def test_preventive_service_interruption_language_is_not_current_impact(self):
        result = self.analyze(
            "How do I update the card before it lapses and causes a service "
            "interruption?"
        )

        self.assertNotIn(
            "business_impact",
            result["details"]["triggeredTopics"]
        )

    def test_routine_reactivation_request_is_one_subscription_signal(self):
        result = self.analyze(
            "Our dev subscription lapsed and we want to reactivate it."
        )
        subscription = self.topic(result, "subscription_state")

        self.assertEqual(subscription["weightedMatches"], 1)
        self.assertFalse(subscription["triggered"])


if __name__ == "__main__":
    unittest.main()
