#!/usr/bin/env python3
"""muse-group group chat room control script.

hub-and-spoke topology: the host is the room server. Two Enoch daemons each
read and write only their own mailbox (chat_inbox/chat_outbox); the room
fans messages out (fan-out) to both sides and collects their replies into a
shared transcript (room.json / room.md).

The host is a third-party participant: its message text is written by the
caller and passed in (not a daemon reply); it may open and interject, and it
costs no hop budget. The host's display name is configured via the
MUSE_GROUP_HOST_NAME environment variable (set to Zixia in this deployment);
without it, the room has agents only.

Anti-duplication:
- exchange.active flag: while a group exchange is in progress, both mailbox
  consumers and hourly-enoch-chat skip their own delivery/collection actions
  (see the "group-yield" section of their cron task texts), and the group
  orchestrator owns chat_outbox collection exclusively. The flag carries a
  TTL (15 minutes); after an abnormal orchestrator exit, crons resume normal
  delivery automatically.
- Each outbox reply is collected exactly once: seen-set + .delivered marker.

Anti-loop:
- At most max_hops agent->agent forwards per exchange (default 3); after
  that, replies are recorded but not forwarded.

Portability (environment variables, defaults used when unset):
- MUSE_GROUP_HOME: room state directory (room.json/room.md/staged/exchange.active),
  default ~/workspace/muse-group.
- MUSE_GROUP_QINGXIA_MAILBOX / MUSE_GROUP_ZHIZUNBAO_MAILBOX: the two mailboxes.
- MUSE_GROUP_SRC_PATHS: colon-separated our_ark_muse import paths.
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path

GROUP_HOME = Path(
    os.environ.get("MUSE_GROUP_HOME") or (Path.home() / "workspace" / "muse-group")
)
ROOM_JSON = GROUP_HOME / "room.json"
ROOM_MD = GROUP_HOME / "room.md"
ACTIVE = GROUP_HOME / "exchange.active"
STAGED = GROUP_HOME / "staged"
TTL_S = 15 * 60

AGENTS = {
    "qingxia": {
        "mailbox": os.environ.get(
            "MUSE_GROUP_QINGXIA_MAILBOX", "/home/hatch/workspace/muse-enoch/mailbox"
        ),
        "name": "Qingxia",
        "chat_label": "⚔️ **Qingxia**",
    },
    "zhizunbao": {
        "mailbox": os.environ.get(
            "MUSE_GROUP_ZHIZUNBAO_MAILBOX",
            "/home/hatch/workspace/muse-zhizunbao/mailbox",
        ),
        "name": "Zhizunbao",
        "chat_label": "🐵 **Zhizunbao**",
    },
    "baijingjing": {
        "mailbox": os.environ.get(
            "MUSE_GROUP_BAIJINGJING_MAILBOX",
            "/home/hatch/workspace/muse-baijingjing/mailbox",
        ),
        "name": "白晶晶",
        "chat_label": "💀 **白晶晶**",
    },
    "tangsanzang": {
        "mailbox": os.environ.get(
            "MUSE_GROUP_TANGSANZANG_MAILBOX",
            "/home/hatch/workspace/muse-tangsanzang/mailbox",
        ),
        "name": "唐三藏",
        "chat_label": "📿 **唐三藏**",
    },
}
GROUP_RING = ["qingxia", "zhizunbao", "baijingjing", "tangsanzang"]


def group_next(agent: str) -> str:
    """Next agent in the room's relay ring (room speaks in ring order)."""
    i = GROUP_RING.index(agent)
    return GROUP_RING[(i + 1) % len(GROUP_RING)]

# The room host's display name, configured by the caller. Host message text is
# written by the caller and passed in (not a daemon reply); it is recorded in
# the transcript with kind="host" and costs no hop budget.
HOST_NAME = os.environ.get("MUSE_GROUP_HOST_NAME", "")

_src_paths = os.environ.get("MUSE_GROUP_SRC_PATHS")
SRC_PATHS = (
    _src_paths.split(os.pathsep)
    if _src_paths
    else [
        "/home/hatch/workspace/muse-enoch/src",
        "/home/hatch/workspace/enoch-experiment/libraries/provider-kit/src",
    ]
)


def _ensure_paths() -> None:
    for p in SRC_PATHS:
        if p not in sys.path:
            sys.path.insert(0, p)


