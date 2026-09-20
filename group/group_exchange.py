#!/usr/bin/env python3
"""群聊交换驱动: 开一轮交换, 收集两边回复, 按 hop 上限互相转发, 收尾.

用法:
    python3 group_exchange.py --speaker <主持人名> --text "..." [--max-hops 3]
                             [--timeout-s 1500] [--poll-s 30]
                             [--host-name NAME --host-text "..."]
                             [--host-name NAME --host-drop-dir DIR --host-wait-s 90]

主持人 (host) 是第三方参与者: 发言正文由调用方写好传入, 不是 daemon 回复,
不占 hop 预算. 主持人显示名用 --host-name 指定 (默认读 MUSE_GROUP_HOST_NAME
环境变量).

--host-text: 交换开场时把 "[群聊] <host>: <text>" 扇出给两边 daemon,
  并记入 transcript (kind=host).

--host-drop-dir: 主持人插话模式. 调用方在 <DIR>/<exchange_id>/ 下按顺序写
  host-1.txt, host-2.txt, ...; 驱动每完成一次 hop 转发后等 --host-wait-s 秒
  (默认 90) 收下一条主持人插话, 扇出给两边 daemon 并记 transcript
  (kind=host, 不占 hop 预算). 超时无新文件则直接继续, 不阻塞.

R 推理不由本脚本做: 两个 mailbox consumer 的每分钟 R 循环会回答 daemon 的
inference 请求 (群聊进行中它们的投递被旗标暂停, 但 R 照常). 本脚本只负责
chat_outbox 的收集、转投与 transcript.
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
    """等调用方写下第 idx 条主持人插话, 返回正文; 超时返回 None."""
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
    args = ap.parse_args()

    if (args.host_text or args.host_drop_dir) and not args.host_name:
        ap.error("--host-text/--host-drop-dir 需要 --host-name (或 MUSE_GROUP_HOST_NAME)")

    t0 = time.time()
    st = gc.start_exchange(args.speaker, args.text)
    eid = st["exchange_id"]
    print(f"exchange {eid} started; seed seqs={st['seed_seqs']}", flush=True)

    host_name = args.host_name
    drop_dir = Path(args.host_drop_dir) if args.host_drop_dir else None
    if drop_dir:
        (drop_dir / eid).mkdir(parents=True, exist_ok=True)
    host_n = 0

    def host_turn() -> None:
        """如启用插话模式, 等一条主持人插话并扇出; 超时则跳过."""
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

    if args.host_text:
        hseqs = gc.fanout_room_message(host_name, args.host_text, eid)
        print(f"--- **{host_name}** ---", flush=True)
        print(args.host_text, flush=True)
        print(f"[host fanout] seqs={hseqs}", flush=True)

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
