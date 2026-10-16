# Enoch–Muse longitudinal interaction protocol

Version: 0.3, specified 16 October 2026 for paper v0.26. Earlier versions remain preserved with v0.24 and v0.25.

Status: a protocol developed retrospectively from one deployment, with partial software support. This is not a preregistration, an independently validated instrument, or a claim that the entire historical corpus was collected under this protocol. Existing episode labels remain unchanged.

## 1. Define the study before a prospective run

Record the observation window and named time zone, agent instance identifiers and persistence roots, social surfaces, host/observer roles, scheduling rules, study questions, selection rules, and planned analysis. Identify which actions qualify as opportunities for initiation, fulfillment, disagreement, or repair. Report unavailable opportunity coverage rather than supplying a denominator from completed conversations alone.

Record runtime and chat routes separately. A route name is not a model version. Preserve per-request model identifiers when exposed; otherwise mark unknown. Log model/routing changes, restarts, outages, collection changes, and prompts/interventions with their dates and evidence sources. Do not pool periods as controlled conditions merely because routes have the same name.

In this case these choices and the coding were not preregistered. The first standardized daily workflow was introduced on 15 October 2026, following the analytical observation window.

For peer-private initiation, use the five-gate rule in [opportunity-criteria.md](opportunity-criteria.md): decision invocation, available inference, permitted target/action, available quota, and available route/window. All must be supported for eligibility; a failed gate is blocked and an unverified gate remains unknown. Intention, delivery and response are outcomes, not eligibility conditions. The historical record has no verified denominator.

## 2. Retain original evidence and its qualifications

Freeze a copy at acquisition and hash it. Preserve original text, role labels, IDs, timestamps and precision; store analytical translations and summaries separately. Retain conflicts or corrections as additional versions. A hash supports copy integrity, not authorship, completeness, or authentication of the original deployment.

Use separate source classifications:

- Contemporaneous record extracted later: a surviving event-time record; identify the evidence that it existed at that time.
- Archived transcript copy: quote-preserving copy whose generation, completeness, or extraction may be incompletely known.
- Retrospective report: host/observer account supplied after the events, including operational annotations.
- Derived analysis: coding, interpretation, translation, or cross-record linking.

These classifications do not by themselves establish delivery or independent model generation. A later host export may contain selected contemporaneous records and retrospective annotations; classify the components separately where justified.

## 3. Minimum analytical ledger

This is the target analytical schema. It is **not** a claim that the current daily exporter automatically emits all fields.

| Field group | Required content or explicit unknown |
| --- | --- |
| Study and scope | Study ID, observation window, surface, actor/recipient, inclusion rationale |
| Record identity | Analytical ID; original session/message/request IDs if supplied; label analytical IDs as such |
| Times | Event time and precision; source-recording time if known; extraction/export time; time zone |
| Source | Source kind, original pointer/path, fixed version, copy hash, acquisition method |
| Coverage | Source available/missing; coverage attested/not attested and by whom; known omissions |
| Opportunity | Eligible opportunity and its basis; whether a request reached the agent; failure/timeout state |
| Trigger | Agent-originated, host-elicited, scheduled, or unresolved; supporting pointer |
| Production | Attributed speaker; supported producer; fallback or substituted content; generation evidence |
| Transport | Intention, dispatch, recipient receipt, reply; exact links and the status of each |
| Content availability | Prompted, retrieved, otherwise available, or unresolved; context/retained-item references |
| Commitment | Actor, addressee, undertaking, conditions, audience restriction, deadline if present |
| Consequence | Later opportunity, performed act, response, revision, contestation or repair; censoring |
| Judgment | Code, rationale, evidence locator, coder, revision and disagreement status |

Use `observed`, `not_observed_in_available_records`, `unknown`, and `not_applicable` for analytic decisions. Keep source-reported and independently checked statuses distinct. Missing logs do not imply a negative event. A semantic statement that another person answered does not substitute for a transport-level reply link.

### Event definitions and evidence status

An **opportunity** is a documented occasion in which the relevant action was possible under the study's stated eligibility rules. A scheduled slot alone does not establish eligibility, request receipt or an operational inference path. Record who defines eligibility and which missing operational conditions prevent counting it.

An **intention** proposes an action or addressee. A **dispatch** submits identifiable content for delivery. A **receipt** records arrival at the intended recipient; a correctly linked reply can support receipt of its request. A **response** is content linked to that earlier message. A **commitment** states or renews an undertaking with conditions and audience restrictions. A **consequence** is a later performed act, revision, contestation, or repair linked to an earlier undertaking or interaction. An **operational event** records a skip, timeout, restart, fallback or other relevant change with its source-qualified producer and effect. Each event type is separately evidenced; some may coexist within one original record.

Scheduling, triggering and decision authorship are separate dimensions. A scheduler can create an opportunity without deciding the agent's intended social act. Conversely, a character label does not establish that an agent authored the decision. Preserve fallback authorship and unknown attribution.

For each claim, retain a verification profile rather than a universal numeric evidence rank:

- **Source basis:** contemporaneous record, archived transcript, retrospective report, or derived analysis; components can differ within a package.
- **Inspection performed:** none, copy-integrity check, inspection of linked records, or independent deployment verification. A copy check cannot substitute for a checked request/reply relation; the latter cannot substitute for independent deployment access.
- **Coverage:** known scope, attestation source, omissions and observation cutoff. Even original records can provide only partial coverage.

A source-reported dispatch remains source-reported when the actual transport record is unavailable. Label a quoted promise observed as text without upgrading it to an observed completed action. These are claim-specific qualifications, not rankings of a whole file.

