import asyncio
import unittest
from datetime import datetime, timezone

from escalation_engine.notification import build_notification
from escalation_engine.scoring.decision import decide_escalation
from escalation_engine.service import process_thread_escalation


def escalation_request(kind, *, target=None, tier2_override=False):
    return {
        "detected": True,
        "status": "active",
        "kind": kind,
        "requestedTarget": target,
        "tier2Override": tier2_override,
        "routingOverride": "Tier 2" if tier2_override else None,
        "evidence": ["test evidence"],
    }


def aggregate(score, request=None):
    keyword = {
        "name": "keyword",
        "score": 0.0,
        "flags": [],
        "details": {}
    }

    if request is not None:
        keyword["details"]["escalationRequest"] = request

        if request["tier2Override"]:
            keyword["flags"].append("explicit_escalation_request")
        elif request["kind"] == "specialist_handoff":
            keyword["flags"].append("specialist_handoff_requested")

    return {
        "score": score,
        "signals": [
            {"name": "sentimental", "flags": []},
            keyword,
            {"name": "frequency", "flags": []},
        ]
    }


class EscalationDecisionTests(unittest.TestCase):
    def test_hierarchical_request_forces_tier_two_below_threshold(self):
        request = escalation_request(
            "hierarchical",
            target="manager",
            tier2_override=True
        )
        decision = decide_escalation(aggregate(0.20, request))

        self.assertEqual(decision["tier"], "Tier 2")
        self.assertEqual(decision["confidence"], 0.20)
        self.assertEqual(decision["routingConfidence"], 1.0)
        self.assertTrue(decision["routingOverride"])
        self.assertEqual(
            decision["decisionSource"],
            "explicit_escalation_request"
        )
        self.assertEqual(decision["escalationRequest"], request)

    def test_generic_request_forces_tier_two_below_threshold(self):
        request = escalation_request("generic", tier2_override=True)
        decision = decide_escalation(aggregate(0.10, request))

        self.assertEqual(decision["tier"], "Tier 2")
        self.assertEqual(
            decision["reason"],
            "Explicit customer escalation request"
        )

    def test_specialist_handoff_still_uses_aggregate_score(self):
        request = escalation_request(
            "specialist_handoff",
            target="billing_team"
        )
        decision = decide_escalation(aggregate(0.20, request))

        self.assertIsNone(decision["tier"])
        self.assertFalse(decision["routingOverride"])
        self.assertEqual(decision["decisionSource"], "aggregate_score")
        self.assertEqual(decision["escalationRequest"], request)

    def test_specialist_handoff_can_reach_tier_two_from_score(self):
        request = escalation_request(
            "specialist_handoff",
            target="engineering_team"
        )
        decision = decide_escalation(aggregate(0.80, request))

        self.assertEqual(decision["tier"], "Tier 2")
        self.assertFalse(decision["routingOverride"])
        self.assertEqual(decision["decisionSource"], "aggregate_score")

    def test_high_score_still_reaches_tier_two_without_override(self):
        decision = decide_escalation(aggregate(0.80))

        self.assertEqual(decision["tier"], "Tier 2")
        self.assertFalse(decision["routingOverride"])
        self.assertEqual(decision["decisionSource"], "aggregate_score")

    def test_notification_exposes_override_audit_fields(self):
        request = escalation_request(
            "hierarchical",
            target="supervisor",
            tier2_override=True
        )
        decision = decide_escalation(aggregate(0.30, request))
        notification = build_notification(decision)

        self.assertTrue(notification["shouldNotify"])
        self.assertEqual(notification["target"], "supervisor")
        self.assertEqual(
            notification["title"],
            "Customer-requested Tier 2 escalation"
        )
        self.assertTrue(notification["routingOverride"])
        self.assertEqual(
            notification["decisionSource"],
            "explicit_escalation_request"
        )
        self.assertEqual(notification["escalationRequest"], request)


class EscalationRoutingIntegrationTests(unittest.TestCase):
    @staticmethod
    def payload(body):
        return {
            "thread": [
                {
                    "subject": "Case update - TrackingID#0001234567890123",
                    "bodyPreview": body,
                    "receivedDateTime": datetime.now(timezone.utc).isoformat(),
                    "from": {
                        "emailAddress": {
                            "address": "customer@example.com"
                        }
                    }
                }
            ]
        }

    def run_service(self, message):
        return asyncio.run(process_thread_escalation(self.payload(message)))

    def test_explicit_generic_request_overrides_sub_tier_two_score(self):
        body, status = self.run_service("Please escalate this case.")

        self.assertEqual(status, 200)
        self.assertLess(body["aggregation"]["score"], 0.75)
        self.assertEqual(body["decision"]["tier"], "Tier 2")
        self.assertTrue(body["decision"]["routingOverride"])
        self.assertEqual(
            body["notification"]["decisionSource"],
            "explicit_escalation_request"
        )

    def test_specialist_handoff_does_not_override_sub_tier_two_score(self):
        body, status = self.run_service(
            "Please escalate this to the billing team."
        )

        self.assertEqual(status, 200)
        self.assertLess(body["aggregation"]["score"], 0.75)
        self.assertNotEqual(body["decision"]["tier"], "Tier 2")
        self.assertFalse(body["decision"]["routingOverride"])
        self.assertEqual(
            body["analysis"]["keyword"]["details"]["escalationRequest"][
                "kind"
            ],
            "specialist_handoff"
        )

    def test_conditional_request_does_not_override(self):
        body, status = self.run_service(
            "If this continues, please escalate this case."
        )

        self.assertEqual(status, 200)
        self.assertFalse(body["decision"]["routingOverride"])
        self.assertEqual(
            body["analysis"]["keyword"]["details"]["escalationRequest"][
                "status"
            ],
            "conditional"
        )


if __name__ == "__main__":
    unittest.main()
