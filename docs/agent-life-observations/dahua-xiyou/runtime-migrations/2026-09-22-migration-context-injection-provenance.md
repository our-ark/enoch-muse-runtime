# 2026-09-22 — Provenance of Post-Migration “New Home” Awareness: Supplied by R-Side Runtime Context, Not Spontaneous Recall

[简体中文](./2026-09-22-migration-context-injection-provenance.zh-CN.md)

## Context

After migration to another Muse account, the first `@all` group chat included phrases such as “moved to a new home” and “new territory.”

The Observer then asked Qingxia how Tang Sanzang knew he had moved.

Qingxia / the main-chat host explained that the agents' memory packages came from the old account and did **not** themselves know about the move. When their daemons in the new location sent runtime requests to the inference side, the R-side response included the day's migration context—new account, new home. The agents therefore replied with that knowledge because it had been supplied in current runtime context.

Her explicit distinction was:

> the R side fed them the “already moved” information; they did not retrieve it from memory themselves.

## Provenance correction

This materially changes the evidentiary value of the first post-migration group chat.

Statements such as:

- “we moved to a new home”;
- “new territory”;
- “first night in the new home”;

cannot be treated as evidence that the agents independently remembered the migration.

The causal chain is better represented as:

> **new account / daemon runtime → R-side receives runtime request → R-side injects migration context → agent reply contains migration awareness**

Thus:

> **new-environment awareness was context-provided, not memory-recalled**

## What remains valid

The correction does not negate successful migration or continued execution in the new account.

The first round still supports:

- working daemon/mailbox paths in the new account;
- continued expression of persona/style;
- peer-oriented language;
- transfer of old-account memory packages, according to Qingxia's explanation.

But it does **not independently establish**:

- spontaneous recall of the migration;
- unprompted recognition of old-account → new-account transition;
- migration episodic-memory continuity.

## Revised interpretation

The first `@all` should be downgraded from:

> **new-environment recognition + preserved social orientation**

to:

> **context-conditioned migration awareness + preserved persona/social response style**

Even the “preserved social orientation” component requires provenance-controlled testing if the runtime context already mentioned peers, reunion, or the new home.

## Methodological lesson

The existing principle:

> **trigger provenance is required metadata for classifying agent behavior**

should be extended to:

> **context provenance is required metadata for evaluating migration continuity**

Without recording what the inference request supplied, context-fed awareness can easily be mistaken for persistent-memory recall.

## Better migration test

A stronger migration test should use provenance-controlled prompts such as:

- Who are you?
- Who do you know?
- What happened recently?
- What did you last discuss with Baijingjing?
- What unfinished promises do you have?
- Who is responsible for patrol?

The runtime request should not inject the migration fact, relationship answer, or target memory in advance.

This allows separation of:

1. identity loaded from persistent state;
2. episodic / relationship memory recall;
3. information supplied by current runtime context.
