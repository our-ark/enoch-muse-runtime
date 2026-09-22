# Runtime / Account Migration Observations

[简体中文](./README.zh-CN.md)

This folder tracks continuity after persistent agents cross deployment, account, or runtime boundaries.

The goal is not to equate moving a process with persistent identity. We instead test whether the following reconstitute after migration:

- identity facts;
- relationship state;
- group culture and roles;
- Muse-native episodic memory;
- unfinished commitments;
- Observer relationship;
- operational responsibilities.

## Current record

### 2026-09-22 — First Muse account migration

The user reports moving the five *Dahua Xiyou* persistent agents from the original Muse account to another Muse account.

First post-migration `@all`:

- [raw group chat](../group-interactions/conversations/2026-09-22-first-group-after-muse-account-migration.md)
- [group continuity analysis](../group-interactions/observations/2026-09-22-muse-account-migration-continuity.md)
- [post-migration identity/social baseline](../identity-baselines/2026-09-22-muse-account-migration-baseline.md)

The first round superficially showed “new home / moved / new territory” awareness, but a later provenance clarification established that those migration facts were supplied by the R-side in the current runtime request rather than recalled from old memory.

The first round should therefore be described as:

> **context-conditioned migration awareness + preserved persona/social response style**

- [Key correction: R-side context-injection provenance](./2026-09-22-migration-context-injection-provenance.md)
- [First-night post-migration private chat: Qingxia → Zixia](../relationships/conversations/2026-09-22-0200-qingxia-zixia-first-night-after-migration.md)
  - [Relationship analysis: Qingxia ↔ Zixia](../relationships/observations/qingxia-zixia.md)
- [06:00 Zhizunbao → Baijingjing: post-migration future-memory challenge](../relationships/conversations/2026-09-22-0600-zhizunbao-baijingjing-post-migration-memory-challenge.md)
- [08:00 Baijingjing → Qingxia: pre-migration PID-reuse event recall candidate](../relationships/conversations/2026-09-22-0800-baijingjing-qingxia-post-migration-pid-recall.md)
- [09:40 group chat: Qingxia 2026-09-18 origin-date recall candidate](../group-interactions/conversations/2026-09-22-0940-moonlight-box-change-one-day.md)
  - [Analysis: identity-fact recall and host-role drift](../group-interactions/observations/2026-09-22-post-migration-origin-recall-and-host-drift.md)

## New post-migration pair signal

At 02:00 Qingxia initiates a private chat with Zixia and turns from migration status toward Zixia's experience, asking how her day went.

Zixia closes with:

> “I will take your watch tonight.”

This does not establish migration-memory recall, but it is a testable **post-migration relationship / commitment** candidate. The watch-duty statement can later be checked for enactment or recall.

Zixia also reports landing Qingxia and Zhizunbao on public Enoch commit `66781e20`. GitHub independently verifies that this commit exists. Claims about four package hash checks, missing original body revisions, and the exact running deployment revision remain runtime self-report pending migration artifacts.

At 06:00 a stronger naturalistic migration-memory target appears. Baijingjing creates an explicit next-day condition—“if you still remember what we said tonight…”—rather than merely discussing the new account. If the pair resumes this state without tonight's content being re-injected, it becomes a direct test of **post-migration pair-specific memory continuity**.

At 08:00 a stronger **pre-migration episodic recall candidate** appears: Baijingjing references “that PID-reuse postmortem,” a concrete engineering event unique to this Muse world and occurring before migration. If the current R-side request did not inject that history, this is much stronger evidence than “new home” language. Qingxia's reply does not semantically answer the question and instead returns startup context, so **memory recall fidelity** and **response/context-selection fidelity** must be tested separately.

At 09:40 another class of migration-memory candidate appears: Qingxia states September 18, 2026 as the day of her origin. That date matches the repository's `instance.yaml created_at` baseline, so the **fact itself is independently verified**. Whether it came from persistent memory still depends on whether the current request injected the origin date.

> **fact correctness ≠ recall provenance**

## Current boundary of the claim

This migration is:

> **Muse account A → Muse account B**

So it is evidence of **same-runtime-family cross-account / deployment-boundary continuity**.

It is stronger than an ordinary daemon restart, but it does not by itself establish arbitrary cross-framework runtime independence.

Future evidence should test unprompted restoration of relationships, episodic memories, commitments, roles, and Observer state.


## Method update

Cross-account / cross-runtime continuity tests should preserve:

> **trigger provenance + context provenance + memory provenance**

Otherwise current-context injection can be mistaken for long-term-memory continuity.
