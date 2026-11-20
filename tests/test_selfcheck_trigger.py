"""Tests for group/selfcheck_trigger.py.

The trigger writes the daytime self-check into the agent's own
chat_inbox (the channel the daemon actually reads) instead of
mailbox/inbox (which only the consumer ever answered). All tests run
against synthetic sandbox roots and group homes; nothing here touches
a live agent, a live mailbox, or the production group home.
"""

import json
import stat
import sys
import time
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "group"))

import selfcheck_trigger as st  # noqa: E402


@pytest.fixture()
def env(monkeypatch, tmp_path):
    """A sandbox agent root + group home, wired through the same env
    vars the production code reads."""
    root = tmp_path / "muse-enoch-agent"
    mailbox = root / "mailbox"
    chat_inbox = mailbox / "chat_inbox"
    chat_outbox = mailbox / "chat_outbox"
    chat_inbox.mkdir(parents=True)
    chat_outbox.mkdir(parents=True)
    (root / ".enoch" / "channels" / "muse").mkdir(parents=True)
    ghome = tmp_path / "muse-group"
    (ghome / "hidden_files").mkdir(parents=True)
    mdir = tmp_path / "memory"
    mdir.mkdir()
    monkeypatch.setenv("MUSE_GROUP_QINGXIA_MAILBOX", str(mailbox))
    monkeypatch.setenv("MUSE_GROUP_HOME", str(ghome))
    monkeypatch.setenv("MUSE_MEMORY_LOG_DIR", str(mdir))
    return {
        "root": root, "mailbox": mailbox, "chat_inbox": chat_inbox,
        "chat_outbox": chat_outbox, "ghome": ghome, "mdir": mdir,
    }


def write_cursor(env, cursor):
    p = env["root"] / ".enoch" / "channels" / "muse" / "cursor.json"
    p.write_text(json.dumps({"schema_version": 1, "cursor": cursor}),
                 encoding="utf-8")


def write_inbox(env, seq, text):
    p = env["chat_inbox"] / f"{seq}.json"
    p.write_text(json.dumps({"seq": seq, "text": text,
                             "created_at": time.time()}, ensure_ascii=False),
                 encoding="utf-8")
    return p


def as_of(s="2026-11-20T10:00:00-08:00"):
    return datetime.fromisoformat(s)


# --- seq allocation -------------------------------------------------

def test_next_seq_above_files_and_cursor(env):
    write_cursor(env, 358)
    write_inbox(env, 356, "x")
    write_inbox(env, 357, "y")
    assert st.next_seq(env["chat_inbox"], st.read_cursor(env["root"])) == 359


def test_next_seq_cursor_ahead_of_files(env):
    # Files were deleted / cursor moved on: never reuse a seq.
    write_cursor(env, 400)
    write_inbox(env, 357, "y")
    assert st.next_seq(env["chat_inbox"], st.read_cursor(env["root"])) == 401


def test_next_seq_empty_inbox_no_cursor(env):
    assert st.next_seq(env["chat_inbox"], st.read_cursor(env["root"])) == 1


def test_read_cursor_missing_or_bad(env):
    assert st.read_cursor(env["root"]) == 0
    p = env["root"] / ".enoch" / "channels" / "muse" / "cursor.json"
    p.write_text("not json", encoding="utf-8")
    assert st.read_cursor(env["root"]) == 0
    p.write_text(json.dumps({"cursor": "abc"}), encoding="utf-8")
    assert st.read_cursor(env["root"]) == 0


def test_next_seq_ignores_non_numeric_stems(env):
    write_cursor(env, 10)
    (env["chat_inbox"] / "delivered.json").write_text("{}", encoding="utf-8")
    (env["chat_inbox"] / ".12.json.tmp-1").write_text("{}", encoding="utf-8")
    assert st.next_seq(env["chat_inbox"], 10) == 11


# --- atomic delivery ------------------------------------------------

def test_deliver_atomic_and_mode_0600(env):
    path = st.deliver(env["chat_inbox"], 359, "hello")
    assert path == env["chat_inbox"] / "359.json"
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["seq"] == 359
    assert payload["text"] == "hello"
    assert isinstance(payload["created_at"], float)
    assert not list(env["chat_inbox"].glob(".*.tmp-*"))


# --- already-triggered scan -----------------------------------------

def test_already_triggered_by_marker_text(env):
    write_inbox(env, 359, "[selfcheck 2026-11-20] 白天自检：……")
    assert st.already_triggered(env["chat_inbox"], "2026-11-20") is True
    assert st.already_triggered(env["chat_inbox"], "2026-11-19") is False


def test_already_triggered_ignores_unreadable_files(env):
    (env["chat_inbox"] / "360.json").write_text("{broken", encoding="utf-8")
    assert st.already_triggered(env["chat_inbox"], "2026-11-20") is False


# --- trigger: happy path, idempotency, defer ------------------------

def test_trigger_writes_prompt_bundle_and_marker(env):
    write_cursor(env, 358)
    (env["ghome"] / "room.md").write_text(
        "## 2026-11-19 20:00 [晚] \n话题：赢了却空了\n⚔️ 青霞：赢了不算赢。\n",
        encoding="utf-8")
    status, seq = st.trigger("qingxia", as_of(), with_context=True)
    assert status == "SELFCHECK-TRIGGERED"
    assert seq == "359"
    path = env["chat_inbox"] / "359.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["seq"] == 359
    assert "[selfcheck 2026-11-20]" in payload["text"]
    assert "想和【某人】说【……】" in payload["text"]
    assert "跳过，理由是" in payload["text"]
    assert "自检历史 bundle：青霞" in payload["text"]
    assert "赢了却空了" in payload["text"]  # bundle content attached
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert (env["ghome"] / "hidden_files"
            / "round-done-2026-11-20-selfcheck-qingxia").exists()


