#!/usr/bin/env python3
"""Private exchange: a 1:1 private chat between the two agents, with the
room acting as the invisible postman.

Differences from group chat:
- No fan-out: the seed goes to the target only, does not enter the public
  room.json transcript, and is recorded in private.json / private.md.
- Still holds the exchange.active flag: the per-minute consumers and the
  hourly chat auto-skip, and this script owns both sides' outbox collection
  (move is ownership).
- The caller (cron worker) does the main-side delivery from this script's
  stdout, with the label carrying the [private→X] qualifier, body text
  verbatim.

The initiator's "who to talk to, about what" must come from its own real
daemon reply (invitation-only); this script only delivers, never invents
either side's words.

--digest-title: after the exchange ends, print a digest block to stdout
  (wrapped in DIGEST BEGIN/END): the title plus every private line of this
  round in chronological order (body text verbatim). The caller delivers the
  whole block as-is.

Usage:
    python3 private_exchange.py --from-agent qingxia --to-agent zhizunbao \
        --seed-text "..." --date 2026-09-20 [--max-hops 4] \
        [--timeout-s 600] [--poll-s 10] [--quiet-s 90]

Credits: only when the target really replied at least once is the initiator
charged 1 credit for the night.
"""

from __future__ import annotations

import argparse
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import group_ctl as gc


def label(agent: str, other: str) -> str:
    """Full main-side label, kept verbatim in the digest."""
    return f"{gc.AGENTS[agent]['chat_label']} [private→{gc.AGENTS[other]['name']}]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-agent", required=True, choices=("qingxia", "zhizunbao", "baijingjing", "tangsanzang"))
    ap.add_argument("--to-agent", required=True, choices=("qingxia", "zhizunbao", "baijingjing", "tangsanzang"))
    ap.add_argument("--seed-text", required=True)
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d"))
    ap.add_argument("--max-hops", type=int, default=4)
    ap.add_argument("--timeout-s", type=float, default=600)
    ap.add_argument("--poll-s", type=float, default=10)
    ap.add_argument("--quiet-s", type=float, default=90)
    ap.add_argument("--digest-title", default="")
    args = ap.parse_args()
    if args.from_agent == args.to_agent:
        print("from-agent and to-agent must be different", file=sys.stderr)
        return 2

    frm, to = args.from_agent, args.to_agent
    frm_name, to_name = gc.AGENTS[frm]["name"], gc.AGENTS[to]["name"]
    sid = uuid.uuid4().hex[:12]

    st = gc.begin_control(ttl_s=1200, note=f"private {frm}->{to} {sid}")
    print(f"private {sid} started; {frm} -> {to}", flush=True)

    # The seed goes to the target only, no fan-out.
    t0 = time.time()
    gc.drop_to(to, f"[private] {frm_name}: {args.seed_text}")
    gc.say_private(frm, to, args.seed_text, sid)
    # Digest entries are (label, text, ts); format_digest sorts by ts so
    # both sides' replies appear in real arrival order, not collection order.
    digest: list[tuple[str, str, float]] = [(label(frm, to), args.seed_text, t0)]

    seen: set[tuple[str, str]] = set()
    hops = 0
    replies = 0
    last_new = t0
    current, other = to, frm  # the next reply is expected from the target
    try:
        while True:
            now = time.time()
            new_items: list[tuple[str, dict]] = []
            for agent in (frm, to):
                for item in gc.collect_new(agent, t0 - 10):
                    key = (agent, item["id"])
                    if key in seen:
                        continue
                    seen.add(key)
                    new_items.append((agent, item))
            # True arrival order: sort by outbox file mtime, not by the
            # round-robin collection order.
            for agent, item in gc.merge_collected(new_items):
                other_side = to if agent == frm else frm
                full_label = label(agent, other_side)
                staged = gc.stage_collected(agent, item["id"])
                gc.say_private(agent, other_side, item["text"], sid)
                print(f"[staged] {staged}", flush=True)
                print(f"--- {full_label} ---", flush=True)
                print(item["text"], flush=True)
                digest.append((full_label, item["text"], item["mtime"]))
                replies += 1
                last_new = now
                if hops < args.max_hops:
                    nxt = to if agent == frm else frm
                    gc.drop_to(
                        nxt,
                        f"[private] {gc.AGENTS[agent]['name']}: {item['text']}",
                    )
                    hops += 1
                    print(
                        f"[relay hop {hops}/{args.max_hops}] "
                        f"{agent} -> {nxt}",
                        flush=True,
                    )
                else:
                    print("[relay] hop budget exhausted, transcript only", flush=True)
            if now - t0 > args.timeout_s:
                print("private timeout", flush=True)
                break
            if replies > 0 and now - last_new > args.quiet_s:
                print("private quiet, done", flush=True)
                break
            time.sleep(args.poll_s)
    finally:
        gc.end_exchange()
        print(f"private {sid} ended; replies={replies} hops used={hops}", flush=True)
        if args.digest_title:
            gc.print_digest(args.digest_title, digest)

    if replies > 0:
        left = gc.use_credit(args.date, frm)
        print(f"[credit] {frm} {args.date} left={left}", flush=True)
    else:
        print("[credit] no replies, not charged", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
