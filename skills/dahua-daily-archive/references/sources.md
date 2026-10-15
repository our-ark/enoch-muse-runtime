# 来源格式和导出

程序仅用 Python 3.11+ 标准库。它读取来源、写限定日期的摘录与哈希；不连接 GitHub、不创建定时任务、不更改活跃来源。不导入 `group_ctl.py`，以免触发运行侧行为。

```bash
python3 skills/dahua-daily-archive/scripts/export_day.py export \
  --date 2026-10-15 --timezone America/Los_Angeles \
  --room /path/to/muse-group/room.json \
  --peer-private /path/to/muse-group/private.json \
  --host-private /path/to/approved-host-private-export.json \
  --operations /path/to/approved-operations-export.json \
  --out /path/to/archive-checkout/docs/agent-life-observations/dahua-xiyou/daily
```

未提供的来源参数、或指定文件不存在，都会记录为缺失，绝不等于零活动。实际路径由紫霞在 Muse 上确认；这些 `/path/to/` 是命令参数说明，不是部署路径。读取失败、损坏 JSON、未知说话人、无法解析的时间会终止本次导出。使用只含本项目的来源，不能把整份 Muse 账户导出交给程序。

## 群聊：现有 room.json

`{"transcript": [{"t": 1792051200, "speaker": "青霞", "text": "原话", "exchange_id": "original-id", "kind": "agent"}]}`

字段与 `group/group_ctl.py::say` 对应。`kind` 可为 `agent`、`host`、`human`；说话人限制为四位角色、紫霞及 `observer`／`观察者`。拼音标识也接受。`t` 为 Unix 秒或含时区的 ISO 时间，不使用文件修改时间替代事件时间。记录中的 kind 是来源标签，不能认证生成者。

## 同伴私聊：现有 private.json

`{"transcript": [{"t": 1792051200, "from": "qingxia", "to": "tangsanzang", "text": "原话", "session_id": "original-id"}]}`

字段与 `group/group_ctl.py::say_private` 对应。仅四位角色之间的记录属于此来源。原 session ID 保留；程序不合并正文相同但来自不同位置的记录。

## 紫霞私聊：限定项目的 host 导出

与私聊格式相同，但每条一端为 `zixia`／`紫霞`，另一端为四位角色之一。来自 Muse 原生导出时，逐字复制消息字段；无法取得 host 原话时只列出实际存在的角色发言。程序固定标记该来源为 `host_export`，双边结构和完整覆盖仍未经独立验证。摘要不要放进 transcript；只能作为下方的 observer_report 事件。

本仓库尚未验证 Muse 的通用 host-history 导出 API。安装时应把实际可用的导出接口、分页／留存范围及取回方法记录在私有配置中。若无法获取，保留缺失状态并报告，不能宣称群聊和全部私聊均已完整覆盖。

## 运行事件：独立导出

```json
{"events": [{
  "t": "2026-10-15T20:04:00-07:00",
  "type": "timeout",
  "producer": "system",
  "text": "原始日志中的事件文本，或明确标注的观察者报告",
  "session_id": "original-session-id",
  "evidence_ref": "original-record-id"
}]}
```

`type`：`intent`、`dispatch`、`delivery`、`reply`、`self_check`、`skip`、`timeout`、`observer_report`。`producer`：`agent`、`host`、`system`、`observer`、`unknown`。可以补充 `agent`（四位角色标识）和 `request_id`。这些字段都是**来源提供的值**，程序不会用一条 delivery 事件自动认证所有相同会话的发言，也不会把 host 报告的 skip 改成 agent 的决策。不要复制认证信息、环境变量或完整推理请求。

## 输出与迟到记录

输出为 `YYYY-MM-DD/r001/` 下的 `records.json`、`conversations.zh-CN.md`、`manifest.json`。后续同日材料变化时追加 `r002/` 等目录；旧 revision 原样保留。一个 revision 是完整当日可见摘录的替代快照，不是新增会话集合；分析时每个日期只能选一个 revision，不把版本叠加计数。

`records.json` 保留正文与明确映射的非敏感字段，每条含来源标签、JSON 指针和源记录哈希。manifest 保存各读取文件的 SHA-256、摘录哈希及缺失状态，不公开本机绝对路径，不复制完整源文件。原始来源应在宿主私有留存，以便后续受控核对。

若相关日期的记录没有变化，即使累计来源文件因其他日期增长而改变，重复运行仍复用既有 revision。它保留首次快照的来源哈希，不声称其为最新全文件哈希。程序不猜测完全覆盖、会话已结束或活动总量；空日记录的含义是“这些来源未提供当日正文”，不是“无人互动”。

```bash
python3 skills/dahua-daily-archive/scripts/export_day.py verify \
  /path/to/daily/2026-10-15/r001
```

验证文件哈希、日期范围、结构与可重建正文。它是归档完整性检查，不是对 Muse 实际执行的独立认证。
