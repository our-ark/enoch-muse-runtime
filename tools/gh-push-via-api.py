#!/usr/bin/env python3
"""Replay local unpushed commits to GitHub via the Git Data API.

git push fails in this environment (the vault credential helper hands
GitHub a stale token: "Invalid username or token"). The daily archive
already publishes through the Git Data API (bin/gh-api); this tool
reuses that route to push real commits instead of single archive
snapshots.

Safety model: each local commit is recreated object-by-object
(blob -> tree -> commit) with the exact same tree, parents,
author/committer name+email+timestamp and message, so the commit SHA
GitHub returns must equal the local SHA. The branch ref is only moved
after every commit in the range verifies. A mismatch aborts before
the ref is touched, so the remote branch can never be left pointing
at a rewritten history.

Usage:
    python3 tools/gh-push-via-api.py [--branch main] [--no-ref-update]

Requires the same setup as the dahua archive publisher:
~/workspace/custom-connectors/custom.legacy-github/bin/gh-api and
PYTHONPATH=/opt/muse/skills/custom-connector-setup/bin.
"""
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GH = os.path.expanduser("~/workspace/custom-connectors/custom.legacy-github/bin/gh-api")
ENV = dict(os.environ, PYTHONPATH="/opt/muse/skills/custom-connector-setup/bin")
REPO = "/repos/our-ark/enoch-muse-runtime"


def run_git(*args, binary=False):
    r = subprocess.run(["git", *args], cwd=REPO_DIR, capture_output=True)
    if r.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {r.stderr.decode(errors='replace')[:300]}")
    return r.stdout if binary else r.stdout.decode()


def api(method, path, body=None):
    args = ["python3", GH, method, path]
    tmp = None
    if body is not None:
        fd, tmp = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(body, f, ensure_ascii=False)
        args.append(tmp)
    try:
        r = subprocess.run(args, capture_output=True, text=True, env=ENV)
    finally:
        if tmp:
            os.unlink(tmp)
    out = json.loads(r.stdout)
    assert out["status"] < 300, (
        f"{method} {path} -> {out['status']}: "
        f"{json.dumps(out['body'], ensure_ascii=False)[:400]}"
    )
    return out["body"]


IDENT_RE = re.compile(r"^(.*) <(.*)> (\d+) ([+-]\d{4})$")


def parse_ident(s):
    m = IDENT_RE.match(s)
    assert m, f"unparsable ident: {s}"
    name, email, epoch, tz = m.group(1), m.group(2), int(m.group(3)), m.group(4)
    sign = 1 if tz[0] == "+" else -1
    off = timedelta(hours=int(tz[1:3]), minutes=int(tz[3:5])) * sign
    dt = datetime.fromtimestamp(epoch, timezone(off))
    return {"name": name, "email": email, "date": dt.isoformat()}


def parse_commit(sha):
    raw = run_git("cat-file", "commit", sha, binary=True)
    head, _, msg = raw.partition(b"\n\n")
    fields = {}
    parents = []
    for line in head.decode().splitlines():
        k, _, v = line.partition(" ")
        if k == "parent":
            parents.append(v)
        else:
            fields[k] = v
    for extra in ("gpgsig", "encoding", "mergetag"):
        assert extra not in fields, f"{sha}: unsupported header {extra}"
    return {
        "tree": fields["tree"],
        "parents": parents,
        "author": parse_ident(fields["author"]),
        "committer": parse_ident(fields["committer"]),
        "message": msg.decode(),
    }


def changed_files(sha):
    out = run_git("diff-tree", "--no-commit-id", "-r", sha)
    entries = []
    for line in out.splitlines():
        if not line.startswith(":"):
            continue
        meta, _, path = line.partition("\t")
        parts = meta.split()
        old_mode, new_mode, old_sha, new_sha, status = (
            parts[0][1:], parts[1], parts[2], parts[3], parts[4])
        assert status in "AMD", f"{sha}: unsupported change {status} {path}"
        entries.append({"path": path, "status": status, "mode": new_mode,
                        "sha": new_sha, "old_mode": old_mode})
    return entries


def main():
    branch = "main"
    no_ref_update = "--no-ref-update" in sys.argv
    if "--branch" in sys.argv:
        branch = sys.argv[sys.argv.index("--branch") + 1]
    subprocess.run(["git", "fetch", "origin"], cwd=REPO_DIR,
                   check=True, capture_output=True)
    for args in (["diff", "--quiet"], ["diff", "--cached", "--quiet"]):
        if subprocess.run(["git", *args], cwd=REPO_DIR).returncode != 0:
            raise SystemExit("working tree has uncommitted changes to tracked files; abort")
    base = run_git("rev-parse", f"origin/{branch}").strip()
    remote = api("GET", f"{REPO}/git/ref/heads/{branch}")
    assert remote["object"]["sha"] == base, "remote head moved since fetch; retry"
    commits = run_git("rev-list", "--reverse", f"origin/{branch}..HEAD").split()
    assert commits, "nothing to push"
    prev_commit = base
    prev_tree = run_git("rev-parse", f"{base}^{{tree}}").strip()
    for sha in commits:
        c = parse_commit(sha)
        assert c["parents"] == [prev_commit], f"{sha}: parent chain broken"
        entries = []
        for f in changed_files(sha):
            if f["status"] == "D":
                entries.append({"path": f["path"], "mode": f["old_mode"],
                                "type": "blob", "sha": None})
            else:
                raw = run_git("show", f"{sha}:{f['path']}", binary=True)
                blob = api("POST", f"{REPO}/git/blobs",
                           {"content": base64.b64encode(raw).decode(),
                            "encoding": "base64"})
                assert blob["sha"] == f["sha"], (
                    f"{sha} {f['path']}: blob sha mismatch")
                entries.append({"path": f["path"], "mode": f["mode"],
                                "type": "blob", "sha": blob["sha"]})
        tree = api("POST", f"{REPO}/git/trees",
                   {"base_tree": prev_tree, "tree": entries})
        assert tree["sha"] == c["tree"], (
            f"{sha}: tree sha mismatch ({tree['sha']} != {c['tree']})")
        newc = api("POST", f"{REPO}/git/commits", {
            "message": c["message"], "tree": tree["sha"],
            "parents": [prev_commit],
            "author": c["author"], "committer": c["committer"]})
        assert newc["sha"] == sha, (
            f"commit sha mismatch: {newc['sha']} != {sha}")
        print(f"{sha[:8]} recreated identical: {c['message'].splitlines()[0][:60]}")
        prev_commit, prev_tree = sha, c["tree"]
    if no_ref_update:
        print(f"verified {len(commits)} commits; ref NOT updated (--no-ref-update)")
        return
    upd = api("PATCH", f"{REPO}/git/refs/heads/{branch}",
              {"sha": prev_commit, "force": False})
    assert upd["object"]["sha"] == prev_commit, "ref update mismatch"
    subprocess.run(["git", "fetch", "origin"], cwd=REPO_DIR,
                   check=True, capture_output=True)
    head = run_git("rev-parse", f"origin/{branch}").strip()
    assert head == prev_commit, "post-push verification failed"
    print(f"pushed {len(commits)} commits; origin/{branch} is now {prev_commit}")


if __name__ == "__main__":
    main()
