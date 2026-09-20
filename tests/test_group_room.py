"""Tests for group/group_ctl.py room-server primitives.

Covers: outbox collection windowing/filtering, move-based staging
(ownership), delivered markers, the exchange flag TTL, chronological
merging of both agents' replies, and verbatim digest labels. No daemon,
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
    gc.say("observer", "hello room", "human", "exch9")
    data = json.loads(gc.ROOM_JSON.read_text(encoding="utf-8"))
    assert len(data["transcript"]) == 1
    entry = data["transcript"][0]
    assert entry["speaker"] == "observer"
    assert entry["text"] == "hello room"
    assert entry["exchange_id"] == "exch9"
    md = gc.ROOM_MD.read_text(encoding="utf-8")
    assert "observer" in md and "hello room" in md


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
    gc.say_private("qingxia", "zhizunbao", "a quiet word", "s1")
    data = json.loads(gc.PRIVATE_JSON.read_text(encoding="utf-8"))
    assert len(data["transcript"]) == 1
    e = data["transcript"][0]
    assert (e["from"], e["to"], e["text"]) == ("qingxia", "zhizunbao", "a quiet word")
    assert "a quiet word" in gc.PRIVATE_MD.read_text(encoding="utf-8")
    assert "[private qingxia->zhizunbao]" in gc.PRIVATE_MD.read_text(encoding="utf-8")
    # public transcript unaffected
    assert not gc.ROOM_JSON.exists()


def test_credits_default_and_use(room):
    assert gc.credits_left("2026-09-20", "qingxia") == gc.NIGHTLY_CREDITS
    assert gc.use_credit("2026-09-20", "qingxia") == gc.NIGHTLY_CREDITS - 1
    assert gc.credits_left("2026-09-20", "qingxia") == gc.NIGHTLY_CREDITS - 1
    # a different day is unaffected
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


def test_fanout_room_message(room, tmp_path, monkeypatch):
    dropped = []
    monkeypatch.setattr(
        gc, "drop_to", lambda agent, text: dropped.append((agent, text)) or 99
    )
    monkeypatch.setattr(gc, "HOST_NAME", "host")
    seqs = gc.fanout_room_message("host", "I'm here too", "exchZ")
    assert seqs == {"qingxia": 99, "zhizunbao": 99}
    assert dropped == [
        ("qingxia", "[group] host: I'm here too"),
        ("zhizunbao", "[group] host: I'm here too"),
    ]
    data = json.loads(gc.ROOM_JSON.read_text(encoding="utf-8"))
    assert len(data["transcript"]) == 1
    e = data["transcript"][0]
    assert e["speaker"] == "host"
    assert e["kind"] == "host"
    assert e["text"] == "I'm here too"
    assert e["exchange_id"] == "exchZ"
    assert "I'm here too" in gc.ROOM_MD.read_text(encoding="utf-8")


def test_fanout_room_message_non_host_is_human(room, tmp_path, monkeypatch):
    monkeypatch.setattr(
        gc, "drop_to", lambda agent, text: 99
    )
    monkeypatch.setattr(gc, "HOST_NAME", "host")
    gc.fanout_room_message("observer", "listening in", "exchH")
    data = json.loads(gc.ROOM_JSON.read_text(encoding="utf-8"))
    assert data["transcript"][-1]["kind"] == "human"


def test_format_digest_keeps_text_verbatim():
    out = gc.format_digest(
        "📜 group digest · afternoon",
        [("opening", "Qingxia: let's talk about the moon"), ("⚔️ **Qingxia**", "the moon is round"), ("host interjection", "Zixia: agreed")],
    )
    assert out.startswith("📜 group digest · afternoon\n")
    assert "[opening] Qingxia: let's talk about the moon" in out
    assert "[⚔️ **Qingxia**] the moon is round" in out
    assert "[host interjection] Zixia: agreed" in out
    # chronological order: opening < reply < interjection
    assert out.index("opening") < out.index("the moon is round") < out.index("agreed")


def test_format_digest_sorts_by_timestamp_not_collection_order():
    # Entries arrive from both agents in the driver's fixed poll order, but
    # the digest must follow real arrival times.
    lines = [
        ("⚔️ **Qingxia**", "collected first", 1000.3),
        ("opening", "host opened the round", 1000.0),
        ("🐵 **Zhizunbao**", "arrived second", 1000.2),
        ("host interjection", "interjected third", 1000.4),
    ]
    out = gc.format_digest("title", lines)
    i_open = out.index("host opened the round")
    i_second = out.index("arrived second")
    i_first = out.index("collected first")
    i_third = out.index("interjected third")
    assert i_open < i_second < i_first < i_third
    # labels stay verbatim — not rewritten by the sort
    assert "[⚔️ **Qingxia**] collected first" in out
    assert "[🐵 **Zhizunbao**] arrived second" in out


def test_merge_collected_orders_by_mtime():
    items = [
        ("qingxia", {"id": "a", "mtime": 2000.5, "text": "later q"}),
        ("zhizunbao", {"id": "b", "mtime": 2000.1, "text": "earlier z"}),
        ("qingxia", {"id": "c", "mtime": 2000.3, "text": "middle q"}),
    ]
    merged = gc.merge_collected(items)
    assert [i["id"] for _, i in merged] == ["b", "c", "a"]
    assert [a for a, _ in merged] == ["zhizunbao", "qingxia", "qingxia"]


def test_agent_labels_are_english_and_verbatim():
    assert gc.AGENTS["qingxia"]["name"] == "Qingxia"
    assert gc.AGENTS["qingxia"]["chat_label"] == "⚔️ **Qingxia**"
    assert gc.AGENTS["zhizunbao"]["name"] == "Zhizunbao"
    assert gc.AGENTS["zhizunbao"]["chat_label"] == "🐵 **Zhizunbao**"


def test_private_label_kept_verbatim():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "group"))
    import private_exchange as px  # noqa: E402

    lbl = px.label("qingxia", "zhizunbao")
    assert lbl == "⚔️ **Qingxia** [private→Zhizunbao]"
    # and the digest carries that full label unchanged
    out = gc.format_digest("title", [(lbl, "a quiet word", 1000.0)])
    assert "[⚔️ **Qingxia** [private→Zhizunbao]] a quiet word" in out


def test_await_host_drop_hit_and_miss(tmp_path):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "group"))
    import group_exchange as gx  # noqa: E402

    d = tmp_path / "drops"
    (d / "eid1").mkdir(parents=True)
    (d / "eid1" / "host-1.txt").write_text("the host has arrived", encoding="utf-8")
    assert gx.await_host_drop(d, "eid1", 1, 5) == "the host has arrived"
    t0 = time.time()
    assert gx.await_host_drop(d, "eid1", 2, 0) is None
    assert time.time() - t0 < 5
    # blank files count as not written, must not be picked up
    (d / "eid1" / "host-3.txt").write_text("   \n", encoding="utf-8")
    assert gx.await_host_drop(d, "eid1", 3, 0) is None
