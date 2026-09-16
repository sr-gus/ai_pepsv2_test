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
      "subject": "Urgent billing issue - TrackingID#0001234567890123",
      "bodyPreview": "I need help with this charge immediately.",
      "body": {
        "contentType": "html",
        "content": "<div>I need help with this charge immediately.</div>"
      },
      "receivedDateTime": "2026-07-12T20:30:00Z",
      "from": {
        "emailAddress": {
          "address": "customer@example.com",
          "name": "Example Customer"
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
- `from.emailAddress.name` optionally supplies the sender's display name for
  notification metadata.
- `headers` or `internetMessageHeaders` can provide automatic-reply metadata.

Before running any analyzer, the service requires a numeric `TrackingID#...`
in at least one message's `subject`. The marker is case-insensitive and must
be immediately followed by digits; the digit count is not fixed. IDs are
returned as strings to preserve leading zeros. A TrackingID found only in a
message body does not qualify. If several subjects contain an ID, the newest
matching message supplies the case number, using the shared timestamp selector
and falling back to the last matching message when no valid timestamps exist.

Threads without a matching subject return `200` as a normal filter outcome,
with empty `analysis` and `aggregation` objects, `decision.action="exit"`,
`decision.decisionSource="missing_tracking_id"`, and
`notification.shouldNotify=false`. No analyzer or score aggregation runs;
`tier`, `confidence`, and `routingConfidence` are `null` for this outcome.
Structurally invalid requests still return `400`.

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

The notification includes these fields for Teams messages:

| Field | Source |
| --- | --- |
| `caseNumber` | Digits following `TrackingID#` in the selected subject. |
| `engineerName` | `from.emailAddress.name` of the newest non-automatic message from a configured engineer, trimmed; `null` when unavailable. |
| `engineerEmail` | `from.emailAddress.address` of that same engineer message; `null` when no engineer sender is identified. |

Engineer selection uses `ENGINEER_EMAILS`, the same role classification used
by the analyzers. When multiple engineers participate, the latest human sender
is selected; this is a conversation participant, not proof of case ownership.
Customer names, signatures, and recipients are not used to infer an engineer.
If the selected message has no name, the email remains available separately.
All three metadata fields are `null` when the thread is skipped for missing ID.

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
    sentimental.py                      Azure ML sentiment model client
    keyword.py                          Topic keyword analyzer
    frequency.py                        Communication timing analyzer
    spelling.py                         Bounded one-edit orthographic recovery
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
4. The service selects a case number from subjects containing `TrackingID#...`;
   when none exists, it returns the skipped result before analysis.
5. `process_thread_escalation` runs sentiment, keyword, and frequency analyzers in parallel with a 10 second timeout.
6. `aggregate_results` combines analyzer scores using configured weights and boosts.
7. `decide_escalation` maps the final score to exit, Tier 1, or Tier 2. An
   active generic or hierarchical customer escalation request overrides this
   mapping to Tier 2 without changing the aggregate score. Configurable
   sentiment rules can also establish a minimum tier.
8. `build_notification` creates the final routing payload with the case number
   and latest engineer sender's available name and email.

## Teams / Power Automate

After the successful HTTP call, use a Compose action named `Notification` with
`body('HTTP')?['notification']`, replacing `HTTP` with the actual action name.
`Notification` is the name of a flow action you must create; it is not created
automatically by the `notification` property in the response. Place it before
the condition / Switch so both Teams branches can reference its output.

If the flow already uses Parse JSON, paste
[`docs/power-automate-response.schema.json`](docs/power-automate-response.schema.json)
into its Schema field, and keep the HTTP action's Body as its Content. Then
set the Compose expression to `body('Parse_JSON')?['notification']`, replacing
`Parse_JSON` with the real internal name of that action. Alternatively, access
`body('Parse_JSON')?['notification']?['caseNumber']` and the other fields directly
from Parse JSON without a Compose action. An invalid reference to `Notification`
requires fixing the action name or adding that action; updating the schema alone
does not resolve the reference.

Check `outputs('Notification')?['shouldNotify']` against the boolean `true`
before formatting scores or sending any Teams message. A skipped result has
no numeric score; a Parse JSON schema must allow nullable confidence fields
and empty `analysis` / `aggregation` objects.

Inside the true branch, switch on `outputs('Notification')?['tier']`:

- `Tier 1`: Post a message to myself, with HTML content. The destination is
  the authenticated Teams connection account's own chat.
- `Tier 2`: Post message in a chat or channel, as Flow bot, to the configured
  team and channel.
- Default: no message.

Use these expressions to replace the corresponding message placeholders:

```text
outputs('Notification')?['caseNumber']
coalesce(outputs('Notification')?['engineerName'], outputs('Notification')?['engineerEmail'], 'No identificado')
formatNumber(mul(outputs('Notification')?['confidence'], 100), '0')
```

The last expression produces a score on a 0-100 scale; append `%` in the message.
Do not use `routingConfidence` as the escalation score or recompute the tier
from the percentage: an explicit escalation request can select Tier 2
independently of the aggregate score. When inserting a sender name into HTML,
escape `&`, `<`, and `>` as `&amp;`, `&lt;`, and `&gt;` to keep it as plain text.

## Analyzer Notes

The sentimental analyzer calls the functional Azure ML model. It submits the
cleaned chronological transcript with `Customer:` and `Engineer:` prefixes and
returns the model response. The score is consumed as an increasing risk signal;
the endpoint's class confidence must not be substituted for that risk score.

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
history removed from each one.

`analyzers/frequency.py` evaluates customer follow-ups, unanswered messages,
response delays, automatic replies, and response-time trends. It uses the same
configured engineer email classification as the keyword analyzer.

### Minimum tier rules and spelling tolerance

`ESCALATION_CONFIG["tier_floors"]` enables these inclusive thresholds:

| Condition | Minimum tier |
| --- | --- |
| Sentimental score >= 0.95 | Tier 1 |
| Sentimental >= 0.95 and frequency >= 0.50, corroborated by current pending messages | Tier 2 |

Both rules require a nonempty customer body that is the latest human message.
They do not apply to recognized resolution/closure or simple acknowledgements,
explicitly positive/neutral sentiment labels, failed model results, or invalid
sentiment scores. Tier 2 additionally requires at least two unanswered customer
messages, or one unanswered message with a long/critical response-delay flag.
There is no new frequency-only override and frequency calculations are unchanged.

The final tier is the higher of the aggregate decision and the rule's minimum.
Explicit escalation retains precedence. The aggregate score, weights and boosts
are preserved. An applied rule sets `routingOverride=true` and
`decisionSource=high_sentiment_floor` or `sentiment_frequency_floor`.
`minimumTierRule` records the eligible rule, observed scores and thresholds;
it can be present even when the aggregate already supplies an equal/higher tier.
`confidence` and `routingConfidence` retain the aggregate score for these rules;
neither field is a calibrated probability of the rule being correct.

Keyword and explicit-request matching also accept unique one-character edits
(insertion, deletion, substitution, adjacent transposition) against the curated
`ESCALATION_CONFIG["spelling"]["terms"]` list. Input tokens must be 6-32 letters
by default. Exact vocabulary, protected real words and ambiguous candidates
are never corrected. This uses a cached local deletion index with no additional
dependency or network call. It handles typos, not semantic paraphrases.

Context checks still run after correction: negation, conditional requests,
historical language, specialist targets, deduplication and stale subjects retain
their existing roles. `details.analyzedMessage.text` retains the original clean
body; `details.matchingText` shows the normalized matching text.
`details.spellingCorrections` records original/replacement tokens, distance and
offsets into the normalized pre-correction subject/body. The request classifier
also exposes its corrections and matching text when corrections occur.

Both features can be disabled independently with their `enabled` config fields.
Run the deterministic feature and routing tests without calling Azure ML:

```powershell
python -m unittest tests.test_branch_strategy tests.test_escalation_routing -v
```

The legacy full suite still includes live-model tests and some historical
keyword/frequency score expectations. These need separate maintenance; the
new tests mock the model response, not keyword, frequency or routing behavior.

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
ENGINEER_EMAILS=srgus@2sxtzc.onmicrosoft.com
```

`ENGINEER_EMAILS` is the only supported role-classification setting. Define it
as one Azure Function App setting whose value is a comma-separated list of
complete email addresses. Do not use a JSON array, semicolons, domains, or
wildcards. Matching is case-insensitive and surrounding whitespace is ignored;
the canonical deployed form omits spaces:

```text
ENGINEER_EMAILS=srgus@2sxtzc.onmicrosoft.com,engineer2@contoso.com
```

In the Azure portal, use `ENGINEER_EMAILS` as the setting name and enter only
the value, without wrapping quotes. The equivalent Azure CLI command is:

```powershell
az functionapp config appsettings set `
  --resource-group "<resource-group>" `
  --name "<function-app-name>" `
  --settings "ENGINEER_EMAILS=srgus@2sxtzc.onmicrosoft.com,engineer2@contoso.com"
```

Include every address or alias from which an engineer can send replies. A
sender not listed in `ENGINEER_EMAILS` is classified as a customer; domains
are never used to infer the role.

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
  --engineer-email "srgus@2sxtzc.onmicrosoft.com" `
  --pause
```

The inspector keeps its default output compact: it displays only the cleaned
body used for each interaction, followed immediately by the keyword result and
evidence. Engineer responses and ignored automatic messages remain visible so
the conversation can still be followed chronologically.

### Additional synthetic thread fixtures

Three extra Outlook-shaped datasets exercise a wider range of newly-authored
body lengths without changing the original regression fixture:

- `tests/azure_billing_escalation_threads_short.json`: 8 threads with terse
  customer replies, including one-line follow-ups.
- `tests/azure_billing_escalation_threads_mixed.json`: 8 threads that mix
  short replies with medium-length explanations.
- `tests/azure_billing_escalation_threads_long.json`: 8 threads with long,
  multi-paragraph customer context and decisive language in different body
  positions.

Use `--fixture` with any timeline inspector. `--case` remains one-based:

```powershell
python -m tests.inspect_keyword_timeline `
  --fixture tests\azure_billing_escalation_threads_short.json `
  --case 1 `
  --pause

python -m tests.inspect_frequency_timeline `
  --fixture tests\azure_billing_escalation_threads_mixed.json `
  --case 3 `
  --pause

python -m tests.inspect_sentiment_timeline `
  --fixture tests\azure_billing_escalation_threads_long.json `
  --all
```

`tests/additional_thread_expectations.json` documents each case's intent,
message lengths, and expected escalation context. It intentionally does not
freeze keyword scores, so score calibration can continue independently. The
fixtures are deterministic and can be regenerated with:

```powershell
python -m tests.generate_additional_thread_fixtures
```
