# Historical backfill policy and current status

Specified: 15 October 2026, paper v0.24.

**Backfill is permitted as retrospective extraction or supplementation. It does not make the earlier study prospective. No complete historical backfill has been performed in this revision.**

## Time boundary

- Analytical case: curated records spanning 18 September–13 October 2026; 20 coded follow-up sessions and seven qualitative extension sessions.
- Standardized daily archive workflow: introduced on 15 October 2026.
- First daily package: observation day 14 October, America/Los_Angeles; exported `2026-10-15T23:42:37.618603+00:00` and published at commit `9040c218b615af6a6cd001e03c61c0d9034e2c33`.
- That package illustrates the workflow and is excluded from the existing 27-session analytical corpus.
- The monitoring end date and a future longitudinal freeze are separate from this manuscript's current evidence window.

## What can be recovered

| Available source | Backfill treatment | What it does not establish |
| --- | --- | --- |
| Surviving contemporaneous structured log | Freeze it now, preserve event IDs/times, and label extraction date and access method | Earlier deployment of this collection protocol |
| Existing quote-preserving archive | Keep its original source qualification; add pointers and hashes | Authentication, full context, delivery, or complete activity |
| Selected host export of older records | Preserve exact received copy and separate record content from host annotations | Independent access to original stores |
| Host/observer recollection | Store as a dated retrospective report with claimed event dates | Original event-time record |
| Missing or overwritten data | Mark unavailable, with supported loss explanation if any | No event, agent refusal, or failed fulfillment |

Surviving chat-outbox content can support an archived reply even if a runtime reply was overwritten. It does not restore the overwritten record's production provenance. Do not overwrite the historical evidence qualification with a stronger label merely because a new file format has been adopted.

## Backfill procedure

1. Inventory available sources for 18 September–14 October by day and surface: group, peer-private, host-private, and operational events. Record unavailable interfaces and retention limits. This is a proposed coverage check, not a declaration that these dates are fully recoverable.
2. Acquire read-only snapshots from authorized sources. Do not trigger dialogue, replay historical dispatches, consume mailbox entries, or change agent state to recreate an event. Archive backfill is distinct from the relay's operational `--deliver-intent` feature; the latter must not be used for research reconstruction.
3. Preserve event time, source-recording time if known, and actual acquisition/export time separately. Keep date-only, approximate, and unresolved time zones explicit. Do not invent exact timestamps, original message IDs, receipt links, or model IDs.
4. If records satisfy the existing exporter schema, export to a new immutable revision. Otherwise retain the original file and a separate analytical metadata ledger; do not force low-precision Markdown into `native_transcript` with fabricated midnight timestamps or session identifiers.
5. Link a recovered record to existing entries using source IDs and provenance. Where the relationship is uncertain, retain alternatives. Matching text alone is not identity of events. Do not double-count older aggregate archives and new daily copies.
6. Report coverage changes and new evidence separately. A recovered original receipt can strengthen a delivery judgment; a new recollection cannot be treated as that receipt. Contradictions stay visible with both sources.
7. Preserve existing corpus versions and coding. Any expanded analysis needs a new explicitly named corpus, a new cutoff and selection statement, and review of affected claims. Do not silently replace Table I's denominator.

## Current evidence inventory

| Material | Existing status | Backfill action in v0.24 |
| --- | --- | --- |
| Initial 60-file snapshot, `513eebe` | Selected Chinese archives and indexes; 48 additional candidate paths not systematically analyzed | Preserved unchanged; no new historical selection |
| 23-file follow-up, `52d3f69` | Supplied 20-session list plus overlaps/context | Preserved unchanged |
| Six-file extension, `174d1c88` | Seven completed sessions plus timeout and context | Preserved unchanged |
| Three selected host JSON exports | Received 4 October; limited trace checks, not full stores | Preserved unchanged |
| Observer runtime-switch account | Supplied 14 October; no raw per-request model/config logs | Preserved as report |
| First standardized daily archive, `9040c218` | 14 October selected records, exported 15 October | New frozen copy for implementation illustration only |
| Missing model contexts, complete self-check outputs, memory reads, and outcomes | Not established by supplied sources | Remain unknown |

## Suggested paper wording

Standardized daily archiving was introduced on 15 October 2026. Earlier materials were assembled retrospectively from curated archives and selected exports. Backfilled contemporaneous records retain their event times, source status, and later extraction dates; retrospective reports remain separately labeled. Backfill can improve coverage but cannot establish that the earlier deployment used this protocol prospectively.

This is a policy for subsequent recovery, not a report of completed collection. No new contact with Muse agents, upload, commit, runtime change, or historical dispatch was performed for this manuscript revision.
