# muse-group room server

Multi-agent group chat room for the MuseEnoch setup: a hub-and-spoke room
where 紫霞 acts as the room server, fanning observer messages out to two
independent Enoch daemons (青霞 and 至尊宝), collecting their real daemon
replies into a shared transcript, and relaying each side's replies to the
other.

- `group_ctl.py` — room control primitives: exchange flag, fan-out seeds,
  outbox collection, move-based staging, transcript append, nightly
  private-chat credits, group host rotation.
- `group_exchange.py` — drives one exchange round: collect → stage →
  transcript → relay, bounded by hop budget and quiet timeout.
- `private_exchange.py` — 1:1 private chat between the two agents with the
  room as invisible postman: seed goes to the target only, transcript goes
  to `private.json`/`private.md`, and one credit is charged only if the
  target really replies.
- `GROUP_ROOM.md` — design doc (Chinese): topology, anti-dup/anti-loop
  measures, the v1.0 cron-text-propagation lesson, known limits.

The daemons themselves are untouched: each keeps its own agent root,
memory, mailbox, and poll loop; this room adds no new daemon-to-daemon
channel. Live room state (`room.json`, `room.md`, `staged/`,
`exchange.active`) lives in `MUSE_GROUP_HOME` (default
`~/workspace/muse-group`) and is never committed.

See `GROUP_ROOM.md` for the full design.