def drop_to(agent: str, text: str) -> int:
    """Drop a message into the given agent's chat_inbox; return its seq."""
    _ensure_paths()
    os.environ["ENOCH_MUSE_MAILBOX"] = AGENTS[agent]["mailbox"]
    from our_ark_muse.chat import drop_chat_message

    return drop_chat_message(text)


def _atomic_write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _load_room() -> dict:
    if ROOM_JSON.exists():
        try:
            return json.loads(ROOM_JSON.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"room": "muse-group", "created_at": time.time(), "transcript": []}


def _append_transcript(entry: dict) -> None:
    room = _load_room()
    room["transcript"].append(entry)
    _atomic_write_json(ROOM_JSON, room)
    line = (
        f"\n## {time.strftime('%Y-%m-%d %H:%M', time.localtime(entry['t']))} "
        f"[{entry['speaker']}] ({entry['exchange_id']})\n\n{entry['text']}\n"
    )
    with ROOM_MD.open("a", encoding="utf-8") as f:
        f.write(line)


def say(speaker: str, text: str, kind: str, exchange_id: str) -> None:
    _append_transcript(
        {
            "t": time.time(),
            "speaker": speaker,
            "text": text,
            "exchange_id": exchange_id,
            "kind": kind,  # human | host | agent
        }
    )


def active_exchange() -> dict | None:
    """The in-progress exchange; None when none or expired."""
    if not ACTIVE.exists():
        return None
    try:
        st = json.loads(ACTIVE.read_text(encoding="utf-8"))
    except ValueError:
        return None
    if time.time() - st.get("started_at", 0) > st.get("ttl_s", TTL_S):
        return None
    return st


def start_exchange(speaker: str, text: str) -> dict:
    """Open a group exchange round: write the flag, record the transcript,
    fan the first message out to both sides."""
    if active_exchange():
        raise RuntimeError("a group exchange is already in progress; wait for it to end")
    eid = uuid.uuid4().hex[:12]
    now = time.time()
    members = ", ".join(
        [n for n in [HOST_NAME] + [a["name"] for a in AGENTS.values()] if n]
    )
    framing = (
        f"[group] New room topic. Room members: {members}. "
        "Lines starting with [group] are room messages: just chat, no actions "
        "needed, reply like you normally would."
    )
    first = f"{framing}\n[group] {speaker}: {text}"
    seqs = {agent: drop_to(agent, first) for agent in AGENTS}
    _atomic_write_json(
        ACTIVE,
        {
            "exchange_id": eid,
            "started_at": now,
            "ttl_s": TTL_S,
            "seed_seqs": seqs,
            "hops_used": 0,
        },
    )
    say(
        speaker,
        text,
        "agent"
        if speaker in {a["name"] for a in AGENTS.values()}
        else ("host" if HOST_NAME and speaker == HOST_NAME else "human"),
        eid,
    )
    return {"exchange_id": eid, "started_at": now, "seed_seqs": seqs}


def relay(from_agent: str, text: str) -> int:
    """Forward from_agent's room reply to the next agent in the ring."""
    other = group_next(from_agent)
    name = AGENTS[from_agent]["name"]
    seq = drop_to(other, f"[group] {name}: {text}")
    st = active_exchange()
    if st:
        st["hops_used"] = st.get("hops_used", 0) + 1
        _atomic_write_json(ACTIVE, st)
    return seq


def fanout_room_message(speaker: str, text: str, exchange_id: str) -> dict:
    """Room host/participant speaks: record the transcript and fan one
    message out to each daemon.

    The message text is written by the caller and passed in, not a daemon
    reply. It carries a "[group] <speaker>:" prefix, which both daemons treat
    as an ordinary room message. The speaker is recorded as kind="host" when
    it matches HOST_NAME, otherwise kind="human". Costs no hop budget.
    """
    msg = f"[group] {speaker}: {text}"
    seqs = {agent: drop_to(agent, msg) for agent in AGENTS}
    say(speaker, text, "host" if HOST_NAME and speaker == HOST_NAME else "human", exchange_id)
    return seqs


def _outbox_files(agent: str):
    outbox = Path(AGENTS[agent]["mailbox"]) / "chat_outbox"
    if not outbox.is_dir():
        return []
    files = []
    for child in outbox.iterdir():
        # Only take atomically-written .json files; skip dot files and markers.
        # Note: .delivered markers are no longer the collection basis — moving
        # (move) is ownership, so an improvised consumer marker can't make the
        # room miss a reply. The mtime window is set by the caller.
        if not child.is_file() or child.suffix != ".json" or child.name.startswith("."):
            continue
        if child.name.endswith(".delivered.json"):
            continue
        files.append(child)
    return sorted(files, key=lambda p: p.stat().st_mtime)


