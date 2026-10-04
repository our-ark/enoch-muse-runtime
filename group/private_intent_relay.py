#!/usr/bin/env python3
"""Private-intent relay: turn "想和【X】说【...】" lines in an agent's
chat_outbox into real 1:1 private exchanges.

Why this exists: agents can only *say* things (chat_outbox). Historically
an agent's "想和【某人】说【…】" line inside a nightly self-check went
nowhere — the stats digest quoted it, but nobody delivered it, so it
never became a private chat. This relay closes that gap: an explicit
intent line IS the act of sending. Once the seed lands in the target's
chat_inbox (via private_exchange.py) and the target replies, it counts
as a private chat; private_exchange records it in private.json /
private.md and charges the nightly credit only when the target replied.

Modes:
  --scan-once
      Examine outbox messages for intents not handled before (state:
      $MUSE_GROUP_HOME/private_intent_state.json). At most one exchange
      is launched per run, detached, so a fast caller (the per-minute
      mailbox consumer) never blocks. Digests of finished exchanges are
      printed on later runs, exactly once. On first ever run the state
      is initialised to the current outbox snapshot (no history replay;
      use --deliver-intent for explicit backfill).
  --deliver-intent AGENT MESSAGE_ID
      Process one specific outbox message now (backfill / first test),
      through the same gates.
  --dry-run
      Report what would happen; no state writes, no launches.

Gates, in order: another exchange already active -> stay silent and
leave intents pending; sender out of nightly credits -> intent consumed
and reported as skipped; target unknown / self -> consumed, no launch;
target is the operator （紫霞） -> consumed, no launch (operator-bound
lines already surface through the normal consumer path).

Output protocol on stdout (for the calling worker):
  RELAY-LAUNCHED from=<agent> to=<agent>
  RELAY-SKIPPED reason=<why> from=<agent> to=<agent>
  RELAY-FAILED from=<agent> to=<agent>
  ===== DIGEST BEGIN ===== ... ===== DIGEST END =====   (verbatim digest)

Agent mailboxes come from group_ctl.AGENTS (MUSE_GROUP_<AGENT>_MAILBOX
environment overrides); this script adds the repo's src/ to
MUSE_GROUP_SRC_PATHS for the child exchange process so
group_ctl.drop_to can import our_ark_muse regardless of caller env.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import group_ctl as gc  # noqa: E402

NAME_TO_AGENT = {
    "青霞": "qingxia",
    "至尊宝": "zhizunbao",
    "白晶晶": "baijingjing",
    "唐三藏": "tangsanzang",
}
AGENT_CN = {v: k for k, v in NAME_TO_AGENT.items()}
OPERATOR_NAMES = {"紫霞", "zixia"}
INTENT_RE = re.compile(r"想和【\s*([^】\s]+)\s*】说【(.+?)】", re.S)

STATE_PATH = gc.GROUP_HOME / "private_intent_state.json"
DIGEST_DIR = gc.GROUP_HOME / "private_digests"
DIGEST_BEGIN = "===== DIGEST BEGIN ====="
DIGEST_END = "===== DIGEST END ====="

# Display-only label fixes for the user-facing digest (body text of the
# agents is never touched; group_ctl labels two agents in pinyin).
LABEL_FIXES = [
    ("**Qingxia**", "青霞"),
    ("**Zhizunbao**", "至尊宝"),
    ("[private→Qingxia]", "[private→青霞]"),
    ("[private→Zhizunbao]", "[private→至尊宝]"),
]


def load_state() -> tuple[dict, bool]:
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8")), False
        except ValueError:
            pass
    return {"seen_intents": [], "launches": []}, True


def save_state(state: dict) -> None:
    gc._atomic_write_json(STATE_PATH, state)


def outbox_items(agent: str) -> list[dict]:
    items = []
    for child in gc._outbox_files(agent):
        try:
            payload = json.loads(child.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        items.append({"id": child.stem, "text": text})
    return items


def find_intents(text: str) -> list[tuple[str, str]]:
    return [(m.group(1).strip(), m.group(2).strip()) for m in INTENT_RE.finditer(text)]


def iter_intents(state: dict):
    """Yield (agent, message_id, intent_idx, target_name, seed) for every
    intent not yet recorded in state, in ring order / arrival order."""
    seen = set(state.get("seen_intents", []))
    for agent in gc.GROUP_RING:
        for item in outbox_items(agent):
            for idx, (target, seed) in enumerate(find_intents(item["text"])):
                key = f"{agent}/{item['id']}/{idx}"
                if key not in seen:
                    yield agent, item["id"], idx, target, seed


def mark_seen(state: dict, agent: str, mid: str, idx: int) -> None:
    key = f"{agent}/{mid}/{idx}"
    if key not in state["seen_intents"]:
        state["seen_intents"].append(key)


def prune_state(state: dict) -> None:
    alive = set()
    for agent in gc.GROUP_RING:
        for item in outbox_items(agent):
            for idx in range(len(find_intents(item["text"]))):
                alive.add(f"{agent}/{item['id']}/{idx}")
    state["seen_intents"] = [k for k in state["seen_intents"] if k in alive]
    cutoff = time.time() - 7 * 86400
    state["launches"] = [
        l for l in state["launches"] if not (l.get("reported") and l.get("launched_at", 0) < cutoff)
    ]


def child_env() -> dict:
    env = dict(os.environ)
    paths = [str(REPO / "src")]
    old = env.get("MUSE_GROUP_SRC_PATHS", "")
    paths += old.split(os.pathsep) if old else list(gc.SRC_PATHS)
    # our_ark_muse.chat also needs our_ark_provider_kit, which lives in
    # the Enoch source tree the daemons run from ($ENOCH_SRC, default
    # ~/enoch-body). Include it when present; deployments with a
    # different layout can still override via MUSE_GROUP_SRC_PATHS.
    enoch_src = Path(os.environ.get("ENOCH_SRC") or (Path.home() / "enoch-body"))
    kit = enoch_src / "libraries" / "provider-kit" / "src"
    if kit.is_dir():
        paths.append(str(kit))
    env["MUSE_GROUP_SRC_PATHS"] = os.pathsep.join(dict.fromkeys(p for p in paths if p))
    return env


def launch(state: dict, frm: str, to: str, seed: str, dry_run: bool) -> str:
    lid = uuid.uuid4().hex[:12]
    if dry_run:
        return lid
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    log_path = DIGEST_DIR / f"{lid}.log"
    title = f"私聊 {AGENT_CN.get(frm, frm)}→{AGENT_CN.get(to, to)}"
    cmd = [
        sys.executable,
        str(HERE / "private_exchange.py"),
        "--from-agent", frm,
        "--to-agent", to,
        "--seed-text", seed,
        "--date", time.strftime("%Y-%m-%d"),
        "--max-hops", "4",
        "--timeout-s", "600",
        "--poll-s", "5",
        "--quiet-s", "90",
        "--digest-title", title,
    ]
    with open(log_path, "ab") as log:
        proc = subprocess.Popen(
            cmd, stdout=log, stderr=subprocess.STDOUT,
            start_new_session=True, cwd=str(HERE), env=child_env(),
        )
    state["launches"].append(
        {
            "lid": lid, "from": frm, "to": to, "pid": proc.pid,
            "log": str(log_path), "reported": False,
            "launched_at": time.time(),
        }
    )
    return lid


def process_intent(state, frm, mid, idx, target_name, seed, dry_run, launched_flag):
    """Apply gates to one intent. Returns True if an exchange was launched."""
    if target_name in OPERATOR_NAMES:
        mark_seen(state, frm, mid, idx)
        return False
    to = NAME_TO_AGENT.get(target_name)
    if to is None or to == frm:
        print(f"RELAY-SKIPPED reason=bad-target from={frm} to={target_name}")
        mark_seen(state, frm, mid, idx)
        return False
    if gc.credits_left(time.strftime("%Y-%m-%d"), frm) <= 0:
        print(f"RELAY-SKIPPED reason=no-credit from={frm} to={to}")
        mark_seen(state, frm, mid, idx)
        return False
    if launched_flag[0]:
        return False  # one launch per run; leave this intent pending
    launch(state, frm, to, seed, dry_run)
    mark_seen(state, frm, mid, idx)
    launched_flag[0] = True
    print(f"RELAY-LAUNCHED from={frm} to={to}")
    return True


def collect_digests(state: dict) -> None:
    for rec in state.get("launches", []):
        if rec.get("reported"):
            continue
        try:
            os.kill(rec["pid"], 0)
            continue  # still running
        except (ProcessLookupError, PermissionError, OSError):
            pass
        log = Path(rec["log"])
        text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
        if DIGEST_BEGIN in text and DIGEST_END in text:
            block = text[text.index(DIGEST_BEGIN): text.index(DIGEST_END) + len(DIGEST_END)]
            for old, new in LABEL_FIXES:
                block = block.replace(old, new)
            print(block)
        else:
            print(f"RELAY-FAILED from={rec['from']} to={rec['to']}")
        rec["reported"] = True


def scan_once(dry_run: bool) -> int:
    state, fresh = load_state()
    collect_digests(state)
    if fresh:
        # First run: snapshot everything as seen; history is never replayed
        # implicitly. Backfill goes through --deliver-intent.
        for agent, mid, idx, _t, _s in list(iter_intents(state)):
            mark_seen(state, agent, mid, idx)
        if not dry_run:
            save_state(state)
        print("RELAY-STATE-INITIALIZED")
        return 0
    if gc.active_exchange() is not None:
        # An exchange is in flight; stay silent and leave intents pending.
        if not dry_run:
            save_state(state)
        return 0
    launched_flag = [False]
    for agent, mid, idx, target, seed in list(iter_intents(state)):
        process_intent(state, agent, mid, idx, target, seed, dry_run, launched_flag)
    prune_state(state)
    if not dry_run:
        save_state(state)
    return 0


def deliver_intent(agent: str, mid: str, dry_run: bool) -> int:
    if agent not in gc.AGENTS:
        print(f"unknown agent {agent}", file=sys.stderr)
        return 2
    path = Path(gc.AGENTS[agent]["mailbox"]) / "chat_outbox" / f"{mid}.json"
    if not path.exists():
        print(f"no such outbox message: {path}", file=sys.stderr)
        return 2
    payload = json.loads(path.read_text(encoding="utf-8"))
    intents = find_intents(payload.get("text", ""))
    if not intents:
        print("no intent line in that message", file=sys.stderr)
        return 2
    state, _fresh = load_state()
    if gc.active_exchange() is not None:
        print("RELAY-DEFERRED reason=active-exchange")
        return 0
    launched_flag = [False]
    for idx, (target, seed) in enumerate(intents):
        process_intent(state, agent, mid, idx, target, seed, dry_run, launched_flag)
    if not dry_run:
        save_state(state)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scan-once", action="store_true")
    ap.add_argument("--deliver-intent", nargs=2, metavar=("AGENT", "MESSAGE_ID"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.deliver_intent:
        return deliver_intent(args.deliver_intent[0], args.deliver_intent[1], args.dry_run)
    return scan_once(args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
