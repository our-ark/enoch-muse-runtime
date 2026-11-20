"""End-to-end test of the autonomous-private-chat chain, in a sandbox.

Chain under test (all subprocesses, real scripts, synthetic state):

    selfcheck_trigger.py --agent qingxia
        -> self-check prompt (+ history bundle) lands in qingxia's
           chat_inbox with a cursor-aware seq
    [daemon reply, simulated: the real daemon is not running here --
     the file below is exactly what the daemon's chat loop writes to
     chat_outbox when it answers]
        -> qingxia's chat_outbox gains one intent line
           "想和【至尊宝】说【……】"
    private_intent_relay.py --deliver-intent qingxia <id>
        -> RELAY-LAUNCHED; private_exchange.py (detached) seeds the
           intent into zhizunbao's chat_inbox
        -> the seed is found in zhizunbao's chat_inbox, and the seed
           is recorded in private.json

The detached exchange child is killed at the end of the test (it
would otherwise poll up to its 600 s timeout waiting for a reply
that never comes in the sandbox). Nothing here touches a live agent,
a live mailbox, or the production group home.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
GROUP = REPO / "group"
TRIGGER = GROUP / "selfcheck_trigger.py"
RELAY = GROUP / "private_intent_relay.py"

SEED_TEXT = "昨晚群里你说的那句话，我想再跟你聊聊"
INTENT_LINE = f"想和【至尊宝】说【{SEED_TEXT}】"


def make_agent(tmp_path, dirname, cursor):
    root = tmp_path / dirname
    mailbox = root / "mailbox"
    (mailbox / "chat_inbox").mkdir(parents=True)
    (mailbox / "chat_outbox").mkdir(parents=True)
    cursor_dir = root / ".enoch" / "channels" / "muse"
    cursor_dir.mkdir(parents=True)
    (cursor_dir / "cursor.json").write_text(
        json.dumps({"schema_version": 1, "cursor": cursor}),
        encoding="utf-8")
    return root, mailbox


@pytest.fixture()
def sandbox(tmp_path):
    q_root, q_mailbox = make_agent(tmp_path, "muse-enoch-agent", 358)
    z_root, z_mailbox = make_agent(tmp_path, "muse-zhizunbao-agent", 0)
    # One pre-existing message in zhizunbao's inbox so the relay's
    # drop_to (max+1) allocates seq 6, above the cursor.
    (z_mailbox / "chat_inbox" / "5.json").write_text(
        json.dumps({"seq": 5, "text": "old", "created_at": time.time()},
                   ensure_ascii=False), encoding="utf-8")
    ghome = tmp_path / "muse-group"
    (ghome / "hidden_files").mkdir(parents=True)
    (ghome / "room.md").write_text(
        "## 2026-11-19 20:00 [晚] \n"
        "话题：有没有一次，你明明赢了，心里却空了？\n"
        "🐵 至尊宝：金箍那天饭是热的、心是空的。\n"
        "⚔️ 青霞：赢了不算赢，心里有人接着才算。\n",
        encoding="utf-8")
    mdir = tmp_path / "memory"
    mdir.mkdir()
    env = dict(os.environ)
    env.update({
        "MUSE_GROUP_HOME": str(ghome),
        "MUSE_MEMORY_LOG_DIR": str(mdir),
        "MUSE_GROUP_QINGXIA_MAILBOX": str(q_mailbox),
        "MUSE_GROUP_ZHIZUNBAO_MAILBOX": str(z_mailbox),
        "MUSE_GROUP_BAIJINGJING_MAILBOX": str(tmp_path / "muse-baijingjing-agent" / "mailbox"),
        "MUSE_GROUP_TANGSANZANG_MAILBOX": str(tmp_path / "muse-tangsanzang-agent" / "mailbox"),
        "ENOCH_SRC": "/home/hatch/enoch-body",
    })
    return {
        "tmp": tmp_path, "env": env,
        "q_mailbox": q_mailbox, "z_mailbox": z_mailbox, "ghome": ghome,
        "child_pids": [],
    }


def run(cmd, env, timeout=60):
    return subprocess.run(cmd, env=env, capture_output=True, text=True,
                          timeout=timeout)


def wait_for(predicate, timeout=25.0, interval=0.5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        found = predicate()
        if found:
            return found
        time.sleep(interval)
    return None


def kill_child(sandbox):
    for pid in sandbox["child_pids"]:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    deadline = time.time() + 10
    while sandbox["child_pids"] and time.time() < deadline:
        alive = []
        for pid in sandbox["child_pids"]:
            try:
                os.kill(pid, 0)
                alive.append(pid)
            except ProcessLookupError:
                pass
        if not alive:
            return
        time.sleep(0.5)


def test_full_chain_trigger_to_private_seed(sandbox):
    env = sandbox["env"]
    q_inbox = sandbox["q_mailbox"] / "chat_inbox"
    z_inbox = sandbox["z_mailbox"] / "chat_inbox"
    try:
        # 1. Trigger: self-check prompt into qingxia's chat_inbox.
        r = run([sys.executable, str(TRIGGER), "--agent", "qingxia",
                 "--as-of", "2026-11-20T10:00:00-08:00"], env)
        assert r.returncode == 0, r.stderr
        assert "SELFCHECK-TRIGGERED agent=qingxia seq=359" in r.stdout
        delivered = json.loads(
            (q_inbox / "359.json").read_text(encoding="utf-8"))
        assert "[selfcheck 2026-11-20]" in delivered["text"]
        assert "自检历史 bundle：青霞" in delivered["text"]
        assert "明明赢了，心里却空了" in delivered["text"]  # room topic in bundle

        # 2. Simulate the daemon's own chat reply: one intent line in
        #    qingxia's chat_outbox (exactly what the daemon writes).
        reply_id = "e2e-reply-1"
        (sandbox["q_mailbox"] / "chat_outbox" / f"{reply_id}.json").write_text(
            json.dumps({"id": reply_id, "text": INTENT_LINE,
                        "created_at": time.time()}, ensure_ascii=False),
            encoding="utf-8")

        # 3. Relay: turn the intent line into a real private exchange.
        r = run([sys.executable, str(RELAY), "--deliver-intent",
                 "qingxia", reply_id], env)
        assert r.returncode == 0, r.stderr
        assert "RELAY-LAUNCHED from=qingxia to=zhizunbao" in r.stdout

        # 4. The detached exchange child seeds the intent into
        #    zhizunbao's chat_inbox (and records it in private.json).
        state = json.loads(
            (sandbox["ghome"] / "private_intent_state.json")
            .read_text(encoding="utf-8"))
        assert state["launches"], "relay recorded no launch"
        pid = state["launches"][-1]["pid"]
        sandbox["child_pids"].append(pid)

        def find_seed():
            for child in z_inbox.iterdir():
                if child.suffix != ".json":
                    continue
                try:
                    payload = json.loads(child.read_text(encoding="utf-8"))
                except (ValueError, OSError):
                    continue
                # NOTE: group_ctl labels qingxia "Qingxia" (pinyin) in
                # the seed prefix -- a pre-existing deployment quirk
                # (private_intent_relay LABEL_FIXES exists for it).
                # The seed is the private message itself, verbatim.
                if isinstance(payload.get("text"), str) \
                        and payload["text"] == f"[private] Qingxia: {SEED_TEXT}":
                    return payload
            return None

        seed = wait_for(find_seed)
        if seed is None:
            logs = ""
            ddir = sandbox["ghome"] / "private_digests"
            if ddir.is_dir():
                for lf in ddir.glob("*.log"):
                    logs += f"\n--- {lf.name} ---\n" + lf.read_text(
                        encoding="utf-8", errors="replace")
            raise AssertionError(
                "seed never landed in zhizunbao chat_inbox; "
                f"z_inbox={[c.name for c in z_inbox.iterdir()]}; "
                f"exchange logs:{logs}")
        assert seed is not None
        assert seed["seq"] == 6  # max(5, cursor 0) + 1 via drop_to
        assert seed["seq"] > 0

        private_json = sandbox["ghome"] / "private.json"
        assert private_json.exists()
        assert SEED_TEXT in private_json.read_text(encoding="utf-8")
    finally:
        kill_child(sandbox)


def test_trigger_dry_run_cli(sandbox):
    r = run([sys.executable, str(TRIGGER), "--agent", "qingxia",
             "--as-of", "2026-11-20T10:00:00-08:00", "--dry-run"],
            sandbox["env"])
    assert r.returncode == 0, r.stderr
    assert "SELFCHECK-DRY-RUN agent=qingxia" in r.stdout
    assert "[selfcheck 2026-11-20]" in r.stdout
    assert list((sandbox["q_mailbox"] / "chat_inbox").glob("*.json")) == []
