# Corpus selection and retrospective inclusion audit

This note preserves the initial corpus disclosure from v0.9-v0.12 and documents the separate v0.13 follow-up addition below. It is a retrospective disclosure, not a preregistered protocol or evidence that the original retrieval followed predefined categories. The source deployment itself curated the archive before this paper's retrieval. The initial 55-file selection is preserved separately from five sensitivity additions made after review on 4 October 2026.

## Discovery scope

The frozen repository reference is `513eebe85ccadbdcb1857e87280549e7ae9a660e`, under `docs/agent-life-observations/dahua-xiyou/`. On 3 October 2026, the directory tree was retrieved again at this same reference to reconstruct and preserve the discovery inventory. The returned subtree is `f0dcd5ee5a0fc40f36160d861404101a93f454d9` and is not truncated. This operation adds inventory metadata, not new conversations to the analyzed corpus.

The tree contains 179 Markdown paths. Retaining Chinese paths and English-only paths without a parallel Chinese path produces the 108-document discovery scope: 107 Chinese paths plus `group-interactions/2026-09-28-letting-go.md`. Seventy-one parallel English paths are excluded by this language rule. All 55 already-retrieved documents are Chinese; the English-only document was not retrieved. An earlier manifest note ambiguously described that English exception as though it belonged to the retrieved set; the v0.7 note corrects that distinction.

The complete 108-path inventory, blob hashes, and retrieval flags are in [sources/discovery-inventory.json](sources/discovery-inventory.json). The corresponding frozen directory-tree response is in [sources/discovery-tree-513eebe.json](sources/discovery-tree-513eebe.json). All 60 current local content copies were checked against the snapshot's Git blob hashes and the manifest's SHA-256 hashes; they match.

## Retrospective roles of the retrieved set

Retrieval was question-driven: reconstruct joint authorship of persona prehistory, inspect candidate later references, and identify alternative sources or mediation that constrain identity claims. [sources/selection-audit.csv](sources/selection-audit.csv) assigns every retrieved file a present analytical role and rationale. A role describes how the document fits this reconstruction; it does not recover the original analyst's unstated motivation or imply that each file was independently coded. The roles are primary labels for navigation and can overlap substantively.

| Primary role | Files | Purpose |
| --- | ---: | --- |
| Writing core | 5 | Complete S1-S5 sequence: proposals, critique, decisions, and artifact revision. |
| Persona baseline | 4 | Operational origins and persona assignments before prequel writing. |
| Writing context | 5 | Warm-up and deployment-authored interpretations of stage continuity. |
| Attribution check | 14 | Memory and autobiographical provenance, supplied context, scheduling, displayed reciprocity, duplicate registration, and skip correction. |
| Later interaction context | 17 | Subsequent exchanges and persona context for comparing fictional and operational histories. |
| Production context | 1 | A reported downstream release; not a measure of autonomous production. |
| Navigation context | 9 | Directory indexes and deployment context; not independent conversations. |
| Initial selection | 55 | A dependent record set from one interacting group. |
| Pre-writing sensitivity addition | 5 | Three 20-22 September Moonlight Box conversations and two dependent interpretation notes, added after review. |
| Current total | 60 | Nine indexes and 51 other records; not 60 independent conversations. |

The set includes material that narrows or undermines stronger continuity claims: consumer-inserted approvals, externally supplied context, duplicate registration, host-supplied skip, and displayed dialogue whose delivery is questioned. Including such records does not establish balanced or exhaustive sampling. The supplemental host report is separate from these 60 files and supplies additional, independently unverified corrections. The additions test whether first-person regret, agency, and group framing preceded S1; findings and boundaries are in [sensitivity-check.md](sensitivity-check.md).

## What selection does not establish

The other 48 discovery paths were not systematically analyzed. Their inventory flags mean "not retrieved," not "excluded after full-text review." No per-file exclusion decision, exhaustive screening log, or original predefined sampling rule is claimed. Therefore, these data support a selected case reconstruction rather than a prevalence estimate, a response denominator, or a claim that no contrary episode exists outside the retrieved set.

The CSV includes E01-E30 ledger identifiers where a file has a provisional entry. A blank ledger field denotes contextual material without a separate entry, not a negative result. Both the CSV roles and ledger annotations remain preliminary and were not produced by independent coders.

## v0.13 follow-up addition (12 October 2026)

A later snapshot, `52d3f69d3cc56ed87a37103b6cc8ff4afbc9a39c`, adds the 4-10 October export and corresponding split records. All 23 newly added Chinese archive files were retained: 20 follow-up episode records, one 3 October boundary episode, their overlapping aggregate export, and one dependent interpretation note. Parallel English versions and navigation-index updates were not counted as new analytic material. The original 60-file manifest and 108-path inventory were not overwritten.

The [separate manifest](sources/followup-2026-10-10/manifest.json) records snapshot, paths, roles, Git blob SHA, SHA-256, and verification. The [episode audit](sources/followup-2026-10-10/episode-audit.csv) maps 21 episode rows to the source files and lists local changes as well as absent or unresolved consequences. The [follow-up analysis](followup-audit.md) defines the retrospective distinctions and limits.

The 20 follow-up sessions are all those listed in the supplied export through 10 October 16:49 PDT, not an exhaustive deployment sample. They comprise six group rounds, nine peer-private sessions, and five host-private sessions. Host-private prompts are summarized rather than quoted; skipped self-checks and failures are not included. No initiation-rate denominator exists. The observer's reaction is contextual evidence, not a metric.

Thematic assessment was introduced after reading the new material and the observer's expressed concern about stagnation. It was not preregistered or independently coded. Counterexamples, including whole-peach and voice-debt negotiation, remain included. The follow-up does not establish an estimated decline from an earlier novelty rate, model-specific causes, or absence of development outside the export.

## v0.16 coding scope (13 October 2026)

The new [episode annotations](followup-coding.csv) cover F02-F21 without further episode selection. F01 remains boundary context; the aggregate and interpretation note remain non-independent context. Selection of the older 55 files is still retrospective and cannot be relabeled a predefined inclusion rule. The 48 unexamined candidate paths cannot be treated as all duplicates, indexes, or irrelevant content.

The [codebook](followup-codebook.md) was developed iteratively by Codex after the initial thematic judgment, with no independent human validation recorded. The [commitment traces](followup-commitment-traces.md) include positive local changes as well as unobserved outcomes and an audience-constraint inconsistency. The new table is descriptive episode accounting, not an experiment or validated development score.
