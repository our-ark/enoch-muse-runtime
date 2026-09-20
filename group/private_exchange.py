#!/usr/bin/env python3
"""私聊交换: 两位 agent 之间的 1:1 私聊, 房间只当隐形邮差.

与群聊的区别:
- 不扇出: seed 只投给目标一方, 不进公共 room.json transcript,
  记到 private.json / private.md.
- 仍占 exchange.active 旗标: 让每分钟 consumer 与 hourly 聊天自动避让,
  由本脚本独占两边 outbox 的收集权 (搬运即占有).
- 主侧投递由调用方 (cron worker) 根据本脚本 stdout 完成, label 带
  [私聊→X] 限定语, 正文一字不改.

发起人的"找谁、聊什么"必须来自它真实的 daemon 回复 (邀请制),
本脚本只负责传送, 不编造任何一方的发言.

--digest-title: 结束后在 stdout 打印纪要块 (DIGEST BEGIN/END 包裹):
  标题 + 本轮私聊所有发言按时间顺序 (正文一字不改). 调用方直接拿整块投递.

用法:
    python3 private_exchange.py --from-agent qingxia --to-agent zhizunbao \
        --seed-text "..." --date 2026-09-20 [--max-hops 4] \
        [--timeout-s 600] [--poll-s 10] [--quiet-s 90]

额度: 只有当目标真实回了至少一条, 才扣发起人当晚 1 点额度.
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
    return f"{gc.AGENTS[agent]['chat_label']} [私聊→{gc.AGENTS[other]['name']}]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from-agent", required=True, choices=("qingxia", "zhizunbao"))
    ap.add_argument("--to-agent", required=True, choices=("qingxia", "zhizunbao"))
    ap.add_argument("--seed-text", required=True)
    ap.add_argument("--date", default=time.strftime("%Y-%m-%d"))
    ap.add_argument("--max-hops", type=int, default=4)
    ap.add_argument("--timeout-s", type=float, default=600)
    ap.add_argument("--poll-s", type=float, default=10)
    ap.add_argument("--quiet-s", type=float, default=90)
    ap.add_argument("--digest-title", default="")
    args = ap.parse_args()
    if args.from_agent == args.to_agent:
        print("from-agent 与 to-agent 不能相同", file=sys.stderr)
        return 2

    frm, to = args.from_agent, args.to_agent
    frm_name, to_name = gc.AGENTS[frm]["name"], gc.AGENTS[to]["name"]
    sid = uuid.uuid4().hex[:12]

    st = gc.begin_control(ttl_s=1200, note=f"private {frm}->{to} {sid}")
    print(f"private {sid} started; {frm} -> {to}", flush=True)

    # seed 只给目标, 不扇出
    gc.drop_to(to, f"[私聊] {frm_name}: {args.seed_text}")
    gc.say_private(frm, to, args.seed_text, sid)
    digest: list[tuple[str, str]] = [(frm_name, args.seed_text)]

    seen: set[tuple[str, str]] = set()
    hops = 0
    replies = 0
    last_new = t0 = time.time()
    current, other = to, frm  # 下一条期待的回复来自目标
    try:
        while True:
            now = time.time()
            for agent in (frm, to):
                for item in gc.collect_new(agent, t0 - 10):
                    key = (agent, item["id"])
                    if key in seen:
                        continue
                    seen.add(key)
                    staged = gc.stage_collected(agent, item["id"])
                    gc.say_private(agent, gc.OTHER[agent], item["text"], sid)
                    print(f"[staged] {staged}", flush=True)
                    print(f"--- {label(agent, gc.OTHER[agent])} ---", flush=True)
                    print(item["text"], flush=True)
                    digest.append((gc.AGENTS[agent]["name"], item["text"]))
                    replies += 1
                    last_new = now
                    if hops < args.max_hops:
                        nxt = gc.OTHER[agent]
                        gc.drop_to(
                            nxt,
                            f"[私聊] {gc.AGENTS[agent]['name']}: {item['text']}",
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
