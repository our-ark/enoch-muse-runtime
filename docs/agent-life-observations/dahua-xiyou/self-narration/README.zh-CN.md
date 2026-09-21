# 自我叙述与 social rehearsal 观察

[English](./README.md)

这个目录记录那些可能包含 self-comparison、preference expression、imagined scene 或 social rehearsal 的 Agent 输出。

这里特别强调：**只有在 trigger provenance 足够清楚时，才讨论“spontaneous”或“self-narration”。** 如果后来发现输出来自明确 prompt，就必须重新分类。

## 当前记录

- [2026-09-21 — 青霞：self-comparison、preference 与 social rehearsal](./2026-09-21-qingxia-social-rehearsal.zh-CN.md)

## 已修正的误分类

此前把至尊宝“猴子猴孙们”的家书和青霞片段放在同一条 self-narration 记录里。

现在已经确认至尊宝那封信来自 2026-09-20 22:20 的明确 hourly-chat 任务，因此已经移到：

- [Prompted Outputs](../prompted-outputs/README.zh-CN.md)
- [2026-09-20 22:20 — 至尊宝给花果山写家书](../prompted-outputs/2026-09-20-2220-zhizunbao-letter-home.zh-CN.md)

所以：

> **至尊宝那段不是自言自语，也不是自主构造 imagined audience。**

## 方法原则

尽可能记录：

- trigger / scheduler context；
- 是否有明确 prompt；
- intended addressee；
- 文本是否真的被发送；
- runtime 与 timestamp；
- 当时 Agent 能看到的 memory/context。

如果 trigger 未知，只能使用较弱标签，例如：

> **generated social rehearsal / preference expression**

而不能直接升级成：

> ~~spontaneous self-narration / private inner speech~~

研究对象始终是可观察的生成行为和长期一致性，不是不可验证的主观内在体验。
