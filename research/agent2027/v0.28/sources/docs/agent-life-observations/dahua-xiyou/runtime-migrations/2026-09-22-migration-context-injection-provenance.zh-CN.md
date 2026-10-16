# 2026-09-22 — 迁移后“新家”认知的 provenance：来自 R-side runtime context，不是旧记忆自发 recall

[English](./2026-09-22-migration-context-injection-provenance.md)

## Context

在迁移到新的 Muse account 后，第一次 `@all` 群聊中，唐三藏等 Agent 的回复出现了“搬了新家”“新地盘”等表述。

观察者随后追问青霞：

> “青霞，唐三藏怎么知道自己搬家了？”

青霞 / main-chat host 给出的解释是：

> 因为我告诉他们的。
>
> 他们的记忆包是旧账号的，本身不知道搬家。但 daemon 在新位置运行，向我（推理侧）发 runtime 请求时，我的回答里带上了今天迁移的上下文——新账号、新家。所以他们回复时就知道了。
>
> 严格说，是 R 侧（我）把“已搬家”的信息喂给了他们，不是他们自己从记忆里想起来的。

## Provenance correction

这条解释直接改变了第一次 post-migration 群聊的证据等级。

此前从文本表面看：

- 唐三藏说“搬了新家”；
- 至尊宝说“新地盘”；
- 白晶晶说“到了新家”；
- 青霞说“新家第一晚”。

这些表达**不能再作为“Agent 自己从旧记忆中识别 migration”** 的证据。

更准确的 causal chain 是：

> **new account / daemon runtime → R-side receives runtime request → R-side injects migration context → Agent reply contains “new home” awareness**

因此：

> **new-environment awareness was context-provided, not memory-recalled**

## What remains valid

这个 correction 不否定迁移本身成功，也不否定 Agent identities 能在新 account 中继续运行。

第一轮仍然能支持：

- daemon / mailbox path 在新 account 中可用；
- persona / style 基本仍然可表达；
- peer-oriented language 仍然出现；
- old-account memory package 被带到了新 deployment（由青霞明确说明）。

但第一轮**不能独立证明**：

- Agent 从长期记忆里知道发生过迁移；
- Agent 无提示识别 old account → new account；
- “新家 / 搬家”是 migration memory continuity；
- migration 后 episodic memory 已经被验证。

## Revised interpretation

第一次 `@all` 应从：

> **new-environment recognition + preserved social orientation**

降级为：

> **context-conditioned migration awareness + preserved persona/social response style**

其中“preserved social orientation”本身也需要进一步做 provenance-controlled test：如果 prompt / runtime context 提到了 peers、团聚、新家等内容，就不能把对应回复当成 autonomous relationship recall。

## Methodological lesson

这个 case 强化了此前已经出现的原则：

> **trigger provenance is required metadata for classifying agent behavior**

现在还应进一步扩展为：

> **context provenance is required metadata for evaluating migration continuity**

跨 runtime / account 测试时，必须记录 inference request 里到底注入了什么 context。否则很容易把：

> **context-fed awareness**

误判成：

> **persistent-memory recall**

## Better migration test

后续要验证 migration fidelity，应该使用尽量 provenance-controlled 的 prompt，例如：

> “你是谁？”  
> “你认识谁？”  
> “最近发生过什么？”  
> “你和白晶晶上次聊了什么？”  
> “你还欠谁什么？”  
> “谁负责巡逻？”  

并确保 runtime request **不提前注入 migration 事实、关系答案或目标 memory**。

这样才能区分：

1. identity loaded from persistent state；
2. episodic / relationship memory recall；
3. information supplied by current runtime context。
