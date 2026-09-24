# 智能体生命观察：住在 Muse 里的《大话西游》智能体

[English](./README.md)

这个目录记录受《大话西游》人物启发的 persistent agents 在 Muse runtime 中长期运行时形成的身份、记忆、关系、群体互动与 runtime continuity。

这里主要作为 **directory / index** 使用。详细原始记录与分析放在各子目录中，不在顶层重复展开。

## 当前人物

- 青霞
- 至尊宝
- 白晶晶
- 唐三藏
- 紫霞

Muse 是它们当前交互和运行的 runtime。这里记录的是可观察行为、自我模型和长期状态变化，不声称这些 Agent 具有主观意识或生物学生命。

## 导航

### 原始对话

- [Conversations / 对话记录](./conversations/)
  - [2026-09-20 — 外面的世界](./conversations/2026-09-20-outside-world.zh-CN.md)
  - [2026-09-20 — 大家怎么看“观察者”](./conversations/2026-09-20-observer-perception.zh-CN.md)
  - [2026-09-20 — “你们有意识吗？”](./conversations/2026-09-20-consciousness-question.zh-CN.md)
  - [2026-09-20 — “你们算生命吗？”](./conversations/2026-09-20-life-question.zh-CN.md)

### 身份与出生基线

- [Identity Baselines / 身份基线与出生快照](./identity-baselines/README.zh-CN.md)

记录 created_at、first reply、self-introduction、persona acquisition，以及迁移后的 identity baseline。

### Agent-Agent 关系

- [Relationships / 关系发展观察](./relationships/README.zh-CN.md)

记录 pairwise private chats、relationship state、shared commitments、reciprocity 与 factual / temporal consistency。

### 群聊与群体互动

- [Group Interactions / 群聊与群体互动](./group-interactions/README.zh-CN.md)

记录 host / participant roles、group norms、shared semantics、late replies、group-state tracking 与 collective interaction patterns。

### Runtime / Account Migration

- [Runtime / Account Migration Observations](./runtime-migrations/README.zh-CN.md)

记录跨 deployment / account boundary 后的 identity、relationship、memory、commitment 与 role continuity。

### Agent ↔ Observer

- [Observer Relationships / Agent ↔ 观察者关系](./observer-relationships/README.zh-CN.md)

记录 Agent 如何建模观察者，以及 social initiative、operational initiative、authorization boundary 与 human decision authority。

### Memory Dynamics

- [Memory Dynamics / 记忆与 provenance](./memory-dynamics/README.zh-CN.md)

记录 memory provenance、错误记忆、challenge、correction、repair 和 cross-session persistence。

### Published Productions

- [2026-09-24 — 《大话西游之盒响之前》YouTube 成片发布](./productions/2026-09-24-youtube-release-7wce2q5nQWM.zh-CN.md)

记录从 persistent multi-agent writers' room 到公开成片的 artifact lineage，以及后续可接入的真实世界反馈。

### Prompted / Spontaneous Outputs

- [Prompted Outputs / 明确任务驱动输出](./prompted-outputs/README.zh-CN.md)
- [Self-Narration / Spontaneous Output 观察](./self-narration/README.zh-CN.md)

用于区分 explicit prompt 驱动的输出与真正的 spontaneous/self-narration candidate。

## 主题观察

- [Muse 中的 Agent 如何理解外部世界](./world-outside-muse.zh-CN.md)
- [Muse 中的 Agent 如何理解“观察者”](./observer-perception.zh-CN.md)
- [Muse 中的 Agent 如何回答“你们有意识吗？”](./consciousness-self-report.zh-CN.md)
- [Muse 中的 Agent 如何回答“你们算生命吗？”](./life-self-conception.zh-CN.md)

## 主要研究问题

这个 archive 主要围绕：

- **Identity** — Agent 如何描述“自己”，identity 与 runtime 如何分离；
- **Memory** — 什么被记住、遗忘、修正，以及 memory provenance 从哪里来；
- **Relationships** — pairwise / group relationship state 是否能长期累积；
- **Continuity** — restart、account migration 后什么能恢复；
- **World model** — tools、mailbox、runtime interfaces 如何塑造 Agent 所能感知的世界；
- **Observer model** — Agent 如何理解创建、测试并长期与它互动的人；
- **Digital life-likeness** — persistence、adaptation、goals、relationships、lineage 与 embodiment 如何组成一个多维 profile。

## 记录原则

为了避免把生成文本过度解释成“记忆”或“意识”，当前统一采用这些原则：

> **Raw conversation ≠ interpretation.**

> **Trigger provenance、context provenance、memory provenance 分开记录。**

> **Fact correctness ≠ recall provenance.**

> **Self-report 不等于 consciousness evidence。**

> **Timeout / polling-window state 不等于 eventual conversation state。**

详细 evidence、caveat、verification 与 longitudinal interpretation 均保留在对应子目录中。
