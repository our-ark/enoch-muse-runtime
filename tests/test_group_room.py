"""Tests for group/group_ctl.py room-server primitives.

Covers: outbox collection windowing/filtering, move-based staging
(ownership), delivered markers, and the exchange flag TTL. No daemon,
mailbox, or network is involved — all state lives under tmp_path.
"""

import json
import os
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "group"))
import group_ctl as gc  # noqa: E402


@pytest.fixture()
def room(tmp_path, monkeypatch):
    """Point all module-level room state at a temp dir."""
    home = tmp_path / "group"
    (home / "staged").mkdir(parents=True)
    for key, name in {
        "GROUP_HOME": home,
        "ROOM_JSON": home / "room.json",
        "ROOM_MD": home / "room.md",
        "ACTIVE": home / "exchange.active",
        "STAGED": home / "staged",
        "PRIVATE_JSON": home / "private.json",
        "PRIVATE_MD": home / "private.md",
        "CREDITS_JSON": home / "private_credits.json",
        "HOST_JSON": home / "group_host.json",
    }.items():
        monkeypatch.setattr(gc, key, name)
    monkeypatch.setitem(
        gc.AGENTS,
        "qingxia",
        {**gc.AGENTS["qingxia"], "mailbox": str(tmp_path / "mb-q")},
    )
    monkeypatch.setitem(
        gc.AGENTS,
        "zhizunbao",
        {**gc.AGENTS["zhizunbao"], "mailbox": str(tmp_path / "mb-z")},
    )
    return home


def _outbox(agent, tmp_path, name):
    outbox = tmp_path / agent / "chat_outbox"
    outbox.mkdir(parents=True, exist_ok=True)
    (outbox / f"{name}.json").write_text(
        json.dumps({"request_id": name, "text": f"reply {name}"}), encoding="utf-8"
    )
    # nudge mtime into the collection window
    now = time.time()
    os.utime(outbox / f"{name}.json", (now, now))
    return outbox


def test_collect_new_window_and_filters(room, tmp_path):
    _outbox("mb-q", tmp_path, "new1")
    old = tmp_path / "mb-q" / "chat_outbox" / "old1.json"
    old.write_text(json.dumps({"text": "stale"}), encoding="utf-8")
    stale = time.time() - 3600
    os.utime(old, (stale, stale))
    # noise files must be ignored
    (tmp_path / "mb-q" / "chat_outbox" / "note.txt").write_text("x")
    (tmp_path / "mb-q" / "chat_outbox" / "a.delivered").write_text("x")
    (tmp_path / "mb-q" / "chat_outbox" / "b.delivered.json").write_text("x")

    items = gc.collect_new("qingxia", time.time() - 60)
    assert [i["id"] for i in items] == ["new1"]
    assert items[0]["text"] == "reply new1"


def test_stage_collected_moves_and_claims_ownership(room, tmp_path):
    _outbox("mb-q", tmp_path, "m1")
    dest = gc.stage_collected("qingxia", "m1")
    assert dest == gc.STAGED / "qingxia" / "m1.json"
    assert dest.exists()
    src = tmp_path / "mb-q" / "chat_outbox" / "m1.json"
    assert not src.exists()  # moved, not copied: consumer can no longer see it
    payload = json.loads(dest.read_text(encoding="utf-8"))
    assert payload["text"] == "reply m1"


def test_stage_collected_missing_source_is_noop(room, tmp_path):
    dest = gc.stage_collected("qingxia", "ghost")
    assert dest == gc.STAGED / "qingxia" / "ghost.json"
    assert not dest.exists()


def test_mark_delivered(room, tmp_path):
    gc.mark_delivered("qingxia", "m2", "exch1")
    marker = tmp_path / "mb-q" / "chat_outbox" / "m2.delivered"
    assert marker.exists()
    assert "group-exchange exch1" in marker.read_text(encoding="utf-8")


def test_active_exchange_ttl(room):
    assert gc.active_exchange() is None
    st = {
        "exchange_id": "abc",
        "started_at": time.time(),
        "ttl_s": 60,
        "seed_seqs": {},
        "hops_used": 0,
    }
    gc.ACTIVE.write_text(json.dumps(st), encoding="utf-8")
    assert gc.active_exchange()["exchange_id"] == "abc"
    st["started_at"] = time.time() - 3600  # expired
    gc.ACTIVE.write_text(json.dumps(st), encoding="utf-8")
    assert gc.active_exchange() is None


def test_active_exchange_corrupt_file_is_none(room):
    gc.ACTIVE.write_text("{not json", encoding="utf-8")
    assert gc.active_exchange() is None


def test_end_exchange_clears_flag(room):
    gc.ACTIVE.write_text(
        json.dumps({"exchange_id": "x", "started_at": time.time(), "ttl_s": 60}),
        encoding="utf-8",
    )
    st = gc.end_exchange()
    assert st["exchange_id"] == "x"
    assert not gc.ACTIVE.exists()
    assert gc.end_exchange() is None


def test_say_appends_transcript(room):
    gc.say("观察者", "hello room", "human", "exch9")
    data = json.loads(gc.ROOM_JSON.read_text(encoding="utf-8"))
    assert len(data["transcript"]) == 1
    entry = data["transcript"][0]
    assert entry["speaker"] == "观察者"
    assert entry["text"] == "hello room"
    assert entry["exchange_id"] == "exch9"
    md = gc.ROOM_MD.read_text(encoding="utf-8")
    assert "观察者" in md and "hello room" in md


def test_begin_control_and_end(room):
    assert gc.active_exchange() is None
    st = gc.begin_control(ttl_s=60, note="test")
    assert st["control_only"] is True
    assert gc.active_exchange()["exchange_id"] == st["exchange_id"]
    with __import__("pytest").raises(RuntimeError):
        gc.begin_control()
    gc.end_exchange()
    assert gc.active_exchange() is None


def test_say_private_transcript(room):
    gc.say_private("qingxia", "zhizunbao", "悄悄话", "s1")
    data = json.loads(gc.PRIVATE_JSON.read_text(encoding="utf-8"))
    assert len(data["transcript"]) == 1
    e = data["transcript"][0]
    assert (e["from"], e["to"], e["text"]) == ("qingxia", "zhizunbao", "悄悄话")
    assert "悄悄话" in gc.PRIVATE_MD.read_text(encoding="utf-8")
    # 公共 transcript 不受影响
    assert not gc.ROOM_JSON.exists()


def test_credits_default_and_use(room):
    assert gc.credits_left("2026-09-20", "qingxia") == gc.NIGHTLY_CREDITS
    assert gc.use_credit("2026-09-20", "qingxia") == gc.NIGHTLY_CREDITS - 1
    assert gc.credits_left("2026-09-20", "qingxia") == gc.NIGHTLY_CREDITS - 1
    # 另一天互不影响
    assert gc.credits_left("2026-09-21", "qingxia") == gc.NIGHTLY_CREDITS


def test_credits_exhausted(room):
    import pytest

    for _ in range(gc.NIGHTLY_CREDITS):
        gc.use_credit("2026-09-20", "zhizunbao")
    assert gc.credits_left("2026-09-20", "zhizunbao") == 0
    with pytest.raises(RuntimeError):
        gc.use_credit("2026-09-20", "zhizunbao")


def test_next_host_rotates(room):
    assert gc.next_host() == "qingxia"
    assert gc.next_host() == "zhizunbao"
    assert gc.next_host() == "qingxia"
