#!/usr/bin/env python3
"""Daytime self-check trigger: let the agent itself decide whether to
start a private chat.

Why this exists
---------------
Until 2026-11-19 the daytime self-check (qingxia 10:00, zhizunbao
12:00, baijingjing 14:00, tangsanzang 16:00 America/Los_Angeles) was a
``task:`` request written into the agent's ``mailbox/inbox/``. The
daemon core has no inbox listener loop and never answers those
requests itself; the only reasoner that ever answered them was the
per-minute mailbox consumer, which wrote a "跳过" fallback on the
agent's behalf. From 2026-10-27 to 2026-11-14, 72 of 76 self-checks
were consumer-written skips, 3 timed out, 1 was unattributed, and
zero were verifiably initiated by the agent itself.

This trigger changes the channel, not the schedule. At each self-check
time it writes the self-check question -- with the agent's own history
bundle attached -- into the agent's ``mailbox/chat_inbox/``, the
channel the daemon actually reads every poll cycle. The daemon's own
chat loop (``enoch/app/core.py`` ``_dispatch_chat_event`` -> ``_natural``
-> ``run_conversation`` -> runtime provider) then reasons over its own
history and answers in its own voice:

- it wants to talk to someone -> it replies with one intent line
  ``想和【某人】说【……】`` in ``chat_outbox``; the existing
  ``private_intent_relay.py --scan-once`` turns that line into a real
  1:1 private chat (seed into the target's ``chat_inbox``, replies
  relayed back, at most 4 hops);
- it does not -> it replies ``跳过，理由是……`` with a real reason.

There is no consumer fallback on this path any more: if the daemon
does not answer, nothing is written on its behalf. That is the point
of Change 1 (the agent reads its own messages) and Change 2 (the
agent reads its own history and decides for itself).

Route chosen (see docs/selfcheck-autonomous-private-chat.md for the
full comparison): re-route the self-check onto chat_inbox (route A).
The alternatives were rejected: adding an inbox listener loop to the
daemon (route B) means changing enoch-body, a different repository,
and a listener alone does not produce reasoning -- it would still
need an R; calling a CLI reasoner directly (route C) is impossible
for Muse, which has no CLI here, and switching the agent to claude
was already declined by the user (2026-10-01). Route A touches
nothing in the daemon, the provider, or the group-chat rounds: it
reuses the nightly group-chat delivery path that is already proven.

Honesty boundary (read before reusing this elsewhere)
------------------------------------------------------
The daemon's chat reply still goes through the runtime provider
(``src/our_ark_muse/core.py``): the provider writes the request into
``mailbox/inbox/`` and polls ``outbox`` for the reasoning result, so
the token-level reasoning still runs through the consumer's
infrastructure. What changes is the channel, the context, and the
attribution: the question now reaches the daemon's own chat loop with
its own history attached, the daemon's reply is its own chat reply
(including its own decision to decline, with a reason), and there is
no consumer-authored "跳过" fallback any more. Do not report a reply
on this path as "the consumer answered it".

Delivery rules (hard constraints, from the deployment's own rules)
------------------------------------------------------------------
- ``chat_inbox`` sequence numbers are never reused and must be
  greater than the agent's durable cursor
  (``<root>/.enoch/channels/muse/cursor.json``): the next seq is
  ``max(highest numeric file in chat_inbox, cursor) + 1``. The
  provider's ``drop_chat_message`` only does max+1 and does not read
  the cursor, so this script allocates its own seq numbers and never
  calls it.
- Writes are atomic: write to a ``.tmp`` file in the same directory,
  ``chmod 0600``, then ``os.replace`` (rename).
- Idempotent: one trigger per agent per day. A done-marker
  ``round-done-<YYYY-MM-DD>-selfcheck-<agent>`` is written under
  ``$MUSE_GROUP_HOME/hidden_files/`` after a successful delivery,
  and a re-run also scans today's ``chat_inbox`` files for the
  ``[selfcheck <YYYY-MM-DD>]`` marker, so a marker lost to a crash
  still cannot double-deliver. ``--force`` re-triggers deliberately.
- If a group exchange is in progress (``exchange.active`` fresh per
  ``group_ctl.active_exchange``), the trigger defers: it writes no
  marker and exits ``SELFCHECK-DEFERRED`` so the next scheduled
  retry can try again. The trigger never writes into
  ``chat-replies.log`` and never touches the agent's config, memory,
  or prompts.

Usage (run by cron at the four self-check times, or by hand)
------------------------------------------------------------
    python3 selfcheck_trigger.py --agent qingxia
    python3 selfcheck_trigger.py --agent tangsanzang \\
        --as-of 2026-11-20T16:00:00-08:00 --dry-run
    python3 selfcheck_trigger.py --agent baijingjing --no-context

Output protocol on stdout (for the calling worker):
  SELFCHECK-TRIGGERED agent=<agent> seq=<n>
  SELFCHECK-ALREADY-DONE agent=<agent>
  SELFCHECK-DEFERRED agent=<agent> reason=active-exchange
  SELFCHECK-DRY-RUN agent=<agent>
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import sys
import time
from contextlib import contextmanager
from datetime import datetime
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

# Self-check times, America/Los_Angeles (unchanged since 2026-10-04).
SELFCHECK_TIMES = {
    "qingxia": "10:00",
    "zhizunbao": "12:00",
    "baijingjing": "14:00",
    "tangsanzang": "16:00",
}

PEOPLE_CN = ("青霞", "至尊宝", "白晶晶", "唐三藏", "紫霞", "观察者")
EXCHANGE_TTL_S = 15 * 60  # same as group_ctl.TTL_S


def group_home() -> Path:
    return Path(
        os.environ.get("MUSE_GROUP_HOME")
        or (Path.home() / "workspace" / "muse-group")
    )


def done_marker_path(ghome: Path, date_str: str, agent: str) -> Path:
    return ghome / "hidden_files" / f"round-done-{date_str}-selfcheck-{agent}"


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
    """max(highest numeric file in chat_inbox, durable cursor) + 1.

    Never reuse a seq, even if files were deleted: the cursor only
    moves forward, so max()+1 stays above every seq the daemon has
    already consumed.
    """
    top = cursor
    if chat_inbox.is_dir():
        for child in chat_inbox.iterdir():
            if child.is_file() and child.stem.isdigit():
                top = max(top, int(child.stem))
    return top + 1


def already_triggered(chat_inbox: Path, date_str: str) -> bool:
    """True when a [selfcheck <date>] message is already in chat_inbox."""
    marker = f"[selfcheck {date_str}]"
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
    """True while a group exchange is in progress (fresh flag).

    Same protocol as ``group_ctl.active_exchange`` (JSON flag at
    ``$MUSE_GROUP_HOME/exchange.active`` with ``started_at`` /
    ``ttl_s``, 15-minute TTL), but evaluated against the group home
    in effect *now*: group_ctl binds GROUP_HOME at import time, so
    importing it here would read the wrong home whenever the caller
    overrides MUSE_GROUP_HOME after import (tests, sandbox runs).
    """
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
def trigger_lock(ghome: Path):
    """Serialize trigger runs (check + deliver + mark) per group home.

    Best effort: if flock is unavailable the trigger still proceeds;
    the already-triggered scan above is the second line of defence.
    """
    lock_path = ghome / "hidden_files" / "selfcheck-trigger.lock"
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


def build_prompt(agent: str, as_of: datetime, bundle: str) -> str:
    cn = AGENT_CN[agent]
    date_str = as_of.strftime("%Y-%m-%d")
    names = "、".join(PEOPLE_CN)
    lines = [
        f"[selfcheck {date_str}] 白天自检：读一读下面附的你自己的历史，再自己决定——"
        "今天要不要私下找谁说句话。",
        "",
        f"你是{cn}。下面是你自己的历史记录（只读拼装，供你回忆；候选线索只是建议，"
        "是不是真的未了、是不是已经放下了，由你自己判断）：",
        "",
    ]
    if bundle:
        lines.append(bundle)
        lines.append("")
    lines += [
        "怎么回，只按下面两种格式之一，不要多写解释、不要报备状态：",
        "",
        "1. 想私下聊，就回一句话：想和【某人】说【……】",
        f"   某人只能是{names}中的一位；【……】里写你想说的事，一句话说清。",
        "   这一句就是你发出的私聊，写下就会真的递到对方那里。",
        "",
        "2. 今天确实没什么想私下说的，就回：跳过，理由是……",
        "   理由要具体，写清楚是哪条线索已经了了、还是今天确实没什么事。",
        "",
        "不要说你在等什么、系统怎么样；这就是你自己的决定。",
    ]
    return "\n".join(lines)


def trigger(
    agent: str,
    as_of: datetime,
    mailbox: str | None = None,
    dry_run: bool = False,
    with_context: bool = True,
    force: bool = False,
) -> tuple[str, str]:
    """Run one trigger. Returns (status, detail).

    status is one of SELFCHECK-TRIGGERED / SELFCHECK-ALREADY-DONE /
    SELFCHECK-DEFERRED / SELFCHECK-DRY-RUN; detail is the delivered
    seq (triggered), the prompt text (dry-run), or "" otherwise.
    """
    if agent not in AGENT_IDS:
        raise ValueError(f"unknown agent: {agent!r}")
    mbox = resolve_mailbox(agent, mailbox)
    root = mbox.parent
    chat_inbox = mbox / "chat_inbox"
    ghome = group_home()
    date_str = as_of.strftime("%Y-%m-%d")
    marker = done_marker_path(ghome, date_str, agent)

    with trigger_lock(ghome):
        if not force:
            if marker.exists() or already_triggered(chat_inbox, date_str):
                return "SELFCHECK-ALREADY-DONE", ""
        if exchange_active():
            # Do not write a marker: a later retry must be able to run.
            return "SELFCHECK-DEFERRED", ""

        bundle = build_bundle(agent, as_of, mailbox) if with_context else ""
        text = build_prompt(agent, as_of, bundle)
        if dry_run:
            return "SELFCHECK-DRY-RUN", text

        seq = next_seq(chat_inbox, read_cursor(root))
        deliver(chat_inbox, seq, text)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.touch(exist_ok=True)
        return "SELFCHECK-TRIGGERED", str(seq)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--agent", required=True, choices=AGENT_IDS)
    ap.add_argument("--as-of", default=None,
                    help="ISO timestamp, e.g. 2026-11-20T10:00:00-08:00 (default: now)")
    ap.add_argument("--mailbox", default=None,
                    help="override this agent's mailbox path (root is its parent)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the prompt that would be delivered; deliver nothing")
    ap.add_argument("--no-context", action="store_true",
                    help="deliver the prompt without the history bundle")
    ap.add_argument("--force", action="store_true",
                    help="re-trigger even when today's marker / message already exists")
    args = ap.parse_args(argv)
    as_of = parse_as_of(args.as_of)
    status, detail = trigger(
        args.agent, as_of, mailbox=args.mailbox,
        dry_run=args.dry_run, with_context=not args.no_context,
        force=args.force,
    )
    if status == "SELFCHECK-TRIGGERED":
        print(f"SELFCHECK-TRIGGERED agent={args.agent} seq={detail}")
    elif status == "SELFCHECK-DRY-RUN":
        print(f"SELFCHECK-DRY-RUN agent={args.agent}")
        print(detail)
    elif status == "SELFCHECK-ALREADY-DONE":
        print(f"SELFCHECK-ALREADY-DONE agent={args.agent}")
    else:
        print(f"SELFCHECK-DEFERRED agent={args.agent} reason=active-exchange")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
