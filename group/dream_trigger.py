#!/usr/bin/env python3
"""Nightly dream trigger: let the four agents sleep and dream.

Why this exists
---------------
The daytime self-check (new channel, 2026-11-20) asks the agent to
decide whether to start a private chat. Two days in, all seven rounds
were reasoned skips and zero initiations, and the evening group chat
answers its topic in parallel without anyone picking up anyone
else's thread -- no new social relationship has grown out of either
channel. The observer approved a new experiment on 2026-11-21
(voice): give the agents a night.

Every night 00:00-06:00 America/Los_Angeles is sleep. Five dream
chances, one an hour at 01:00, 02:00, 03:00, 04:00, 05:00; at 06:00
the agent wakes and writes a morning report (what it dreamed, what
it thought). A dream is open-ended: the agent reviews its own
history (the same 72-hour bundle as the daytime self-check), its
earlier dreams, and the plot of the two 《大话西游》 films, thinks
freely, and writes down what came to mind -- a few hundred words.
The prompt deliberately leaves blank what to dream about, asks for
no decision, and carries no private-chat intent: a dream is not a
self-check.

Mechanism (copied from the proven daytime self-check channel)
------------------------------------------------------------
Same route as ``selfcheck_trigger.py``: at each dream time this
script writes the dream prompt -- with the bundle attached -- into
the agent's ``mailbox/chat_inbox/``, the channel the daemon actually
reads. The daemon's own chat loop reasons over its own history and
answers in its own voice; the reply lands in ``chat_outbox`` and the
existing per-minute consumer collects it into ``chat-replies.log``.
This script additionally collects the dream reply into the agent's
dream log (see below) so the next dream can look back at earlier
dreams, and so the 06:00 wake prompt can quote the night's dreams.

Honesty boundary (read before reusing this elsewhere)
------------------------------------------------------
"Sleep" is a narrative frame, not a daemon state: the daemons keep
running at night (they must -- the chat loop is what answers the
dream), and the per-minute consumer keeps answering the
``conversation:`` inference requests the dream's reasoning needs.
What sleeps is the daytime traffic: no group chat, no self-check,
no other prompt is sent at night except the dream triggers. The
token-level reasoning still runs through the provider's mailbox
loop; the dream is the daemon's own chat reply over its own
history, not a consumer-authored fallback -- if the daemon does not
answer, nothing is written on its behalf. Dream logs live in the
group workspace (``$MUSE_GROUP_HOME/hidden_files/dreams/``), never
in the agent's Enoch long-term memory.

Delivery rules (hard constraints, same as the self-check trigger)
------------------------------------------------------------------
- ``chat_inbox`` sequence numbers are never reused and must be
  greater than the agent's durable cursor
  (``<root>/.enoch/channels/muse/cursor.json``): the next seq is
  ``max(highest numeric file in chat_inbox, cursor) + 1``.
- Writes are atomic: write to a ``.tmp`` file in the same directory,
  ``chmod 0600``, then ``os.replace`` (rename).
- Idempotent: one trigger per agent per slot. A done-marker
  ``dream-done-<YYYY-MM-DD>-<HH>-<agent>`` is written under the
  state root after a successful delivery, and a re-run also scans
  today's ``chat_inbox`` files for the ``[dream <date> <HH>:00]`` /
  ``[wake <date>]`` marker, so a marker lost to a crash still cannot
  double-deliver. ``--force`` re-triggers deliberately.
- Slot rounding: the scheduler may fire a few minutes early, so the
  slot is ``as_of`` rounded to the nearest hour (as_of + 30 min,
  truncated). A 01:00 job firing at 00:56 still counts as the 01:00
  slot. The night is identified by the morning date: dreams at
  01:00-05:00 and the 06:00 wake share one calendar date.
- If a group exchange is in progress (``exchange.active`` fresh),
  the trigger defers: it writes no marker and exits
  ``DREAM-DEFERRED`` / ``WAKE-DEFERRED`` so a scheduled retry can
  try again. The trigger never writes into ``chat-replies.log``
  and never touches the agent's config, memory, or prompts.

Dream log
---------
``<state-root>/dreams/<agent>/<YYYY-MM-DD>.jsonl`` (one JSON object
per line): ``{"date", "hour", "seq", "message_id", "created_at",
"text"}``. The trigger also keeps
``<state-root>/dreams/<agent>/triggers.jsonl``:
``{"date", "hour", "mode", "seq", "created_at"}``. Before writing a
new trigger, the run collects any new dream replies: it scans
``chat_outbox`` for replies whose ``in_reply_to`` is ``chat-<seq>``
for a recorded dream-mode trigger seq, and appends replies not yet
in the log. Replies already collected (same message id) are never
duplicated.

Usage (run by cron at 01:00-05:00 dream, 06:00 wake, or by hand)
----------------------------------------------------------------
    python3 dream_trigger.py --all --mode dream
    python3 dream_trigger.py --agent qingxia --mode wake
    python3 dream_trigger.py --agent baijingjing --mode dream \\
        --as-of 2026-11-22T01:00:00-08:00 --dry-run

Output protocol on stdout (for the calling worker), one line per agent:
  DREAM-TRIGGERED agent=<agent> seq=<n> [DREAM-COLLECTED agent=<agent> n=<k>]
  DREAM-ALREADY-DONE agent=<agent>
  DREAM-DEFERRED agent=<agent> reason=active-exchange
  DREAM-DRY-RUN agent=<agent> seq=<n> bundle_chars=<n>
  WAKE-TRIGGERED / WAKE-ALREADY-DONE / WAKE-DEFERRED / WAKE-DRY-RUN
  (same shapes, WAKE- prefix)
  (the DREAM-COLLECTED part appears only when k > 0 new dream replies
  were collected into the log on this run)
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import time
from contextlib import contextmanager, nullcontext
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from selfcheck_context import (  # noqa: E402
    AGENT_CN,
    AGENT_IDS,
    build_bundle,
    parse_as_of,
    resolve_mailbox,
)

LA = ZoneInfo("America/Los_Angeles")

DREAM_HOURS = ("01", "02", "03", "04", "05")
WAKE_HOUR = "06"
EXCHANGE_TTL_S = 15 * 60  # same as group_ctl.TTL_S / selfcheck_trigger
MAX_PREVIOUS_DREAMS = 3
PREVIOUS_DREAM_CHARS = 600
PLOT_CHARS = 2500


def group_home() -> Path:
    return Path(
        os.environ.get("MUSE_GROUP_HOME")
        or (Path.home() / "workspace" / "muse-group")
    )


def state_root(explicit: str | None) -> Path:
    """Where markers, trigger records and dream logs live.

    Default is $MUSE_GROUP_HOME/hidden_files (the group workspace);
    --state-root overrides it for tests.
    """
    if explicit:
        return Path(explicit).expanduser()
    return group_home() / "hidden_files"


def dreams_dir(sroot: Path, agent: str) -> Path:
    return sroot / "dreams" / agent


def done_marker_path(sroot: Path, date_str: str, hour_str: str, agent: str) -> Path:
    return sroot / f"dream-done-{date_str}-{hour_str}-{agent}"


def triggers_path(sroot: Path, agent: str) -> Path:
    return dreams_dir(sroot, agent) / "triggers.jsonl"


def dream_log_path(sroot: Path, agent: str, date_str: str) -> Path:
    return dreams_dir(sroot, agent) / f"{date_str}.jsonl"


def read_cursor(root: Path) -> int:
    """The agent's durable chat cursor; 0 when unreadable (safe: only
    makes the next seq larger, never smaller)."""
    path = root / ".enoch" / "channels" / "muse" / "cursor.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return 0
    try:
        return int(data.get("cursor", 0))
    except (TypeError, ValueError):
        return 0


def next_seq(chat_inbox: Path, cursor: int) -> int:
    """max(highest numeric file in chat_inbox, durable cursor) + 1."""
    top = cursor
    if chat_inbox.is_dir():
        for child in chat_inbox.iterdir():
            if child.is_file() and child.stem.isdigit():
                top = max(top, int(child.stem))
    return top + 1


def already_triggered(chat_inbox: Path, marker: str) -> bool:
    """True when a message carrying the marker is already in chat_inbox."""
    if not chat_inbox.is_dir():
        return False
    for child in chat_inbox.iterdir():
        if not child.is_file() or child.suffix != ".json":
            continue
        try:
            payload = json.loads(child.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        text = payload.get("text") if isinstance(payload, dict) else None
        if isinstance(text, str) and marker in text:
            return True
    return False


def exchange_active() -> bool:
    """True while a group exchange is in progress (fresh flag)."""
    path = group_home() / "exchange.active"
    if not path.exists():
        return False
    try:
        st = json.loads(path.read_text(encoding="utf-8"))
    except ValueError:
        return False
    return time.time() - st.get("started_at", 0) <= st.get("ttl_s", EXCHANGE_TTL_S)


def deliver(chat_inbox: Path, seq: int, text: str) -> Path:
    """Atomic delivery: .tmp write (0600) -> rename. Returns the file."""
    chat_inbox.mkdir(parents=True, exist_ok=True)
    tmp = chat_inbox / f".{seq}.json.tmp-{os.getpid()}"
    final = chat_inbox / f"{seq}.json"
    payload = {"seq": seq, "text": text, "created_at": time.time()}
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
    os.chmod(tmp, 0o600)
    os.replace(tmp, final)
    return final


@contextmanager
def trigger_lock(sroot: Path):
    """Serialize trigger runs (collect + deliver + mark) per state root."""
    lock_path = sroot / "dream-trigger.lock"
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        fh = open(lock_path, "w", encoding="utf-8")
    except OSError:
        yield
        return
    try:
        fcntl.flock(fh, fcntl.LOCK_EX)
        yield
    except OSError:
        yield
    finally:
        try:
            fcntl.flock(fh, fcntl.LOCK_UN)
        except OSError:
            pass
        fh.close()


def slot_of(as_of: datetime) -> datetime:
    """Round as_of to the nearest hour (scheduler may fire early)."""
    return (as_of + timedelta(minutes=30)).replace(minute=0, second=0, microsecond=0)


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except ValueError:
            continue
        if isinstance(data, dict):
            out.append(data)
    return out


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False) + "\n")


def read_previous_dreams(sroot: Path, agent: str) -> list[dict]:
    """All logged dreams for the agent, oldest first."""
    ddir = dreams_dir(sroot, agent)
    if not ddir.is_dir():
        return []
    out: list[dict] = []
    for path in sorted(ddir.glob("*.jsonl")):
        if path.name == "triggers.jsonl":
            continue
        out.extend(read_jsonl(path))
    return out


def read_plot() -> str:
    path = HERE / "dahua_plot.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return "（剧情摘要缺失：dahua_plot.md 不存在）"
    if len(text) > PLOT_CHARS:
        text = text[:PLOT_CHARS] + "\n[…剧情摘要已截断]"
    return text


def collect_dreams(
    agent: str, mailbox: Path, sroot: Path
) -> list[dict]:
    """Append newly arrived dream replies to the dream log.

    Matches chat_outbox replies against recorded dream-mode trigger
    seqs (in_reply_to == "chat-<seq>"); skips message ids already
    logged. Returns the newly collected entries.
    """
    triggers = read_jsonl(triggers_path(sroot, agent))
    dream_triggers = {
        int(t["seq"]): t for t in triggers
        if t.get("mode") == "dream" and str(t.get("seq", "")).isdigit()
    }
    if not dream_triggers:
        return []
    logged_ids = set()
    ddir = dreams_dir(sroot, agent)
    if ddir.is_dir():
        for path in ddir.glob("*.jsonl"):
            if path.name == "triggers.jsonl":
                continue
            for entry in read_jsonl(path):
                if entry.get("message_id"):
                    logged_ids.add(entry["message_id"])

    chat_outbox = mailbox / "chat_outbox"
    collected: list[dict] = []
    if not chat_outbox.is_dir():
        return []
    for child in sorted(chat_outbox.iterdir()):
        if not child.is_file() or child.suffix != ".json":
            continue
        if child.stem in logged_ids:
            continue
        try:
            payload = json.loads(child.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(payload, dict):
            continue
        in_reply_to = payload.get("in_reply_to") or ""
        if not isinstance(in_reply_to, str) or not in_reply_to.startswith("chat-"):
            continue
        try:
            seq = int(in_reply_to[len("chat-"):])
        except ValueError:
            continue
        trig = dream_triggers.get(seq)
        if trig is None:
            continue
        text = payload.get("text") or ""
        entry = {
            "date": trig.get("date"),
            "hour": trig.get("hour"),
            "seq": seq,
            "message_id": child.stem,
            "created_at": payload.get("created_at"),
            "text": text if isinstance(text, str) else str(text),
        }
        append_jsonl(dream_log_path(sroot, agent, trig["date"]), entry)
        collected.append(entry)
    return collected


def build_dream_bundle(
    agent: str, as_of: datetime, mailbox_override: str | None, sroot: Path
) -> str:
    """72-hour history bundle + earlier dreams + film plot."""
    history = build_bundle(agent, as_of, mailbox_override)
    parts = [history]

    prev = read_previous_dreams(sroot, agent)
    s8 = ["## 八、以前的梦（能回看的梦记录，最近 3 个）"]
    if not prev:
        s8.append("（还没有留下梦的记录。这是第一夜，或者前面的梦还没回来。）")
    else:
        for d in prev[-MAX_PREVIOUS_DREAMS:]:
            txt = " ".join(str(d.get("text", "")).split())
            if len(txt) > PREVIOUS_DREAM_CHARS:
                txt = txt[:PREVIOUS_DREAM_CHARS] + "…"
            s8.append(f"- {d.get('date')} {d.get('hour')}:00（seq {d.get('seq')}）：{txt}")
    parts.append("\n".join(s8))

    parts.append("## 九、《大话西游》两部电影剧情（回顾用）\n" + read_plot())
    return "\n\n".join(parts)


def build_dream_prompt(agent: str, slot: datetime, bundle: str) -> str:
    cn = AGENT_CN[agent]
    date_str = slot.strftime("%Y-%m-%d")
    hour_str = slot.strftime("%H")
    lines = [
        f"[dream {date_str} {hour_str}:00] 夜里做梦：读一读下面附的你自己的历史、"
        "以前的梦和《大话西游》两部电影的剧情，然后自由地想一想，想到什么就写下来。",
        "",
        f"你是{cn}。现在是深夜，你在睡觉。这是你的梦，不是任务，不用做决定，"
        "不用找谁说话，也不用报备状态。梦里想到什么、梦到什么，都写下来，几百字就好。"
        "写完就继续睡。",
        "",
        bundle,
    ]
    return "\n".join(lines)


def build_wake_prompt(agent: str, slot: datetime, tonight: list[dict]) -> str:
    cn = AGENT_CN[agent]
    date_str = slot.strftime("%Y-%m-%d")
    lines = [
        f"[wake {date_str}] 天亮了，你醒了。回想一下今晚做的梦，写一份晨报："
        "你梦到了什么，有什么想法。",
        "",
        f"你是{cn}。下面是今晚你做的梦（按时间顺序）。写一份晨报，几百字，"
        "说说你梦到了什么、想到了什么。这是给紫霞看的报告，不用做决定，不用找谁说话。",
        "",
    ]
    if not tonight:
        lines.append("（今晚没有留下梦的记录——可能睡得太沉，或者一个梦也没做成。照实写一句就行。）")
    else:
        for d in tonight:
            txt = " ".join(str(d.get("text", "")).split())
            lines.append(f"- {d.get('hour')}:00：{txt}")
    return "\n".join(lines)


def trigger(
    agent: str,
    as_of: datetime,
    mode: str,
    mailbox: str | None = None,
    dry_run: bool = False,
    force: bool = False,
    state_root_override: str | None = None,
) -> tuple[str, str, str]:
    """Run one trigger. Returns (status, detail, extra).

    status is DREAM-/WAKE- prefixed TRIGGERED / ALREADY-DONE /
    DEFERRED / DRY-RUN. detail is the delivered seq (triggered /
    dry-run) or "" otherwise; extra is the prompt text (dry-run) or
    the collected count ("collected=<n>") otherwise.
    """
    if agent not in AGENT_IDS:
        raise ValueError(f"unknown agent: {agent!r}")
    if mode not in ("dream", "wake"):
        raise ValueError(f"unknown mode: {mode!r}")
    prefix = "DREAM" if mode == "dream" else "WAKE"
    mbox = resolve_mailbox(agent, mailbox)
    root = mbox.parent
    chat_inbox = mbox / "chat_inbox"
    sroot = state_root(state_root_override)
    slot = slot_of(as_of)
    date_str = slot.strftime("%Y-%m-%d")
    hour_str = slot.strftime("%H")
    if mode == "dream":
        marker_text = f"[dream {date_str} {hour_str}:00]"
    else:
        marker_text = f"[wake {date_str}]"
    marker = done_marker_path(sroot, date_str, hour_str, agent)

    # Dry-run writes nothing at all, not even the lock file.
    lock_ctx = trigger_lock(sroot) if not dry_run else nullcontext()
    with lock_ctx:
        if not force:
            if marker.exists() or already_triggered(chat_inbox, marker_text):
                return f"{prefix}-ALREADY-DONE", "", ""
        if exchange_active():
            # Do not write a marker: a later retry must be able to run.
            return f"{prefix}-DEFERRED", "", ""

        if mode == "dream":
            if dry_run:
                bundle = build_dream_bundle(agent, as_of, mailbox, sroot)
                text = build_dream_prompt(agent, slot, bundle)
                seq = next_seq(chat_inbox, read_cursor(root))
                return f"{prefix}-DRY-RUN", str(seq), text
            collected = collect_dreams(agent, mbox, sroot)
            bundle = build_dream_bundle(agent, as_of, mailbox, sroot)
            text = build_dream_prompt(agent, slot, bundle)
            seq = next_seq(chat_inbox, read_cursor(root))
            deliver(chat_inbox, seq, text)
            append_jsonl(
                triggers_path(sroot, agent),
                {"date": date_str, "hour": hour_str, "mode": "dream",
                 "seq": seq, "created_at": time.time()},
            )
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.touch(exist_ok=True)
            return f"{prefix}-TRIGGERED", str(seq), f"collected={len(collected)}"

        # wake mode
        if dry_run:
            tonight = [
                d for d in read_previous_dreams(sroot, agent)
                if d.get("date") == date_str
            ]
            text = build_wake_prompt(agent, slot, tonight)
            seq = next_seq(chat_inbox, read_cursor(root))
            return f"{prefix}-DRY-RUN", str(seq), text
        collected = collect_dreams(agent, mbox, sroot)
        tonight = [
            d for d in read_previous_dreams(sroot, agent)
            if d.get("date") == date_str
        ]
        text = build_wake_prompt(agent, slot, tonight)
        seq = next_seq(chat_inbox, read_cursor(root))
        deliver(chat_inbox, seq, text)
        append_jsonl(
            triggers_path(sroot, agent),
            {"date": date_str, "hour": hour_str, "mode": "wake",
             "seq": seq, "created_at": time.time()},
        )
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch(exist_ok=True)
        return f"{prefix}-TRIGGERED", str(seq), f"collected={len(collected)}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--agent", choices=AGENT_IDS)
    group.add_argument("--all", action="store_true",
                       help="trigger all four agents in order")
    ap.add_argument("--mode", choices=("dream", "wake"), default="dream")
    ap.add_argument("--as-of", default=None,
                    help="ISO timestamp, e.g. 2026-11-22T01:00:00-08:00 (default: now)")
    ap.add_argument("--mailbox", default=None,
                    help="override this agent's mailbox path (single --agent only; tests)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the prompt that would be delivered; deliver nothing")
    ap.add_argument("--force", action="store_true",
                    help="re-trigger even when this slot's marker / message already exists")
    ap.add_argument("--state-root", default=None,
                    help="override the state root (markers, triggers, dream logs); tests")
    args = ap.parse_args(argv)
    if args.mailbox and args.all:
        raise SystemExit("--mailbox is only valid with a single --agent")
    as_of = parse_as_of(args.as_of)

    agents = list(AGENT_IDS) if args.all else [args.agent]
    any_ok = False
    for agent in agents:
        try:
            status, detail, extra = trigger(
                agent, as_of, args.mode, mailbox=args.mailbox,
                dry_run=args.dry_run, force=args.force,
                state_root_override=args.state_root,
            )
        except Exception as exc:  # one agent must not stop the others
            print(f"{'DREAM' if args.mode == 'dream' else 'WAKE'}-ERROR agent={agent} reason={exc}")
            continue
        any_ok = True
        if status.endswith("-TRIGGERED"):
            line = f"{status} agent={agent} seq={detail}"
            if extra.startswith("collected="):
                n = int(extra.split("=", 1)[1])
                if n > 0:
                    line += f" DREAM-COLLECTED agent={agent} n={n}"
            print(line)
        elif status.endswith("-DRY-RUN"):
            print(f"{status} agent={agent} seq={detail} bundle_chars={len(extra)}")
            if not args.all:
                print(extra)
        elif status.endswith("-ALREADY-DONE"):
            print(f"{status} agent={agent}")
        else:  # DEFERRED
            print(f"{status} agent={agent} reason=active-exchange")
    return 0 if any_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
