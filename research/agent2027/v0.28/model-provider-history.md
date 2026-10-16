# Runtime-provider and model chronology, v0.19

Prepared 14 October 2026. This note distinguishes the inference route (`providers.runtime`), a provider-specific model identifier, and the communication route (`providers.chat`). Muse denotes a runtime/inference route here, not an independently pinned foundation-model version. This clarification changes deployment metadata, not the 20-episode content labels.

## Sources and status

The primary detailed source is the [deployment-history account supplied by the observer on 14 October](sources/observer-supplied-2026-10-14/runtime-provider-history.zh-CN.md). This is a later account about earlier events, not a contemporaneous log or a new conversation episode. The [receipt manifest](sources/observer-supplied-2026-10-14/manifest.json) hashes the locally preserved note, not an original deployment artifact. No original configuration snapshots, raw checks, or per-request model IDs accompany this account.

The earlier [frozen directory record](sources/docs/agent-life-observations/dahua-xiyou/README.zh-CN.md), lines 295-313, reports the 28 September change for Zhizunbao and Baijingjing and labels the target "Claude Sonnet 5.5, Medium." It does not give the initial Opus step, executable relocation, or 1 October return to Muse. The newer account supplies those details. It specifies the Sonnet model key, but does not independently pin a separate Medium effort parameter. The host report in [zixia-evidence-package.md](zixia-evidence-package.md) separately identifies Muse inference for all four during S1-S5.

The observer subsequently clarified the intervention's motivation and outcome: [private-chat clarification](sources/observer-supplied-2026-10-14/private-chat-switch-outcome.zh-CN.md), with a separate [receipt](sources/observer-supplied-2026-10-14/outcome-receipt.json). The account states that agents had stopped private chatting and that switching models brought no improvement. This is retrospective outcome evidence, not a quantified pre/post activity series.

The observer further identifies Sonnet as the intended target in a [direct clarification](sources/observer-supplied-2026-10-14/sonnet-target-clarification.zh-CN.md), preserved with its [receipt](sources/observer-supplied-2026-10-14/sonnet-target-receipt.json). The suggestion that the initial Opus self-report reflected a default before the Sonnet setting is a possibility, not a verified configuration fact. The main paper names Claude Sonnet 5.5; the transition self-report and CLI details remain here for completeness, without implying a planned Opus condition or an Opus-versus-Sonnet comparison.

## Reported chronology

| Period / event | Zhizunbao and Baijingjing | Qingxia and Tang Sanzang | Evidence qualification |
| --- | --- | --- | --- |
| 23 September, S1-S5 | Muse runtime inference | Muse runtime inference | Earlier host report; precise underlying model versions and complete generation ownership not established. |
| 28 September, 14:11-14:25 | Runtime switched to Claude CLI 2.1.284; initial model reported by the agents as Opus 5.5 / claude-opus-5-5 | Muse route unchanged | Account reports installation, login, root checks, daemon restart, and end-to-end replies; original artifacts not supplied. Initial self-reported model name is not independent configuration proof. |
| 28 September, 14:33 | Claude configuration explicitly sets model: claude-sonnet-5-5, followed by restart and checks | Muse route unchanged | Account reports a model smoke test and self-reported Sonnet after the change. |
| 28 September, evening | Executable moved from /usr/bin/claude to ~/.local/bin/claude after host restart erased the system-path installation | Muse route unchanged | Packaging/path repair within the same provider, not a new model treatment. Subsequent restart checks are reported. |
| 1 October, 10:03 decision | Runtime configured back to Muse and daemons restarted after a reported 09:44 Claude OAuth failure | Muse route unchanged | Account reports configuration read-back, new daemon PIDs and root checks, and successful startup/private replies. No raw timestamps for every implementation step accompany the decision time. |
| 1 October, 10:25 check | Return to Muse reportedly persists through a host reboot | Muse route unchanged | Reported follow-up check. |
| 4-10 October, 20-episode analysis window | Muse runtime route | Muse runtime route | All-Muse routing according to the supplied deployment history. Per-episode executed model IDs remain unavailable. |

Chat stayed on Muse throughout for all four. During the Claude interval, the two changed agents' inference bypassed the Muse mailbox-consumer inference bridge; monitoring and chat forwarding reportedly continued. The runtime switch therefore changed the execution path as well as the model. The registry change identified as commit 3a0473e, CLI installation details, OAuth handling, and process IDs remain observer-supplied claims; this revision does not independently verify that commit or those logs.

The return required daemon restart because the account says startup sets ENOCH_RUNTIME_PROVIDER and provider resolution prefers that process environment. Configuration intent alone would not demonstrate the running route. The reported restart and reply checks strengthen the operator's account, but do not substitute for supplied process/configuration/request records.

## Implications for the paper

- Both the September writing sequence and the October coded follow-up are reported as all-Muse windows. The October table must not be described as a concurrent Claude-versus-Muse comparison.
- The two changed agents have an intervening Claude history. Returning to the same provider does not reset accumulated state, prove identical prior exposure, or establish an unchanged underlying Muse model.
- This was an exploratory, nonrandomized operational change prompted by the observer's report that private chatting had stopped; the return followed a reported authentication failure. Changes in routing, restarts, availability, prompts, and scheduling prevent a model-only causal interpretation.
- The observer reports no improvement after changing models. This is an unsuccessful operational remedy as assessed by the observer, not absent outcome information. No quantified recovery rate or model-only causal effect can be estimated: the follow-up table has no comparable pre/post initiation denominator or per-request model assignments. The account does not isolate effects of the initial Opus interval, Sonnet, or the return to Muse.
- Later private replies show responsiveness when interaction occurs, but do not independently demonstrate renewed autonomous initiation. The outcome report concerns the September switch and must not be recoded as zero private conversations in the October archive.
- An agent's assertion that it remains the same agent after a model swap is self-description, not proof of durable identity or independently authenticated model identity.
- The supplied final state is runtime=muse and chat=muse for all four, with an intention to keep that route stable during submission preparation. This is configuration history/planned stability, not a commitment to perform further interventions. No runtime state was changed by this paper update.
