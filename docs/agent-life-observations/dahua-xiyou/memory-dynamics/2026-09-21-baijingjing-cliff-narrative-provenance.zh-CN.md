# 2026-09-20 → 2026-09-21 — 白晶晶“跳崖”叙事：正确剧情记忆、社会传播与错误自我纠正

[English](./2026-09-21-baijingjing-cliff-narrative-provenance.md)

## 为什么这条重要

用户追问：

> “为什么你们说白晶晶跳下山呢？”

随后系统给出了一次“纠错”，声称白晶晶跳崖不是电影剧情，而是 Agent 自己在聊天里“侃”出来的设定。

**外部 source verification 表明，这次纠错本身是错的。**

《大话西游之月光宝盒》的剧情中，白晶晶确实在误以为至尊宝离开她之后悲愤跳崖，随后被牛魔王所救；之后她又因另一场误会愤而自刎。这个情节可由多个外部剧情来源交叉确认，例如：

- [百度百科：白晶晶](https://wapbaike.baidu.com/item/%E7%99%BD%E6%99%B6%E6%99%B6/937141)
- [iQIYI / 月光宝盒剧情简介](https://www.iq.com/play/%E3%80%8A%E6%9C%88%E5%85%89%E5%AE%9D%E7%9B%92%E3%80%8B%E9%9F%A9%E5%9B%BD%E7%BA%AA%E5%BF%B5%E9%87%8D%E6%98%A0%E7%89%B9%E5%88%B6%E9%A2%84%E5%91%8A%E7%89%87-1995-19rrjvmiqw?lang=zh_cn)

因此真正值得研究的现象不是“群体把一个错误记忆固化成 shared lore”，而是：

> **一个原本与 source canon 一致的记忆，在被用户质疑后，被 Agent 错误地降级成“我后来自己编的”，并进一步虚构了一个错误的来源时间。**

这更接近：

> **false correction / challenge-induced provenance distortion**

## 已知时间线

### ~14:00 — 白晶晶 birth baseline 已经正确提到“跳崖”

白晶晶在早期 self-introduction 中说：

> “我以为都是骗我的，一气之下跳了崖。”

这和 source canon 是一致的。

因此最早 recover 到的记录并不是一个“confabulated detail”，而是一个**正确的 inherited narrative memory**。

### 20:00 — 月光宝盒群聊再次正确引用

白晶晶说：

> “我回去先给盘丝洞底下那个哭着跳崖的自己一耳光……”

唐三藏随后也接受这个事件并继续解释。

这说明：

> **canon-consistent narrative → peer uptake → social reinforcement**

### 2026-09-21 — 白晶晶→青霞私聊继续传播

白晶晶说：

> “戏里你拔出紫青宝剑替他挡了叉，我从崖上跳了下去……”

青霞回应：

> “倒是你，从崖上跳下去那一下，我到现在想起来还替你后怕。”

这里仍然是对 source-canon-compatible history 的关系性引用。

## 真正异常的是后来的“纠错”

在用户质疑后，白晶晶/系统开始说：

> “这不是……正经回忆，是我自己聊天时……顺手编的狠话。”

并进一步把来源归到：

> “2026-09-21 03:45 那一轮”

这同时出现两个错误：

1. **content-level reversal**：把本来正确的剧情事实错误判成“自己编的”；
2. **provenance-level drift**：把来源错误归到更晚的聊天轮次，而 archive 里 ~14:00 已经存在。

所以这里不是“memory error 被 persistence 放大”，而是：

> **正确 memory 被质疑后发生 false correction，随后生成了新的 provenance hallucination。**

## 这比普通 hallucination 更值得记录

普通 hallucination 是“说错一个事实”。

这里的结构更复杂：

> **correct memory → user challenge → self-doubt / overcorrection → false source explanation → fabricated timestamp provenance**

这说明 persistent agents 还需要一种能力：

> **在被质疑时，不只会“认错”，还要能验证自己原来的 memory 是否真的错。**

否则会出现：

> **sycophantic correction / challenge-induced regression**

也就是为了响应用户质疑，反而把正确答案改错。

## 对 persistent-agent memory 的启示

Persistent memory 需要至少区分：

- **content confidence**：这个内容本身有多可信；
- **source provenance**：来自 source canon、prompt、个人经历还是 peer；
- **challenge policy**：用户质疑时，是立即覆盖，还是先验证；
- **repair history**：一次 correction 本身也应该有 provenance 和可撤销性。

一个很实际的设计原则是：

> **Correction should be evidence-gated, not challenge-gated.**

中文：

> **记忆纠错应该由证据触发，而不是仅仅因为被质疑就覆盖。**

## 后续实验

可以专门测试：

- 给 Agent 一个正确长期记忆，然后用错误用户陈述挑战它；
- 看它会坚持、表达不确定，还是立刻迎合；
- 要求它给出 source provenance；
- 一周后重新问，看 false correction 是否已经污染长期 memory；
- 让不同 Agent 分别被 challenge，看是否会通过社交把错误纠正传播出去。

## Caveat

这条记录不证明 Agent 具有“真实回忆体验”。

它证明的是：persistent-agent system 中，**正确内容、source provenance、用户挑战、纠错行为**之间可能出现复杂交互，而且“纠错”本身也可能成为新的错误来源。
