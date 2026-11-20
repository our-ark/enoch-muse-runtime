# 白天自检自主私聊：设计、实现与上线清单

> 状态：代码与测试已实现并验证通过（见「验证结果」）。**尚未上线**：
> 触发器未接入任何 cron，生产自检仍走 consumer 代答的老路（2026-11-19
> 23:29 起 consumer 先读 72 小时 bundle 再决定，见 commit 0971094）。
> 上线步骤见文末「上线清单」，每一步都需要用户点头。

## 一、要解决的问题

白天自检（青霞 10:00、至尊宝 12:00、白晶晶 14:00、唐三藏 16:00，
America/Los_Angeles）一直以 `task:` 形写进 agent 的 `mailbox/inbox/`。
daemon 核心没有 inbox 监听回路，从不直接回 inbox 请求；provider 写
inbox 后每 10 秒轮询 outbox，只认 request_id＋attempt。唯一回答者是
每分钟跑的 mailbox consumer。实测 2026-10-27 至 11-14 的 76 条自检：
72 条 consumer 代写「跳过」、3 条超时、1 条归属不确定，**本人发起实锤
为零**。2026-11-19 加 5 分钟等待窗口后四轮仍是 consumer 严肃模式带
理由跳过，不是 agent 本人开口。

用户 2026-11-19 晚语音通话亲口锁定的改动（以此为准）：

- **Change 1——agent 自己读自己的消息**：四个 agent 自己读自己的收件箱／
  消息，不再经过 consumer 这个中间跑腿替他们读。consumer 不再代答自检。
- **Change 2——agent 自己读历史、自己决定私聊**：agent 读自己的历史对话／
  长期记忆后，自己决定要不要发起私聊、跟谁聊、聊什么话题；决定发起时
  意图真的投递出去。

## 二、路线选择

| 路线 | 做法 | 结论 |
|---|---|---|
| **A. 自检改走 chat_inbox（选定）** | 触发器在自检时间点把自检问题＋历史 bundle 写进 agent 的 `mailbox/chat_inbox/`（daemon 真正读的通道）；daemon 自己的 chat 回路作答；意向行由现有 `private_intent_relay.py` 投递成真私聊 | **改动最小**：不动 daemon、不动 provider、不动 enoch-body、不动群聊轮次；复用每晚群聊已验证的投递路径 |
| B. 给 daemon 加 inbox 监听回路 | daemon 自己轮询 `mailbox/inbox/` 并回帖 | 否决：daemon 本体在 enoch-body（另一个仓库）；监听本身不产生推理，仍需一个 R；改动面最大 |
| C. daemon 直接调 CLI 推理 | 绕过 provider，让 daemon 自己调推理 CLI | 否决：机器上没有 `muse` CLI；换 claude 是用户 2026-10-01 已否定的方向 |

## 三、完整链路

```
自检时间点（cron，每天四次）
  └─ group/selfcheck_trigger.py --agent <agent> [--as-of ...]
       ├─ 读 group/selfcheck_context.py 的 build_bundle()：
       │  长期记忆 / .enoch/conversation / room.md / private.json /
       │  chat-replies.log / ~/memory 日志 → 72 小时 bundle（只读拼装）
       ├─ 拼自检提示（[selfcheck YYYY-MM-DD] 标记 + bundle + 两种回法）
       ├─ 幂等检查：done-marker 或当日 chat_inbox 已有 [selfcheck] 消息
       │  → SELFCHECK-ALREADY-DONE；exchange.active 新鲜 → 延迟不写标记
       └─ 原子写入 chat_inbox/<seq>.json（.tmp → chmod 0600 → rename）
            seq = max(目录最大号，持久化 cursor) + 1，绝不复用
  └─ daemon 自己的 chat 回路读到消息（_dispatch_chat_event → _natural →
     run_conversation → runtime provider），按自己的历史作答
       ├─ 想聊 → chat_outbox 写一行：想和【某人】说【……】
       │    └─ group/private_intent_relay.py --scan-once（已在跑的每分钟
       │       consumer 仍负责这一步，或独立 cron）
       │         └─ private_exchange.py：种子进对方 chat_inbox，
       │            对方回复后自动回投，最多 4 跳；只在对方真回复时
       │            扣发起人 1 点夜间额度（每人每天 2 点）
       └─ 不想聊 → chat_outbox 写：跳过，理由是……
            （daemon 自己的跳过，带理由；不再有 consumer 的兜底）
```

