#!/usr/bin/env python3
"""Build a timestamped history bundle for one agent's daytime self-check.

Why this exists
---------------
The daytime self-check prompt (stored in each agent's own
``.enoch/cron.json``, created 2026-10-04) carries no context at all: it
is the bare question "is there anything you want to say privately
today?" plus the generic Enoch wrapper. The reply therefore depends
entirely on whether the reasoner that answers the request can find a
live, unresolved thread in the agent's own history at that moment.
A 2026-11-19 investigation found exactly that pattern: every
substantive reply in the window pointed at a concrete thread from the
previous 24-72 hours, and every skip pointed at none -- while the
reasoner had no deterministic place to look, so it hunted ad hoc
through host logs (or did not find the thread at all).

This script is the deterministic place to look. It assembles, for one
agent at one trigger time, a bounded, timestamped bundle from every
history source that agent has, and prints it to stdout. It is a recall
aid, not a decider: it lists candidate threads with their evidence and
says so. Whether a candidate is genuinely unresolved, parked by its
owner ("等它自己来", "不急"), or already resolved is a judgement call
the reasoning worker makes from the evidence, per the decision
procedure in the mailbox-consumer task text. The script never decides,
never writes, and never invents a thread.

Honesty boundary (read before reusing this elsewhere)
------------------------------------------------------
This does not make the agent itself answer. The Enoch daemon core has
no inbox listener loop, so the daytime self-check request is still
answered by the per-minute mailbox consumer reasoning in the agent's
standpoint. What this script changes is the evidence that reasoning
stands on: instead of improvising from whatever the worker happens to
remember, it stands on the agent's own timestamped history. The
resulting reply is still consumer-authored and must still be reported
as such; only the evidence is now traceable.

Sources (all read-only; missing sources are reported, never fatal)
-------------------------------------------------------------------
1. Long-term memory: ``<root>/.enoch/memory/long_term.json`` -- the
   agent's own durable decisions and rules. NOTE: in this deployment
   it has not been written since 2026-09-27/29, so it is identity and
   standing-rule context only, never evidence of recent events. The
   bundle flags its newest entry date so the reader can see the staleness.
2. The agent's own recent words: ``<root>/.enoch/conversation/*.json``
   (newest 5 by file mtime at or before --as-of). Each file holds the
   agent's replies from one conversation round; files carry no internal
   timestamps, so recency is file mtime.
3. Recent group chat: ``$MUSE_GROUP_HOME/room.md`` -- last 3 dated
   rounds at or before --as-of, with the topic, the agent's own reply,
   and any reply that mentions the agent by name.
4. Recent private exchanges: ``$MUSE_GROUP_HOME/private.json``
   (``transcripts`` list of {t, from, to, text, session_id}) -- last 3
   sessions involving the agent at or before --as-of.
5. Host log lines about the agent: ``$MUSE_GROUP_HOME/hidden_files/
   chat-replies.log`` -- lines mentioning the agent's Chinese name
   within the 72-hour window (cap 20, newest first). Log timestamps
   are read as America/Los_Angeles wall time, the zone the room and
   the recent log lines are written in; a few older lines were written
   in UTC, so a line within a few hours of the boundary may be
   misclassified -- the bundle is a recall aid, not proof.
6. Host daily memory logs: ``$MUSE_MEMORY_LOG_DIR/YYYY-MM-DD.md``
   (default ~/memory) -- lines mentioning the agent's Chinese name in
   the last 3 calendar days (scan cap 150, newest first; §6 displays
   the newest 10). Time-aware: a line dated the trigger day counts
   only if its time (own leading HH:MM, else its section header's)
   is at or before --as-of, so a same-day line written after the
   trigger cannot leak future knowledge into the bundle.

Candidate threads (suggestions only)
--------------------------------------
An evidence item becomes a *candidate* when it is inside the 72-hour
window, names a person, and carries an open marker (a question, an
explicit unfulfilled commitment such as 想明白了第一个告诉你 /
没想好, or a live wait addressed to someone: 等你 / 等他 / 在等).
The marker set is deliberately narrow: bare 等, 留着, 记得, 以后
were dropped because they fire on past-tense reminiscence as easily
as on a live thread, and group-chat answers are mostly reminiscence.
Candidates are drawn from: the group-chat topic, the agent's own
words, lines that mention the agent, other agents'
own lines in group chat (someone else's open thread is a thread the
agent may pick up), private exchanges, host log lines, and the host's
daily memory log (the only place that narrates who talked to whom in
the operator's private exchanges, whose other side is not recorded
in chat-replies.log). They are listed with the quote and the marker
that fired. They are not decisions: a candidate may already be
resolved in a later line, or parked by its owner. The decision
procedure lives in the consumer task text, not here.

Portability
-----------
No agent root is derived from a name (青霞's root is
``muse-enoch-agent``, never ``muse-qingxia-agent`` -- see the consumer
task text). Roots come from the explicit map below, overridable per
agent with ``MUSE_GROUP_<AGENT>_MAILBOX`` (same convention as
``group_ctl.py``) or ``--mailbox``. Group home comes from
``MUSE_GROUP_HOME`` (default ``~/workspace/muse-group``); memory logs
from ``MUSE_MEMORY_LOG_DIR`` (default ``~/memory``).

Usage
-----
    python3 selfcheck_context.py --agent qingxia
    python3 selfcheck_context.py --agent tangsanzang \\
        --as-of 2026-11-15T16:00:00-08:00
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

LA = ZoneInfo("America/Los_Angeles")

AGENT_IDS = ("qingxia", "zhizunbao", "baijingjing", "tangsanzang")
AGENT_CN = {
    "qingxia": "青霞",
    "zhizunbao": "至尊宝",
    "baijingjing": "白晶晶",
    "tangsanzang": "唐三藏",
}
# Explicit identity map. Never derive a root from an agent name:
# qingxia's root is muse-enoch-agent; muse-qingxia-agent is an abandoned
# empty shell. Keep in sync with the mailbox-consumer task text.
DEFAULT_ROOT_DIRS = {
    "qingxia": "muse-enoch-agent",
    "zhizunbao": "muse-zhizunbao-agent",
    "baijingjing": "muse-baijingjing-agent",
    "tangsanzang": "muse-tangsanzang-agent",
}
PEOPLE_CN = ("青霞", "至尊宝", "白晶晶", "唐三藏", "紫霞", "观察者")

RECENT_HOURS = 72
MAX_CONVERSATION_FILES = 5
MAX_ROOM_ROUNDS = 3
MAX_PRIVATE_SESSIONS = 3
MAX_LOG_LINES = 20
MAX_MEMORY_LOG_LINES = 150  # scan cap (newest first); §6 displays the newest 10
MAX_BUNDLE_CHARS = 8000
SNIPPET_CHARS = 220
# Per-section budgets (chars). They sum below the total cap on purpose:
# section seven (candidates) must never be cut off by earlier sections.
BUDGETS = {
    "long_term": 900,
    "conversation": 900,
    "room": 900,
    "private": 600,
    "log": 900,
    "memory_logs": 700,
    "candidates": 2500,
}

# Generic open-thread markers (linguistic, not story keywords: no
# specific thread such as 半句/碗/手帕 is hardcoded here).
# The set is deliberately narrow: it fires on an unfulfilled
# commitment ("想明白了第一个告诉你", "没想好"), a direct question,
# or a live wait addressed to someone ("等你/等他"). Bare "等",
# "留着", "记得", "以后" were dropped -- they fire on past-tense
# reminiscence ("等了五百年", "我留着穗子") as easily as on a live
# thread, and reminiscence is what group-chat answers mostly are.
OPEN_MARKERS = (
    "还没", "没说完", "半句", "想问", "想跟你说",
    "别忘了", "还欠", "没回", "没接", "卡着",
    "没想好", "想明白", "第一个告诉", "没来得及",
    "等你", "等我", "等他", "等她", "等不到", "在等",
    "？", "?",
)
# Parked markers are NOT classified here -- the reasoning worker judges
# parked vs open from the evidence. They are listed in the consumer
# task text (等它自己来 / 不急 / 先放着).

LOG_LINE_RE = re.compile(
    r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]\s+(\S+)\s+(\S+):\s?(.*)$"
)
ROOM_SECTION_RE = re.compile(
    r"^## (\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?) \[([^\]]*)\]\s*$"
)


def parse_la(s: str) -> datetime | None:
    """Parse 'YYYY-MM-DD HH:MM[:SS]' as America/Los_Angeles wall time."""
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=LA)
        except ValueError:
            continue
    return None


def parse_as_of(s: str | None) -> datetime:
    if not s:
        return datetime.now(LA)
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        raise SystemExit(f"bad --as-of value: {s!r} (want ISO, e.g. 2026-11-15T16:00:00-08:00)")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=LA)
    return dt.astimezone(LA)


def snippet(text: str, limit: int = SNIPPET_CHARS) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= limit else text[:limit] + "…"


def resolve_mailbox(agent: str, override: str | None) -> Path:
    if override:
        return Path(override).expanduser()
    env = f"MUSE_GROUP_{agent.upper()}_MAILBOX"
    if env in __import__("os").environ:
        return Path(__import__("os").environ[env]).expanduser()
    home = Path.home() / "workspace"
    return home / DEFAULT_ROOT_DIRS[agent] / "mailbox"


def group_home() -> Path:
    import os

    return Path(os.environ.get("MUSE_GROUP_HOME") or (Path.home() / "workspace" / "muse-group"))


def memory_log_dir() -> Path:
    import os

    return Path(os.environ.get("MUSE_MEMORY_LOG_DIR") or (Path.home() / "memory"))


def read_long_term(root: Path) -> tuple[list[dict], str]:
    path = root / ".enoch" / "memory" / "long_term.json"
    if not path.exists():
        return [], f"缺失：{path} 不存在"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as exc:
        return [], f"读失败：{path} ({exc})"
    mems = data.get("memories", []) if isinstance(data, dict) else []
    newest = ""
    for m in mems:
        upd = str(m.get("updated_at") or m.get("created_at") or "")
        if upd > newest:
            newest = upd
    return mems, newest


def read_conversation(root: Path, as_of: datetime, limit: int) -> list[dict]:
    conv = root / ".enoch" / "conversation"
    if not conv.is_dir():
        return []
    files = []
    for child in conv.iterdir():
        if child.suffix != ".json" or not child.is_file():
            continue
        try:
            mtime = datetime.fromtimestamp(child.stat().st_mtime, tz=timezone.utc).astimezone(LA)
        except OSError:
            continue
        if mtime <= as_of:
            files.append((mtime, child))
    files.sort(key=lambda t: t[0], reverse=True)
    out = []
    for mtime, child in files[:limit]:
        try:
            data = json.loads(child.read_text(encoding="utf-8", errors="replace"))
        except (ValueError, OSError):
            continue
        replies = []
        for step in data.get("steps", []) if isinstance(data, dict) else []:
            r = step.get("reply")
            if isinstance(r, str) and r.strip():
                replies.append(r.strip())
        if replies:
            out.append({"mtime": mtime, "file": child.name, "replies": replies})
    return out


def read_room(ghome: Path, agent_cn: str, as_of: datetime) -> list[dict]:
    path = ghome / "room.md"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    sections = []
    cur: dict | None = None
    for line in text.splitlines():
        m = ROOM_SECTION_RE.match(line)
        if m:
            if cur is not None:
                sections.append(cur)
            ts = parse_la(m.group(1))
            cur = {"ts": ts, "head": m.group(2), "lines": []}
            continue
        if cur is not None:
            cur["lines"].append(line)
    if cur is not None:
        sections.append(cur)
    out = []
    for sec in reversed(sections):
        if sec["ts"] is None or sec["ts"] > as_of:
            continue
        body = "\n".join(sec["lines"])
        topic = ""
        for line in sec["lines"]:
            if line.startswith("话题："):
                topic = line[len("话题："):].strip()
                break
        own = ""
        mentions = []
        others = []
        # Per-agent blocks look like "⚔️ 青霞：<text>" (possibly multi-line).
        blocks = re.split(r"(?m)^[^\s]{1,4} (青霞|至尊宝|白晶晶|唐三藏)：", body)
        # blocks[0] is preamble; then name, text, name, text, ...
        for i in range(1, len(blocks) - 1, 2):
            name, txt = blocks[i], blocks[i + 1]
            txt = txt.strip()
            if name == agent_cn:
                own = txt
            elif agent_cn in txt:
                mentions.append((name, txt))
            else:
                others.append((name, txt))
        out.append(
            {"ts": sec["ts"], "head": sec["head"], "topic": topic, "own": own,
             "mentions": mentions, "others": others}
        )
        if len(out) >= MAX_ROOM_ROUNDS:
            break
    return list(reversed(out))


def read_private(ghome: Path, agent: str, as_of: datetime) -> list[dict]:
    path = ghome / "private.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    entries = data.get("transcripts", []) if isinstance(data, dict) else []
    mine = []
    for e in entries:
        if not isinstance(e, dict):
            continue
        if e.get("from") != agent and e.get("to") != agent:
            continue
        t = e.get("t")
        try:
            ts = datetime.fromtimestamp(float(t), tz=timezone.utc).astimezone(LA)
        except (TypeError, ValueError):
            continue
        if ts <= as_of:
            mine.append({"ts": ts, "from": e.get("from"), "to": e.get("to"),
                         "text": str(e.get("text", "")), "session": e.get("session_id")})
    mine.sort(key=lambda e: e["ts"])
    # Last MAX_PRIVATE_SESSIONS sessions, in order.
    sessions: list[str] = []
    for e in mine:
        if e["session"] not in sessions:
            sessions.append(e["session"])
    keep = set(sessions[-MAX_PRIVATE_SESSIONS:])
    return [e for e in mine if e["session"] in keep]


def read_log_lines(
    ghome: Path, agent_cn: str, as_of: datetime, window: timedelta
) -> list[dict]:
    path = ghome / "hidden_files" / "chat-replies.log"
    if not path.exists():
        return []
    out = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    for line in lines:
        if agent_cn not in line:
            continue
        m = LOG_LINE_RE.match(line)
        if not m:
            continue
        ts = parse_la(m.group(1))
        if ts is None or ts > as_of or ts < as_of - window:
            continue
        out.append({"ts": ts, "who": m.group(2), "text": m.group(4)})
    return out[-MAX_LOG_LINES:]


def read_memory_logs(
    mdir: Path, agent_cn: str, as_of: datetime
) -> list[dict]:
    """Host daily memory-log lines naming the agent, newest first.

    Time-aware: a line dated before as_of's date is entirely in the
    past and always counts. A line dated as_of's date counts only if
    its time can be established (its own leading HH:MM, else its
    section header's first HH:MM -- headers carry times in several
    shapes, e.g. "## 17:07 ..." and "## ...（16:02–16:05）") and is
    at or before as_of -- the daily log is written all day, and a
    same-day line written after the trigger would leak future
    knowledge into the bundle (in one real case the 12:02 line
    already narrated the 12:00 round's answer). An untimed header
    resets the section time to unknown, and a dateless line on
    as_of's date is excluded: conservative, but such lines are
    usually ops records, not conversation threads.
    """
    section_re = re.compile(r"(\d{1,2}:\d{2})")
    bullet_re = re.compile(r"^-\s+(\d{1,2}:\d{2})\b")
    out = []
    # Days iterate newest-first, so the cap below keeps the NEWEST lines.
    for back in range(0, 3):
        day = (as_of - timedelta(days=back)).date()
        path = mdir / f"{day.isoformat()}.md"
        if not path.exists():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        section_time: datetime | None = None
        for line in lines:
            if line.startswith("## "):
                m = section_re.search(line)
                section_time = parse_la(f"{day.isoformat()} {m.group(1)}") if m else None
                continue
            if agent_cn not in line or not line.strip():
                continue
            ts = None
            bm = bullet_re.match(line)
            if bm:
                ts = parse_la(f"{day.isoformat()} {bm.group(1)}")
            elif section_time is not None:
                ts = section_time
            if day < as_of.date():
                pass  # whole day is in the past
            elif ts is None or ts > as_of:
                continue  # same-day line at/after the trigger, or dateless
            out.append({"day": day.isoformat(), "text": line.strip()})
    return out[:MAX_MEMORY_LOG_LINES]


def find_candidates(
    agent: str, agent_cn: str, room: list[dict], private: list[dict], log_lines: list[dict],
    mlogs: list[dict], as_of: datetime,
) -> list[dict]:
    """Suggest candidate threads: recent, names a person, open marker.

    Suggestions only. Resolution / parked-state judgement belongs to
    the reasoning worker, not to this heuristic. ``person`` is always
    the *other party* of the thread: the person named in the agent's
    own words, the person who mentioned the agent, the speaker of
    another agent's open line in group chat, the other side of a
    private exchange, or a person named alongside the agent in the
    host's daily log (the host log is the only place that narrates
    who talked to whom in the operator's private exchanges, whose
    other side is not recorded in chat-replies.log).
    """
    window_start = as_of - timedelta(hours=RECENT_HOURS)
    cands: list[dict] = []

    def scan(ts, source, person, text, marker=None):
        if ts is None or ts < window_start or ts > as_of:
            return
        if not person or person == agent_cn:
            return
        if marker is None:
            marker = next((mk for mk in OPEN_MARKERS if mk in text), None)
        if marker:
            cands.append(
                {"ts": ts, "source": source, "person": person,
                 "marker": marker, "quote": snippet(text)}
            )

    def named_in(text):
        return next((p for p in PEOPLE_CN if p in text and p != agent_cn), None)

    for sec in room:
        scan(sec["ts"], "群聊", named_in(sec.get("topic", "")), sec.get("topic", ""))
        if sec.get("own"):
            scan(sec["ts"], "群聊（我说的）", named_in(sec["own"]), sec["own"])
        for name, txt in sec.get("mentions", []):
            scan(sec["ts"], f"群聊（{name}提到我）", name, txt)
        for name, txt in sec.get("others", []):
            scan(sec["ts"], f"群聊（{name}说的）", name, txt)
    for e in private:
        other = e["to"] if e["from"] == agent else e["from"]
        scan(e["ts"], "私聊", AGENT_CN.get(str(other), str(other)), e["text"])
    for ln in log_lines:
        person = named_in(ln["text"])
        if person is None and ln["who"] != agent_cn:
            person = ln["who"]
        scan(ln["ts"], "日志", person, ln["text"])
    for ln in mlogs:
        # Day-granular: use noon of that day. A line dated the first
        # day of the window may be a few hours older than 72h; the
        # bundle is a recall aid, not proof.
        day_ts = datetime.fromisoformat(ln["day"]).replace(tzinfo=LA) + timedelta(hours=12)
        # A summary line often names several people (e.g. that night's
        # host) and carries several markers. Take the (marker, person)
        # pair closest together: the thread belongs to the person
        # nearest the open marker, not to the first-named person.
        # E.g. "...（白晶晶主持）...还没想好...第一个告诉紫霞" belongs
        # to 紫霞 (3 chars from 第一个告诉), not to 白晶晶.
        best: tuple[int, str, str] | None = None  # (dist, marker, person)
        for mk in OPEN_MARKERS:
            start = 0
            while True:
                mpos = ln["text"].find(mk, start)
                if mpos == -1:
                    break
                start = mpos + 1
                for p in PEOPLE_CN:
                    if p == agent_cn or p == "观察者":
                        continue
                    ppos = ln["text"].find(p)
                    while ppos != -1:
                        dist = abs(ppos - mpos)
                        if best is None or dist < best[0]:
                            best = (dist, mk, p)
                        ppos = ln["text"].find(p, ppos + 1)
        if best is not None:
            scan(day_ts, "宿主每日日志", best[2], ln["text"], marker=best[1])
    # Newest first: the freshest thread is the most decision-relevant,
    # and it must survive if the section budget truncates the list.
    cands.sort(key=lambda c: c["ts"], reverse=True)
    return cands


def truncate(text: str, limit: int) -> str:
    """Truncate one section to its budget, marking the cut."""
    if len(text) <= limit:
        return text
    return text[:limit] + "\n[…本节已截断]"


def build_bundle(agent: str, as_of: datetime, mailbox_override: str | None) -> str:
    cn = AGENT_CN[agent]
    mailbox = resolve_mailbox(agent, mailbox_override)
    root = mailbox.parent
    ghome = group_home()
    mdir = memory_log_dir()
    window = timedelta(hours=RECENT_HOURS)

    head = [
        f"# 自检历史 bundle：{cn}（{agent}）",
        f"触发时刻（洛杉矶）：{as_of.strftime('%Y-%m-%d %H:%M')}",
        "只读拼装，不作决定；候选≠决定。长期记忆自 2026-09-27 起未再写入，只作身份参考。",
        "",
    ]

    # 1. long-term memory
    mems, newest = read_long_term(root)
    s1 = ["## 一、长期记忆（身份与旧决定）"]
    if not mems:
        s1.append(f"（无：{newest}）")
    else:
        s1.append(f"（共 {len(mems)} 条，最新更新 {newest or '未知'}；2026-09-27 后未再写入，近况不在此处）")
        for m in mems:
            s1.append(f"- [{m.get('id', '?')}] {snippet(str(m.get('text', '')), 120)}")
    s1.append("")

    # 2. own recent words
    conv = read_conversation(root, as_of, MAX_CONVERSATION_FILES)
    s2 = ["## 二、最近我自己说过的话（.enoch/conversation，最近 5 轮）"]
    if not conv:
        s2.append("（无）")
    for c in conv:
        for r in c["replies"]:
            s2.append(f"- {c['mtime'].strftime('%m-%d %H:%M')}：{snippet(r, 160)}")
    s2.append("")

    # 3. group chat
    room = read_room(ghome, cn, as_of)
    s3 = ["## 三、最近群聊（room.md，最近 3 轮）"]
    if not room:
        s3.append("（无）")
    for sec in room:
        s3.append(f"- {sec['ts'].strftime('%m-%d %H:%M')} [{sec['head']}] 话题：{snippet(sec['topic'], 160)}")
        if sec.get("own"):
            s3.append(f"  我说的：{snippet(sec['own'], 160)}")
        for name, txt in sec.get("mentions", []):
            s3.append(f"  {name}提到我：{snippet(txt, 160)}")
    s3.append("")

    # 4. private exchanges
    priv = read_private(ghome, agent, as_of)
    s4 = ["## 四、最近私聊（private.json，最近 3 组）"]
    if not priv:
        s4.append("（无）")
    for e in priv:
        direction = "→" if e["from"] == agent else "←"
        other = e["to"] if e["from"] == agent else e["from"]
        s4.append(f"- {e['ts'].strftime('%m-%d %H:%M')} {cn}{direction}{AGENT_CN.get(str(other), other)}：{snippet(e['text'], 160)}")
    s4.append("")

    # 5. host log lines
    logs = read_log_lines(ghome, cn, as_of, window)
    s5 = [f"## 五、宿主日志里与我有关的近况（chat-replies.log，{RECENT_HOURS} 小时内，最多 {MAX_LOG_LINES} 条）"]
    if not logs:
        s5.append("（无）")
    for ln in logs[-12:]:
        s5.append(f"- {ln['ts'].strftime('%m-%d %H:%M')} {ln['who']}：{snippet(ln['text'], 160)}")
    s5.append("")

    # 6. host daily memory logs (newest first; display newest 10)
    mlogs = read_memory_logs(mdir, cn, as_of)
    s6 = ["## 六、宿主每日日志里提到我的行（~/memory，最近 3 天）"]
    if not mlogs:
        s6.append("（无）")
    for ln in mlogs[:10]:
        s6.append(f"- {ln['day']}：{snippet(ln['text'], 140)}")
    s6.append("")

    # 7. candidate threads (suggestions only)
    cands = find_candidates(agent, cn, room, priv, logs, mlogs, as_of)
    s7 = [f"## 七、候选未了线索（建议，非决定；{RECENT_HOURS} 小时内、指名了人、带未了标记）"]
    if not cands:
        s7.append("（无候选。没有证据就不写 intent，按口径带理由跳过。）")
    for c in cands:
        s7.append(
            f"- {c['ts'].strftime('%m-%d %H:%M')} [{c['source']}] 与{c['person']}有关"
            f"（标记：{c['marker']}）：{c['quote']}"
        )
    s7.append("")

    parts = head + [
        truncate("\n".join(s1), BUDGETS["long_term"]),
        truncate("\n".join(s2), BUDGETS["conversation"]),
        truncate("\n".join(s3), BUDGETS["room"]),
        truncate("\n".join(s4), BUDGETS["private"]),
        truncate("\n".join(s5), BUDGETS["log"]),
        truncate("\n".join(s6), BUDGETS["memory_logs"]),
        truncate("\n".join(s7), BUDGETS["candidates"]),
    ]
    out = "\n".join(parts)
    if len(out) > MAX_BUNDLE_CHARS:
        out = out[:MAX_BUNDLE_CHARS] + "\n[…bundle 已截断，超长部分未列出]"
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--agent", required=True, choices=AGENT_IDS)
    ap.add_argument("--as-of", default=None,
                    help="ISO timestamp, e.g. 2026-11-15T16:00:00-08:00 (default: now)")
    ap.add_argument("--mailbox", default=None,
                    help="override this agent's mailbox path (root is its parent)")
    args = ap.parse_args(argv)
    as_of = parse_as_of(args.as_of)
    sys.stdout.write(build_bundle(args.agent, as_of, args.mailbox))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
