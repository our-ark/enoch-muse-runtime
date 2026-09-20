#!/usr/bin/env python3
"""muse-group 群聊房间控制脚本.

hub-and-spoke 拓扑: 主持人 (host) 是房间服务器. 两个 Enoch daemon 各自只读写自己的
mailbox (chat_inbox/chat_outbox), 房间负责把发言扇出 (fan-out) 到两边,
并把两边的回复收进共享 transcript (room.json / room.md).

主持人是第三方参与者: 发言正文由调用方写好传入 (不是 daemon 回复),
可开场、可插话, 不占 hop 预算. 主持人的显示名由环境变量 MUSE_GROUP_HOST_NAME
配置 (本部署设为紫霞); 不设则房间只有 agents.

防重:
- exchange.active 旗标: 群聊交换进行中时, 两个 mailbox consumer 与
  hourly-enoch-chat 跳过各自的投递/收集动作 (见各自 cron 文本的"群聊避让"),
  由群聊编排独占 chat_outbox 的收集权. 旗标带 TTL (15 分钟), 编排异常
  退出后 cron 自动恢复正常投递.
- 每个 outbox 回复只收集一次: seen 集合 + .delivered 标记.

防环:
- 每次交换最多 max_hops 次 agent->agent 转发 (默认 3), 之后只收录不转发.

可移植性 (环境变量, 不设则用默认):
- MUSE_GROUP_HOME: 房间状态目录 (room.json/room.md/staged/exchange.active),
  默认 ~/workspace/muse-group.
- MUSE_GROUP_QINGXIA_MAILBOX / MUSE_GROUP_ZHIZUNBAO_MAILBOX: 两边 mailbox.
- MUSE_GROUP_SRC_PATHS: 冒号分隔的 our_ark_muse import 路径.
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
        "name": "青霞",
        "chat_label": "⚔️ **青霞**",
    },
    "zhizunbao": {
        "mailbox": os.environ.get(
            "MUSE_GROUP_ZHIZUNBAO_MAILBOX",
            "/home/hatch/workspace/muse-zhizunbao/mailbox",
        ),
        "name": "至尊宝",
        "chat_label": "🐵 **至尊宝**",
    },
}
OTHER = {"qingxia": "zhizunbao", "zhizunbao": "qingxia"}

# 房间主持人 (host) 的显示名, 由调用方配置. 主持人的发言正文由调用方写好
# 传入 (不是 daemon 回复), 记 transcript 时 kind="host", 不占 hop 预算.
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
    """往指定 agent 的 chat_inbox 投一条消息, 返回 seq."""
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
    """进行中的交换, 无或过期返回 None."""
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
    """开一轮群聊交换: 写旗标, 记 transcript, 向两边扇出首条消息."""
    if active_exchange():
        raise RuntimeError("已有进行中的群聊交换, 先等它结束")
    eid = uuid.uuid4().hex[:12]
    now = time.time()
    members = "、".join(
        [n for n in [HOST_NAME] + [a["name"] for a in AGENTS.values()] if n]
    )
    framing = (
        f"[群聊] 房间新话题. 房间成员: {members}. "
        "以 [群聊] 开头的都是房间里的发言, 纯聊天、不用执行动作, "
        "直接像平时聊天一样回就行."
    )
    first = f"{framing}\n[群聊] {speaker}: {text}"
    seqs = {
        "qingxia": drop_to("qingxia", first),
        "zhizunbao": drop_to("zhizunbao", first),
    }
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
    """把 from_agent 的房间回复转给另一位 agent."""
    other = OTHER[from_agent]
    name = AGENTS[from_agent]["name"]
    seq = drop_to(other, f"[群聊] {name}: {text}")
    st = active_exchange()
    if st:
        st["hops_used"] = st.get("hops_used", 0) + 1
        _atomic_write_json(ACTIVE, st)
    return seq


def fanout_room_message(speaker: str, text: str, exchange_id: str) -> dict:
    """房间主持人/参与者发言: 记 transcript, 向两边 daemon 各扇出一条.

    发言正文由调用方写好传入, 不是 daemon 回复. 带 "[群聊] <说话人>:"
    前缀, 两边 daemon 照常当房间发言回复. 说话人是主持人 (HOST_NAME)
    时 kind="host", 否则 kind="human". 不占 hop 预算.
    """
    msg = f"[群聊] {speaker}: {text}"
    seqs = {
        "qingxia": drop_to("qingxia", msg),
        "zhizunbao": drop_to("zhizunbao", msg),
    }
    say(speaker, text, "host" if HOST_NAME and speaker == HOST_NAME else "human", exchange_id)
    return seqs


def _outbox_files(agent: str):
    outbox = Path(AGENTS[agent]["mailbox"]) / "chat_outbox"
    if not outbox.is_dir():
        return []
    files = []
    for child in outbox.iterdir():
        # 只看原子写好的 .json; 点文件与标记文件跳过.
        # 注意: 不再以 .delivered 标记作为收集依据 —— 搬运 (move) 即占有,
        # 避免 consumer 即兴标记导致房间漏收. mtime 窗口由调用方限定.
        if not child.is_file() or child.suffix != ".json" or child.name.startswith("."):
            continue
        if child.name.endswith(".delivered.json"):
            continue
        files.append(child)
    return sorted(files, key=lambda p: p.stat().st_mtime)


def collect_new(agent: str, since_ts: float):
    """收集该 agent 在 since_ts 之后产生的 outbox 回复 (不看标记)."""
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


def stage_collected(agent: str, mid: str) -> Path:
    """把已收集的回复搬运到房间 staged 存档 (move 即占有, 防 consumer 重投).

    daemon 写 outbox 是原子 rename, move 不会撕裂文件; daemon 写后不再读回.
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


# ---------------------------------------------------------------------------
# 私聊 / 夜班额度 / 群聊主持人轮换
# ---------------------------------------------------------------------------

PRIVATE_JSON = GROUP_HOME / "private.json"
PRIVATE_MD = GROUP_HOME / "private.md"
CREDITS_JSON = GROUP_HOME / "private_credits.json"
HOST_JSON = GROUP_HOME / "group_host.json"
NIGHTLY_CREDITS = 3  # 每位 agent 每晚私聊额度


def begin_control(ttl_s: int = 1800, note: str = "") -> dict:
    """只占旗标、不扇出: 邀请阶段 / 私聊交换用, 让 consumer 自动避让."""
    if active_exchange():
        raise RuntimeError("已有进行中的群聊交换, 先等它结束")
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
    """记私聊 transcript (与公共 room.json 分开)."""
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
        f"[私聊 {from_agent}->{to_agent}] ({session_id})\n\n{text}\n"
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
        raise RuntimeError(f"{agent} 今晚私聊额度已用完 ({date_str})")
    day[agent] = left - 1
    _atomic_write_json(CREDITS_JSON, data)
    return left - 1


def next_host() -> str:
    """群聊主持人轮换: qingxia -> zhizunbao -> qingxia ..."""
    order = ["qingxia", "zhizunbao"]
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
