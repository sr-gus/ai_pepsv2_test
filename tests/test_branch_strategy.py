import asyncio
import copy
import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from escalation_engine.analyzers.keyword import analyze_keywords
from escalation_engine.config import ESCALATION_CONFIG
from escalation_engine.notification import build_notification
from escalation_engine.scoring.aggregation import aggregate_results
from escalation_engine.scoring.decision import decide_escalation
from escalation_engine.service import process_thread_escalation


def message(text, *, sender="customer@example.com", minutes_ago=0, subject="RE: Case - TrackingID#123"):
    return {
        "subject": subject, "bodyPreview": text,
        "receivedDateTime": (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat(),
        "from": {"emailAddress": {"address": sender}},
    }


class SpellingBehaviorTests(unittest.TestCase):
    def analyze(self, text):
        return asyncio.run(analyze_keywords([message(text)]))

    def test_english_and_spanish_requests_survive_typos(self):
        for text, kind in (
            ("Please esclate this case.", "generic"),
            ("Please esxalate this case.", "generic"),
            ("Please escallate this case.", "generic"),
            ("Please escaalte this case.", "generic"),
            ("I need a supervsor.", "hierarchical"),
            ("Necesito un supervsor.", "hierarchical"),
            ("Necesito una escalcion.", "generic"),
        ):
            with self.subTest(text=text):
                result = self.analyze(text)
                request = result['details']['escalationRequest']
                self.assertTrue(request['tier2Override'])
                self.assertEqual(request['kind'], kind)
                self.assertEqual(request['matchType'], 'orthographic')

    def test_specialist_target_typo_does_not_become_generic_override(self):
        for text in (
            "Please escalate this to billng.",
            "Please esclate this to the billing team.",
            "Please escalate this to enginering.",
            "Necesito escalar el caso a la facturcion.",
        ):
            with self.subTest(text=text):
                request = self.analyze(text)['details']['escalationRequest']
                self.assertEqual(request['kind'], 'specialist_handoff')
                self.assertFalse(request['tier2Override'])

    def test_negated_conditional_historical_requests_stay_inactive(self):
        for text, status in (
            ("Please do not esclate this case.", 'negated'),
            ("No necesito un supervsor.", 'negated'),
            ("If this continues, please esclate this case.", 'conditional'),
            ("If this continues, I need a supervsor.", 'conditional'),
            ("Thanks for esclating this case.", 'historical'),
            ("This was already esclated.", 'historical'),
        ):
            with self.subTest(text=text):
                request = self.analyze(text)['details']['escalationRequest']
                self.assertFalse(request['tier2Override'])
                self.assertEqual(request['status'], status)

    def test_topic_evidence_recovers_typo_and_keeps_original(self):
        result = self.analyze('There is a duplciate charge.')
        exact = self.analyze('There is a duplicate charge.')
        self.assertEqual(result['score'], exact['score'])
        self.assertIn('billing_issue', result['details']['triggeredTopics'])
        self.assertEqual(result['details']['analyzedMessage']['text'], 'There is a duplciate charge.')
        edit = result['details']['spellingCorrections']['content'][0]
        self.assertEqual((edit['original'], edit['replacement'], edit['distance']), ('duplciate', 'duplicate', 1))

    def test_fuzzy_matches_keep_negation_resolution_and_deduplication(self):
        for text in (
            'There is no duplciate charge.',
            'The duplciate charge is resolved.',
            'There is a duplicate charge, a duplciate charge, a duplicate charge.',
        ):
            with self.subTest(text=text):
                fuzzy = self.analyze(text)
                exact = self.analyze(text.replace('duplciate', 'duplicate'))
                self.assertEqual(fuzzy['score'], exact['score'])
                self.assertEqual(fuzzy['details']['weightedTotalMatches'], exact['details']['weightedTotalMatches'])

    def test_ambiguous_short_and_real_words_are_not_corrected(self):
        for text in (
            'I can manage this directory directly.',
            'The product is changing and we are filling the form.',
            'I need a manger.',
            'Please sclate this case.',  # two edits
            'Please escalte this case.',  # ambiguous: escalate / escale
            'The payment was declined.',  # exact match always wins
        ):
            with self.subTest(text=text):
                result = self.analyze(text)
                self.assertEqual(result['details']['spellingCorrections']['content'], [])
        with patch.dict(ESCALATION_CONFIG['spelling'], {'terms': ['manager', 'manages']}):
            self.assertEqual(self.analyze('The managet replied.')['details']['spellingCorrections']['content'], [])

    def test_quoted_stale_subject_and_engineer_typos_do_not_override(self):
        customer = message('Thank you.', minutes_ago=2, subject='RE: Please esclate this case - TrackingID#123')
        customer['body'] = {'contentType': 'html', 'content': '<div>Thank you.</div><div id="appendonsend"></div><div>Please esclate this case.</div>'}
        with patch.dict(os.environ, {'ENGINEER_EMAILS': 'engineer@example.com'}):
            result = asyncio.run(analyze_keywords([
                customer, message('Please esclate this case.', sender='engineer@example.com'),
            ]))
        self.assertEqual(result['score'], 0)
        self.assertFalse(result['details']['escalationRequest']['tier2Override'])

    def test_spelling_can_be_disabled(self):
        with patch.dict(ESCALATION_CONFIG['spelling'], {'enabled': False}):
            result = self.analyze('Please esclate this case.')
        self.assertEqual(result['score'], 0)
        self.assertFalse(result['details']['escalationRequest']['tier2Override'])


class MinimumTierTests(unittest.TestCase):
    def aggregate(self, *, sentimental=0.99, frequency=0.1, unanswered=1, flags=(), text='We still need help.'):
        keyword = asyncio.run(analyze_keywords([message(text)]))
        return aggregate_results(
            {'score': sentimental, 'label': 'negative', 'success': True},
            keyword,
            {'name': 'frequency', 'score': frequency, 'flags': list(flags),
             'details': {'unansweredCustomerMessages': unanswered}},
        )

    def test_high_sentiment_alone_guarantees_tier_one_without_keywords(self):
        aggregate = self.aggregate()
        before = copy.deepcopy(aggregate)
        decision = decide_escalation(aggregate)
        self.assertLess(aggregate['score'], 0.5)
        self.assertEqual(decision['tier'], 'Tier 1')
        self.assertEqual(decision['decisionSource'], 'high_sentiment_floor')
        self.assertEqual(decision['confidence'], aggregate['score'])
        self.assertEqual(decision['routingConfidence'], aggregate['score'])
        self.assertEqual(aggregate, before)

    def test_user_example_guarantees_tier_two_with_current_pending_messages(self):
        decision = decide_escalation(self.aggregate(frequency=0.5, unanswered=2))
        self.assertEqual(decision['tier'], 'Tier 2')
        self.assertEqual(decision['confidence'], 0.55)
        self.assertEqual(decision['decisionSource'], 'sentiment_frequency_floor')
        notification = build_notification(decision)
        self.assertTrue(notification['shouldNotify'])
        self.assertEqual(notification['target'], 'supervisor')
        self.assertEqual(notification['minimumTierRule'], decision['minimumTierRule'])
        self.assertIn('minimum tier rule', notification['summary'])

    def test_thresholds_are_inclusive_and_configurable(self):
        for sentiment, frequency, tier in ((0.949, 0.49, 'Tier 1'), (0.95, 0.49, 'Tier 1'), (0.95, 0.50, 'Tier 2')):
            with self.subTest(sentiment=sentiment, frequency=frequency):
                decision = decide_escalation(self.aggregate(sentimental=sentiment, frequency=frequency, unanswered=2))
                self.assertEqual(decision['tier'], tier)
                if sentiment < 0.95:
                    self.assertFalse(decision['routingOverride'])
        with patch.dict(ESCALATION_CONFIG['tier_floors'], {'sentimental_min_score': 0.999}):
            self.assertIsNone(decide_escalation(self.aggregate())['tier'])

    def test_historical_frequency_without_current_backlog_cannot_force_tier_two(self):
        for unanswered, flags in ((0, ['rapid_followup']), (1, ['rapid_followup'])):
            decision = decide_escalation(self.aggregate(frequency=0.5, unanswered=unanswered, flags=flags))
            self.assertEqual(decision['tier'], 'Tier 1')
        decision = decide_escalation(self.aggregate(frequency=0.6, unanswered=1, flags=['critical_response_delay']))
        self.assertEqual(decision['tier'], 'Tier 2')

    def test_frequency_alone_has_no_new_override(self):
        self.assertFalse(decide_escalation(self.aggregate(sentimental=0.1, frequency=1, unanswered=3))['routingOverride'])

    def test_existing_higher_tier_and_explicit_override_win(self):
        aggregate = self.aggregate()
        aggregate['score'] = 0.9
        decision = decide_escalation(aggregate)
        self.assertEqual(decision['tier'], 'Tier 2')
        self.assertFalse(decision['routingOverride'])
        self.assertEqual(decision['decisionSource'], 'aggregate_score')
        decision = decide_escalation(self.aggregate(text='Please esclate this case.'))
        self.assertEqual(decision['decisionSource'], 'explicit_escalation_request')

    def test_resolution_empty_or_responded_message_cannot_trigger_floor(self):
        for text in ('Thanks, the issue is resolved.', 'Everything is working as expected.', 'Gracias, ya se resolvio.', 'Thank you.', 'Gracias.', ''):
            with self.subTest(text=text):
                self.assertFalse(decide_escalation(self.aggregate(text=text))['routingOverride'])
        aggregate = self.aggregate()
        aggregate['signals'][1]['details']['analyzedMessage']['isLatestHumanMessage'] = False
        self.assertFalse(decide_escalation(aggregate)['routingOverride'])

    def test_invalid_positive_failed_or_missing_model_output_cannot_trigger_floor(self):
        for change in ({'score': None}, {'score': True}, {'score': float('nan')}, {'score': 2}, {'success': False}, {'label': 'positive'}, {'label': 'neutral'}):
            with self.subTest(change=change):
                aggregate = self.aggregate()
                aggregate['signals'][0].update(change)
                self.assertFalse(decide_escalation(aggregate)['routingOverride'])

    def test_floors_can_be_disabled(self):
        with patch.dict(ESCALATION_CONFIG['tier_floors'], {'enabled': False}):
            self.assertIsNone(decide_escalation(self.aggregate())['tier'])

    def test_full_service_uses_real_keyword_and_frequency_with_mocked_model(self):
        thread = [message('We still need help.', minutes_ago=i) for i in (3, 2, 1, 0)]
        with patch.dict(os.environ, {'ENGINEER_EMAILS': 'engineer@example.com'}), patch(
            'escalation_engine.service.analyze_sentimental',
            new=AsyncMock(return_value={'score': 0.99, 'success': True}),
        ):
            result, status = asyncio.run(process_thread_escalation({'thread': thread}))
        self.assertEqual(status, 200)
        self.assertEqual(result['analysis']['keyword']['score'], 0)
        self.assertEqual(result['analysis']['frequency']['score'], 0.5)
        self.assertEqual(result['decision']['tier'], 'Tier 2')
        self.assertEqual(result['decision']['decisionSource'], 'sentiment_frequency_floor')


if __name__ == '__main__':
    unittest.main()
