# Eligible opportunities for peer-private initiation

Specified 16 October 2026 for protocol v0.3 / manuscript v0.26. This is a proposed operational rule for future instrumented use and retrospective source-qualified assessment. It does not add opportunity counts to the historical case.

## Unit and timing

An opportunity is an identified decision occasion for one agent, with an opening time/window, trigger and eligibility evidence. A schedule entry is only an offered slot. A self-check invitation, actual inference invocation, intention, dispatch and recipient reply are separate events. A spontaneous intention may also identify a decision occasion, provided its provenance is preserved.

Fix the gates before a prospective run. Evaluate them at the decision occasion; retain later failures separately. Use an original task/request ID where available; otherwise create a clearly labeled analytical occasion ID and leave the native ID unknown. Retries of one request do not automatically become independent opportunities.

## Preconditions

| Gate | Evidence needed | Does not suffice |
| --- | --- | --- |
| G1. Decision opportunity reached the agent | Delivered self-check/request or a documented spontaneous reasoning invocation, with source attribution | Scheduled task name or host assertion alone without qualification |
| G2. Inference path available | Operational runtime/provider evidence for that occasion; identify timeout, authentication failure or substituted fallback | A generic “completed” task whose output was supplied by a consumer |
| G3. Permitted target and action | At least one permitted peer target and enabled private-message permission; applicable exclusions recorded | Another character's existence or a host-only target |
| G4. Quota available | Applicable credit/quota snapshot or a documented no-quota policy at the occasion | A later quota balance or an unspecified global setting |
| G5. Route/window available | Relevant private route enabled, no blocking concurrent exchange/known outage at opening, and an adequate configured decision window | A future successful delivery or a past health check alone |

Each gate is `met`, `blocked`, or `unknown`, with a source locator and verification profile. Report host assertions as such; do not silently promote them to independently verified execution.

- All gates met: **eligible**, qualified by the weakest relevant source support.
- Any gate blocked: **blocked**; retain unknown states for other gates as well.
- No blocked gate but at least one unknown: **eligibility_unknown**.

Blocked and unknown occasions remain in the observation inventory. They are not discarded from reporting or counted as agent refusals.

## Outcome and observation completeness are separate

Do not require intention, successful dispatch, receipt or response as eligibility gates: those are outcomes. An agent can initiate and then encounter a routing failure. Record that initiative and the failed transport separately instead of removing the occasion from the denominator after seeing its outcome.

For an eligible occasion, record whether a source-attributed agent intention is supported, an authenticated agent decline/no-intent output is supported, or the decision outcome is unresolved. Infrastructure-written skip is not agent decline. A timed-out or missing output does not provide a negative decision.

A no-initiation conclusion requires both eligibility and sufficiently complete observation of the decision/intention path through a prespecified cutoff. Record missing logs and censoring separately. A recipient's silence is not evidence that the sender chose not to initiate.

Report eligible, blocked, eligibility-unknown, and outcome-unknown counts separately. An initiation fraction may be described only for an explicitly bounded, adequately observed eligible set; disclose censored eligible occasions and do not silently exclude them. The present archives do not establish that denominator, so the manuscript reports no initiation rate.

## Application to existing material

- September model switching is an operational intervention; comparable eligible-opportunity counts are unavailable.
- Reported self-check skips in later summaries do not establish all five gates or decision authorship.
- The 14 October operations export attributes four skips to system fallbacks; it is a host-supplied account, not authenticated raw self-check execution.
- The 13 October group timeout is a different interaction surface. Record its failed discussion attempt, not four private-initiation refusals. A group-discussion eligibility rule would need its own preconditions.

These rules are analyst specifications. The current daily exporter does not automatically collect the five gates.
