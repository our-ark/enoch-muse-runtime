#!/usr/bin/env python3
"""Group exchange driver: open an exchange round, collect both sides'
replies, relay them to each other within the hop budget, then wrap up.

Usage:
    python3 group_exchange.py --speaker <host-name> --text "..." [--max-hops 3]
                             [--timeout-s 1500] [--poll-s 30]
                             [--host-name NAME --host-text "..."]
                             [--host-name NAME --host-drop-dir DIR --host-wait-s 90]

The host is a third-party participant: its message text is written by the
caller and passed in, not a daemon reply, and it costs no hop budget. The
host's display name is given with --host-name (defaults to the
MUSE_GROUP_HOST_NAME environment variable).

--host-text: at exchange start, fan "[group] <host>: <text>" out to both
  daemons and record it in the transcript (kind=host).

--host-drop-dir: host interjection mode. The caller writes host-1.txt,
  host-2.txt, ... in order under <DIR>/<exchange_id>/; after each relay hop
  the driver waits --host-wait-s seconds (default 90) for the next host
  interjection, fans it out to both daemons and records it in the transcript
  (kind=host, no hop budget). A timeout with no new file simply continues,
  never blocks.

--digest-title: after the exchange ends, print a digest block to stdout
  (wrapped in DIGEST BEGIN/END): the title plus every line of this round in
  chronological order (body text verbatim). The caller delivers the whole
  block as-is.

R inference is not done by this script: both mailbox consumers' per-minute R
loops answer the daemons' inference requests (during a group exchange their
delivery is paused by the flag, but R continues normally). This script only
collects chat_outbox, relays, and keeps the transcript.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import group_ctl as gc


def await_host_drop(drop_dir: Path, exchange_id: str, idx: int, wait_s: float) -> str | None:
    """Wait for the caller to write the idx-th host interjection; return its
    text, or None on timeout."""
    target = drop_dir / exchange_id / f"host-{idx}.txt"
    deadline = time.time() + max(0.0, wait_s)
    while True:
        try:
            text = target.read_text(encoding="utf-8").strip()
        except OSError:
            text = ""
        if text:
            return text
        if time.time() >= deadline:
            return None
        time.sleep(2)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--speaker", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--max-hops", type=int, default=3)
    ap.add_argument("--timeout-s", type=float, default=1500)
    ap.add_argument("--poll-s", type=float, default=10)
    ap.add_argument("--quiet-s", type=float, default=120)
    ap.add_argument("--host-name", default=os.environ.get("MUSE_GROUP_HOST_NAME", ""))
    ap.add_argument("--host-text", default="")
    ap.add_argument("--host-drop-dir", default="")
    ap.add_argument("--host-wait-s", type=float, default=90)
    ap.add_argument("--digest-title", default="")
    args = ap.parse_args()

    if (args.host_text or args.host_drop_dir) and not args.host_name:
        ap.error("--host-text/--host-drop-dir require --host-name (or MUSE_GROUP_HOST_NAME)")

    t0 = time.time()
    st = gc.start_exchange(args.speaker, args.text)
    eid = st["exchange_id"]
    print(f"exchange {eid} started; seed seqs={st['seed_seqs']}", flush=True)

    # Digest entries are (label, text, ts). The label is kept verbatim;
    # format_digest sorts by ts, so both sides' replies appear in real
    # arrival order, not in collection order.
    digest: list[tuple[str, str, float]] = [("opening", f"{args.speaker}: {args.text}", t0)]

    host_name = args.host_name
    drop_dir = Path(args.host_drop_dir) if args.host_drop_dir else None
    if drop_dir:
        (drop_dir / eid).mkdir(parents=True, exist_ok=True)
    host_n = 0

    def host_turn() -> None:
        """If interjection mode is on, wait for one host interjection and fan
        it out; skip on timeout."""
        nonlocal host_n
        if not drop_dir:
            return
        host_n += 1
        text = await_host_drop(drop_dir, eid, host_n, args.host_wait_s)
        if not text:
            print(f"[host] no drop host-{host_n}, skip", flush=True)
            return
        hseqs = gc.fanout_room_message(host_name, text, eid)
        print(f"--- **{host_name}** ---", flush=True)
        print(text, flush=True)
        print(f"[host fanout] seqs={hseqs}", flush=True)
        digest.append(("host interjection", f"{host_name}: {text}", time.time()))

    if args.host_text:
        hseqs = gc.fanout_room_message(host_name, args.host_text, eid)
        print(f"--- **{host_name}** ---", flush=True)
        print(args.host_text, flush=True)
        print(f"[host fanout] seqs={hseqs}", flush=True)
        digest.append(("host interjection", f"{host_name}: {args.host_text}", time.time()))

    seen: set[tuple[str, str]] = set()
    hops = 0
    last_new = t0
    try:
        while True:
            now = time.time()
            new_items: list[tuple[str, dict]] = []
            for agent in ("qingxia", "zhizunbao"):
                for item in gc.collect_new(agent, t0 - 10):
                    key = (agent, item["id"])
                    if key in seen:
                        continue
                    seen.add(key)
                    new_items.append((agent, item))
            # True arrival order: sort by outbox file mtime, not by the
            # round-robin collection order.
            for agent, item in gc.merge_collected(new_items):
                label = gc.AGENTS[agent]["chat_label"]
                staged = gc.stage_collected(agent, item["id"])
                gc.say(gc.AGENTS[agent]["name"], item["text"], "agent", eid)
                print(f"[staged] {staged}", flush=True)
                print(f"--- {label} ---", flush=True)
                print(item["text"], flush=True)
                digest.append((label, item["text"], item["mtime"]))
                last_new = now
                if hops < args.max_hops:
                    other = gc.OTHER[agent]
                    seq = gc.relay(agent, item["text"])
                    hops += 1
                    print(
                        f"[relay hop {hops}/{args.max_hops}] "
                        f"{agent} -> {other} (seq {seq})",
                        flush=True,
                    )
                    host_turn()
                    last_new = time.time()
                else:
                    print("[relay] hop budget exhausted, transcript only", flush=True)
            if now - t0 > args.timeout_s:
                print("exchange timeout", flush=True)
                break
            if hops >= args.max_hops and now - last_new > args.quiet_s:
                print("exchange quiet, done", flush=True)
                break
            time.sleep(args.poll_s)
    finally:
        gc.end_exchange()
        print(f"exchange {eid} ended; hops used={hops}", flush=True)
        if args.digest_title:
            gc.print_digest(args.digest_title, digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
