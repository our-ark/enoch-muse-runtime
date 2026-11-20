"""Tests for group/selfcheck_context.py.

The bundle builder is read-only: all state lives under tmp_path, no
daemon, mailbox, or network is involved. Fixtures mimic the deployed
layout (agent root with .enoch/memory + .enoch/conversation, group
home with room.md / private.json / hidden_files/chat-replies.log,
host memory logs).
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "group"))
import selfcheck_context as sc  # noqa: E402

AS_OF = "2026-11-16T12:00:00-08:00"


@pytest.fixture()
def env(tmp_path, monkeypatch):
    """Fake deployment rooted at tmp_path; returns paths dict."""
    home = tmp_path / "home"
    ws = home / "workspace"
    # Agent root: qingxia's real root name is muse-enoch-agent on purpose
    # (the name-derived muse-qingxia-agent must never be used).
    root = ws / "muse-enoch-agent"
    mailbox = root / "mailbox"
    (root / ".enoch" / "memory").mkdir(parents=True)
    (root / ".enoch" / "conversation").mkdir(parents=True)
    (mailbox / "chat_inbox").mkdir(parents=True)
    (mailbox / "chat_outbox").mkdir(parents=True)
    ghome = ws / "muse-group"
    (ghome / "hidden_files").mkdir(parents=True)
    mdir = home / "memory"
    mdir.mkdir(parents=True)
    monkeypatch.setenv("MUSE_GROUP_HOME", str(ghome))
    monkeypatch.setenv("MUSE_MEMORY_LOG_DIR", str(mdir))
    monkeypatch.setenv("MUSE_GROUP_QINGXIA_MAILBOX", str(mailbox))
    # HOME is used only by the default-root fallback; point it at the
    # fake home so a test that forgets the env override still lands here.
    monkeypatch.setenv("HOME", str(home))
    return {"home": home, "ws": ws, "root": root, "mailbox": mailbox,
            "ghome": ghome, "mdir": mdir}


def write_long_term(root, entries):
    p = root / ".enoch" / "memory" / "long_term.json"
    p.write_text(json.dumps(
        {"schema_version": 1, "memories": entries}, ensure_ascii=False), encoding="utf-8")


def write_conversation(root, name, replies, mtime_epoch):
    p = root / ".enoch" / "conversation" / name
    p.write_text(json.dumps(
        {"schema_version": 1,
         "steps": [{"reply": r, "state": "planned"} for r in replies]},
        ensure_ascii=False), encoding="utf-8")
    os.utime(p, (mtime_epoch, mtime_epoch))


def test_bundle_includes_all_sources(env):
    write_long_term(env["root"], [
        {"id": "mem_1", "type": "decision", "text": "测试记忆：喜欢直接说中文。",
         "created_at": "2026-09-18T21:30:12+00:00", "updated_at": "2026-09-18T21:30:12+00:00"},
    ])
    write_conversation(env["root"], "a1.json", ["我说过一句没说完的话。"], 1794772800)
    (env["ghome"] / "room.md").write_text(
        "## 2026-11-15 20:03 [群聊·晚/主持：至尊宝]\n\n话题：有没有一次，你明明赢了，心里却空了？\n\n"
        "⚔️ 青霞：有。赢了剑，心里却空了。\n\n🐵 至尊宝：青霞，你那半句话还没说完吧？\n",
        encoding="utf-8")
    (env["ghome"] / "private.json").write_text(json.dumps(
        {"session": "private", "transcript": [], "transcripts": [
            {"t": 1794787500.0, "from": "tangsanzang", "to": "qingxia",
             "text": "青霞，那半句话不用急着说完。", "session_id": "aa11"},
        ]}, ensure_ascii=False), encoding="utf-8")
    (env["ghome"] / "hidden_files" / "chat-replies.log").write_text(
        "[2026-11-15 20:03:36] 青霞 abc123: 有。赢了剑，心里却空了。\n",
        encoding="utf-8")
    (env["mdir"] / "2026-11-15.md").write_text(
        "青霞那半句话还卡着，等她自己开口。\n", encoding="utf-8")

    out = sc.build_bundle("qingxia", sc.parse_as_of(AS_OF), None)
    assert "测试记忆：喜欢直接说中文" in out
    assert "我说过一句没说完的话" in out
    assert "有没有一次，你明明赢了" in out
    assert "那半句话不用急着说完" in out
    assert "赢了剑，心里却空了" in out
    assert "半句话还卡着" in out
    assert "候选未了线索" in out
    # Long-term memory staleness must be visible.
    assert "2026-09-27" in out


def test_as_of_excludes_future_items(env):
    (env["ghome"] / "room.md").write_text(
        "## 2026-11-15 20:03 [群聊·晚/主持：至尊宝]\n\n话题：过去的话题。\n\n"
        "⚔️ 青霞：过去的话。\n\n"
        "## 2026-11-19 20:03 [群聊·晚/主持：至尊宝]\n\n话题：未来的话题。\n\n"
        "⚔️ 青霞：未来的话。\n",
        encoding="utf-8")
    out = sc.build_bundle("qingxia", sc.parse_as_of("2026-11-16T12:00:00-08:00"), None)
    assert "过去的话题" in out
    assert "未来的话题" not in out
    assert "未来的话" not in out


def test_missing_sources_are_reported_not_fatal(env, tmp_path, monkeypatch):
    # Point baijingjing at a nonexistent root so nothing is read from
    # the real deployment.
    monkeypatch.setenv("MUSE_GROUP_BAIJINGJING_MAILBOX", str(tmp_path / "nope" / "mailbox"))
    out = sc.build_bundle("baijingjing", sc.parse_as_of(AS_OF), None)
    # baijingjing has no fixture root at all in this env; every section
    # must degrade to a note, and the call must still succeed.
    assert "缺失" in out or "（无）" in out
    assert "自检历史 bundle：白晶晶" in out


def test_candidates_need_person_and_open_marker(env):
    room = (
        "## 2026-11-16 10:00 [群聊·晚/主持：至尊宝]\n\n话题：今天的话题。\n\n"
        "⚔️ 青霞：我想问至尊宝一件事，还没想好怎么说。\n\n"
        "💀 白晶晶：那条手帕我还留着，等不到他是一回事。\n\n"
        "📿 唐三藏：青霞，你上次说的那件事，后来怎么样了？\n"
    )
    (env["ghome"] / "room.md").write_text(room, encoding="utf-8")
    out = sc.build_bundle("qingxia", sc.parse_as_of(AS_OF), None)
    cand = out.split("## 七、")[1]
    # 青霞's own line names 至尊宝 + 还没 -> candidate.
    assert "至尊宝" in cand
    # 唐三藏's line asks 青霞 a question -> candidate with 唐三藏.
    assert "唐三藏" in cand
    # 白晶晶's own open line (others-scan) -> candidate with 白晶晶.
    assert "白晶晶" in cand
    assert "手帕" in cand
    # The bare topic names nobody and has no marker -> not a candidate.
    assert "今天的话题" not in cand


def test_old_items_are_not_candidates(env):
    (env["ghome"] / "room.md").write_text(
        "## 2026-11-10 20:03 [群聊·晚/主持：至尊宝]\n\n话题：很久以前的话题。\n\n"
        "⚔️ 青霞：我想问至尊宝一件事，还没想好怎么说。\n",
        encoding="utf-8")
    out = sc.build_bundle("qingxia", sc.parse_as_of(AS_OF), None)
    assert "（无候选。" in out


def test_builder_writes_nothing(env):
    write_long_term(env["root"], [])
    before = sorted(str(p) for p in env["home"].rglob("*"))
    sc.build_bundle("qingxia", sc.parse_as_of(AS_OF), None)
    after = sorted(str(p) for p in env["home"].rglob("*"))
    assert before == after


def test_candidates_section_survives_huge_earlier_sections(env):
    # Long operational lines in the host logs must not push section 7
    # out of the bundle.
    long_line = "x" * 400
    (env["mdir"] / "2026-11-15.md").write_text(
        "\n".join(f"{long_line} 青霞" for _ in range(20)), encoding="utf-8")
    (env["ghome"] / "room.md").write_text(
        "## 2026-11-16 10:00 [群聊·晚/主持：至尊宝]\n\n话题：今天的话题。\n\n"
        "⚔️ 青霞：我想问至尊宝一件事，还没想好怎么说。\n",
        encoding="utf-8")
    out = sc.build_bundle("qingxia", sc.parse_as_of(AS_OF), None)
    assert "## 七、候选未了线索" in out
    assert "至尊宝" in out.split("## 七、")[1]
    assert len(out) <= sc.MAX_BUNDLE_CHARS + 100


def test_memory_log_cap_keeps_newest_lines(env):
    # Days are read newest-first; the 150-line scan cap must keep the
    # newest lines, not the first ones (an earlier bug kept the oldest).
    (env["mdir"] / "2026-11-14.md").write_text(
        "\n".join(f"旧行 {i} 青霞" for i in range(160)), encoding="utf-8")
    (env["mdir"] / "2026-11-16.md").write_text(
        "## 11:00 上午\n- 11:00 最新行 青霞\n", encoding="utf-8")
    out = sc.read_memory_logs(env["mdir"], "青霞", sc.parse_as_of(AS_OF))
    assert len(out) == 150
    assert out[0]["day"] == "2026-11-16"
    assert any("最新行" in ln["text"] for ln in out)


def test_memory_log_same_day_future_lines_excluded(env):
    # A same-day line written after the trigger must not leak into
    # the bundle (in one real case the 12:02 line already narrated
    # the 12:00 round's answer). Dateless same-day lines are also out.
    (env["mdir"] / "2026-11-16.md").write_text(
        "无时间行 青霞，还没说完。\n"
        "## 11:00 上午\n- 11:00 早行 青霞，还没说完。\n"
        "## 13:00 下午\n- 13:00 晚行 青霞，还没说完。\n",
        encoding="utf-8")
    out = sc.read_memory_logs(env["mdir"], "青霞", sc.parse_as_of(AS_OF))
    texts = [ln["text"] for ln in out]
    assert any("早行" in t for t in texts)
    assert not any("晚行" in t for t in texts)
    assert not any("无时间行" in t for t in texts)


def test_memory_log_lines_feed_candidates(env):
    # The host daily log is the only place that narrates who talked to
    # whom in the operator's private exchanges.
    (env["mdir"] / "2026-11-15.md").write_text(
        "青霞那半句话还卡着，等她自己开口，紫霞替她记着。\n", encoding="utf-8")
    out = sc.build_bundle("qingxia", sc.parse_as_of(AS_OF), None)
    cand = out.split("## 七、")[1]
    assert "紫霞" in cand
    assert "半句" in cand


def test_memory_log_candidate_names_nearest_person(env, tmp_path, monkeypatch):
    # A summary line names several people; the thread belongs to the
    # person nearest the marker, not the first-named (e.g. the host).
    monkeypatch.setenv("MUSE_GROUP_ZHIZUNBAO_MAILBOX", str(tmp_path / "nope" / "mailbox"))
    (env["mdir"] / "2026-11-15.md").write_text(
        "2026-11-14 晚群聊（白晶晶主持）上，至尊宝说粗瓷碗的事还没想好要问什么，"
        "等想明白了第一个告诉紫霞。\n",
        encoding="utf-8")
    out = sc.build_bundle("zhizunbao", sc.parse_as_of(AS_OF), None)
    cand = out.split("## 七、")[1]
    assert "与紫霞有关" in cand
    assert "与白晶晶有关" not in cand


def test_mailbox_override_beats_default_map(tmp_path, monkeypatch):
    box = tmp_path / "somewhere" / "mailbox"
    (box / "chat_inbox").mkdir(parents=True)
    out = sc.build_bundle("qingxia", sc.parse_as_of(AS_OF), str(box))
    assert "自检历史 bundle：青霞" in out
