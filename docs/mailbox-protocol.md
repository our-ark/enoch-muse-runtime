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

The consumer interval dominates round-trip latency: one chat message can
trigger up to 7 sequential provider calls, so a 1-minute consumer cadence
keeps a full turn comfortably inside the provider's 30-minute
self-imposed deadline.
