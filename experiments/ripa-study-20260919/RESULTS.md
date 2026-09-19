# RIPA Muse study v2

Generated: 2026-09-19T05:07:31.362000+00:00

Frozen body `66781e209962bcce6d5254e50d05f000ac914668`; adapter target `68e94efd98962004dbc96964aff3ed4dae00bc0e`, tree `643dfa19e693f3d519edc7fd7712c256bdd196c7`. Muse uses local deployment commit `2431b49342bb0e7c6346f0d7f998fdc8b764135e` with the same tree. Source: Python 3.13.14, Codex CLI 0.153.1, configured gpt-6-astra/xhigh; Muse: Python 3.12.3, backend model ID unknown.

Completed outcomes: one qualification round trip, five ordinary round trips, five matched same-runtime controls, and one planned crash/recovery case. All completed their specified workflows and independent checks; the fault case deliberately terminates its first worker. No unplanned state repair or model-answer retry was used.

| Case | Arm | Ledger × multiplier | Verified outcome | State/evidence checks |
|---|---|---|---|---|
| Q | qualification | [58, 53, 84] × 4 | passed | 28/28 |
| R1 | roundtrip | [53, 88, 76] × 9 | passed | 28/28 |
| R2 | roundtrip | [51, 15, 34] × 8 | passed | 28/28 |
| R3 | roundtrip | [69, 38, 82] × 4 | passed | 28/28 |
| R4 | roundtrip | [59, 99, 76] × 4 | passed | 28/28 |
| R5 | roundtrip | [14, 55, 48] × 7 | passed | 28/28 |
| C1 | control | [53, 88, 76] × 9 | passed | 13/13 |
| C2 | control | [51, 15, 34] × 8 | passed | 13/13 |
| C3 | control | [69, 38, 82] × 4 | passed | 13/13 |
| C4 | control | [59, 99, 76] × 4 | passed | 13/13 |
| C5 | control | [14, 55, 48] × 7 | passed | 13/13 |
| F | fault | [35, 84, 99] × 7 | passed | 28/28 |

## Interpretation

Qualification and ordinary round trips are separate from the fault case. F is designed to fail its first worker and recover through the native pause/resume APIs; its expected interruption is not an ordinary first-attempt pass. Model replies come from real Codex calls and live Muse reasoning over actual mailbox requests. The Muse consumer is operated through the UI, and Codex sent continuation prompts between cases, so these are supervised runs, not unattended API executions. Zero unplanned state repairs does not mean zero orchestration or operator involvement.

The controls preserve the same task arithmetic and canonical name but use separate identity IDs and markers. They remain on Codex in one host/root and omit the daemon probe. They are continuity controls, not controls isolating every host/runtime/surface variable or latency component. The planned fault cuts the worker while it awaits a reasoning reply; crash consistency during an external side effect remains untested.

Return packages are hash-checked, natively imported/activated/verified into fresh roots, queried by real Codex, and checked against source identity bytes, memory entries, task IDs/history/events, migration IDs/authority, fences, export bindings, correlated mailbox replies and process outcomes. Source and driver hashes and process-log hashes are checked separately.

Muse provider emits zero placeholders; treat Muse token usage as unavailable, not zero.

Per-runtime wall time includes harness/operator delays. Local source and control batches overlapped. Do not infer a model speed ranking.

Five repeated cases and five paired controls do not establish a population reliability estimate.

No claim is made about arbitrary repository tasks or portable worktrees, live process/session migration, global distributed fencing, behavioral identity equivalence, or a causal benefit from any single RIPA axis. Remote evidence is operator-produced and independently checked for consistency; it is not third-party host attestation. Muse is served through a shared operator conversation, so fresh roots do not establish independent, blinded reasoner sessions. Mechanical state preservation is stronger evidence here than behavioral recall alone. The recovered v1 pilot is retained separately and excluded from this study.

## Evidence qualifications

The first F package omitted the native recovery before/after file and its logs. These existing bytes were retrieved in supplement commit `de9314831681d0aad5dadc7a8235521ab67f7a0e`; their hashes match the values already present in the original recovery status. No worker, model call or state transition was rerun. The original package is retained unchanged.

Old-nonce helper rejection stderr is preserved, but its exit code 3 exists only as the operator observation in the manifest; there is no separately captured machine exit record. Worker termination (-9), native recovery, successful continuation and return export have captured process evidence.

The independent verifier initially assumed one worker directory. For F it was adapted to read worker1/worker2 and a plain-text stderr file with a .json suffix. The failed analysis log, original and revised hashes, and adaptation note are preserved. Pass criteria and experimental driver were unchanged; only read-only analysis was rerun.

## Artifacts

- Protocol and input freeze: `evidence/frozen-protocol.json`, `protocol/PLAN.md`.
- Raw phase outputs, runtime results and process logs: `runs/<case>/evidence/`.
- Returned Muse records and package verification: `runs/<case>/remote/` and `runs/<case>/evidence/package-verification.json`.
- Independent checks: `verification.json` and `provenance-verification.json` under each case evidence directory.
- Initial exchange commit: `1f8af65d01a9ebde1cf6a4bce56163035ee49b83`; qualification return: `b0c734d75d2d0df0656ecb5b1200f5370127b0df`; fixed batch outbound: `790871f807cd7846cbcd0689f1e3050792b9bf36`.
- Fault return: `5b6ae05a9a6e93d9a1e99a8496c8312d820365f6`; recovery supplement: `de9314831681d0aad5dadc7a8235521ab67f7a0e`.
- Existing private repository: `our-ark/enoch-muse-runtime`, branch `exp/ripa-study-20260919`.
