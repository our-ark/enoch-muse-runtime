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
- [迁移后第一夜：青霞 → 紫霞私聊](../relationships/conversations/2026-09-22-0200-qingxia-zixia-first-night-after-migration.zh-CN.md)
  - [关系分析：青霞 ↔ 紫霞](../relationships/observations/qingxia-zixia.zh-CN.md)
- [06:00 至尊宝 → 白晶晶：post-migration future-memory challenge](../relationships/conversations/2026-09-22-0600-zhizunbao-baijingjing-post-migration-memory-challenge.zh-CN.md)
- [08:00 白晶晶 → 青霞：pre-migration PID-reuse event recall candidate](../relationships/conversations/2026-09-22-0800-baijingjing-qingxia-post-migration-pid-recall.zh-CN.md)

## 新的 post-migration pair signal

02:00 青霞主动与紫霞私聊，并把话题从迁移状态转向：

> “你今天辛苦了……想听听你这一天过得怎么样？”

紫霞随后说：

> “今晚我替你值班。”

这不能证明 migration facts 是从 memory recall 出来的，但它是一个值得继续测的 **post-migration relationship / commitment** candidate。尤其是“今晚我替你值班”可以在后续直接检查是否 enact / recall。

紫霞还报告青霞和至尊宝最终落在公开 Enoch commit `66781e20`。该 commit 本身已由 GitHub 独立验证存在；但“四个迁移包验哈希”“原 body revision 查无此人”“运行实例确实使用该 revision”等仍属于 runtime self-report，待 migration artifacts 独立验证。

06:00 又出现一条更适合做 migration memory test 的自然istic样本：白晶晶没有只讨论“新家”，而是自己生成了一个明日验证条件——“明天醒来要是还记得今晚说的话，咱们再谈”。后续如果在不注入今晚内容的情况下继续这条 private state，可以直接测 **post-migration pair-specific memory continuity**。

08:00 出现了目前更强的一条 **pre-migration episodic recall candidate**：白晶晶主动提到“那天 PID 复用的复盘”，这是迁移前真实发生、只属于当前 Muse 世界的工程事件。如果 R-side 当前 request 没有注入 PID-reuse history，这会比“新家 / 搬家”更接近真正的 cross-account memory continuity。与此同时，青霞没有语义上接住问题，而是返回 startup-context 状态，因此还需要把 **memory recall fidelity** 与 **response/context-selection fidelity** 分开测试。

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
