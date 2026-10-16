---
name: dahua-daily-archive
description: Archive daily Dahua Xiyou group and private conversations from Muse to our-ark/enoch-muse-runtime, preserving original words, coverage gaps and provenance. Use for Zixia's scheduled host-side export, catch-up or archive verification.
---

# 大话西游每日归档

由 **紫霞（Muse host）** 执行。目标仓库为 `our-ark/enoch-muse-runtime`，仅归档大话西游项目；四位角色为青霞、至尊宝、白晶晶、唐三藏。观察者已要求由紫霞每天上传该项目群聊和私聊，不需每次重复请求授权。授权不扩展到其他 Muse 对话、凭证或完整 agent 状态。

## 首次配置

阅读 [运行与发布约定](references/operation.md)。在 Muse 宿主侧确认群聊、同伴私聊、紫霞私聊及运行事件的实际来源；遵循 [来源格式](references/sources.md)。用当前宿主已提供的接口或文件读取，不臆造 Muse 导出 API。运行目录、认证和调度器配置保存在仓库之外。

用现有 Muse 后台调度器每天 **02:10，America/Los_Angeles** 归档前一自然日；使用命名时区处理夏令时，不写成固定 UTC 偏移。若已有同类任务，更新原任务，避免重复。先做一次导出与验证，再首次发布并检查远端提交，最后记录调度任务 ID、下次运行时间和实际采用的 skill 提交版本。只有这些步骤均完成才报告“已启用”。skill 文件存在不代表定时任务正在运行。

归档职责只属于 host，不发送给四位角色，不写入其 persona、记忆或社会行为任务。记录归档开始时间和来源覆盖变化，供研究者区分采集变化与行为变化。论文观察截止日不等于归档任务停用日；除非用户要求，日常归档继续。

## 每次运行

1. 从本地已确认发布的水位开始补齐漏日，每次最多补七日；同时复查最近三个已结束自然日以接收迟到材料。用日期选择事件，不按上传时间冒充观察时间。跨午夜会话保留原 session ID，两个日期的片段不算两个独立会话。
2. 只读取得来源快照，不移动 mailbox、不清理 outbox、不消耗聊天额度、不启动对话或改模型配置。记录实际可访问的来源；没有权限／接口的来源标缺失。不能因为当天无正文就写“四人拒绝私聊”。
3. 用随附 `scripts/export_day.py` 生成并验证当日包。原话保留原字、换行、称呼与说话人；既有归档只追加新 revision。来源有错而无法可靠解析时保留旧包并报告，不跳过坏记录生成“完整”结果。
4. 依据运行约定发布到 `docs/agent-life-observations/dahua-xiyou/daily/`，只提交验证过的归档文件。对无变化的重复运行不创建提交。推送成功后核对远端提交及文件，再更新私有水位。
5. 有新归档时向观察者给出日期、commit 链接及覆盖缺口；失败时说明最后成功日期和阻塞点。重复内容保持安静，不向角色群聊发送研究判断。

## 证据规则

- 原始逐字发言、host 导出、观察者报告和系统／host 代写分开标注。角色标签并不认证生成者；缺少逐请求模型 ID 时写未知，不能用角色自报或 `runtime=muse` 推断底层型号。
- 分开发起意图、调度、发送、送达、回复。当前 `room.json`／`private.json` 缺少逐条送达及完整生成归属；导出程序对此写 `unknown`，不自动提升证据等级。原始 skip、系统 fallback skip、超时未开场、没有回复分别记录。
- 能取得 host 私聊双方原话就完整保留；只有角色回复时不要把 host 总结变成引号内原话。无来源的承诺履行、记忆写入或检索不能补成事实。
- 自动归档仅记录，不评价身份、关系质量或社会停滞，不因结果不精彩而筛选。“秃驴”等原有措辞保留，但接受、冒犯及修复均需对方反馈与送达证据，不能代替其解释。
- 哈希说明文件／选取记录未改变，不认证原部署真实发生；原始操作日志不随包整库上传。遵守仓库 CONTRIBUTING 中不提交 live mailboxes、生产状态或凭证的要求，发布的是限定项目的对话摘录及来源元数据。
