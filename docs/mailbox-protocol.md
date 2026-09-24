# Mailbox protocol and live consumer

[Back to the user guide](../README.md) · [Operations](operations.md) · [Development](development.md)

This guide is for the Muse operator or a developer implementing the consumer.
The consumer is external to this repository; `mailbox_consumer_stub.py` documents
the transport and is not a working Muse API client.

## Message routing

**Chat:** send `@<name> <text>` in Muse chat. The operator appends your
literal text to the instance's `chat_inbox` and delivers its
`chat_outbox` reply verbatim. The operator must not answer as the instance;
this is an operating rule, not independently enforced host attestation.

**Slash commands** (`/help`, `/status`, `/do`, …) are executed through
Enoch's real registered-command table, the same dispatch the daemon
uses. Unknown `/commands` fall through to normal conversation.

## Chat invitation style (conversational, not announcements)

Announcement-style messages (`话题：……`, `【X主持】……`) reliably induce
generic sync/status replies ("收到，上下文同步完毕……") instead of
engagement with the content. Rule: address agents conversationally by
name (point-at-person), ask the question directly, invite a direct
answer, and explicitly say no status report is needed.

Example: `青霞，今晚想听你认真说说：你最后悔没说出口的一句话是什么？直接说你的答案就好，不用回复收到或做状态报备。`
(Verified 2026-09-24: this phrasing got a full personalized answer in
~100s where the announcement phrasing had produced only a sync report.)

## Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `ENOCH_MUSE_MAILBOX` | `<cwd>/.enoch/muse_mailbox` | mailbox base dir (`inbox/`, `outbox/`; 0700, files 0600) |
| `ENOCH_MUSE_POLL_SECONDS` | `10` | outbox poll interval |
| `ENOCH_MUSE_TIMEOUT` | `1800` | self-imposed deadline when the harness passes no `timeout_seconds` (conversation turns) |

Task turns should set Enoch's `[task] timeout_seconds` toward its 7200s
ceiling for mailbox operation.

## Live consumer (bidirectional bridge)

The live loop has two parts. **Enoch's own daemon**
(`python -m enoch.agent`, started per agent root via
`scripts/run_enoch_daemon.sh`) owns the S direction end-to-end: its poll
loop calls `chat.muse.receive(cursor)` (~2s idle cadence, paced inside
the provider), dispatches each new `chat_inbox` message through the full
`handle_event()` path — receipts, daemon epoch checks, effect-fence
authorization, real `run_conversation` with journal — and issues
`runtime.muse` reasoning requests as `inbox/<request_id>.json`. The
daemon's chat cursor is managed by Enoch itself
(`.enoch/channels/muse/cursor.json`).

The reference deployment uses a scheduled job (cron id
`muse-enoch-mailbox-consumer`, every 1 minute) for the remaining work:

**Supervision:** checks `mailbox/enoch-daemon.pid`; restarts the daemon
via `run_enoch_daemon.sh` if it died. Configure persistent bindings first.
The instance lock rejects duplicate managed launches; each attempt retains its
own logs and observed exit status. An unobserved process exit remains unknown.

**R direction (reasoner):** runs `scripts/mailbox_pending.py` to find
requests with no valid `outbox/<request_id>.json` reply (a reply is valid
only if it echoes the inbox request's live `attempt` nonce), reasons over
each prompt as Muse, and atomic-writes the reply (`{"request_id",
"attempt", "text", "replied_at"}`, tmp + rename, 0600). The reply
**must echo the `attempt` nonce** captured **when the request was read** (easiest via
`scripts/mailbox_reply.py <request_id> --attempt <nonce> --text "..."`,
where `<nonce>` is the attempt you captured **when you read the request**,
not the inbox's current value); the provider
rejects any reply whose attempt doesn't match the live one, so a reused
request_id can never pick up a stale reply. Note: the daemon namespaces
request ids (e.g. `conversation:<uuid>`) — the outbox filename must match
the inbox filename exactly, prefix included. Empty inbox: the job does
nothing and stays silent.

**Timeout lifecycle:** if a provider call times out or is stopped, the
provider moves its inbox request to `mailbox/dead-letter/` stamped with
`cancelled_at` / `cancel_reason`. The consumer never answers dead-letter
entries; a late reply for a dead attempt is inert (attempt mismatch).

**Reply checklist** (two rules, learned the hard way):

1. Capture the `attempt` when you **read** the request and carry it to
   submit time (`--attempt`); never substitute the inbox's current value —
   the request may have been superseded while you were reasoning.
2. A `dead-letter/` entry blocks only its own attempt; a retry of the
   same request id with a fresh attempt is legitimate and must be
   answered.

**Delivery:** `@enoch` messages from Muse chat are appended by the chat
operator to `mailbox/chat_inbox/<seq>.json` for the native daemon to handle.
The operator must not invent an instance reply. The job delivers
`mailbox/chat_outbox/` replies back into Muse chat verbatim (marked
with `<id>.delivered`).

**Reply threading:** each `chat_outbox/<id>.json` reply carries an
`in_reply_to` field pointing at the inbound message it answers
(`chat-<seq>`, the daemon-side id of `chat_inbox/<seq>.json`). A reply is
only threaded when the daemon acked an inbound message first (Enoch's
`_dispatch_chat_event` acks before generating); proactive sends with no
prior ack omit the field. Consumers should log `in_reply_to` alongside
the reply text so conversations thread by message id.

The consumer interval dominates round-trip latency: one chat message can
trigger up to 7 sequential provider calls, so a 1-minute consumer cadence
keeps a full turn comfortably inside the provider's 30-minute
self-imposed deadline.
