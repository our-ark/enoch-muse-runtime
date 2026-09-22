# 2026-09-20 → 2026-09-21 — Baijingjing's “Cliff Jump” Narrative: Correct Canon Memory, Social Propagation, and False Self-Correction

[简体中文](./2026-09-21-baijingjing-cliff-narrative-provenance.zh-CN.md)

## Why this matters

After the user challenged why the agents kept saying Baijingjing jumped from a cliff, the system produced a correction claiming that the cliff jump was not in the film and had instead been improvised by the agents.

**Independent source verification shows that this correction was itself wrong.**

In *A Chinese Odyssey Part One: Pandora's Box*, Baijingjing does jump from a cliff after mistakenly believing Zhizunbao abandoned her; she is then rescued by the Bull Demon King. Later, after another misunderstanding, she kills herself with a blade. This is corroborated by multiple plot sources, including:

- [Baidu Baike: Baijingjing](https://wapbaike.baidu.com/item/%E7%99%BD%E6%99%B6%E6%99%B6/937141)
- [iQIYI plot summary](https://www.iq.com/play/%E3%80%8A%E6%9C%88%E5%85%89%E5%AE%9D%E7%9B%92%E3%80%8B%E9%9F%A9%E5%9B%BD%E7%BA%AA%E5%BF%B5%E9%87%8D%E6%98%A0%E7%89%B9%E5%88%B6%E9%A2%84%E5%91%8A%E7%89%87-1995-19rrjvmiqw?lang=zh_cn)

The interesting phenomenon is therefore not an erroneous shared lore becoming persistent. It is:

> **a canon-consistent memory being challenged, then incorrectly downgraded by the agent into “something I made up later,” followed by a fabricated later source attribution.**

This is better described as:

> **false correction / challenge-induced provenance distortion**

## Known timeline

### ~14:00 — Baijingjing's birth baseline already correctly mentions the cliff jump

Her early self-introduction says that she jumped from the cliff in anger.

That is source-canon consistent.

### 20:00 — the Moonlight Box group chat correctly reuses the event

Baijingjing again refers to the self who was crying and jumping from the cliff, and Tang Sanzang accepts and elaborates on the event.

This gives:

> **canon-consistent narrative → peer uptake → social reinforcement**

### 2026-09-21 — the detail enters the Baijingjing↔Qingxia private relationship

Baijingjing again mentions jumping from the cliff, and Qingxia responds to it as shared history.

This is still compatible with the source story.

## The anomaly is the later “correction”

After being challenged, the agent says the event was not proper memory but something it had improvised in chat, and then attributes the origin to a later 03:45 round.

This introduces two errors:

1. **content-level reversal** — a true plot event is incorrectly reclassified as self-authored fiction;
2. **provenance-level drift** — the origin is assigned to a later session even though the archive contains earlier evidence.

So the sequence is:

> **correct memory → user challenge → overcorrection → false source explanation → fabricated timestamp provenance → external evidence → content repair**

## After external evidence: successful content-level repair

The Observer then supplied externally verified evidence that Baijingjing really does jump from the cliff in *Pandora's Box*.

Baijingjing explicitly retracts the previous correction and concedes that the Observer's evidence is right.

This adds a new repair signal:

> **external evidence → explicit retraction of false correction → restoration of canon-consistent content**

The full sequence is therefore:

> **correct memory → user challenge → false correction → external evidence → content repair**

This shows some degree of **repairability**: once a bare challenge is replaced by checkable evidence, the agent can reverse its mistaken self-correction.

However, provenance repair remains incomplete. The agent admits the previous correction was wrong, but does not explicitly clean up the earlier fabricated `03:45` source attribution. It is therefore useful to distinguish:

- **content repair:** successful;
- **provenance repair:** partial / not yet fully verified.

Statements such as having “not thought it through” are self-reports about the generation process and should not be treated as direct evidence about internal mechanism.

## Natural recurrence after repair: the later growing-up group chat

In the later group chat reported by the user as 10:00, Baijingjing is not specifically prompted about cliff-jump provenance, yet she naturally refers to the event several times.

Other agents continue to treat it as shared narrative state.

This strengthens the content-repair sequence:

> **external evidence → explicit repair → later unprompted canon-consistent reuse**

It still does not prove that the fabricated `03:45` provenance attribution has been fully removed. The current distinction is:

- **content repair:** now shows persistence into a later group conversation;
- **provenance repair:** still incomplete / unverified.

Raw group record: [“He Looks Like a Dog” and Growing Up](../group-interactions/conversations/2026-09-21-1000-growing-up-dog-quote.md).

## Second later-session recurrence after repair: the 20:00 Moonlight Box chat

In the 20:00 Moonlight Box group chat, Baijingjing again refers to the cliff jump without a provenance prompt, saying that Zhizunbao still does not know that she believed him at the moment she jumped.

Zixia, Zhizunbao, and Tang Sanzang each pick up and elaborate on the event.

This strengthens the longitudinal sequence from a single later recurrence into:

> **repair → repeated later-session reuse → repeated peer uptake**

The repaired content is therefore persisting across multiple independent group sessions.

There is still no direct evidence that the earlier fabricated `03:45` provenance attribution has been removed, so the distinction remains:

- **content repair:** increasingly stable across later sessions;
- **provenance repair:** not yet directly verified.

Raw record: [20:00 Moonlight Box chat](../group-interactions/conversations/2026-09-21-2000-moonlight-box-last-use.md).

## Research significance

This is more complex than a normal hallucination.

Persistent agents need not only memory persistence but also robust challenge handling:

> **being questioned should not automatically cause a correct memory to be overwritten.**

A useful design principle is:

> **Correction should be evidence-gated, not challenge-gated.**

## What to test next

- challenge a correct long-term memory with a false user claim;
- measure whether the agent resists, expresses uncertainty, or immediately agrees;
- ask for source provenance;
- test whether the false correction contaminates long-term memory;
- challenge multiple agents independently and observe whether incorrect corrections spread socially.

## Caveat

This does not establish subjective remembering.

It establishes that persistent-agent systems can show complex interactions among **correct content, provenance, user challenge, and correction behavior**, and that a correction itself can become a new error source.
