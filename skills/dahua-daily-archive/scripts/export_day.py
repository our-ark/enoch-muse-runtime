#!/usr/bin/env python3
"""Read-only source extraction; immutable daily revisions. No network or agent calls."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
import fcntl
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import sys
import tempfile
from zoneinfo import ZoneInfo

STREAMS = ("group", "peer_private", "host_private", "operations")
ACTORS = {
    "qingxia": "青霞", "zhizunbao": "至尊宝", "baijingjing": "白晶晶",
    "tangsanzang": "唐三藏", "zixia": "紫霞", "observer": "观察者",
}
ALIASES = {**{k: k for k in ACTORS}, **{v: k for k, v in ACTORS.items()}}
PEERS = set(ACTORS) - {"zixia", "observer"}
EVENT_TYPES = {"intent", "dispatch", "delivery", "reply", "self_check", "skip", "timeout", "observer_report"}
PRODUCERS = {"agent", "host", "system", "observer", "unknown"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def stamp(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        require(math.isfinite(value), "Non-finite event time")
        result = datetime.fromtimestamp(value, timezone.utc)
    elif isinstance(value, str):
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(result.tzinfo is not None, "Event time needs an explicit timezone")
        result = result.astimezone(timezone.utc)
    else:
        raise ValueError("Event time must be Unix seconds or timezone-aware ISO text")
    return result


def text_field(row, key, required=True):
    value = row.get(key)
    if not required and value is None:
        return None
    require(isinstance(value, str), f"Expected text field: {key}")
    return value


def actor(value):
    require(isinstance(value, str) and value in ALIASES, "Unknown or out-of-scope actor")
    return ALIASES[value]


def window(day, tz):
    zone = ZoneInfo(tz)
    d = date.fromisoformat(day)
    require(d.isoformat() == day, "Date must be YYYY-MM-DD")
    start = datetime.combine(d, time.min, zone)
    end = datetime.combine(d + timedelta(days=1), time.min, zone)
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def collect(day, tz, paths):
    start, end = window(day, tz)
    records, sources, availability = [], {}, {}
    for stream in STREAMS:
        path = paths.get(stream)
        if path is None or not Path(path).exists():
            availability[stream] = "missing"
            sources[stream] = {"status": "missing", "coverage": "not_attested"}
            continue
        raw = Path(path).read_bytes()
        data = json.loads(raw)
        key = "events" if stream == "operations" else "transcript"
        require(isinstance(data, dict) and isinstance(data.get(key), list), f"Invalid {stream} source shape")
        availability[stream] = "available"
        sources[stream] = {"status": "available", "coverage": "not_attested", "snapshot_sha256": sha(raw), "bytes": len(raw)}
        for index, row in enumerate(data[key]):
            require(isinstance(row, dict), f"Invalid {stream} record")
            when = stamp(row.get("t"))
            if not start <= when < end:
                continue
            record = {
                "surface": stream, "source_id": stream,
                "source_pointer": f"/{key}/{index}", "source_index": index,
                "source_record_sha256": sha(encode(row)),
                "timestamp_utc": when.isoformat(), "text": text_field(row, "text"),
                "delivery": "unknown", "generation_origin": "unknown",
                "request_id": text_field(row, "request_id", False),
                "message_id": text_field(row, "message_id", False),
            }
            if stream == "group":
                record.update(speaker=actor(row.get("speaker")), recipient=None,
                              session_id=text_field(row, "exchange_id"),
                              source_kind="native_transcript", declared_kind=text_field(row, "kind"))
                require(record["declared_kind"] in {"agent", "host", "human"}, "Unknown group kind")
            elif stream in {"peer_private", "host_private"}:
                sender, target = actor(row.get("from")), actor(row.get("to"))
                require(sender != target, "Private exchange requires distinct participants")
                if stream == "peer_private":
                    require({sender, target} <= PEERS, "Peer-private source includes non-peer participant")
                else:
                    require("zixia" in {sender, target} and bool({sender, target} & PEERS), "Host-private source must pair Zixia with a study peer")
                record.update(speaker=sender, recipient=target, session_id=text_field(row, "session_id"),
                              source_kind="native_transcript" if stream == "peer_private" else "host_export")
            else:
                require(row.get("type") in EVENT_TYPES, "Unknown operation type")
                require(row.get("producer") in PRODUCERS, "Operation producer must be explicit (unknown is allowed)")
                record.update(source_kind="operations_export", event_type=row["type"], reported_producer=row["producer"],
                              session_id=text_field(row, "session_id", False),
                              evidence_ref=text_field(row, "evidence_ref", False),
                              speaker=actor(row["agent"]) if row.get("agent") is not None else None, recipient=None)
            records.append(record)
    records.sort(key=lambda r: (r["timestamp_utc"], STREAMS.index(r["surface"]), r["source_index"]))
    payload = {"schema_version": 1, "observation_date": day, "timezone": tz,
               "window_start_utc": start.isoformat(), "window_end_utc_exclusive": end.isoformat(),
               "availability": availability, "coverage": "not_attested", "records": records}
    return payload, sources


def render(payload):
    lines = [f"# 大话西游每日归档 · {payload['observation_date']}", "",
             f"时区：{payload['timezone']}。整理者：紫霞（Muse host）。", "",
             "这是所取得来源的当日摘录；来源覆盖及原始执行未独立认证。记录存在不等于确认送达、独立生成或自主发起。", "",
             "后续 revision 替代同日较早快照，不能叠加计数；跨日会话按原 session ID 关联。", "",
             "| 来源 | 可访问状态 | 当日记录条数 |", "| --- | --- | --- |"]
    counts = Counter(r["surface"] for r in payload["records"])
    for stream in STREAMS:
        lines.append(f"| {stream} | {payload['availability'][stream]} | {counts[stream]} |")
    lines += ["", "missing 表示未取得来源，不表示没有活动；零条也不证明无人互动。条数不是完整会话数。", ""]
    for n, r in enumerate(payload["records"], 1):
        speaker = ACTORS.get(r["speaker"], "未注明角色")
        target = " → " + ACTORS[r["recipient"]] if r["recipient"] else ""
        lines += [f"## {n}. {r['timestamp_utc']} · {speaker}{target}", "",
                  f"来源：{r['source_id']} {r['source_pointer']}；会话：{json.dumps(r['session_id'], ensure_ascii=False)}。",
                  f"来源类型：{r['source_kind']}；生成归属：unknown；送达：unknown。"]
        if r["surface"] == "operations":
            lines.append(f"事件：{r['event_type']}；来源标注的产生者：{r['reported_producer']}（未独立认证）。")
        fence = "`" * max(3, 1 + max((len(m) for m in re.findall(r"`+", r["text"])), default=0))
        lines += ["", fence + "text", r["text"], fence, ""]
    return "\n".join(lines).encode()


def verify(revision):
    revision = Path(revision)
    manifest = json.loads((revision / "manifest.json").read_bytes())
    require(manifest.get("schema_version") == 1, "Unsupported manifest")
    require(set(manifest["files"]) == {"records.json", "conversations.zh-CN.md"}, "Unexpected archive file set")
    for name, digest in manifest["files"].items():
        require(sha((revision / name).read_bytes()) == digest, f"Archive hash mismatch: {name}")
    payload = json.loads((revision / "records.json").read_bytes())
    require(sha(encode(payload)) == manifest["content_sha256"], "Content fingerprint mismatch")
    require(render(payload) == (revision / "conversations.zh-CN.md").read_bytes(), "Transcript rendering mismatch")
    start, end = window(payload["observation_date"], payload["timezone"])
    require(manifest["observation_date"] == payload["observation_date"], "Manifest date mismatch")
    require(payload["window_start_utc"] == start.isoformat() and payload["window_end_utc_exclusive"] == end.isoformat(), "Window mismatch")
    require(set(payload["availability"]) == set(STREAMS), "Missing source coverage")
    for r in payload["records"]:
        require(start <= stamp(r["timestamp_utc"]) < end, "Out-of-window record")
    return manifest


def export(day, tz, paths, out):
    payload, sources = collect(day, tz, paths)
    fingerprint = sha(encode(payload))
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    with (out / ".archive.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        day_dir = out / day
        day_dir.mkdir(exist_ok=True)
        old = sorted((p for p in day_dir.iterdir() if re.fullmatch(r"r\d{3,}", p.name)), key=lambda p: int(p.name[1:]))
        previous = verify(old[-1]) if old else None
        if previous and previous["content_sha256"] == fingerprint:
            return {"status": "unchanged", "revision": str(old[-1]), "missing_sources": [k for k, v in payload["availability"].items() if v == "missing"]}
        number = int(old[-1].name[1:]) + 1 if old else 1
        target = day_dir / f"r{number:03d}"
        files = {"records.json": encode(payload), "conversations.zh-CN.md": render(payload)}
        manifest = {"schema_version": 1, "observation_date": day, "timezone": tz,
                    "exported_at_utc": datetime.now(timezone.utc).isoformat(), "revision": target.name,
                    "supersedes": old[-1].name if old else None, "content_sha256": fingerprint,
                    "sources": sources, "files": {k: sha(v) for k, v in files.items()},
                    "scope": "Selected records only; hashes establish copy consistency, not deployment authenticity or complete coverage."}
        temp = Path(tempfile.mkdtemp(prefix=".revision-", dir=day_dir))
        try:
            for name, raw in files.items():
                (temp / name).write_bytes(raw)
            (temp / "manifest.json").write_bytes(encode(manifest))
            verify(temp)
            temp.rename(target)
        finally:
            if temp.exists():
                shutil.rmtree(temp)
        return {"status": "created", "revision": str(target), "records": len(payload["records"]),
                "missing_sources": [k for k, v in payload["availability"].items() if v == "missing"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("export")
    build.add_argument("--date", required=True)
    build.add_argument("--timezone", default="America/Los_Angeles")
    build.add_argument("--room", type=Path)
    build.add_argument("--peer-private", type=Path)
    build.add_argument("--host-private", type=Path)
    build.add_argument("--operations", type=Path)
    build.add_argument("--out", type=Path, required=True)
    check = sub.add_parser("verify")
    check.add_argument("revision", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "verify":
            m = verify(args.revision)
            result = {"status": "verified", "revision": str(args.revision), "content_sha256": m["content_sha256"]}
        else:
            paths = dict(group=args.room, peer_private=args.peer_private, host_private=args.host_private, operations=args.operations)
            result = export(args.date, args.timezone, paths, args.out)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, OverflowError) as exc:
        print(f"Archive failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
