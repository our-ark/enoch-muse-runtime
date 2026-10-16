# Supplement S1: evidence companion, v0.28

For **Enoch–Muse: A Protocol and Testbed for Longitudinal Studies of Persistent Multi-Agent Interaction** (IEEE conference draft, 16 October 2026).

Supplement S1 is distributed in this versioned repository directory and its companion ZIP. Cite the full commit permalink for this release. This artifact is not a conference submission; independent validation remains incomplete.

## Protocol and backfill

Begin with [research-protocol.md](research-protocol.md) for the target evidence fields, claim boundaries and implementation status, and [backfill-protocol.md](backfill-protocol.md) for historical recovery rules. The protocol was specified retrospectively on 15 October; this supplement does not turn earlier collection into a prospective study. No complete historical backfill has been performed.

The [new source receipt](sources/protocol-2026-10-15/receipt.json) freezes the exporter, its tests and instructions, and the first daily package (14 October observations exported 15 October). This is separate implementation evidence, excluded from the existing 27-session analytical corpus. Source hashes and nine offline unit tests verify selected file-handling properties, not original generation or complete deployment coverage.

## Start here

1. Begin with the [coding rules](followup-codebook.md), [20 episode rows](followup-coding.csv), [descriptive counts](followup-coding-summary.json), and [commitment traces](followup-commitment-traces.md) for Table II in v0.28 (Table I in earlier versions). Read [followup-audit.md](followup-audit.md) and the [episode audit](sources/followup-2026-10-10/episode-audit.csv) for continuity with limited development, local counterexamples, and source limits.
2. Use [protocol-worked-decisions.md](protocol-worked-decisions.md), [evidence-locators.md](evidence-locators.md) and [followup-coding.csv](followup-coding.csv) to resolve Table III's illustrative contrasts and E/F evidence IDs. Reference numbers in older analytical notes belong to their historical manuscript versions; record IDs and source locators remain stable.
3. Read [host-export-assessment.md](host-export-assessment.md) for the older selected JSON exports and their timestamp annotation erratum.
4. Consult [evidence-ledger.md](evidence-ledger.md), [selection-protocol.md](selection-protocol.md), and [sensitivity-check.md](sensitivity-check.md) for selection boundaries and the pre-writing comparison.

5. Read [the seven-session qualitative extension](followup-extension-2026-10-13.md) for N01-N07, incomplete X01, E40-E44, later use of the whole-peach norm, and precise source lines. The [Chinese assessment](followup-assessment-2026-10-13.md) gives additional reasoning. Table II contains the unchanged original 20 sessions.

6. See [model-provider-history.md](model-provider-history.md) for the reported Claude interval and 1 October return to all-Muse routing; its [separately supplied account](sources/observer-supplied-2026-10-14/runtime-provider-history.zh-CN.md) is not part of the frozen Git snapshots.

## Included materials

- Sixty unchanged Chinese records from tree `513eebe85ccadbdcb1857e87280549e7ae9a660e`, preserving `sources/docs/`: nine indexes and 51 transcripts or interpretations.
- The original 108-path discovery inventory, frozen tree response, 60-file manifest, and selection audit. Forty-eight candidate files were not systematically analyzed.
- Three minimally redacted derivatives of JSON exports received on 4 October, with the original receipt, public receipt and redaction map. Original files remain private; dialogue and trace identifiers are preserved.
- Twenty-three additional Chinese files at tree `52d3f69d3cc56ed87a37103b6cc8ff4afbc9a39c`, under `sources/followup-2026-10-10/`: 20 follow-up episode records (six group, nine peer-private, five host-private), one 3 October boundary episode, one overlapping aggregate, and one dependent interpretation note.
- The follow-up hash manifest, 21-row episode audit, record maps, and analytical companions.
- The v0.16 codebook, 20-row descriptive coding, JSON summary, selected outcome traces, and reproducible count/anchor checks.
- The observer-supplied runtime-provider history received 14 October, its local receipt manifest, and a source-qualified timeline. A separate direct clarification and receipt preserve the observer's report that switching was intended to restore private chatting and brought no improvement. These add no conversation episodes, activity counts, or independently verified configuration traces.
- Six unchanged files at tree `174d1c88b635ce3d979bd5a26cc3e5046e7ac5cc`: the October 10-13 aggregate, three dependent indexes, and two historical context files, with retrieval metadata and hashes. These add seven completed sessions and one incomplete attempt; indexes and context add no episodes.
- A separate direct clarification identifies Sonnet as the intended model. The possible default origin of the initial Opus self-report remains unverified; transition and CLI details are preserved in the chronology rather than the main text.
- The saved public routing-code commit. Code existence does not prove execution.
- `bundle-manifest.json` lists names, sizes, and SHA-256 hashes of every other packaged file.