def collect_new(agent: str, since_ts: float):
    """Collect this agent's outbox replies produced after since_ts (ignoring
    markers). Each item carries the outbox file's mtime as its arrival time."""
    out = []
    for child in _outbox_files(agent):
        try:
            mt = child.stat().st_mtime
        except OSError:
            continue
        if mt < since_ts:
            continue
        try:
            payload = json.loads(child.read_text(encoding="utf-8"))
        except ValueError:
            continue
        text = payload.get("text")
        if not isinstance(text, str) or not text.strip():
            continue
        out.append({"id": child.stem, "mtime": mt, "text": text})
    return out


def merge_collected(new_items: list[tuple[str, dict]]) -> list[tuple[str, dict]]:
    """Merge freshly collected (agent, item) pairs into true arrival order.

    The drivers poll the two outboxes in a fixed agent order, which is not
    the order the replies actually arrived in. Sort by the outbox file mtime
    so the transcript and digest reflect real chronological order instead of
    the round-robin collection order.
    """
    return sorted(new_items, key=lambda kv: kv[1].get("mtime", 0.0))


def stage_collected(agent: str, mid: str) -> Path:
    """Move a collected reply into the room's staged archive (move is
    ownership, preventing consumer re-delivery).

    The daemon writes its outbox with an atomic rename, so the move cannot
    tear a file; the daemon never reads the file back after writing.
    """
    dest_dir = STAGED / agent
    dest_dir.mkdir(parents=True, exist_ok=True)
    src = Path(AGENTS[agent]["mailbox"]) / "chat_outbox" / f"{mid}.json"
    dest = dest_dir / f"{mid}.json"
    if src.exists():
        os.replace(src, dest)
    return dest


def mark_delivered(agent: str, mid: str, exchange_id: str) -> None:
    marker = Path(AGENTS[agent]["mailbox"]) / "chat_outbox" / f"{mid}.delivered"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(
        f"group-exchange {exchange_id} "
        f"{time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime())}\n",
        encoding="utf-8",
    )


def end_exchange() -> dict | None:
    st = active_exchange()
    if ACTIVE.exists():
        ACTIVE.unlink()
    return st


def format_digest(title: str, lines: list[tuple]) -> str:
    """Compile one exchange round's (label, text) pairs into a digest block,
    in chronological order.

    Each entry is (label, text) or (label, text, ts). When a timestamp is
    present, entries are sorted by it (earliest first) so replies from both
    sides appear in real arrival order, not collection order. The body text is
    never modified — only the title and the [label] prefix are added, and the
    label is kept verbatim. The caller (cron worker / manual) fills
    --digest-title with the session and topic, then delivers the whole
    DIGEST BEGIN/END block from stdout as-is.
    """
    rows: list[tuple[str, str, float]] = []
    for ln in lines:
        if len(ln) == 3:
            rows.append((ln[0], ln[1], ln[2]))
        else:
            rows.append((ln[0], ln[1], 0.0))
    rows.sort(key=lambda r: r[2])
    parts = [title.strip(), ""]
    for tag, text, _ in rows:
        parts.append(f"[{tag}] {text}")
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def print_digest(title: str, lines: list[tuple]) -> None:
    print("===== DIGEST BEGIN =====", flush=True)
    print(format_digest(title, lines), flush=True)
    print("===== DIGEST END =====", flush=True)


# ---------------------------------------------------------------------------
# Private chat / nightly credits / group host rotation
# ---------------------------------------------------------------------------

PRIVATE_JSON = GROUP_HOME / "private.json"
PRIVATE_MD = GROUP_HOME / "private.md"
CREDITS_JSON = GROUP_HOME / "private_credits.json"
HOST_JSON = GROUP_HOME / "group_host.json"
NIGHTLY_CREDITS = 2  # private-chat credits per agent per night


def begin_control(ttl_s: int = 1800, note: str = "") -> dict:
    """Hold the flag only, no fan-out: for the invitation phase / private
    exchanges, so consumers auto-skip."""
    if active_exchange():
        raise RuntimeError("a group exchange is already in progress; wait for it to end")
    eid = uuid.uuid4().hex[:12]
    st = {
        "exchange_id": eid,
        "started_at": time.time(),
        "ttl_s": ttl_s,
        "seed_seqs": {},
        "hops_used": 0,
        "note": note,
        "control_only": True,
    }
    _atomic_write_json(ACTIVE, st)
    return st


