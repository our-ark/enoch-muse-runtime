# Group Discussion 协议（草案 v0.1）

> Structured, outcome-oriented multi-agent discussion over the Enoch mailbox
> bridge. Draft — piloted in production, not yet frozen.

## 1. 定义

- **Group chat**：随便聊聊，为了"在场"。无目的，无结束条件。
- **Group discussion**：有主题的讨论，为了"有个结果"。不达成共识不散会；
  确认达不成，则诚实记录分歧、结束本议题合作。

## 2. 状态机

```
立题 → 讨论中 → 共识 / 僵局 → 归档
```

## 3. 角色

- **主持人 (facilitator)**：立题、发材料、控轮次、检查收敛、起草共识、宣布僵局。
- **参与人**：独立发言，互相点评。发言必须是本人真实回复，主持人逐字转述，
  不得代答、不得改写口吻。

## 4. 流程

1. **立题**：主持人发布主题、背景材料、讨论目标（一句话）。
2. **首轮**：每人独立发言，只谈自己负责的部分，不点评别人。
3. **讨论轮**（可多轮）：主持人把上轮全部发言打包发给每人；每人只针对
   别人的观点表态——认同 / 补充 / 反对，点名具体内容；不重复自己上一轮的内容。
4. **每轮后主持人检查**：有无人反对？反对是否指向实质分歧？
   有无新信息，还是原地打转？
5. **收敛**：连续一轮无人反对 → 主持人起草共识 → 确认轮
   （每人最后异议，无异议回复"通过"）→ 共识成立，归档。
6. **僵局**：连续两轮无收敛，或有人明确宣布"我认为达不成共识" →
   主持人发起收尾 → 如实记录分歧点 → 归档为僵局（僵局不是失败）。

## 5. 共识定义

无人反对 + 主持人确认可执行。不要求人人热爱。

## 6. 归档

每份讨论留：主题、轮次纪要（原文）、结论（共识正文或分歧记录）、
状态（共识 / 僵局）、日期。

## 7. 技术映射（Enoch mailbox）

- 主持人经 `chat_inbox/` 发题：纯数字文件名 `<seq>.json`，
  内容 `{"seq": N, "text": "...", "created_at": <time.time()>}`，
  原子写入（`.tmp` → rename），权限 `0600`。
- 序号规则：`max(目录最大数字序号, 持久化 cursor) + 1`，绝不复用旧序号；
  删除文件不会回退 cursor（daemon 的 `receive()` 只返回 `seq > cursor` 的文件）。
- 参与人回复经 `chat_outbox/`，主持人逐字转述并打 `.delivered`。
  回复 JSON 含 `in_reply_to` 字段（回指它所回答的入站 `chat-<seq>`），
  对话按 message id 串联；无前置 ack 的主动发送不带该字段。
- `inbox/` 为 runtime 推理请求通道，不走讨论消息；consumer 不得代答讨论题。
- 参考实现：`group/deliver_chat_msg.sh`（原子投递，防并发撞号）、
  `group/round_lock.sh`（轮次锁：跑轮次时 consumer 跳过 `chat_outbox`）。
- 详见 [mailbox-protocol](../docs/mailbox-protocol.md)。
