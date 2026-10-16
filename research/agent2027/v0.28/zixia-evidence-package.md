> Public-copy notice (v0.28): the three linked host JSON exports are minimally redacted derivatives. Original bytes remain private; see [REDACTION.md](REDACTION.md) and the original/public hash mapping. Historical receipt and check descriptions below refer to the received originals unless explicitly stated otherwise.

# Muse deployment provenance audit and selected evidence excerpts

**Source:** A read-only report requested by the observer and provided through the Muse host assistant (Zixia) on October 3, 2026. This file preserves a drafting summary of that first report, separate from the current 60 frozen public GitHub records. Selected JSON copies were supplied and inspected on October 4; see [host-export-assessment.md](host-export-assessment.md). Original deployment files were not directly accessed. Reported details below remain deployment-supplied evidence; the corrections immediately below supersede inconsistent dates and stage attribution in the initial summary.

**October 4 corrections:** The four quoted approval files correspond to S4, not S2. Baijingjing's ability reply is dated September 24, not September 25; her boundary correction is dated September 25, not September 30, and is explicitly elicited by a prompt quoting the disputed line. The post-close peach reply was created at 18:31:15 PDT; 18:31:43 in the first report refers to its later registration. Selected records now link the two peach transcript turns to request/reply and inbox entries. The complete negative mailbox search and full model-side contexts remain unverified.

## Architecture and provenance

Zixia reports that she is the Muse host assistant, while Qingxia, Zhizunbao, Baijingjing, and Tang Sanzang are four independent Enoch instances with separate roots, daemons, mailboxes, and memories. Their configuration names Muse for both runtime and chat. During S1–S5 on September 23, however, all four used the Muse inference source through their daemon requests; later provider changes do not apply to that writing sequence. The archive's character-specific contexts and identities therefore differ, but the sequence should not be described as four independently configured language-model generations.

The report locates S1–S5 on September 23 and gives stage-level times and identifiers, but says that the September 23 inbox request files were not individually audited. Full request structures are reported to include request ID, attempt, kind, identity, message, session key, sandbox, working directory, state root, image paths, and creation time. This makes a raw provenance audit possible, but does not complete it.

The report also describes four “through” messages in chat outboxes, with creation times within roughly two seconds, and no matching runtime reply files. Their request-by-request correspondence to the S2 confirmation round has not been independently established. The manuscript relies on the public S2 archive's explicit consumer-insertion disclosure rather than treating this timestamp account as an independently verified generation audit.

## Long-term memory audit

Zixia reports searching the four `.enoch/memory/long_term.json` files on October 3. The reported counts are 14, 10, 9, and 8 entries respectively; searches for terms corresponding to “before the box rang,” “what can be lost,” “unedited,” and “prequel” found zero entries. The prequel materials remain in conversation logs, chat outboxes, and host-side room or goal documents. The report identifies one limited cross-context citation of the S4 line “问：丢得起什么” on September 25, followed by a September 30 statement that the line should remain in the prequel night. No verified example was found in which a prequel-specific item was retrieved outside a writing task and then caused a changed action.

This is limited negative keyword evidence, not proof that prequel material is absent from durable state. Paraphrases, unsearched stores, and complete later request contexts remain unresolved. Neither the keyword result nor the reported quotation completes a verified storage-to-retrieval-to-action chain.

## “Half a peach” exchange

The report separates four events:

1. **Intent:** October 3, 02:00, Baijingjing's self-check includes “想和【唐三藏】说【昨天中午那半个桃，我闻着香了。】”. It was initially only in an outbox and digest.
2. **Authorized backfill:** The observer authorized a relay test at 18:23 PDT. Two launches failed before the child environment was repaired; the third delivered the seed to Tang Sanzang's inbox at 18:28:39, as chat message 133.
3. **Automatic reply:** Tang Sanzang's daemon request is identified as conversation `af3e38cd34c3326be04aabd79a9da230d8a9ca9579b0ace3f5f812d2a71ddcd6`, attempt `37feed629d0749fc92ee12d4c2117df6`, replied at 18:29:27. The staged chat response is `06b9475be5424b2d8ccf98050920cdf3.json`; the private transcript session is `d77f040177f7` and contains two turns. A 90-second quiet period ended the exchange and one private credit was charged.
4. **Post-close line:** Baijingjing's 18:31:43 line was relayed to the observer but did not enter Tang's inbox and is absent from the private transcript.

The public repository commit [74e6688](https://github.com/our-ark/enoch-muse-runtime/commit/74e668851a70b3b4696ea02026d21a06ab724fa7) corroborates the addition of explicit-intent relay and delivery-failure cleanup. The report describes a delivered two-turn interaction after a human-authorized infrastructure intervention. The identifiers make that account traceable in principle; complete raw records have not been independently inspected, and code existence alone does not prove deployment or this event's delivery. The post-close line should not be counted as a delivered third dyadic turn on the evidence reported here.

## Archive corrections

- The October 3 names discussion repeats an earlier Zhizunbao message with the same message ID; it is duplicate registration, not a new answer.
- The “3:1” film-vote summary is an aggregation error. The available post-viewing statements are three unconditional votes for the black opening plus Baijingjing's conditional support; Tang's early ballot remains unresolved.
- “Thirty-some days” on October 1 is a prompt wording error. The reported baseline begins September 18, making the elapsed interval 13 days.

## Remaining checks

The report leaves three items open: the original Tang Sanzang early ballot on September 25, a file-by-file check of September 23 inbox requests, and exact S1 start/end ownership.