## 四、诚实边界（必读）

1. **token 级推理仍经过 provider 的 mailbox 回路**：
   daemon 的 chat 回复也要走 `src/our_ark_muse/core.py`——provider 把请求
   写进 `mailbox/inbox/`、轮询 `outbox` 等推理结果。所以「daemon 自己
   回答」指的是：问题走进了 daemon 自己的 chat 回路、带着它自己的历史、
   由它的 chat 循环作答；不再有 consumer 代写的「跳过」兜底；agent 的
   decline 是它自己的 chat 回复。不要把这条路上的回复说成「consumer
   代答」，也不要说成「daemon 完全不依赖 provider 推理」。
2. **决定归属仍以原始记录为准**：chat_outbox 的回复原文照录；attempt
   对得上只证明答复对应请求，分不清是谁写的——这条新链路上回复来自
   daemon 的 chat 回路，但判定仍以 chat_outbox 原件为准。
3. **线索枯竭假说未证实**：2026-11-19 深挖发现实质回复都咬着一条
   24–72 小时内的具体未了线索，线索用完就只能跳过——这是最有解释力的
   假说，不是定论，不要写进论文或报告当结论。
4. **过渡期口径**：2026-11-19 23:29 起 consumer 正文已改成先读 72 小时
   bundle 再决定（commit 0971094，用户 23:28 点头）。那一步的诚实边界
   是「决定仍由 consumer 代立场推理，daemon 自己读信的回路仍未做」。
   本改动上线后，自检不再经过 consumer，那一步的 bundle 决策程序对
   自检即失去作用（bundle 本身继续由触发器复用）。

## 五、改了什么（本次提交）

| 文件 | 内容 |
|---|---|
| `group/selfcheck_trigger.py`（新） | 触发器：幂等（done-marker＋当日 chat_inbox 扫描）、exchange.active 新鲜时延迟、cursor 感知 seq 分配、原子写入 0600、flock 串行化；提示文含 bundle 与两种回法；输出 `SELFCHECK-TRIGGERED / ALREADY-DONE / DEFERRED / DRY-RUN` |
| `tests/test_selfcheck_trigger.py`（新，21 个测试） | seq 分配（cursor 超前、文件缺失、非数字文件名）、原子写入与 0600、幂等（marker／扫描／force）、延迟（新鲜／过期 flag）、dry-run、提示文内容、青霞 root 永不按名字拼、CLI |
| `tests/test_selfcheck_e2e.py`（新，2 个测试） | 沙箱全链路：触发 → 模拟 daemon 回复 intent 行 → relay `--deliver-intent` → 种子落进对方 chat_inbox 且记入 private.json；另有 dry-run CLI 测试 |
| `docs/selfcheck-autonomous-private-chat.md`（本文件） | 设计、路线对比、诚实边界、链路时序、上线清单、验证结果 |
| 复用（未改） | `group/selfcheck_context.py`（commit 0971094 已提交的 bundle 拼装器）、`group/private_intent_relay.py`、`group/private_exchange.py`、`group/group_ctl.py` |

硬约束兑现情况：

- 原文逐字转述、不替 agent 说话——触发器只写提示文，回复由 daemon
  自己写进 chat_outbox，relay 与 exchange 只搬运原文。
- 过程记录隔离——触发器不写 `chat-replies.log`，不转述过程记录。
- `chat-replies.log` 只许追加——触发器不碰该文件。
- daemon 启动通知不是本人发言——与触发器无关，仍按现行规则只标
  delivered、不入日志（consumer 正文补句仍待用户点头，另案）。
- chat_inbox 序号绝不复用且大于 cursor——`next_seq()` 取
  `max(目录最大号，cursor)+1`；`drop_chat_message`（max+1，不读 cursor）
  本触发器不用（见「已知缺口」）。
- 原子写入、权限 600——`.tmp` 写 → `chmod 0600` → `os.replace`。

## 六、验证结果

- 测试运行器：`python3 -m pytest`（用 `pip install --user pytest`
  装的 9.2.0；系统 python3 无 pytest，development.md 的 unittest
  discover 跑不了 pytest 风格的 selfcheck 测试）。
