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

- `subject` and `bodyPreview` provide the text analyzed for sentiment and keywords.
- `receivedDateTime` must use ISO 8601 and drives message ordering and frequency metrics.
- `from.emailAddress.address` identifies the sender.
- `headers` is optional and can be an object or string used to detect automatic replies.

Engineer messages are identified exclusively by matching
`from.emailAddress.address` against the comma-separated `ENGINEER_EMAILS`
environment variable. Matching is case-insensitive. Any sender that is not
configured as an engineer is treated as a customer.

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
6. `decide_escalation` maps the final score to exit, Tier 1, or Tier 2.
7. `build_notification` creates the final routing payload.

## Analyzer Notes

The sentimental analyzer is intentionally a placeholder at the moment:

- `analyzers/sentimental.py`

It currently returns fixed scores and flags. Because of those fixed values,
the current engine may escalate low-risk content. Treat its scoring behavior
as integration scaffolding until the implementation is completed.

`analyzers/keyword.py` is implemented and evaluates only the newest message in the thread, using `receivedDateTime` when available and falling back to the last valid message.

`analyzers/frequency.py` evaluates customer follow-ups, unanswered messages,
response delays, automatic replies, and response-time trends. It uses the same
configured engineer email classification as the keyword analyzer.

## Configuration

`escalation_engine/config.py` contains:

- Topic keyword lists and trigger thresholds.
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