## Interpretation boundaries

The initial sources support attributed script revision and task-elicited persona-relevant expression. Follow-up sources show recurrent group themes and responsive private dialogue, including local commitments, preference revision, and an evaluated conversational act. Sustained, opportunity-tested consequences are less clearly documented. The observer additionally reports no improvement in private chatting after an operational model switch. This outcome report does not establish total inactivity, a measured decline in creativity, or the causes of stagnation.

The coded follow-up covers its supplied session list through 10 October 16:49 PDT, not all deployment activity. The separate qualitative extension continues from 10 October 17:07 through 13 October; it adds seven completed sessions without changing the original codes. All four new host-private sessions quote both sides, unlike the earlier host summaries. The no-peer-initiation claim is summary-level, and memory-source agreements do not establish implementation. Missing self-check and failure records prevent initiation-rate estimates. Host-private prompts survive as summaries; full request contexts are unavailable. Aggregate and split files overlap. There is no independent reliability study.

Neither set establishes durable prequel uptake, causal identity change, exhaustive generation ownership, or complete mailbox histories. Hashes preserve received copies and repository fidelity, not deployment authentication. Host-specific path prefixes in the three JSON exports use `<HOST_ROOT>`; relative paths and original IDs remain. Use the public hash map and record locators for review.


## v0.20 conceptual positioning

The paper explicitly extends PAI-Bench's distinction between recall, expression, and enactment to jointly negotiated narratives and relational commitments. It does not run PAI-Bench or establish collective identity formation. Social initiative is treated as a separate outcome, not an automatic identity-fidelity criterion. This positioning change adds no episodes, codes, or empirical results.


## v0.21 repository access

The paper now links the public repository from an Introduction footnote on the first page. The final data statement and frozen-snapshot citations remain. This editorial change adds no data or claims, and does not publish this locally prepared supplement.


## v0.22 availability wording

The first Introduction paragraph now explicitly states that code and the curated conversation archive are publicly available, followed by the repository footnote. The footnote supplies the URL. This does not claim that the locally prepared supplement has been published. No data, coding, or research findings changed.


## v0.28 protocol application

The [blank structured template](protocol-record-template.json) and [five worked decisions](protocol-worked-decisions.md) supplement the expanded event definitions, verification profiles and analyst decision procedure in [research-protocol.md](research-protocol.md). They add no episodes and do not change the original coding. The examples are retrospective, hypothetical interpretation contrasts, not an independent before/after experiment or measured reduction in research errors. No additional end-to-end instrumentation is claimed.


## v0.28 independent-review preparation and traceability

- [opportunity-criteria.md](opportunity-criteria.md) specifies five eligibility gates and distinguishes eligibility, outcome and observation completeness. Historical opportunity denominators remain unknown.
- [protocol-case-ledger.md](protocol-case-ledger.md) and [protocol-case-ledger.json](protocol-case-ledger.json) match all four Table III rows to literal anchors or JSON pointers and frozen source hashes. These are author/Codex worked examples, not independently validated labels.
- [protocol-validation-plan.md](protocol-validation-plan.md) and [the coordinator pilot archive](protocol-pilot-8-episodes-2026-10-16.zip) provide the unrun eight-target, two-reader pilot. There are no reviewers, collected judgments, agreement scores or accuracy results. The coordinator must release T before P, not both at once.
- The pilot's source additions, protocol guidance and order co-vary. Same-corpus design and visible archival annotations prevent claims of held-out or fully blinded validation.

This is the public release artifact. No DOI has been assigned. The prepared pilot remains unrun; making its plan public does not create validation results.

## Commitment example and offline inspection

[commitment-worked-example.md](commitment-worked-example.md) traces obligation terms, conditional opportunity, a performed sentence, its quoted acceptance, and what remains open. It does not equate an accepted conversational act with full repayment or sustained relationship change.

Run `python3 verify_artifact.py` from the artifact directory to check file hashes, literal anchors, JSON pointers and saved annotation counts. This is read-only, requires only Python standard-library modules, and never runs archived scripts or calls model services. It does not validate semantic judgments or authenticate the original deployment.

## Public-copy provenance

Read [REDACTION.md](REDACTION.md) and [redaction-manifest.json](redaction-manifest.json) before using the three selected host exports. All other frozen source files and the original 20-episode coding retain their bytes. [RELEASE-CHECKS.md](RELEASE-CHECKS.md) separates mechanical checks from research validation.
