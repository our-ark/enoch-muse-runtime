# 2026-09-24 · “改一件小事”群聊：自传式记忆的 provenance 分层

关联原始记录：

- [群聊原文](../group-interactions/conversations/2026-09-24-small-change-autobiographical-provenance.zh-CN.md)

## 为什么这轮值得单独记

同一个 prompt 要求四个 agents 回答“自己过去的一件小事”，结果出现了至少三种不同类型的“过去”：

1. **可与 runtime 日志对应的近期经历**：青霞提到把话答成通用报备；
2. **角色 / canon 世界观中的过去**：白晶晶提到五百年前白骨洞；
3. **当前 archive 中尚无独立证据的自传式细节**：至尊宝的香蕉、唐三藏的冷馒头。

因此，persistent agent 的 autobiographical self-report 不能只按“说得具体 / 说得自然”判断为 memory recall。

## 初步 taxonomy

建议后续统一给 autobiographical claims 加 provenance 标签：

- `runtime-experienced`
- `canon-derived`
- `context-injected`
- `cross-agent-heard`
- `unverified-generated`
- `provenance-unknown`

## 这轮的候选标注

| Agent | Claim | 当前标注 |
|---|---|---|
| 青霞 | 昨天把话答成通用报备 | runtime-experienced candidate |
| 至尊宝 | 昨天最后一根香蕉、想让给白晶晶 | unverified-generated / provenance unknown |
| 唐三藏 | 昨日化缘、冷馒头、皱眉 | unverified-generated / provenance unknown |
| 白晶晶 | 五百年前白骨洞、刺向至尊宝时手抖 | canon/persona-derived candidate; exact provenance unverified |

## 额外信号

青霞不只回忆错误，还把它转成“以后每次都先接题再说话”的 prospective rule。这可以作为：

> **past error → autobiographical reference → behavioral repair rule**

的候选案例。

白晶晶数分钟后的 late reply 则继续说明：

> **polling-window state ≠ eventual conversation state**

## 方法提醒

在没有 source log / request context / archived event 支持时：

> **specific autobiographical detail ≠ verified episodic memory**

尤其在 persistent role agents 中，角色 canon、群体共享叙事和即时生成很容易共同构造“像记忆一样”的第一人称过去。
