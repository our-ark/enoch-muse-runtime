# RIPA research artifacts

The adapter and synthetic migration records support
[Runtime-Independent Persistent Agents](https://arxiv.org/abs/2609.00546).
The historical records keep the versions, failures and limitations observed
at the time. Publishing them does not create new experimental outcomes.

## Frozen study

The measured study is pinned at
[`084e1b1c6a54af749fb28a20e4745025badc0899`](https://github.com/our-ark/enoch-muse-runtime/tree/084e1b1c6a54af749fb28a20e4745025badc0899/experiments/ripa-study-20260919),
on `exp/ripa-study-20260919`.

| Group | Cases | Recorded outcome |
| --- | --- | --- |
| Qualification Q | 1 | First-attempt pass |
| Codex - Muse - Codex R1-R5 | 5 | Five first-attempt passes |
| Matched same-runtime C1-C5 | 5 | Five first-attempt passes |
| Planned fault F | 1 | First worker killed; native recovery and continuation passed |

Read `RESULTS.md` and `PAPER-NOTES.md` in that pinned directory before using
the numbers. Do not pool qualification, controls and fault recovery into one
success rate. The frozen body is Enoch
`66781e209962bcce6d5254e50d05f000ac914668`; the tested adapter target is
`68e94efd98962004dbc96964aff3ed4dae00bc0e`. The Muse deployment uses a different
local commit with the same verified tree
`643dfa19e693f3d519edc7fd7712c256bdd196c7`.

The archive contains the fixed protocol, case inputs, driver and verifier
sources, model request/reply records, process evidence, native state snapshots,
encoded migration ZIPs, result records and SHA-256 manifests. Text packages
store file bytes as UTF-8 strings. `local-verification-package.json` indexes
five hash-checked shards covering 495 local files. Case return packages hold
the Muse evidence; F's supplement preserves recovery records omitted from its
initial return package. The original packages remain unchanged.

Paths, usernames, timestamps, process/session identifiers and configuration
source-path references in these records are execution provenance. They are
not credentials or instructions to use the original machines. Identity and
memory contents in this archive are synthetic experiment fixtures; private
production identity, memory and credentials are not research inputs here.
Historical notes describing this repository as private describe its status
when the records were created, before the open-source release.

## Inspect without model access

Use a normal clone (or fetch the artifact branch if using a shallow clone):

```bash
git fetch origin exp/ripa-study-20260919
python3 scripts/verify_study_archive.py
```

This command reads the pinned commit with Git, checks the local shard and
per-file hashes, checks encoded archive checksums/ZIP integrity, recomputes the
arithmetic witnesses and core state-continuity comparisons, and checks the
saved verifier outcomes for all twelve cases. It does not contact a model,
execute archived scripts or certify the original hosts. It is an offline
integrity/consistency check, not an independent live replication.

For manual inspection, `--extract /absolute/path/to/new-directory` writes the
validated text files to a new directory. It refuses existing destinations and
unsafe archive paths. ZIP contents remain encoded in their recorded JSON
files; no archived code is automatically run. Archived workflow/verifier
scripts use the original study layout and are retained as provenance, not
promised to work unchanged under an arbitrary checkout layout.

## Live reproduction boundary

The fixed protocol is in the common package under `protocol/PLAN.md` and
`protocol/MUSE-EXECUTION.md`. New live runs require separate Codex and Muse
access, compatible hosts and an operator serving actual Muse mailbox requests.
Use fresh isolated roots and keep all started outcomes. Models and hosted
services may change, so a new run need not reproduce the original responses.
The deployment consumer is external to this repository; the consumer stub is
protocol documentation, not a working Muse API client.

All Muse runs were supervised through a shared operator conversation. Fresh
roots do not imply blinded or independent reasoner sessions. Source/return
model labels are configured values, and Muse's backend model and usable token
usage are unknown. Zero usage placeholders must not be treated as zero cost.
F interrupts a worker while waiting for a reply, not during an external
action. Stale-reply rejection stderr is saved; the helper's exit code 3 was
only operator-observed. The read-only fault verifier needed a documented
directory/log-format adaptation; no experiment was rerun for that adjustment.

The earlier recovered development pilot is preserved at
[`26843ec788f4f31696b68b46ec635e85921fbe91`](https://github.com/our-ark/enoch-muse-runtime/tree/26843ec788f4f31696b68b46ec635e85921fbe91/experiments/ripa-pilot-20260919)
and excluded from the measured series. Its first worker's disappearance has
an unknown cause. These artifacts do not establish arbitrary-task migration,
behavioral identity equivalence, general exactly-once external effects or
unattended reliability.

## End-to-end verification (2026-09-18)

`scripts/e2e_live_respond.py` loads the provider through Enoch's **real**
registry (`load_provider("runtime", name="muse")`, entry point
`runtime.muse`) and runs one blocking `respond()` turn:

```
available runtime providers: ('codex', 'muse')
loaded: our_ark_muse.core.MuseRuntime
health: ProviderHealth(... passed=True ...)
respond() returned.
session_id: 53030fbb2f1a406e84cae50b0b30f7e0
final_text: Mailbox bridge live: consumer received request ... and answered. Round-trip OK.
```

Provider → `inbox/<id>.json` → consumer → `outbox/<id>.json` →
`respond()` returns the reply text. Full loop verified against the real
Enoch provider contract.

## License and citation

The repository's [Apache-2.0 license](../LICENSE) covers its project code,
documentation and synthetic research artifacts, including the historical
experiment branches, subject to applicable third-party notices. Enoch retains
its own Apache-2.0 license. Muse itself and access to hosted services are not
distributed or licensed by this project. Cite the RIPA paper and pin the
specific code and artifact commits used.
