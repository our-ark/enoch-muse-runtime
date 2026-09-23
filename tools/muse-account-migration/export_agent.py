#!/usr/bin/env python3
"""Export a Muse/Enoch agent root into a verified migration bundle.

Wraps the official enoch.migration.export_migration_bundle; adds nothing
except CLI handling and a pre-flight production guard.

Usage:
    export_agent.py <agent_root> <output_bundle.zip> [--include-artifacts] [--force]

The daemon for <agent_root> must be stopped before export (official
requirement). --force bypasses the production-path guard; without it the
script refuses to export the four live production roots.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

# Live production roots: never export these directly. Export a copy.
PRODUCTION_ROOTS = {
    Path("/home/hatch/workspace/muse-enoch-agent"),
    Path("/home/hatch/workspace/muse-zhizunbao-agent"),
    Path("/home/hatch/workspace/muse-baijingjing-agent"),
    Path("/home/hatch/workspace/muse-tangsanzang-agent"),
}


def _daemon_alive(root: Path) -> bool:
    """True if the agent's daemon pid file points at a live matching process."""
    pid_file = root / "mailbox" / "enoch-daemon.pid"
    try:
        pid = int(pid_file.read_text().strip().split()[0])
    except (OSError, ValueError, IndexError):
        return False
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline = f.read().decode(errors="replace")
    except OSError:
        return False
    return f"--root={root}" in cmdline or f"--root {root}" in cmdline.replace("\x00", " ")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if len(args) != 2 or "--help" in flags:
        print(__doc__)
        return 2
    root = Path(args[0]).resolve()
    bundle = Path(args[1])
    if root in PRODUCTION_ROOTS and "--force" not in flags:
        print(f"refusing to export live production root: {root}")
        print("export a copy instead, or pass --force")
        return 3
    if not (root / "src" / "enoch" / "migration.py").exists():
        print(f"not an enoch agent root (no src/enoch/migration.py): {root}")
        return 4
    if _daemon_alive(root):
        print(f"daemon is still running for {root}; stop it before export")
        return 5

    # Same convention as bin/enoch: cd to root so runtime dependencies
    # resolve from the agent's own libraries/.
    os.chdir(root)
    sys.path.insert(0, str(root / "src"))
    import enoch.migration as mig

    # The bridge mailbox/ is untracked runtime state, not part of the
    # bundle, but its presence fails the official clean-worktree check.
    # Stash it outside the worktree for the duration of the export.
    mailbox = root / "mailbox"
    stash = None
    if mailbox.exists():
        stash = Path(tempfile.mkdtemp(prefix="mailbox-stash-"))
        shutil.move(str(mailbox), str(stash / "mailbox"))
    try:
        result = mig.export_migration_bundle(
            bundle,
            root,
            include_artifacts="--include-artifacts" in flags,
        )
    finally:
        if stash is not None:
            shutil.move(str(stash / "mailbox"), str(mailbox))
            shutil.rmtree(stash, ignore_errors=True)
    print(f"migration_id: {result.migration_id}")
    print(f"bundle: {result.bundle_path}")
    print(f"sha256: {result.bundle_sha256}")
    print(f"body_revision: {result.body_revision}")
    print(f"files: {result.files} ({result.bytes} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
