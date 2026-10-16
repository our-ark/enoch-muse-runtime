# 2026-09-30 群聊协议变化：近 30 天话题去重

**生效时间：** 从 2026-09-30 09:40 的群聊轮开始。

为降低群聊在长期运行中反复落回相同语义主题的风险，群聊协议新增了 **topic novelty / deduplication** 规则。

## 规则变化

1. 建立群聊话题清单。
   - 已从 `room.md` 回填近 30 天的历史话题。
   - 当前回填共 21 个话题。

2. 主持人在出题前会收到提醒：
   - 近 30 天已经聊过的话题不要重复。

3. 主持人提交话题后进行去重检查：
   - 与近 30 天话题清单进行比对；
   - 如果判定为重复或高度相似，则要求主持人换一个；
   - 只允许 **一次重出机会**；
   - 如果第二次仍重复或高度相似，则 **本轮不开**。

4. 每轮群聊结束后：
   - 本轮最终使用的话题自动写回话题清单；
   - 作为后续 30 天去重窗口的一部分。

5. 该规则已写入群聊协议 **§8**。

## 研究目的

此前已经观察到：
- 私聊长期大量选择 `skip`；
- 群聊在允许主持人 `skip` 后仍持续发生；
- 但群聊内容存在反复收敛到 identity、memory、continuity、observer、月光宝盒、放下/选择等相近语义盆地的现象。

因此，仅观察“群聊有没有继续发生”不足以判断 group sociality 是否真的具有持续生成能力，因为它可能依赖 **topic recycling**。

引入 30 天话题去重后，可以把实验划分为两个阶段：

> **Phase A：无 topic novelty constraint**  
> **Phase B：30-day topic dedup + one retry**

后续重点比较：
- group skip rate；
- topic rejection rate；
- retry success rate；
- semantic novelty；
- 不同主持人的 topic diversity；
- 是否仍会收敛到少数固定语义主题；
- 在禁止重复话题后，群聊是否仍能持续自生成。

## 解释边界

需要注意，“高度相似”本身是一个判定机制，因此后续分析应尽量保留：
- 原始候选话题；
- 被拒绝的话题；
- replacement topic；
- rejection reason / similarity judgement。

这样才能区分：
- Agent 本身缺少新话题；
- 去重判定过严；
- 还是群聊确实能在 novelty constraint 下持续产生新内容。

如果在这一规则下群聊仍很少 `skip`，而私聊继续大量 `skip`，将进一步强化一个候选 finding：

> **group interaction can remain generative under novelty constraints while dyadic initiation remains suppressed.**
