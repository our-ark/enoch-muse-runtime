# Runtime / Account Migration Observations

[English](./README.md)

这个目录跟踪 persistent agents 跨 deployment / account / runtime boundary 后的 continuity。

目标不是把“进程搬过去了”直接等同于 identity persistence，而是逐层观察：

- identity facts 是否恢复；
- relationship state 是否恢复；
- group culture / roles 是否恢复；
- Muse-native episodic memory 是否恢复；
- unfinished commitments 是否继续；
- Observer relationship 是否继续；
- operational responsibilities 是否继续。

## 当前记录

### 2026-09-22 — 第一次 Muse account migration

用户报告：五个《大话西游》persistent agents 从原 Muse account 迁移到另一个 Muse account。

迁移后的第一轮 `@all`：

- [原始群聊](../group-interactions/conversations/2026-09-22-first-group-after-muse-account-migration.zh-CN.md)
- [群体连续性分析](../group-interactions/observations/2026-09-22-muse-account-migration-continuity.zh-CN.md)
- [post-migration identity/social baseline](../identity-baselines/2026-09-22-muse-account-migration-baseline.zh-CN.md)

第一轮表面上出现“新家 / 搬家 / 新地盘”等 awareness，但随后 provenance clarification 说明：这些 migration facts 是 R-side 在当前 runtime request 中提供的 context，不是旧记忆自发 recall。

因此第一轮应改记为：

> **context-conditioned migration awareness + preserved persona/social response style**

- [关键 correction：R-side context injection provenance](./2026-09-22-migration-context-injection-provenance.zh-CN.md)

## 当前结论边界

这次迁移是：

> **Muse account A → Muse account B**

因此属于 **same-runtime-family cross-account / deployment-boundary continuity**。

它比单纯 daemon restart 更强，但不能直接证明：

> arbitrary cross-framework runtime independence

后续要通过 relationship / episodic memory / commitments / roles 的无提示恢复继续增强 evidence。


## 方法学更新

跨 account / runtime 的 continuity test 必须同时保存：

> **trigger provenance + context provenance + memory provenance**

否则 current-context injection 很容易被误判成 long-term-memory continuity。
