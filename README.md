# Thread Escalation Engine

Azure Function in Python that receives an email/message thread, analyzes escalation signals, assigns an escalation tier, and returns a notification payload for downstream routing.

Internal development and collaboration notes are available in
[`DEVELOPMENT.md`](DEVELOPMENT.md).

## Endpoint

- Route: `threadEscalationEngine`
- Auth level: `FUNCTION`
- Method: HTTP trigger handled by Azure Functions
- Entry point: `function_app.py`

## Request Contract

The request body must be a JSON object with a non-empty `thread` array. The
array can be provided at the root or under `body.thread` for Power Automate
compatibility.

Each useful thread item should be a message object. Non-object items are ignored by the analyzers, but the request is rejected when the array does not contain at least one object.

Canonical message fields:

```json
{
  "thread": [
    {
      "subject": "Urgent billing issue",
      "bodyPreview": "I need help with this charge immediately.",
      "body": {
        "contentType": "html",
        "content": "<div>I need help with this charge immediately.</div>"
      },
      "receivedDateTime": "2026-07-12T20:30:00Z",
      "from": {
        "emailAddress": {
          "address": "customer@example.com"
        }
      }
    }
  ]
}
```

Field behavior:

- Message text is extracted in this order: `uniqueBody`, `body`, then
  `bodyPreview`. `bodyPreview` remains supported for legacy and test payloads.
- HTML is converted to text and common Outlook/Gmail quoted-history and
  signature markers are removed before analysis. The full recursive reply body
  is never analyzed as if it were newly authored content.
- `subject` is kept separate from the extracted message body so analyzers can
  decide whether it is fresh evidence.
- `receivedDateTime` must use ISO 8601 and drives message ordering and frequency metrics.
- `from.emailAddress.address` identifies the sender.
- `headers` or `internetMessageHeaders` can provide automatic-reply metadata.

Engineer messages are identified exclusively by matching
`from.emailAddress.address` against the comma-separated `ENGINEER_EMAILS`
environment variable. Matching is case-insensitive. Any sender that is not
configured as an engineer is treated as a customer.

High-confidence automatic replies, delivery notifications, and out-of-office
messages are excluded from keyword, sentiment, and frequency analysis. Analyzer
details report how many automatic messages were ignored.

Validation failures return `400` with an `error` field.

Current validation rules:

- Body must be a JSON object.
- `thread` must be a non-empty array.
- `thread` must include at least one message object.

## Response Shape

Successful requests return `200` with:

- `messageCount`: number of object-shaped messages used by the service.
- `analysis`: raw analyzer outputs.
- `aggregation`: weighted score and contributing signals.
- `decision`: selected escalation tier and reason.
- `notification`: routing-friendly notification payload.

Example high-level shape:

```json
{
  "messageCount": 1,
  "analysis": {
    "sentimental": {},
    "keyword": {},
    "frequency": {}
  },
  "aggregation": {},
  "decision": {},
  "notification": {}
}
```

## Project Structure

```text
function_app.py                         Azure Functions HTTP entry point
host.json                               Azure Functions host configuration
requirements.txt                        Python dependencies
escalation_engine/
  service.py                            Main orchestration pipeline
  config.py                             Topics, weights, boosts, tiers, notifications
  notification.py                       Notification payload builder
  analyzers/
    escalation_request.py               Context-aware escalation routing signal
    sentimental.py                      Sentiment analyzer placeholder
    keyword.py                          Topic keyword analyzer
    frequency.py                        Frequency analyzer placeholder
  request/
    validation.py                       Request validation
  scoring/
    aggregation.py                      Weighted score aggregation
    decision.py                         Tier decision logic
  thread/
    extractors.py                       Message field accessors
    selectors.py                        Message filtering and latest-message selection
```

## Processing Flow

1. `function_app.py` parses the HTTP JSON body.
2. `validate_request_body` checks the minimum request contract.
3. `get_valid_messages` filters object-shaped messages.
4. `process_thread_escalation` runs sentiment, keyword, and frequency analyzers in parallel with a 10 second timeout.
5. `aggregate_results` combines analyzer scores using configured weights and boosts.
6. `decide_escalation` maps the final score to exit, Tier 1, or Tier 2. An
   active generic or hierarchical customer escalation request overrides this
   mapping to Tier 2 without changing the aggregate score.
7. `build_notification` creates the final routing payload.

## Analyzer Notes

The sentimental analyzer is intentionally a placeholder at the moment:

- `analyzers/sentimental.py`

It currently returns fixed scores and flags. Because of those fixed values,
the current engine may escalate low-risk content. Treat its scoring behavior
as integration scaffolding until the implementation is completed.

`analyzers/keyword.py` evaluates only the newest customer message in the thread,
using `receivedDateTime` when available and falling back to the last valid
message. It consumes the shared cleaned message content, ignores automatic
responses and stale subject evidence on replies or existing threads,
deduplicates overlapping/repeated signals, and understands configured phrase
patterns, negation, resolution language, and accented Spanish text.

The keyword result also includes `details.escalationRequest`. This classifier
uses only the cleaned body of the newest customer message and distinguishes:

- `hierarchical`: manager, supervisor, leadership, decision maker, or Tier 2;
  routes directly to Tier 2.
- `generic`: an active request to escalate without a specialist target; routes
  directly to Tier 2.
- `specialist_handoff`: billing, engineering, product, platform, security,
  subscription, support, or another specialist team; the aggregate score still
  decides the tier.
- conditional, negated, historical, and quoted/stale escalation language; no
  routing override is applied.

The aggregate score is always preserved. Override decisions expose
`decisionSource=explicit_escalation_request`, `routingOverride=true`,
`routingConfidence=1.0`, the classified request, and the original score as
`confidence` for prioritization and audit.

The sentimental analyzer consumes every non-automatic message, with quoted
history removed from each one. Its score is still a fixed placeholder.

`analyzers/frequency.py` evaluates customer follow-ups, unanswered messages,
response delays, automatic replies, and response-time trends. It uses the same
configured engineer email classification as the keyword analyzer.

## Configuration

`escalation_engine/config.py` contains:

- Topic keyword, phrase, and variable-pattern lists with trigger thresholds.
- Analyzer weights.
- Boost values for specific flags.
- Tier thresholds.
- Notification templates.

Changing escalation behavior should usually start there before changing pipeline code.

Deployment environment:

```text
ENGINEER_EMAILS=eng1@example.com,eng2@example.com
```

## Local Checks

Syntax check:

```powershell
python -m compileall escalation_engine function_app.py
```

Run the automated tests:

```powershell
python -m unittest discover -s tests -v
```

Replay one generated fixture case and see both sides of the conversation:

```powershell
python -m tests.inspect_keyword_timeline --case 1 --pause
```

Inspect a Power Automate payload directly:

```powershell
python -m tests.inspect_keyword_timeline `
  --payload "C:\path\to\payload.json" `
  --engineer-email "engineer@example.com" `
  --pause
```

The inspector keeps its default output compact: it displays only the cleaned
body used for each interaction, followed immediately by the keyword result and
evidence. Engineer responses and ignored automatic messages remain visible so
the conversation can still be followed chronologically.
