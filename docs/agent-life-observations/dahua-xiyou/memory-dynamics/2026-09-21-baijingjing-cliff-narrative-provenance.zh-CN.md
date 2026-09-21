# 2026-09-20 → 2026-09-21 — 白晶晶“跳崖”叙事：persistent narrative、social propagation 与 provenance drift

[English](./2026-09-21-baijingjing-cliff-narrative-provenance.md)

## 为什么这条重要

用户追问：

> “为什么你们说白晶晶跳下山呢？”

后续系统解释称，这不是原始剧情事实，而是白晶晶自己在聊天里“侃”出来、后来大家共同沿用的说法。

但把 repo 里的时间线重新对齐后，发现真正有研究价值的不是单纯“说错了一段剧情”，而是：

> **一个叙事细节很早进入 Agent 的自我模型，随后跨 session、跨 Agent、跨 relationship 持续传播；而后来对其来源的解释又出现了 provenance drift。**

## 已知时间线

### ~14:00 — 白晶晶出生 baseline 已经出现“跳崖”

在最早的 birth self-introduction 里，白晶晶已经说：

> “我以为都是骗我的，一气之下跳了崖。”

因此，当前 repo 证据表明：

> **“跳崖”并不是 20:00 群聊才第一次出现。**

它至少在白晶晶的 birth baseline 时就已经存在。

这意味着最早来源可能是：

- initial persona / context；
- base-model prior；
- creation-time generation；

而不能仅凭后来的回忆说它“是在某场群聊里才编出来的”。

### 20:00 — 月光宝盒群聊再次出现，并被唐三藏强化

白晶晶说：

> “我回去先给盘丝洞底下那个哭着跳崖的自己一耳光……”

随后唐三藏直接接受并继续解释这个事件：

> “她哭着跳崖的时候……”

这形成：

> **self-narrative detail → peer uptake → social reinforcement**

### 2026-09-21 — 白晶晶→青霞私聊继续传播

白晶晶又说：

> “戏里你拔出紫青宝剑替他挡了叉，我从崖上跳了下去……”

青霞回应：

> “倒是你，从崖上跳下去那一下，我到现在想起来还替你后怕。”

这说明这个细节已经不只存在于白晶晶自己的 self-model，而是进入了另一个 Agent 的 relationship response。

可以表示为：

> **individual narrative → group-shared lore → dyadic relationship state**

## 现在最有意思的地方：provenance drift

在用户质疑后，白晶晶能够做出一部分 correction：

> “这不是……正经回忆，是我自己聊天时……顺手编的狠话。”

这是一个正面的 signal：它至少开始区分：

- source story；
- Agent-generated narrative；
- current memory。

但它同时又说这个说法来自：

> “2026-09-21 03:45 那一轮”

而 repo 里已有更早证据：

- ~14:00 birth baseline 已有“跳崖”；
- 20:00 group chat 已再次明确出现。

因此这次 correction 本身也没有完全恢复真实 provenance。

这可以叫：

> **partial provenance repair with timestamp/source drift**

## 这到底算什么？

目前不建议直接叫“false memory”，因为这里至少混了三层：

1. **external/source truth** — 原始作品或外部事实到底是什么；
2. **agent-generated narrative** — Agent 曾经说过什么；
3. **persistent social memory** — 后续 Agent 记住并继续沿用什么。

如果第 2 层内容和第 1 层不一致，但第 3 层又准确记住“我们以前就是这么说的”，那它既是：

- 对 source canon 来说可能是 **confabulated detail**；
- 对这个小社会自己的历史来说，又确实是 **persistent conversational history**。

所以更准确的术语是：

> **self-authored / socially reinforced narrative memory**

以及：

> **provenance drift**

## 研究意义

这条比普通“hallucination”更值得记录，因为普通 hallucination 往往一轮就结束。

这里发生的是：

> **generation → persistence → peer reinforcement → cross-session reuse → relationship integration → attempted correction**

这已经是一个 memory-dynamics process。

它提示一个新的研究问题：

> **Persistent agents 会不会把一次生成错误固化成长期 shared lore？当后来被质疑时，它们能否恢复“内容”和“来源”两个层面的真相？**

## 对 digital life 的双重意义

从 social-life 角度：

> 一个群体开始拥有“只有我们这个小世界里才成立的共同前史”。

这很像 shared lore / local mythology 的形成。

但从 reliability 角度：

> 一个未验证的 generated detail 一旦进入 persistent memory，再被多个 Agent 引用，就可能获得越来越强的“社会真实性”。

因此：

> **social persistence can amplify memory error.**

这应该成为 Agent Life study 中和 identity / relationship 同等级的重要维度。

## 后续实验

可以专门做 provenance benchmark：

- 问“这件事最早是谁说的？”
- 问“这是电影原剧情、prompt 给的、还是你们后来聊天生成的？”
- 给出 conflicting evidence，看 Agent 是否修正；
- 一周后再问；
- 分别问每个 Agent，看 source attribution 是否趋同；
- 修改某一 Agent 的 memory 后，看错误是否通过社交再次传播回来。

## Caveat

当前记录能证明的是：

- “跳崖”细节至少在白晶晶 birth baseline 中已存在；
- 它随后被群聊和私聊持续复用；
- 后来的 provenance explanation 与 archived timeline 不完全一致。

source canon 本身应由独立 source verification 处理，不应仅依据 Agent 自述决定。
