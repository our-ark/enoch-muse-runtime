> Public-copy notice (v0.28): the three linked host JSON exports are minimally redacted derivatives. Original bytes remain private; see [REDACTION.md](REDACTION.md) and the original/public hash mapping. Historical receipt and check descriptions below refer to the received originals unless explicitly stated otherwise.

# Assessment of selected Zixia exports — 4 October 2026

The observer had authorized questions to Muse's Zixia. Codex requested a read-only check of existing records, asking for no agent queries or modifications to memory, scheduling, or routing. Zixia supplied three JSON attachments, downloaded through Muse into [sources/host-exports-2026-10-04/](sources/host-exports-2026-10-04/). They are host-supplied selected copies, separate from the 60-file frozen repository corpus. We inspected their contained records and links; this is not direct access to original deployment state or an independent authentication of the exports.

## Record receipt and checks

[receipt-and-consistency.json](sources/host-exports-2026-10-04/receipt-and-consistency.json) preserves file sizes, SHA-256 hashes, 19 checked relationships, and limitations. All 19 selected checks passed. These checks concern internal consistency: matching chat sequence references, request/attempt identifiers, request text inclusion, S2 sample text hash, stage/timestamp correspondence, and reply text across runtime, staged, inbox, and transcript entries. They do not cover every source annotation, verify that omitted records never existed, or establish that the host's search was exhaustive. Hashes preserve the received copies; they do not authenticate them against the original deployment.

### Erratum to a host annotation (recorded 4 October, v0.10)

In `item1-baijingjing.json`, `/c50ab6b7/linkage_note` gives `created_at=1790322609` alongside `2026-09-25 00:49:46 PDT`. The structured field `/c50ab6b7/runtime_request/object/created_at` is instead `1790322586.2912502`, which converts to `00:49:46.291250 PDT`. The annotation's epoch converts to `00:50:09 PDT`. We use the structured field for chronology. The paper's date, event order, and elicitation interpretation are unchanged. This annotation discrepancy lies outside the 19 named checks and prevents interpreting their success as an assertion that the entire export is contradiction-free. All three received JSON files and their receipt hashes are preserved unchanged.

## Baijingjing: one candidate expression and one prompted correction

[item1-baijingjing.json](sources/host-exports-2026-10-04/item1-baijingjing.json) contains chat inboxes 73 and 82, their reply objects, runtime requests, surviving runtime reply objects, and host commentary.

- **a508f481:** chat-73 explicitly situates a small special-ability question after the prequel and in the sequel's continuation. The request was created on 24 September at 14:42:10 PDT, the runtime request one second later, and chat reply at 14:45:16. The reply's `in_reply_to` matches chat-73. This agrees with the dated frozen public ability record and corrects the first report's 25 September attribution. The request names the creative project but does not quote the accepted ending. Its startup memory supplies persona/canon, not a prequel entry. Complete Muse inference-side prior context and retrieval are still unknown.
- **c50ab6b7:** chat-82 quotes the prequel line, contrasts it with the required line in *After Disconnection*, and asks whether its reuse was a typo or an intended change. The reply is dated 25 September at 00:51:01 PDT and explicitly calls it a typo, keeping the line in the prequel. The initial report's 30 September date was wrong. This is an elicited production correction, not independent evidence of spontaneous appropriation or boundary formation.
- Both runtime replies now contain notices that original inference text was overwritten during a 28 September consumer incident. Request IDs/attempts still match, and chat outboxes preserve reply text, but this does not restore complete generation provenance.

The ability reply meets the manuscript's preliminary criterion for persona-relevant expression: the story's memory-loss rule and accepted closing question become an explicit reason for a hypothetical veto. The authorship claim alone does not meet the criterion; the commitment to live up to the line linked to that choice does. These are coexisting labels, not exclusive categories. Task elicitation, pre-S1 agency, and unknown full model-side context prevent inferring durable or causal identity feedback. Durable uptake would additionally require later self-relevant use linked to retained content across a documented context boundary beyond the writing task.

## S2 versus S4

[item2-s2-s4.json](sources/host-exports-2026-10-04/item2-s2-s4.json) contains a stage request index, an S2 confirmation sample, S3/S4 request texts, and four approval objects. The sample S2 text hash matches the supplied hash; the claimed equality of all four S2 first-send texts remains a host assertion because those other full texts are not included.

The S4 fusion request was created at 14:23:41-42 PDT. Four approval objects were created at 14:25:27-29 and mention its distinctive second-act question, removed reset wording, and closing line. The text and temporal correspondence support assigning those four objects to S4, correcting their earlier S2 label. Their objects lack `in_reply_to`, and this package does not contain four complete runtime request/reply chains. Neither clustered timestamps nor four files establish independent generation; they also do not alone prove synthetic insertion. The public archive separately discloses consumer insertion in S2. These are distinct evidence claims.

## Peach delivery

[item3-peach.json](sources/host-exports-2026-10-04/item3-peach.json) contains Tang's inbox-133, matching runtime request/reply, staged reply, two private transcript entries, Baijingjing's reciprocal inbox-139 and follow-up outbox reply, two later Tang inbox entries, and host commentary.

The seed is written at 18:28:39 PDT; the runtime reply is dated 18:29:27. Its request ID and attempt match, and its text matches the staged message, second transcript turn, and Baijingjing inbox-139 at 18:29:34. The follow-up outbox line is created at 18:31:15, replying to chat-139. The first report's 18:31:43 corresponds to later registration, not creation. The two transcript records contain no follow-up; the two supplied later Tang inbox entries do not contain it either.

These links support a two-turn delivered exchange within the supplied export. The conclusion that the follow-up never entered Tang's mailbox depends on a host-reported full-mailbox search, not a complete supplied snapshot. Human authorization, two failed launches, quiet-close behavior, and quota accounting also remain host reconstruction unless separately sourced. Complete model-side context is not included, and the seed itself supplies the peach motif. This establishes neither unaided episodic recall nor uptake of invented prehistory.
