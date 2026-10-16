# Independent-review pilot plan — v0.26

Prepared 16 October 2026. **Status: prepared, not run; no reviewers recruited and no judgments collected.** The user has indicated that independent reviewers are not currently available. This document specifies a future feasibility pilot, not a completed validation or a preregistration of the historical study.

## Question and design

Can two independent readers make inspectable, source-qualified judgments about the same interaction records, and where do their judgments differ? Use eight target episodes selected from the existing 20-session corpus without inspecting outcome fields during selection: two group, four peer-private, two host-private. Rank IDs within each stratum by SHA-256 of the fixed seed plus episode ID; select the required number. Preserve the full selection manifest and do not replace inconvenient cases.

This is a retrospective, within-reader staged comparison:

1. **T — transcript-only:** each reader receives only verbatim-utterance excerpts and the same five claim questions. Both submit independently; the coordinator freezes and hashes both responses before providing the next package.
2. **P — protocol plus sources:** each receives the protocol guide, opportunity gates, the source-qualified archive/context records, and fresh copies of the same forms. Preserve T answers; do not overwrite them. Readers remain independent until both P submissions are frozen.
3. **Audit:** inspect cited locations and stated claim requirements, retain disagreements, and record the basis of any adjudication. Do not treat agreement as truth.

Reader R1 and R2 see opposite target orders; P reverses each reader's T order. This changes ordering but does not remove learning or carryover. Reviewers must disclose prior contact with the paper, deployment, original labels, or this discussion, Chinese reading ability, and any AI assistance. Independent human validation cannot be claimed for model-generated labels.

## What this pilot can and cannot test

T and P differ in evidence availability, protocol instructions and order. Therefore changes cannot be attributed solely to the protocol. P is a combined evidence-and-guidance condition. The same historical corpus informed protocol design; it is not held out, and target/context episodes overlap and are dependent.

Primary descriptive outputs are reader agreement within each stage, claim-level source traceability, unresolved requirements, and time/burden. No power calculation or population-level significance claim is appropriate for eight dependent targets. No accuracy claim can be made without an independently audited reference record set. The evaluation is not a benchmark for the agents themselves.

A stronger later design would separately compare transcript plus generic guidance, full evidence plus generic guidance, and the same full evidence plus protocol guidance, using independent assignments, new cases and an independently audited reference. That experiment is not implemented or performed here.

## Fixed claim questions

For each target, both stages ask whether the provided material supports:

- Q1: at least one response that addresses another participant's contribution;
- Q2: fresh agent-originated initiation of this episode;
- Q3: a stated or renewed prospective commitment/norm;
- Q4: a completed act satisfying a specified commitment, with its terms identified;
- Q5: an attributable local change in preference, norm, or subsequent interaction.

Responses are **S** (supported), **C** (contradicted), **U** (unresolved), or **NA** (not applicable), with a quotation, locator, reasoning and missing evidence. C requires counterevidence; silence is not contradiction. An unfilled cell is not U and must not be scored as a completed judgment. These codes belong to this pilot, not the frozen 20-episode annotation set.

## Analysis specified before collecting judgments

- Report completed/missing cases and cells per reader and stage; no imputation.
- For each stage, report the exact agreement numerator/denominator for paired completed judgments, plus the full category cross-tabulation. Report joint NA separately and provide a second denominator excluding NA. Cells share readers and episodes; do not present them as independent trials.
- For S/C claims, mechanically check that each citation resolves and the quoted span matches. Semantic support then requires human audit; a matching string is not sufficient.
- Record unsupported assertions, justified supported claims, and unresolved requirements separately after audit. An all-U strategy is not evidence of superior interpretation; count supported positive findings as well as appropriately withheld stronger claims.
- Compare each reader's T/P transitions descriptively, including unchanged correct restraint and newly supported positive findings. Report evidence added in P beside each changed judgment.
- Preserve initial answers, audit decisions, disagreements and final records separately. If only authors adjudicate, describe this as author adjudication, not independent ground truth. No “error reduction” or accuracy statistic without a suitable reference.

## Packet composition and blinding limits

The coordinator archive contains separately releasable T and P packages and blank response/audit forms. Send only T initially. The target IDs and extraction map are retained for reproducibility. Source excerpts reproduce the text following the archive's exact `原文（` marker; summary paragraphs are excluded from T, and missing host turns are not invented.

P includes the eight full target files and a fixed set of linked context files. It contains no original coding CSV, manuscript results, worked decision answers, or populated evaluation forms. However the original archives themselves contain host summaries and interpretive annotations. These are visible source material, not independent verdicts, and prevent a claim of fully blinded P assessment. Readers are told to distinguish annotations from quoted speech and supported execution.

Record-level hashes establish fidelity to frozen sources, not original deployment authenticity. This plan does not authorize contacting reviewers or agents, publishing private exports, or changing live collection. Materials are prepared locally for later review.