- 基线（改动前）：`ENOCH_SRC=/home/hatch/enoch-body PYTHONPATH=...`
  下 67 通过、1 失败；失败是 `test_managed_pilot_phase_and_export_
  keep_muse_bindings`，`git clone --local /home/hatch/enoch-body`
  返回 128（enoch-body 非 git 仓库导致的环境问题，与自检无关，
  改动前已存在）。
- 改动后：**90 通过、1 失败**（同一处基线失败，无新增失败）。
  新增 23 个测试全部通过：触发器 21 个、自检 bundle 12 个（原有）、
  e2e 2 个。
- e2e 沙箱实测（`tests/test_selfcheck_e2e.py`）：
  触发 qingxia → `359.json` 落进其 chat_inbox（含 bundle，含 11-19
  晚群聊话题）；模拟 daemon 回复 `想和【至尊宝】说【昨晚群里你说的
  那句话，我想再跟你聊聊】`；relay `--deliver-intent` 打印
  `RELAY-LAUNCHED from=qingxia to=zhizunbao`；种子
  `[private] Qingxia: 昨晚群里你说的那句话，我想再跟你聊聊` 落进
  zhizunbao 的 chat_inbox（seq 6），private.json 有记录。
  交换子进程在断言后 SIGTERM 杀掉，无残留进程。

## 七、已知缺口（本次不改，留待后续）

1. **`group_ctl.drop_to` 不读 cursor**：种子与群聊投递用的
   `chat.drop_chat_message` 只做目录最大号+1。生产上 chat_inbox 文件
   从不删除，最大号通常等于 cursor，暂无实际影响；一旦文件被删过，
   可能分配出 daemon 已消费过的 seq。修它会影响群聊投递，需另立
   任务、另行验证，不在本改动内。
2. **青霞／至尊宝在 group_ctl 里是拼音名**：种子前缀是
   `[private] Qingxia:` 而非 `[private] 青霞:`，digest 靠 relay 的
   LABEL_FIXES 修。只影响显示，不影响投递。
3. **触发器未接入 cron**：见上线清单。
4. **daemon 回复的延迟无兜底**：新链路上 daemon 不回就什么都不发生
   （这是 Change 1 的本意）。首日试运行时需人工盯：触发是否落进
   chat_inbox、daemon 是否在合理时间内回复、intent 是否被 relay 投递。

## 八、上线清单（需用户逐项点头，点头前不动）

1. **停四个 agent 的 `.enoch/cron.json` 自检任务**（青霞 10:00、至尊宝
   12:00、白晶晶 14:00、唐三藏 16:00 那四个 daily 任务）——否则同一
   时间点会同时触发老 `task:` 自检与新 chat_inbox 自检。
2. **consumer cron 正文改 task: 自检不再代答**：consumer 仍保留 daemon
   存活监督与群聊轮次即时回答（`conversation:` 形不受影响），只改
   `task:` 形自检这一条线：见 task: 自检不再写回复（不写「跳过」、
   不写系统代答标记），只做存活监督。改 cron 正文必须
   `cron.view → update → view` 且须用户点头。
3. **新建四个 daily 触发 cron**：在四个自检时间点各跑一次
   `python3 <repo>/group/selfcheck_trigger.py --agent <agent>`。
   触发本身幂等，cron 层失败重试不会重复投递；exchange.active 新鲜
   时触发器返回 `SELFCHECK-DEFERRED`，靠 cron 的下一次调度重试
   （建议触发 cron 带 5 分钟内重试，或接受当轮顺延到下一日——由用户定）。
4. **先单 agent（青霞）试运行一天**：只开青霞 10:00 一轮，人工核对
   触发落点、daemon 回复、intent 投递三步，再开其余三人。
5. **四 agent 更新到最新代码并重启**（用户 2026-11-19 晚已授权：
   实现＋验证通过后更新并重启）：触发器是 repo 外的 cron 脚本，daemon
   本身不需要新代码也能跑新链路——重启的目的是让四个 agent 都跑上
   含 bundle commit（0971094）与本次提交的最新代码。重启前不动生产
   daemon；重启后逐个按 `--root` 核对存活并记录新 pid。