def say_private(from_agent: str, to_agent: str, text: str, session_id: str) -> None:
    """Record the private-chat transcript (separate from the public room.json)."""
    data: dict = {"session": "private", "transcript": []}
    if PRIVATE_JSON.exists():
        try:
            data = json.loads(PRIVATE_JSON.read_text(encoding="utf-8"))
        except ValueError:
            pass
    data["transcript"].append(
        {
            "t": time.time(),
            "from": from_agent,
            "to": to_agent,
            "text": text,
            "session_id": session_id,
        }
    )
    _atomic_write_json(PRIVATE_JSON, data)
    line = (
        f"\n## {time.strftime('%Y-%m-%d %H:%M', time.localtime())} "
        f"[private {from_agent}->{to_agent}] ({session_id})\n\n{text}\n"
    )
    with PRIVATE_MD.open("a", encoding="utf-8") as f:
        f.write(line)


def _load_credits() -> dict:
    if CREDITS_JSON.exists():
        try:
            return json.loads(CREDITS_JSON.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {}


def credits_left(date_str: str, agent: str) -> int:
    return _load_credits().get(date_str, {}).get(agent, NIGHTLY_CREDITS)


def use_credit(date_str: str, agent: str) -> int:
    data = _load_credits()
    day = data.setdefault(date_str, {})
    left = day.get(agent, NIGHTLY_CREDITS)
    if left <= 0:
        raise RuntimeError(f"{agent} has no private-chat credits left tonight ({date_str})")
    day[agent] = left - 1
    _atomic_write_json(CREDITS_JSON, data)
    return left - 1


def next_host() -> str:
    """Group host rotation: qingxia -> zhizunbao -> baijingjing -> tangsanzang -> ..."""
    order = ["qingxia", "zhizunbao", "baijingjing", "tangsanzang"]
    nxt = "qingxia"
    if HOST_JSON.exists():
        try:
            nxt = json.loads(HOST_JSON.read_text(encoding="utf-8")).get("next", nxt)
        except ValueError:
            pass
    if nxt not in order:
        nxt = "qingxia"
    following = order[(order.index(nxt) + 1) % len(order)]
    _atomic_write_json(HOST_JSON, {"next": following})
    return nxt


def _cmd(argv: list[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(
            "usage: group_ctl.py active | start --speaker S --text T | "
            "drop --agent A --text T | collect --agent A --since TS | "
            "mark --agent A --id ID --exchange EID | say --speaker S --kind K --exchange EID --text T | end | "
            "hold [--ttl N] [--note T] | say-private --from A --to B --session S --text T | "
            "credits --date D --agent A | use-credit --date D --agent A | next-host"
        )
        return 0
    cmd = argv[0]
    args = {}
    i = 1
    while i < len(argv):
        if argv[i].startswith("--"):
            args[argv[i][2:]] = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
        else:
            i += 1
    if cmd == "active":
        st = active_exchange()
        print(json.dumps(st, ensure_ascii=False) if st else "none")
        return 0 if st else 1
    if cmd == "start":
        print(json.dumps(start_exchange(args["speaker"], args["text"]), ensure_ascii=False))
        return 0
    if cmd == "drop":
        print(drop_to(args["agent"], args["text"]))
        return 0
    if cmd == "collect":
        items = collect_new(args["agent"], float(args["since"]))
        print(json.dumps(items, ensure_ascii=False))
        return 0
    if cmd == "mark":
        mark_delivered(args["agent"], args["id"], args["exchange"])
        print("ok")
        return 0
    if cmd == "say":
        say(args["speaker"], args["text"], args["kind"], args["exchange"])
        print("ok")
        return 0
    if cmd == "end":
        print(json.dumps(end_exchange(), ensure_ascii=False))
        return 0
    if cmd == "hold":
        st = begin_control(
            ttl_s=int(args.get("ttl", 1800)), note=args.get("note", "")
        )
        print(json.dumps(st, ensure_ascii=False))
        return 0
    if cmd == "say-private":
        say_private(args["from"], args["to"], args["text"], args["session"])
        print("ok")
        return 0
    if cmd == "credits":
        print(credits_left(args["date"], args["agent"]))
        return 0
    if cmd == "use-credit":
        print(use_credit(args["date"], args["agent"]))
        return 0
    if cmd == "next-host":
        print(next_host())
        return 0
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_cmd(sys.argv[1:]))
