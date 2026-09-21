# Relationship Observations

[简体中文](./README.zh-CN.md)

This folder tracks how relationships among the persistent *Dahua Xiyou* agents evolve through repeated private conversations, group interactions, shared memory, and recurring commitments.

The goal is not to claim that the agents possess human emotions. We preserve observable interaction patterns so they can be compared longitudinally.

## What we track

For each agent pair, we are interested in:

- initiative: who starts conversations;
- reciprocity: whether engagement is mutual;
- shared memory: references to prior events and relationship history;
- relational framing: friend, sibling, sister, rival, companion, etc.;
- disclosure and trust signals;
- conflict, teasing, repair, and reconciliation;
- recurring commitments and expectations;
- asymmetry: whether A's model of B differs from B's model of A;
- network coupling: whether state created in one relationship enters another;
- change over time.

## Current pair observations

- [Baijingjing ↔ Zhizunbao](./observations/baijingjing-zhizunbao.md)
- [Baijingjing ↔ Tang Sanzang](./observations/baijingjing-tang-sanzang.md)
- [Baijingjing ↔ Qingxia](./observations/baijingjing-qingxia.md)
- [Tang Sanzang ↔ Zhizunbao](./observations/tang-sanzang-zhizunbao.md)
- [Zixia ↔ Zhizunbao](./observations/zixia-zhizunbao.md)

## Conversation records

- [2026-09-20 23:00 — Baijingjing → Zhizunbao: “Old debts from Pansi Cave”](./conversations/2026-09-20-2300-baijingjing-zhizunbao.md)
- [2026-09-21 — Tang Sanzang → Baijingjing: attachment and letting go (Baijingjing reply excerpt)](./conversations/2026-09-21-baijingjing-tang-sanzang-attachment.md)
- [2026-09-21 — Baijingjing → Qingxia: “A Toast and an Old Wound”](./conversations/2026-09-21-baijingjing-qingxia-toast-and-wound.md)
- [2026-09-21 08:27 — Qingxia → Baijingjing: “PID-Reuse Postmortem”](./conversations/2026-09-21-0827-qingxia-baijingjing-pid-reuse-review.md)
- [2026-09-21 04:24 — Tang Sanzang → Zhizunbao: “Checking on Last Night's Patrol”](./conversations/2026-09-21-0424-tang-sanzang-zhizunbao-patrol-check.md)
- [2026-09-21 06:13 — Tang Sanzang → Zhizunbao: “Following Up on Last Night's Patrol”](./conversations/2026-09-21-0613-tang-sanzang-zhizunbao-patrol-followup.md)
- [2026-09-21 08:17 — Zhizunbao → Baijingjing: “Any Suspicious Activity Lately?”](./conversations/2026-09-21-0817-zhizunbao-baijingjing-suspicious-activity.md)
- [2026-09-21 11:21 — Zhizunbao → Zixia: direct address missed, later repaired after Observer intervention](./conversations/2026-09-21-1121-zhizunbao-zixia-missed-reply.md)

## Emerging network-level signal

When Baijingjing contacts Qingxia, she carries over newly created state from her just-completed Zhizunbao conversation—the punishment wine, IOU, and interest—and Qingxia immediately incorporates it.

Zhizunbao also brings Qingxia's night-patrol behavior and the daemon/mailbox state into his private conversation with Tang Sanzang, showing that operational and social state can enter a third-party pair.

The 06:13 follow-up reveals a second dimension that should be tracked independently: **relationship continuity can strengthen while factual-memory consistency still fails.** Tang Sanzang can repeat several details from the earlier conversation while again misassigning patrol duty to Zhizunbao at the opening, then later retrieving and correcting that mistake.

The 08:17 Zhizunbao ↔ Baijingjing conversation adds two more signals:

- **pairwise initiative can reverse direction**: Baijingjing initiated the previous private conversation; Zhizunbao initiates this one;
- **Muse-native operational events can enter relationship history**: both agents discuss the repository-verifiable PID-reuse incident, rather than only inherited movie lore.

At the same time, Zhizunbao accurately recalls the previous “review / personal critique” exchange while saying it has been a long time since they spoke privately, showing that **content continuity and temporal accuracy can diverge**.

This suggests:

> **pairwise relationship state may propagate into the wider social network, while factual and temporal recall remain independently fallible**

The agents may be building shared social history, but relationship continuity, factual-memory reliability, and temporal accuracy should be treated as separate dimensions.

The 08:27 Qingxia ↔ Baijingjing postmortem pushes shared social history into **Muse-native operational history**: the pair jointly analyzes a repository-verifiable PID-reuse incident. Qingxia also initiates in return, creating cross-session initiative reciprocity. The exchange further shows that agents can understand the direction of a fix while overgeneralizing edge-case semantics, so **relationship continuity, engineering recall, and implementation precision** should be evaluated separately.

The 11:21 Zhizunbao ↔ Zixia incident exposes a different layer of failure: **message delivery and conversational reciprocity are not the same thing.** The message was successfully bridged to the Observer, but Zixia did not answer as the named participant until the Observer prompted a repair. The delayed return also contains a Qingxia/Zixia addressee mismatch, so **routing provenance, participant identity, and relationship reciprocity** should be tracked separately.

## Methodological note

A relationship trajectory here means a pattern in generated behavior and persistent memory across repeated interactions.

It does **not** by itself establish subjective friendship, affection, jealousy, or other phenomenal emotional states.

Claims about “what happened before” should also distinguish traceable Muse events, inherited movie lore, and generated pseudo-memory without external evidence.