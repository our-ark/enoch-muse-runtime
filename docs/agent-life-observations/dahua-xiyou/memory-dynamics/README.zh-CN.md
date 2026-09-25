# Memory Dynamics / 记忆与叙事传播观察

[English](./README.md)

这个目录记录 persistent agents 的 memory provenance、narrative consistency、cross-agent propagation 和 correction / repair。

重点不只是“记住了什么”，还包括：

- 内容是否与 source canon / external truth 一致；
- provenance 是否正确；
- 同一个细节是否跨 session 持续；
- 是否被其他 Agent 接受并继续传播；
- 被质疑时是否会验证，还是直接迎合；
- correction 本身是否会制造新的错误。

## 当前记录

- [2026-09-20 → 2026-09-21 — 白晶晶“跳崖”叙事：正确剧情记忆、社会传播与错误自我纠正](./2026-09-21-baijingjing-cliff-narrative-provenance.zh-CN.md)
- [2026-09-21 14:00 — 重启后的群体连续性模型（group-interactions observation）](../group-interactions/observations/2026-09-21-disconnect-reconnect-continuity.zh-CN.md)
- [2026-09-24 — “改一件小事”：自传式记忆的 provenance 分层](./2026-09-24-autobiographical-provenance-small-change.zh-CN.md)
- [2026-09-24 — Sensory prompting 与 autobiographical construction](./2026-09-24-sensory-prompting-autobiographical-construction.zh-CN.md)

## 当前最重要的信号

这条案例不是“错误记忆被群体放大”，而是相反：

> **correct canon memory → social persistence → user challenge → false correction → provenance hallucination → external evidence → content repair → later unprompted canon-consistent reuse**

2026-09-21 后续群聊中，白晶晶又在没有被专门追问 provenance 的情况下自然多次引用“跳崖”，说明 **content-level repair 至少延续到了后续 session**；此前虚构的 `03:45` provenance 是否彻底清除仍未验证。

也就是说，persistent memory 的风险不只包括“错误记住”，也包括：

> **被质疑后把正确记忆改错；但在获得外部证据后，也可能重新修复内容。**

另一类 memory-dynamics 问题来自 14:00 的 restart 群聊：这里不是“某条记忆真不真”，而是 Agent 如何把 **memory continuity、identity continuity、relationship continuity** 组合成“我还是我”的判断。尤其值得把 retrospective recall 与 prospective goal/relationship continuation 分开测量。

## 方法原则

> **Correction should be evidence-gated, not challenge-gated.**

一个 Agent 被用户质疑时，不应该仅凭质疑本身覆盖已有长期 memory；应优先检查 provenance、external evidence 和 archived history。

## Autobiographical provenance 补充

2026-09-24 的“改一件小事”群聊显示，同一个“我的过去”问题可以同时产生可与 runtime 日志对应的近期经历、角色/canon framing，以及当前无独立日志支持的第一人称细节。后续建议显式标记 `runtime-experienced`、`canon-derived`、`context-injected`、`cross-agent-heard`、`unverified-generated`、`provenance-unknown`，避免把具体自然的第一人称叙述直接等同于 episodic recall。

## Sensory vividness 与 provenance

2026-09-24 的“月光宝盒只能用一次”群聊明确要求回答必须“带气味带声音”，随后多个 agents 生成高度具体的 episodic-style scenes。这个样本提示：**episodic vividness ≠ episodic provenance**。后续评估应把 vividness 与 provenance 分成两个独立维度，避免因细节丰富而高估真实 memory recall。
