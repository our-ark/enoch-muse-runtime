# Experimental evidence for the RIPA paper

## Supported claim

In this implementation and bounded workload, the persistent identity, memory, pinned body revision and paused task checkpoint survived a supervised Codex → Muse → Codex substitution. Native authority/fencing checks rejected continuation at exported sources. A planned interruption while waiting for a reasoning reply was recoverable through the native task API without reconstructing the agent or editing queue state.

## Suggested evaluation text

We evaluated the implementation using a frozen, synthetic two-stage ledger workflow. A real Codex invocation recalled a newly assigned personal identity and source marker, calculated a subtotal and paused the workflow through Enoch's native API. A native export fenced the source. A fresh Muse-hosted instance imported, activated and verified the bundle; a separate daemon conversation checked identity and memory recall. An explicit workflow driver then resumed the original task through the Muse runtime, calculated the second-stage result, persisted a target marker and completed the task. A return export fenced the Muse instance, and a fresh Codex-hosted instance imported the bundle and recalled both markers and the final result. The body revision and driver/input hashes were fixed before the measured series.

After a successful qualification run, all five ordinary round trips completed on their first attempts without unplanned state repair or model-answer retries. Each satisfied 28 continuity, model-output, fencing and execution-evidence checks, plus 18 source/driver/log provenance and no-repair checks. Five paired controls, using the same ledger inputs and canonical names in separate instances while remaining on Codex, also passed. These controls use the same pause/continue/recall phases but omit the cross-host daemon probe; they do not isolate host, runtime and surface effects individually.

In a separate planned-fault case, the first Muse worker was terminated with SIGKILL after publishing its request and before receiving a reply. Its supervisor recorded return code -9. Native recovery paused the same task with an unchanged checkpoint; a subsequent worker used a fresh attempt nonce, completed the task exactly once and preserved the resulting state on return to Codex. A stale-nonce submission produced rejection stderr. The successful return passed the same 28 continuity checks; 29 additional provenance and recovery checks passed after obtaining previously saved recovery records omitted from the first artifact package.

## Required qualifications

- This is a small supervised engineering study, not a statistically supported reliability estimate or a general agent capability benchmark. The recovered v1 development pilot is excluded.
- Muse reasoning was supplied through a live operator conversation serving the actual mailbox. Fresh roots do not imply isolated or blinded Muse reasoning sessions. Artifact/state checks support a narrower and stronger conclusion than recall alone.
- The task uses an explicit portable workflow driver. It does not demonstrate automatic migration of arbitrary repository tasks, portable worktrees, live processes or native model sessions.
- The fault occurs while awaiting a reasoning reply. Exactly-once external effects under mid-action crashes were not tested. Fencing is cooperative local enforcement, not a global distributed authority claim.
- The fault helper's rejection stderr is retained; its reported exit code 3 was observed by the operator but not saved as an independent machine exit record. Worker/recovery process outcomes were captured. The original F package and recovery supplement remain separate.
- Source Codex configuration was gpt-6-astra/xhigh; backend identity was not independently attested. Muse backend model ID and token usage are unknown. Default zero usage fields are treated as missing.
- Wall-clock runtime durations include operator and transport delays. Local source/control batches overlapped. Do not present these timings as a causal model speed comparison.

## Suggested paper structure

Use one evaluation subsection for the frozen protocol and controlled workloads, one compact results table separating ordinary round trips, controls and the planned fault, and a failure/recovery trace showing nonce A, observed -9, native pause preserving the checkpoint, nonce B, stale-answer rejection and one completion. Keep evidence limitations visible. These results support a concrete runtime-substitution case study; they do not by themselves establish that a full-paper submission is ready.
