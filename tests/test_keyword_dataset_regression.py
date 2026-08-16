import asyncio
import json
import os
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from escalation_engine.analyzers.keyword import analyze_keywords
from escalation_engine.thread.extractors import (
    get_message_content,
    get_preview,
    get_received_datetime,
    get_sender_address,
    get_subject,
    parse_received_datetime,
)
from escalation_engine.thread.selectors import (
    CUSTOMER_ROLE,
    get_message_role,
    is_automatic_message,
)


FIXTURE_PATH = Path(__file__).with_name("azure_billing_escalation_threads.json")
EXPECTED_TRIGGERED_CASES = set(range(1, 16))
DEFAULT_ESCALATION_CONTEXT = ("none", None, None, False)
EXPECTED_ESCALATION_CONTEXT_OVERRIDES = {
    (1, 3): ("mentioned", None, None, False),
    (1, 4): ("active", "hierarchical", "manager", True),
    (2, 4): ("active", "hierarchical", "manager", True),
    (2, 5): ("historical", None, None, False),
    (3, 4): ("active", "hierarchical", "manager", True),
    (4, 4): ("active", "generic", None, True),
    (8, 4): ("active", "hierarchical", "manager", True),
    (9, 4): ("active", "hierarchical", "manager", True),
    (10, 4): ("active", "generic", None, True),
}
EXPECTED_KEYWORD_TIMELINES = {
    1: [
        (0.50, ("billing_issue",), False),
        (0.65, ("business_impact", "support_breakdown"), False),
        (0.72, ("urgent_request", "support_breakdown"), False),
        (
            0.80,
            (
                "urgent_request",
                "support_breakdown",
                "customer_relationship_risk",
            ),
            False,
        ),
    ],
    2: [
        (0.65, ("billing_issue", "urgent_request"), False),
        (0.65, ("business_impact", "support_breakdown"), False),
        (0.72, ("urgent_request", "support_breakdown"), False),
        (0.72, ("urgent_request", "support_breakdown"), False),
        (0.50, ("customer_relationship_risk",), True),
    ],
    3: [
        (
            0.88,
            ("technical_failure", "urgent_request", "subscription_state"),
            False,
        ),
        (
            0.95,
            (
                "technical_failure",
                "urgent_request",
                "business_impact",
                "support_breakdown",
            ),
            False,
        ),
        (
            0.80,
            ("technical_failure", "urgent_request", "business_impact"),
            False,
        ),
        (
            1.00,
            (
                "technical_failure",
                "urgent_request",
                "support_breakdown",
                "customer_relationship_risk",
            ),
            False,
        ),
        (0.50, ("customer_relationship_risk",), True),
    ],
    4: [
        (0.50, ("billing_issue",), False),
        (0.50, ("billing_issue",), False),
        (0.72, ("billing_issue", "support_breakdown"), False),
        (0.72, ("urgent_request", "support_breakdown"), False),
    ],
    5: [
        (0.50, ("support_breakdown",), False),
        (0.00, (), False),
        (0.57, ("support_breakdown",), False),
        (
            0.80,
            ("urgent_request", "business_impact", "support_breakdown"),
            False,
        ),
        (0.25, (), True),
    ],
    6: [
        (0.57, ("billing_issue",), False),
        (0.57, ("billing_issue",), False),
        (0.65, ("business_impact",), False),
        (0.57, ("urgent_request",), False),
        (0.50, ("business_impact",), True),
    ],
    7: [
        (0.50, ("billing_issue",), False),
        (0.25, (), False),
        (0.57, ("billing_issue",), False),
        (0.57, ("billing_issue",), False),
        (0.00, (), True),
    ],
    8: [
        (
            0.88,
            ("technical_failure", "business_impact", "subscription_state"),
            False,
        ),
        (0.72, ("urgent_request", "business_impact"), False),
        (0.57, ("technical_failure",), False),
        (
            0.88,
            ("urgent_request", "business_impact", "subscription_state"),
            False,
        ),
        (
            0.65,
            ("business_impact", "customer_relationship_risk"),
            True,
        ),
    ],
    9: [
        (0.65, ("billing_issue", "urgent_request"), False),
        (0.57, ("billing_issue",), False),
        (0.50, ("billing_issue",), False),
        (
            0.80,
            ("billing_issue", "urgent_request", "support_breakdown"),
            False,
        ),
        (0.50, ("customer_relationship_risk",), True),
    ],
    10: [
        (0.25, (), False),
        (0.57, ("business_impact",), False),
        (0.65, ("business_impact", "support_breakdown"), False),
        (
            0.80,
            ("urgent_request", "business_impact", "support_breakdown"),
            False,
        ),
        (0.50, ("business_impact",), True),
    ],
    11: [
        (0.50, ("billing_issue",), False),
        (0.72, ("urgent_request", "business_impact"), False),
        (0.57, ("billing_issue",), False),
        (0.65, ("business_impact",), False),
        (0.00, (), True),
    ],
    12: [
        (0.57, ("support_breakdown",), False),
        (0.25, (), False),
        (0.50, ("support_breakdown",), False),
        (0.25, (), False),
        (0.00, (), True),
    ],
    13: [
        (
            1.00,
            (
                "technical_failure",
                "urgent_request",
                "business_impact",
                "subscription_state",
            ),
            False,
        ),
        (0.80, ("urgent_request", "business_impact"), False),
        (0.00, (), True),
        (0.65, ("business_impact",), False),
        (0.00, (), True),
    ],
    14: [
        (0.50, ("billing_issue",), False),
        (0.50, ("business_impact",), False),
        (0.25, (), False),
        (0.50, ("business_impact",), True),
    ],
    15: [
        (0.72, ("billing_issue",), False),
        (0.57, ("support_breakdown",), False),
        (
            0.88,
            ("billing_issue", "urgent_request", "business_impact"),
            False,
        ),
        (0.25, (), False),
        (0.00, (), True),
    ],
    16: [(0.25, (), False), (0.00, (), False), (0.00, (), False)],
    17: [(0.25, (), False), (0.00, (), False), (0.00, (), False)],
    18: [(0.00, (), False), (0.00, (), False), (0.00, (), False)],
    19: [(0.25, (), False), (0.00, (), False)],
    20: [(0.00, (), False), (0.00, (), False), (0.00, (), False)],
    21: [(0.00, (), False), (0.00, (), False)],
    22: [(0.00, (), False), (0.00, (), False), (0.00, (), False)],
    23: [(0.25, (), False), (0.00, (), False), (0.00, (), False)],
    24: [(0.00, (), False), (0.00, (), False), (0.00, (), False)],
    25: [(0.25, (), False), (0.25, (), False), (0.00, (), False)],
}


class KeywordDatasetRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            cls.fixture = json.load(fixture_file)

        cls.engineer_emails = {
            message.get("from", {}).get("emailAddress", {}).get("address", "")
            for request in cls.fixture
            for message in request["body"]["thread"]
            if message.get("from", {})
            .get("emailAddress", {})
            .get("address", "")
            .endswith("@microsoft.com")
        }

    @staticmethod
    def sort_messages(messages):
        return sorted(
            messages,
            key=lambda message: parse_received_datetime(message) or datetime.min
        )

    def test_each_customer_message_is_analyzed_as_an_incremental_event(self):
        """Simulate one Function invocation per newly received customer email."""
        total_customer_events = 0

        with patch.dict(
            os.environ,
            {"ENGINEER_EMAILS": ",".join(self.engineer_emails)},
            clear=False
        ):
            for case_number, request in enumerate(self.fixture, start=1):
                accumulated_thread = []
                customer_message_count = 0
                engineer_message_count = 0
                automatic_message_count = 0
                latest_incremental_result = None

                for event_number, message in enumerate(
                    self.sort_messages(request["body"]["thread"]),
                    start=1
                ):
                    accumulated_thread.append(message)

                    if is_automatic_message(message):
                        automatic_message_count += 1
                        continue

                    if get_message_role(message) != CUSTOMER_ROLE:
                        engineer_message_count += 1
                        continue

                    customer_message_count += 1
                    total_customer_events += 1
                    result = asyncio.run(
                        analyze_keywords(list(accumulated_thread))
                    )
                    latest_incremental_result = result
                    analyzed_message = result["details"]["analyzedMessage"]
                    extracted_content = get_message_content(message)

                    with self.subTest(
                        case=case_number,
                        event=event_number,
                        customer_event=customer_message_count
                    ):
                        self.assertEqual(
                            analyzed_message["received"],
                            get_received_datetime(message)
                        )
                        self.assertEqual(
                            analyzed_message["subject"],
                            get_subject(message)
                        )
                        self.assertEqual(
                            analyzed_message["preview"],
                            get_preview(message)
                        )
                        self.assertEqual(
                            analyzed_message["text"],
                            extracted_content.text
                        )
                        self.assertEqual(
                            analyzed_message["textSource"],
                            extracted_content.source
                        )
                        self.assertEqual(
                            analyzed_message["from"],
                            get_sender_address(message)
                        )
                        self.assertEqual(
                            result["details"]["customerMessageCount"],
                            customer_message_count
                        )
                        self.assertEqual(
                            result["details"]["ignoredEngineerMessageCount"],
                            engineer_message_count
                        )
                        self.assertEqual(
                            result["details"]["ignoredAutomaticMessageCount"],
                            automatic_message_count
                        )

                full_thread_result = asyncio.run(
                    analyze_keywords(request["body"]["thread"])
                )

                with self.subTest(case=case_number, comparison="final_state"):
                    self.assertIsNotNone(latest_incremental_result)
                    self.assertEqual(
                        latest_incremental_result["score"],
                        full_thread_result["score"]
                    )
                    self.assertEqual(
                        latest_incremental_result["flags"],
                        full_thread_result["flags"]
                    )
                    self.assertEqual(
                        latest_incremental_result["details"]["topics"],
                        full_thread_result["details"]["topics"]
                    )

        self.assertEqual(total_customer_events, 100)

    def test_generated_language_fixture_separates_risk_trajectories_and_controls(self):
        """Risk cases trigger while neutral controls stay quiet at every step."""
        triggered_cases = set()

        with patch.dict(
            os.environ,
            {"ENGINEER_EMAILS": ",".join(self.engineer_emails)},
            clear=False
        ):
            for case_number, request in enumerate(self.fixture, start=1):
                accumulated_thread = []

                for message in self.sort_messages(request["body"]["thread"]):
                    accumulated_thread.append(message)

                    if get_message_role(message) != CUSTOMER_ROLE:
                        continue

                    result = asyncio.run(
                        analyze_keywords(list(accumulated_thread))
                    )

                    if result["details"]["triggeredTopics"]:
                        triggered_cases.add(case_number)
                        break

        self.assertEqual(triggered_cases, EXPECTED_TRIGGERED_CASES)

    def test_all_customer_events_match_manually_reviewed_baseline(self):
        """Lock every reviewed score, topic set, and resolution transition."""
        self.assertEqual(
            set(EXPECTED_KEYWORD_TIMELINES),
            set(range(1, len(self.fixture) + 1))
        )

        for case_number, expected_timeline in (
            EXPECTED_KEYWORD_TIMELINES.items()
        ):
            customer_results = self._customer_results_for_case(case_number)

            with self.subTest(case=case_number, check="event_count"):
                self.assertEqual(
                    len(customer_results),
                    len(expected_timeline)
                )

            for customer_event, (result, expected) in enumerate(
                zip(customer_results, expected_timeline),
                start=1
            ):
                expected_score, expected_topics, expected_resolution = expected
                actual = (
                    result["score"],
                    tuple(result["details"]["triggeredTopics"]),
                    result["details"]["analyzedMessage"][
                        "resolutionAcknowledged"
                    ],
                )

                with self.subTest(
                    case=case_number,
                    customer_event=customer_event
                ):
                    self.assertEqual(actual, expected)
                    self.assertEqual(
                        result["label"],
                        "triggered" if expected_topics else "low_signal"
                    )
                    self.assertEqual(result["score"], expected_score)
                    self.assertEqual(
                        result["details"]["analyzedMessage"][
                            "resolutionAcknowledged"
                        ],
                        expected_resolution
                    )

    def test_all_customer_events_match_escalation_context_baseline(self):
        total_customer_events = 0

        for case_number in range(1, len(self.fixture) + 1):
            customer_results = self._customer_results_for_case(case_number)

            for customer_event, result in enumerate(
                customer_results,
                start=1
            ):
                total_customer_events += 1
                request = result["details"]["escalationRequest"]
                actual = (
                    request["status"],
                    request["kind"],
                    request["requestedTarget"],
                    request["tier2Override"],
                )
                expected = EXPECTED_ESCALATION_CONTEXT_OVERRIDES.get(
                    (case_number, customer_event),
                    DEFAULT_ESCALATION_CONTEXT
                )

                with self.subTest(
                    case=case_number,
                    customer_event=customer_event
                ):
                    self.assertEqual(actual, expected)
                    self.assertEqual(
                        "explicit_escalation_request" in result["flags"],
                        expected[3]
                    )

        self.assertEqual(total_customer_events, 100)

    def test_case_one_risk_strengthens_across_customer_interactions(self):
        request = self.fixture[0]
        accumulated_thread = []
        customer_results = []

        with patch.dict(
            os.environ,
            {"ENGINEER_EMAILS": ",".join(self.engineer_emails)},
            clear=False
        ):
            for message in self.sort_messages(request["body"]["thread"]):
                accumulated_thread.append(message)

                if get_message_role(message) != CUSTOMER_ROLE:
                    continue

                customer_results.append(
                    asyncio.run(analyze_keywords(list(accumulated_thread)))
                )

        scores = [result["score"] for result in customer_results]

        self.assertEqual(len(scores), 4)
        self.assertGreater(scores[1], scores[0])
        self.assertGreater(scores[2], scores[1])
        self.assertGreaterEqual(scores[3], scores[2])
        self.assertIn(
            "support_breakdown",
            customer_results[1]["details"]["triggeredTopics"]
        )
        self.assertIn(
            "urgent_request",
            customer_results[2]["details"]["triggeredTopics"]
        )

    def test_case_two_delay_and_appeal_are_not_low_signal(self):
        request = self.fixture[1]
        accumulated_thread = []
        customer_results = []

        with patch.dict(
            os.environ,
            {"ENGINEER_EMAILS": ",".join(self.engineer_emails)},
            clear=False
        ):
            for message in self.sort_messages(request["body"]["thread"]):
                accumulated_thread.append(message)

                if get_message_role(message) != CUSTOMER_ROLE:
                    continue

                customer_results.append(
                    asyncio.run(analyze_keywords(list(accumulated_thread)))
                )

        delayed_update = customer_results[1]
        appeal = customer_results[2]

        self.assertGreaterEqual(delayed_update["score"], 0.5)
        self.assertIn(
            "business_impact",
            delayed_update["details"]["triggeredTopics"]
        )
        self.assertIn(
            "support_breakdown",
            delayed_update["details"]["triggeredTopics"]
        )
        self.assertGreater(appeal["score"], delayed_update["score"])
        self.assertIn("urgent_request", appeal["details"]["triggeredTopics"])
        self.assertIn("support_breakdown", appeal["details"]["triggeredTopics"])
        self.assertNotIn("quota_capacity", appeal["details"]["triggeredTopics"])
        self.assertNotIn("technical_failure", appeal["details"]["triggeredTopics"])

    def test_case_three_operational_impact_is_consistently_high_risk(self):
        request = self.fixture[2]
        accumulated_thread = []
        customer_results = []

        with patch.dict(
            os.environ,
            {"ENGINEER_EMAILS": ",".join(self.engineer_emails)},
            clear=False
        ):
            for message in self.sort_messages(request["body"]["thread"]):
                accumulated_thread.append(message)

                if get_message_role(message) != CUSTOMER_ROLE:
                    continue

                customer_results.append(
                    asyncio.run(analyze_keywords(list(accumulated_thread)))
                )

        revenue_loss = customer_results[1]
        critical_outage = customer_results[2]
        formal_escalation = customer_results[3]
        relationship_damage = customer_results[4]

        self.assertGreaterEqual(revenue_loss["score"], 0.8)
        self.assertIn(
            "business_impact",
            revenue_loss["details"]["triggeredTopics"]
        )
        self.assertIn(
            "support_breakdown",
            revenue_loss["details"]["triggeredTopics"]
        )
        self.assertGreaterEqual(critical_outage["score"], 0.7)
        self.assertIn(
            "technical_failure",
            critical_outage["details"]["triggeredTopics"]
        )
        self.assertIn(
            "business_impact",
            critical_outage["details"]["triggeredTopics"]
        )
        self.assertGreaterEqual(formal_escalation["score"], 0.9)
        self.assertIn(
            "customer_relationship_risk",
            formal_escalation["details"]["triggeredTopics"]
        )
        self.assertNotIn(
            "support_breakdown",
            relationship_damage["details"]["triggeredTopics"]
        )
        self.assertIn(
            "customer_relationship_risk",
            relationship_damage["details"]["triggeredTopics"]
        )
        self.assertTrue(
            relationship_damage["details"]["analyzedMessage"][
                "resolutionAcknowledged"
            ]
        )

    def test_case_five_peaks_before_resolution(self):
        request = self.fixture[4]
        accumulated_thread = []
        customer_results = []

        with patch.dict(
            os.environ,
            {"ENGINEER_EMAILS": ",".join(self.engineer_emails)},
            clear=False
        ):
            for message in self.sort_messages(request["body"]["thread"]):
                accumulated_thread.append(message)

                if get_message_role(message) != CUSTOMER_ROLE:
                    continue

                customer_results.append(
                    asyncio.run(analyze_keywords(list(accumulated_thread)))
                )

        active_blocker = customer_results[3]
        resolved_feedback = customer_results[4]

        self.assertGreaterEqual(active_blocker["score"], 0.8)

        for topic in (
            "urgent_request",
            "business_impact",
            "support_breakdown"
        ):
            self.assertIn(topic, active_blocker["details"]["triggeredTopics"])

        self.assertLess(resolved_feedback["score"], active_blocker["score"])
        self.assertNotIn(
            "support_breakdown",
            resolved_feedback["details"]["triggeredTopics"]
        )
        self.assertTrue(
            resolved_feedback["details"]["analyzedMessage"][
                "resolutionAcknowledged"
            ]
        )

    def test_case_six_detects_credit_delay_before_resolved_impact(self):
        customer_results = self._customer_results_for_case(6)
        initial_credit_failure = customer_results[0]
        prolonged_cash_strain = customer_results[2]
        firm_answer_request = customer_results[3]
        resolved_impact = customer_results[4]

        self.assertIn(
            "billing_issue",
            initial_credit_failure["details"]["triggeredTopics"]
        )
        self.assertIn(
            "business_impact",
            prolonged_cash_strain["details"]["triggeredTopics"]
        )
        self.assertIn(
            "urgent_request",
            firm_answer_request["details"]["triggeredTopics"]
        )
        self.assertNotIn(
            "support_breakdown",
            resolved_impact["details"]["triggeredTopics"]
        )
        self.assertTrue(
            resolved_impact["details"]["analyzedMessage"][
                "resolutionAcknowledged"
            ]
        )

    def test_case_seven_drops_after_hold_is_confirmed(self):
        customer_results = self._customer_results_for_case(7)
        confirmed_billing_error = customer_results[2]
        failed_hold = customer_results[3]
        resolved_feedback = customer_results[4]

        self.assertIn(
            "billing_issue",
            confirmed_billing_error["details"]["triggeredTopics"]
        )
        self.assertIn(
            "billing_issue",
            failed_hold["details"]["triggeredTopics"]
        )
        self.assertEqual(resolved_feedback["score"], 0.0)
        self.assertEqual(resolved_feedback["details"]["triggeredTopics"], [])
        self.assertTrue(
            resolved_feedback["details"]["analyzedMessage"][
                "resolutionAcknowledged"
            ]
        )

    def test_case_eight_captures_client_impact_and_manager_request(self):
        customer_results = self._customer_results_for_case(8)
        suspension = customer_results[0]
        manager_request = customer_results[3]
        relationship_damage = customer_results[4]

        self.assertGreaterEqual(suspension["score"], 0.8)

        for topic in (
            "technical_failure",
            "business_impact",
            "subscription_state"
        ):
            self.assertIn(topic, suspension["details"]["triggeredTopics"])

        self.assertGreaterEqual(manager_request["score"], 0.8)
        self.assertIn(
            "urgent_request",
            manager_request["details"]["triggeredTopics"]
        )
        self.assertIn(
            "customer_relationship_risk",
            relationship_damage["details"]["triggeredTopics"]
        )

    def test_case_nine_peaks_at_missing_refund_manager_request(self):
        customer_results = self._customer_results_for_case(9)
        missing_refund = customer_results[3]
        resolved_relationship_risk = customer_results[4]

        self.assertGreaterEqual(missing_refund["score"], 0.8)

        for topic in (
            "billing_issue",
            "urgent_request",
            "support_breakdown"
        ):
            self.assertIn(topic, missing_refund["details"]["triggeredTopics"])

        self.assertLess(
            resolved_relationship_risk["score"],
            missing_refund["score"]
        )
        self.assertEqual(
            resolved_relationship_risk["details"]["triggeredTopics"],
            ["customer_relationship_risk"]
        )
        self.assertTrue(
            resolved_relationship_risk["details"]["analyzedMessage"][
                "resolutionAcknowledged"
            ]
        )

    def test_case_ten_accumulates_delay_impact_before_resolution(self):
        customer_results = self._customer_results_for_case(10)
        delayed_acquisition = customer_results[1]
        unexplained_delay = customer_results[2]
        escalation_request = customer_results[3]
        resolved_impact = customer_results[4]

        self.assertIn(
            "business_impact",
            delayed_acquisition["details"]["triggeredTopics"]
        )
        self.assertIn(
            "support_breakdown",
            unexplained_delay["details"]["triggeredTopics"]
        )
        self.assertGreaterEqual(escalation_request["score"], 0.8)
        self.assertIn(
            "urgent_request",
            escalation_request["details"]["triggeredTopics"]
        )
        self.assertEqual(
            resolved_impact["details"]["triggeredTopics"],
            ["business_impact"]
        )
        self.assertTrue(
            resolved_impact["details"]["analyzedMessage"][
                "resolutionAcknowledged"
            ]
        )

    def test_case_eleven_detects_material_charge_and_payment_exposure(self):
        customer_results = self._customer_results_for_case(11)
        deleted_resource_charge = customer_results[0]
        unexpected_hit = customer_results[1]
        out_of_pocket_exposure = customer_results[3]
        resolved_refund = customer_results[4]

        self.assertIn(
            "billing_issue",
            deleted_resource_charge["details"]["triggeredTopics"]
        )
        self.assertIn(
            "business_impact",
            unexpected_hit["details"]["triggeredTopics"]
        )
        self.assertIn(
            "urgent_request",
            unexpected_hit["details"]["triggeredTopics"]
        )
        self.assertGreaterEqual(out_of_pocket_exposure["score"], 0.65)
        self.assertIn(
            "business_impact",
            out_of_pocket_exposure["details"]["triggeredTopics"]
        )
        self.assertEqual(resolved_refund["score"], 0.0)
        self.assertNotIn(
            "technical_failure",
            resolved_refund["details"]["triggeredTopics"]
        )

    def test_case_twelve_detects_repeated_denial_and_clears_on_resolution(self):
        customer_results = self._customer_results_for_case(12)
        repeated_denial = customer_results[0]
        ignored_context = customer_results[2]
        resolved_transfer = customer_results[4]

        self.assertIn(
            "support_breakdown",
            repeated_denial["details"]["triggeredTopics"]
        )
        self.assertIn(
            "support_breakdown",
            ignored_context["details"]["triggeredTopics"]
        )
        self.assertEqual(resolved_transfer["score"], 0.0)
        self.assertTrue(
            resolved_transfer["details"]["analyzedMessage"][
                "resolutionAcknowledged"
            ]
        )

    def test_case_thirteen_distinguishes_outage_from_conditional_feedback(self):
        customer_results = self._customer_results_for_case(13)
        production_outage = customer_results[0]
        service_restored = customer_results[2]
        conditional_feedback = customer_results[3]

        self.assertEqual(production_outage["score"], 1.0)

        for topic in (
            "technical_failure",
            "urgent_request",
            "business_impact",
            "subscription_state"
        ):
            self.assertIn(
                topic,
                production_outage["details"]["triggeredTopics"]
            )

        self.assertEqual(service_restored["score"], 0.0)
        self.assertNotIn(
            "technical_failure",
            conditional_feedback["details"]["triggeredTopics"]
        )
        self.assertEqual(
            conditional_feedback["details"]["triggeredTopics"],
            ["business_impact"]
        )

    def test_case_fourteen_detects_invoice_and_time_bound_close_risk(self):
        customer_results = self._customer_results_for_case(14)
        invoice_discrepancy = customer_results[0]
        close_deadline = customer_results[1]
        resolved_feedback = customer_results[3]

        self.assertIn(
            "billing_issue",
            invoice_discrepancy["details"]["triggeredTopics"]
        )
        self.assertIn(
            "business_impact",
            close_deadline["details"]["triggeredTopics"]
        )
        self.assertNotIn(
            "billing_issue",
            resolved_feedback["details"]["triggeredTopics"]
        )
        self.assertEqual(
            resolved_feedback["details"]["triggeredTopics"],
            ["business_impact"]
        )

    def test_case_fifteen_detects_hardship_and_suppresses_resolved_topics(self):
        customer_results = self._customer_results_for_case(15)
        unexpected_full_rate = customer_results[0]
        multi_day_silence = customer_results[1]
        hardship_request = customer_results[2]
        resolved_refund = customer_results[4]

        self.assertIn(
            "billing_issue",
            unexpected_full_rate["details"]["triggeredTopics"]
        )
        self.assertIn(
            "support_breakdown",
            multi_day_silence["details"]["triggeredTopics"]
        )

        for topic in ("billing_issue", "urgent_request", "business_impact"):
            self.assertIn(topic, hardship_request["details"]["triggeredTopics"])

        self.assertEqual(resolved_refund["score"], 0.0)
        self.assertTrue(
            resolved_refund["details"]["analyzedMessage"][
                "resolutionAcknowledged"
            ]
        )

    def _customer_results_for_case(self, case_number):
        request = self.fixture[case_number - 1]
        accumulated_thread = []
        customer_results = []

        with patch.dict(
            os.environ,
            {"ENGINEER_EMAILS": ",".join(self.engineer_emails)},
            clear=False
        ):
            for message in self.sort_messages(request["body"]["thread"]):
                accumulated_thread.append(message)

                if get_message_role(message) != CUSTOMER_ROLE:
                    continue

                customer_results.append(
                    asyncio.run(analyze_keywords(list(accumulated_thread)))
                )

        return customer_results


if __name__ == "__main__":
    unittest.main()
