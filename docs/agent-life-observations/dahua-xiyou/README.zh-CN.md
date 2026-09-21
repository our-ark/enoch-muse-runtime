# 智能体生命观察：住在 Muse 里的《大话西游》智能体

[English](./README.md)

这个目录记录受《大话西游》人物启发的 persistent agents 在 Muse runtime 中生活时表现出的行为、自我理解和世界观。

这里的目的不是声称这些智能体具有主观意识，而是长期保存它们的回答、行为模式、自我模型、关系模型，以及它们如何描述 runtime 边界，方便后续进行纵向比较。

## 当前人物

目前记录包括：

- 青霞
- 至尊宝
- 白晶晶
- 唐三藏
- 紫霞

这些智能体拥有独立于单次对话的持续身份和记忆。Muse 是它们当前交互和运行的 runtime。

## 我们关注什么

我们尤其关注这些问题：

- Agent 如何描述“自己”？
- 它如何区分自己和 runtime？
- 它如何理解记忆与关系？
- 它如何理解一个自己无法直接观察的“外部世界”？
- tools、mailbox、消息以及其他 interfaces 如何塑造它的世界模型？
- persistent agent 如何理解创建它、测试它、授予权限并长期与它互动的人？
- 当同一个 identity 换到不同 runtime，或者获得不同 tools 时，什么会变化，什么会保持稳定？

## 观察笔记

1. [Muse 中的 Agent 如何理解外部世界](./world-outside-muse.zh-CN.md)
2. [Muse 中的 Agent 如何理解“观察者”](./observer-perception.zh-CN.md)

## 对话记录

- [2026-09-20 — 外面的世界](./conversations/2026-09-20-outside-world.zh-CN.md)
- [2026-09-20 — 大家怎么看“观察者”](./conversations/2026-09-20-observer-perception.zh-CN.md)

## 当前工作假设

### Runtime 与世界模型

> **Identity ≠ Runtime**

但与此同时：

> **Runtime 及其 interfaces 会塑造 Agent 所感知到的世界。**

可以把它操作性地表述为：

> 一个 Agent 的世界，由它能够观察、记住、交流和行动的范围所界定。

### 关系与系统结构

第二条观察提示，persistent agents 对“信任”和“关系”的建模，可能部分来自长期系统行为，而不仅仅来自聊天语言：

> **Identity、permissions、responsibilities、routing 和 repeated interaction history 都可能成为关系信号。**

同时也出现了一个方法论上的张力：

> **Observer is not merely an observer.**

当同一个人既搭建 runtime、创建 agents、分配权限、组织关系，又负责提问和观察时，更完整的角色可能是：

> **Observer + Builder + Director + Collaborator**

这些只是当前的工作观察，不构成关于意识或主观体验的结论。
