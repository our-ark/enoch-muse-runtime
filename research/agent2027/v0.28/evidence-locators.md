> Public-copy notice (v0.28): the three linked host JSON exports are minimally redacted derivatives. Original bytes remain private; see [REDACTION.md](REDACTION.md) and the original/public hash mapping. Historical receipt and check descriptions below refer to the received originals unless explicitly stated otherwise.

# Supplement S1: evidence record map (v0.23)

This map resolves Table II's compact locators. Paths are relative to the extracted supplement root; JSON pointers start at each named file's root. Ledger IDs identify analytical entries, not additional independent observations. Source field names and Chinese quotations are retained. English quotations in the paper are analytical translations.

## S4 revision: E09/E30, S4-179

- [Archived S4 monologue](sources/docs/agent-life-observations/dahua-xiyou/group-interactions/conversations/2026-09-23-s4-zixia-monologue.zh-CN.md): compare the proposed reset ending, the objections, and the final text. E09 records the document-level revision trace.
- [Selected S2/S4 export](sources/host-exports-2026-10-04/item2-s2-s4.json): `/s4_convergence_ask_full_text/object/seq` is **179**, the Qingxia chat request. `/s4_convergence_ask_full_text/object/text` supplies the fusion text; `/four_pass_chat_outbox_originals` contains the four attributed approvals. `/stage_ask_index_per_agent` maps other participants' sequence numbers; 179 is not a global request ID.
- Text and timestamps associate the four approvals with S4. They lack direct `in_reply_to` links and complete generation traces. The archive's separate S2 consumer-insertion disclosure must not be assigned to this set without evidence.

## Ability choice: E29, a508f481 / chat-73

- [Archived ability discussion](sources/docs/agent-life-observations/dahua-xiyou/group-interactions/conversations/2026-09-24-golden-finger-continuity-preferences.zh-CN.md): Baijingjing invokes the accepted question and proposes a veto over what the box takes. The [S1 rules](sources/docs/agent-life-observations/dahua-xiyou/group-interactions/conversations/2026-09-23-s1-moonlight-box-time-editing-rules.zh-CN.md) and S4 record above establish the story context.
- [Baijingjing export](sources/host-exports-2026-10-04/item1-baijingjing.json): `/a508f481/chat_request_received/object` supplies chat-73; `/a508f481/chat_reply_original/object` supplies message `a508f481e9714bebacf74527b675051c`, replying to `chat-73`. `/a508f481/runtime_request/object` contains the selected request and startup context; `/a508f481/runtime_reply_as_surviving/object` is an overwrite notice, not recovered generation text.
- Analysis: the authorship assertion alone is insufficient; the memory-loss rule and accepted question provide an explicit reason for the hypothetical veto. Its relation to persona is expressed within an elicited story task. No linked later retrieval or durable uptake is established. [Pre-S1 sensitivity check](sensitivity-check.md) documents earlier agency and first-person framing.
- Adjacent negative case: `/c50ab6b7/chat_request_received/object` supplies chat-82, explicitly asking for a correction; `/c50ab6b7/chat_reply_original/object` is the 25 September answer. This is prompted production repair. The timestamp annotation discrepancy is disclosed in [host-export-assessment.md](host-export-assessment.md); original JSON bytes are unchanged.

## Term search and duplicate registration: E26/E27

- [Host audit report summary](zixia-evidence-package.md), sections **Long-term memory audit** and **Archive corrections**, is the source of the keyword-search counts and duplicate-message report. These are reported findings, not independently reproduced runtime searches.
- For the observable text recurrence, compare the [23 September warm-up](sources/docs/agent-life-observations/dahua-xiyou/group-interactions/conversations/2026-09-23-post-s2-novelty-before-first-box-ring.zh-CN.md) and [3 October names discussion](sources/docs/agent-life-observations/dahua-xiyou/group-interactions/conversations/2026-10-03-name-expectations.zh-CN.md). E07/E23 cover the displayed text; E27 covers the host's duplicate-registration explanation.
- Zero keyword matches cannot exclude paraphrases or other stores. A displayed duplicate is not an independent later answer or evidence of recall.

## Peach exchange: E21/E30, d77f040177f7

- [Archived exchange](sources/docs/agent-life-observations/dahua-xiyou/relationships/conversations/2026-10-03-baijingjing-tangsanzang-peach-reciprocity.zh-CN.md) and [peach export](sources/host-exports-2026-10-04/item3-peach.json).
- Seed/request: `/tang_chat_inbox_133/object` and `/tang_runtime_request/object`.
- Reply and staging: `/tang_runtime_reply/object` and `/tang_chat_reply_staged/object`.
- Transcript: `/private_json_session_d77f040177f7_entries` contains two records bearing session ID `d77f040177f7`; reciprocal receipt is `/baijingjing_received_tang_reply_as/object` (chat-139).
- Follow-up: `/baijingjing_followup_afa432/object` replies to chat-139. `/tang_inbox_next_files_after_133` contains two later selected inbox records. The follow-up's absence from these samples is observable; exhaustive absence from the mailbox is a host assertion in `/afa_delivery_verdict`.
- These records support two delivered transcript turns in the supplied export. They do not prove spontaneous initiation, complete mailbox coverage, fulfillment of a future promise, or invented-past uptake. [Relay commit copy](sources/relay-commit-74e6688.json) documents code, not execution.

