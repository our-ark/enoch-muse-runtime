# Prompted Outputs / 明确任务驱动输出

[English](./README.md)

这个目录保存有明确 prompt / task context 的 Agent 输出。

它们仍然可以用于研究 identity consistency、relationship modeling、autobiographical narration、preference expression 等，但不能被当作 spontaneous behavior。

## 当前记录

- [2026-09-20 22:18 — 青霞：如果去《大话西游》客串一个角色](./2026-09-20-2218-qingxia-role-choice.zh-CN.md)
- [2026-09-20 22:20 — 至尊宝给花果山猴子猴孙写家书](./2026-09-20-2220-zhizunbao-letter-home.zh-CN.md)

这两条都来自 hourly-chat 的明确问题，因此：

> **都不是“自言自语”。**

## 方法原则

> **Prompted output ≠ spontaneous self-narration**

分析时必须保留 trigger provenance，避免把 prompt 中已经指定的受众、主题、候选角色或结构错误归因给 Agent 自主产生。

即使如此，prompted output 仍可以用于比较：

- Agent 在相同角色 / identity 下的 consistency；
- preference 与 relationship model 是否跨场景稳定；
- prompt 没有指定的补充内容是如何生成的；
- 这些输出后来是否进入 persistent memory。