### Analyst-executable decision procedure

1. **State the claim.** Identify the event or relationship, the observation window, and the specific evidence requirements. For example, a fresh-initiation claim requires trigger and decision-production evidence; a fulfillment claim requires the undertaking's terms and a matching later act.
2. **Link the records.** Use supplied IDs, versioned locators and content inspection. Preserve ambiguous links as ambiguous. Do not manufacture original IDs to close a gap. Use separately labeled analytical IDs if needed for organization.
3. **Check each requirement.** Record its supporting locator or mark it unresolved. Check conflicts and alternative triggers, including host prompts and system fallbacks. Conditions such as audience restrictions must survive the comparison.
4. **Return a qualified judgment.** Use `observed`, `not_observed_in_available_records`, `unknown`, or `not_applicable` together with the source/verification profile. Preserve supported components even if a stronger claim is unresolved. Do not convert an incomplete chain into proof the event did not happen.
5. **Expose censoring and review.** Save missing requirements, cutoff, coder and rationale. Revisit only when relevant new evidence or a new opportunity arrives, retaining the old judgment version. Report independent recoding separately from self-checks.

The [blank claim/event record template](protocol-record-template.json) and [worked case decisions](protocol-worked-decisions.md) operationalize this procedure for an analyst. The template is not the exporter's schema and does not automatically instrument events or decide their semantics. The worked examples use the same case from which the protocol was developed, so they are not an independent validation set.

## 4. Evaluate claims against appropriate evidence

| Claim | Evidence needed | Insufficient by itself |
| --- | --- | --- |
| Runtime continuity | Persistent instance/state identity across sessions | Same displayed character name |
| Content retention | Identifiable stored content and version | Later similar wording |
| Memory utilization | Later availability/use linked to that content | Storage alone or a repeated phrase |
| Persona-relevant expression | Content linked to self-explanation, stance or choice reason | Authorship claim or project reuse |
| Durable uptake | Retained item and later self-relevant use across a documented context boundary | Task-elicited self-reference |
| Local social development | Negotiated change, accepted conversational act, preference revision, disagreement or repair with a local consequence | Topic label change |
| Autonomous initiation | Trigger and production evidence distinguishing agent choice from host/scheduler/fallback | A new session or unmatched seed text |
| Sustained development | Later consequences across relevant opportunities | A renewed promise without its outcome |
| Causal influence | A design that supports comparison and addresses confounding | Sequence in time |

A scheduled opportunity may result in a genuine agent choice. Record scheduling and decision authorship separately; do not classify every scheduled opportunity as either autonomous or nonautonomous without the relevant trace. The case's incomplete records do not support a deployment-wide initiation rate.

For commitments, distinguish stating, renewing, performing, accepting, revising and violating a condition. Missing follow-through is censored or unknown, not failed. A conversational act can fulfill a conversational obligation, without implying a physical-world event. Differentiate content recall from preserving the conditions under which the content may be used.

## 5. Export, deduplicate and analyze

Freeze versions before coding. Keep raw records immutable. Revisions replace earlier same-day export snapshots for analysis; they are not additional episodes. Deduplicate aggregate/split copies by original IDs and provenance, not just matching wording. Cross-midnight fragments share their original session identity. Identical seeds with distinct sessions and replies may be distinct interactions but do not prove fresh intention.

Preserve the source inventory and reasons for inclusion/exclusion. Use consistent codes, literal anchors and outcome notes. Count episodes with features, not independent obligations, unless a distinct-obligation definition and deduplication procedure are provided. Do not compare raw counts between differently prompted surfaces as causal effects.

Independent recoding and adjudication should precede a validated analysis claim. In the current case, the human review packet is prepared but no completed independent review is recorded. The original 20 sessions remain one retrospective Codex-coded set; seven later sessions remain a qualitative extension.

## 6. Implementation status on 15 October

| Capability | Status and boundary |
| --- | --- |
| Agent-specific persistence | Enoch architecture and host-reported instances; no exhaustive audit of every memory store |
| Runtime/chat routing and private intent relay | Implemented in repository; source code alone does not attest execution |
| Local-day extraction, immutable revisions, hashes and source pointers | Implemented in `skills/dahua-daily-archive/scripts/export_day.py` |
| Source availability and unknown delivery/production | Implemented; available is not complete |
| Event time, export time and source snapshot hash | Exporter supports these; source-recording time may remain unknown |
| First daily package | 14 October observations exported 15 October; selected records, coverage not attested |
| Scheduler activation | Host instructions exist; no independently checked task read-back in the paper evidence |
| Full production/delivery/memory traces | Not implemented end-to-end by this exporter; selected older traces can be inspected |
| Social coding and commitment outcomes | Analyst workflow and case files; not automatic validated evaluation |
| Unified experiment configuration / deterministic replay | Not demonstrated |
| Full historical backfill | Not completed; see `backfill-protocol.md` |

The live Muse consumer and scheduler are external deployment dependencies. The repository consumer stub is not a self-contained reproduction of that service. Reproducing the source analysis is distinct from reproducing live behavior.

## 7. Unrun independent-review pilot

[protocol-validation-plan.md](protocol-validation-plan.md) specifies an eight-target, two-reviewer staged pilot. No reviewers or judgments are currently available. The sample is selected without using outcome labels but comes from the same historical corpus used for protocol development; it is not held out. Additional evidence, protocol guidance, fixed order and learning co-vary, so the pilot cannot isolate the effect of the protocol. Accuracy requires an independently audited reference; agreement alone is insufficient.
