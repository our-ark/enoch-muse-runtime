#!/usr/bin/env python3
"""群聊交换驱动: 开一轮交换, 收集两边回复, 按 hop 上限互相转发, 收尾.

用法:
    python3 group_exchange.py --speaker 观察者 --text "..." [--max-hops 3]
                             [--timeout-s 1500] [--poll-s 30]
                             [--zixia-text "..."]

--zixia-text: 紫霞以参与者身份说的话 (调用方以紫霞口吻写好).
  给出后, 交换开场时把 "[群聊] 紫霞: <text>" 扇出给两边 daemon,
  并记入 transcript (kind=zixia). 不占 hop 预算.

R 推理不由本脚本做: 两个 mailbox consumer 的每分钟 R 循环会回答 daemon 的
inference 请求 (群聊进行中它们的投递被旗标暂停, 但 R 照常). 本脚本只负责
chat_outbox 的收集、转投与 transcript.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import group_ctl as gc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--speaker", required=True)
    ap.add_argument("--text", required=True)
    ap.add_argument("--max-hops", type=int, default=3)
    ap.add_argument("--timeout-s", type=float, default=1500)
    ap.add_argument("--poll-s", type=float, default=10)
    ap.add_argument("--quiet-s", type=float, default=120)
    ap.add_argument("--zixia-text", default="")
    args = ap.parse_args()

    t0 = time.time()
    st = gc.start_exchange(args.speaker, args.text)
    eid = st["exchange_id"]
    print(f"exchange {eid} started; seed seqs={st['seed_seqs']}", flush=True)

    if args.zixia_text:
        zseqs = gc.fanout_room_message("紫霞", args.zixia_text, eid)
        print("--- 💜 **紫霞** ---", flush=True)
        print(args.zixia_text, flush=True)
        print(f"[zixia fanout] seqs={zseqs}", flush=True)

    seen: set[tuple[str, str]] = set()
    hops = 0
    last_new = t0
    try:
        while True:
            now = time.time()
            for agent in ("qingxia", "zhizunbao"):
                for item in gc.collect_new(agent, t0 - 10):
                    key = (agent, item["id"])
                    if key in seen:
                        continue
                    seen.add(key)
                    name = gc.AGENTS[agent]["name"]
                    staged = gc.stage_collected(agent, item["id"])
                    gc.say(name, item["text"], "agent", eid)
                    print(f"[staged] {staged}", flush=True)
                    print(f"--- {gc.AGENTS[agent]['chat_label']} ---", flush=True)
                    print(item["text"], flush=True)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