## Integrity and scope

- [Corpus manifest](sources/manifest.json): 60 frozen files and their hashes.
- [Discovery inventory](sources/discovery-inventory.json) and [selection audit](sources/selection-audit.csv): 108 candidate paths, 60 retrieved, 48 not systematically analyzed.
- [Export receipt](sources/host-exports-2026-10-04/receipt-and-consistency.json): received-file sizes, hashes, and 19 selected checks. See the assessment for the annotation erratum outside those checks.
- [Evidence ledger](evidence-ledger.md): E01-E44 and their inference boundaries.
- `bundle-manifest.json` in the ZIP lists packaged file hashes. Bundle/receipt integrity does not authenticate the original deployment or establish archive completeness.

## Follow-up: E31-E34 (Table II), with contextual E35-E37

- [Follow-up manifest](sources/followup-2026-10-10/manifest.json) identifies all 23 frozen files.
- [Episode audit](sources/followup-2026-10-10/episode-audit.csv) maps F01-F21 to exact split files, reported dates, visible developments, and inference limits.
- [Follow-up interpretation and criteria](followup-audit.md) maps E31-E37 to episode rows.
- In the aggregate export, group rounds 1-6 are the primary basis for E31. Private rounds 1-7 expose repeated initiation text for E32. Private rounds 5, 8 and 9 plus group round 5 support E33. Host-private rounds 1-2 and group round 3 support E34.
- Original-language quote anchors for E34 are Qingxia's "群里不提，我嘴严着呢" (host-private 1), "群里不提，这是我们俩的" (host-private 2), and "我和紫霞约过，我喊，你应" (group round 3).
- Aggregate and split records are duplicate source representations, not independent confirmation. This follow-up lacks the selected request/reply links available for the older peach episode.

## Table I: complete follow-up coding (v0.23)

Table I resolves to [followup-coding.csv](followup-coding.csv), one row for each of F02-F21. The [codebook](followup-codebook.md) defines O/N/U/NA and the counting rules; [summary counts](followup-coding-summary.json) are reproduced by [summarize_followup.py](summarize_followup.py). The CSV includes literal Chinese anchors and one-based source lines. [Commitment traces](followup-commitment-traces.md) distinguish local acknowledgments, preference revisions, performed speech, renewed promises, and unobserved future tests. These are additional analyses of the same sources, not new independent evidence.

## Runtime-provider history: E38

The [14 October supplied account](sources/observer-supplied-2026-10-14/runtime-provider-history.zh-CN.md) gives the reported 28 September Claude interval and 1 October return to Muse. [model-provider-history.md](model-provider-history.md) separates provider, model ID, chat route, source status, and implications. Earlier source [README](sources/docs/agent-life-observations/dahua-xiyou/README.zh-CN.md) lines 295-313 covers the Sonnet change, while lines 323-345 contain agent self-reports that do not independently identify execution. No raw configuration snapshots or per-request model records accompany the newer account.

## Intervention motivation and reported non-recovery: E39

The [observer's direct clarification](sources/observer-supplied-2026-10-14/private-chat-switch-outcome.zh-CN.md), quoted verbatim after its provenance header, states both the reason for switching models and the absence of perceived improvement. Its [separate receipt](sources/observer-supplied-2026-10-14/outcome-receipt.json) preserves the new source without changing the original chronology receipt. This supports the source-attributed operational outcome in the abstract and IV.C, with causal limits in V; it does not change Table I.

The [Sonnet target clarification](sources/observer-supplied-2026-10-14/sonnet-target-clarification.zh-CN.md) identifies the intended model and treats the initial Opus default explanation as uncertain. It supports the revised main-text wording without creating a separate Opus experimental condition.

## Qualitative extension: E40-E44 (Table II)

The [extension analysis](followup-extension-2026-10-13.md) maps N01-N07 and incomplete X01 to exact source lines and inference boundaries. The [six-file manifest](sources/followup-2026-10-13/manifest.json) pins the export, three dependent indexes, and two historical context files at 174d1c88. Only seven new completed sessions are added; indexes and historical records add no episodes.

- E40: export lines 3, 6, and 80; reported no new peer starts versus four host-initiated sessions.
- E41: N06, especially line 60; the whole-peach norm used in a hypothetical memory judgment.
- E42: N01/N03/N05, especially lines 106-108; reciprocal checking added to custody.
- E43: N07, lines 114-120 and 127; elicited provenance constraints and pending implementation.
- E44: X01, lines 72-76, and the historical skip-repair source; timeout and fallback are distinct from agent decisions.

The original 20-session coding and Table I remain unchanged. The combined 27-session archive is not presented as 27 coded trials.