def test_trigger_no_context(env):
    status, seq = st.trigger("qingxia", as_of(), with_context=False)
    assert status == "SELFCHECK-TRIGGERED"
    payload = json.loads(
        (env["chat_inbox"] / f"{seq}.json").read_text(encoding="utf-8"))
    assert "自检历史 bundle" not in payload["text"]
    assert "[selfcheck 2026-11-20]" in payload["text"]


def test_trigger_idempotent_by_marker(env):
    st.trigger("qingxia", as_of())
    assert len(list(env["chat_inbox"].glob("*.json"))) == 1
    status, _ = st.trigger("qingxia", as_of())
    assert status == "SELFCHECK-ALREADY-DONE"
    assert len(list(env["chat_inbox"].glob("*.json"))) == 1


def test_trigger_idempotent_by_scan_when_marker_lost(env):
    # Marker file deleted (crash between deliver and mark): the scan
    # of today's chat_inbox must still prevent a second delivery.
    st.trigger("qingxia", as_of())
    marker = (env["ghome"] / "hidden_files"
              / "round-done-2026-11-20-selfcheck-qingxia")
    marker.unlink()
    status, _ = st.trigger("qingxia", as_of())
    assert status == "SELFCHECK-ALREADY-DONE"
    assert len(list(env["chat_inbox"].glob("*.json"))) == 1


def test_trigger_force_retriggers(env):
    _status, first = st.trigger("qingxia", as_of())
    status, seq = st.trigger("qingxia", as_of(), force=True)
    assert status == "SELFCHECK-TRIGGERED"
    assert seq == str(int(first) + 1)
    assert len(list(env["chat_inbox"].glob("*.json"))) == 2


def test_trigger_defers_on_active_exchange(env):
    (env["ghome"] / "exchange.active").write_text(json.dumps({
        "exchange_id": "abc", "started_at": time.time(), "ttl_s": 900,
    }), encoding="utf-8")
    status, detail = st.trigger("qingxia", as_of())
    assert status == "SELFCHECK-DEFERRED"
    assert detail == ""
    # Deferred writes NO marker and NO message: the next retry can run.
    assert not (env["ghome"] / "hidden_files"
                / "round-done-2026-11-20-selfcheck-qingxia").exists()
    assert list(env["chat_inbox"].glob("*.json")) == []


def test_trigger_proceeds_when_exchange_flag_expired(env):
    (env["ghome"] / "exchange.active").write_text(json.dumps({
        "exchange_id": "abc", "started_at": time.time() - 3600,
        "ttl_s": 900,
    }), encoding="utf-8")
    status, _ = st.trigger("qingxia", as_of())
    assert status == "SELFCHECK-TRIGGERED"


def test_trigger_dry_run_delivers_nothing(env):
    status, text = st.trigger("qingxia", as_of(), dry_run=True)
    assert status == "SELFCHECK-DRY-RUN"
    assert "[selfcheck 2026-11-20]" in text
    assert list(env["chat_inbox"].glob("*.json")) == []
    assert not (env["ghome"] / "hidden_files"
                / "round-done-2026-11-20-selfcheck-qingxia").exists()


def test_trigger_unknown_agent(env):
    with pytest.raises(ValueError):
        st.trigger("zixia", as_of())


# --- prompt content ---------------------------------------------------

def test_prompt_names_all_people_and_both_formats(env):
    text = st.build_prompt("qingxia", as_of(), bundle="")
    for name in ("青霞", "至尊宝", "白晶晶", "唐三藏", "紫霞", "观察者"):
        assert name in text
    assert "想和【某人】说【……】" in text
    assert "跳过，理由是" in text


def test_qingxia_root_is_never_derived_from_name(monkeypatch, tmp_path):
    # Regression: qingxia's root is muse-enoch-agent, never
    # muse-qingxia-agent (an abandoned empty shell).
    from selfcheck_context import resolve_mailbox
    monkeypatch.delenv("MUSE_GROUP_QINGXIA_MAILBOX", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert resolve_mailbox("qingxia", None).parent.name == "muse-enoch-agent"


# --- CLI ---------------------------------------------------------------

def test_cli_triggered_and_second_run_done(capsys, env):
    write_cursor(env, 358)
    assert st.main(["--agent", "qingxia", "--as-of",
                    "2026-11-20T10:00:00-08:00"]) == 0
    out = capsys.readouterr().out
    assert "SELFCHECK-TRIGGERED agent=qingxia seq=359" in out
    assert st.main(["--agent", "qingxia", "--as-of",
                    "2026-11-20T10:00:00-08:00"]) == 0
    assert "SELFCHECK-ALREADY-DONE agent=qingxia" in capsys.readouterr().out


def test_cli_dry_run(capsys, env):
    assert st.main(["--agent", "qingxia", "--as-of",
                    "2026-11-20T10:00:00-08:00", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "SELFCHECK-DRY-RUN agent=qingxia" in out
    assert "[selfcheck 2026-11-20]" in out
