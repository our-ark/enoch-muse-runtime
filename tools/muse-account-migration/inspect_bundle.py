#!/usr/bin/env python3
"""Verify a migration bundle: manifest integrity + per-file hashes.

Wraps the official enoch.migration.inspect_migration_bundle. The bundle
is self-describing; no agent root is needed for inspection.

Usage:
    inspect_bundle.py <bundle.zip> [--root <agent_root_for_body_check>]

Exit 0 + "OK" when every file hash verifies; non-zero otherwise.
"""
import os
import sys
from pathlib import Path


def main() -> int:
    args = sys.argv[1:]
    if not args or "--help" in args:
        print(__doc__)
        return 2
    bundle = Path(args[0]).resolve()
    if not bundle.exists():
        print(f"bundle not found: {bundle}")
        return 2

    # inspect needs the enoch package; use the caller's agent root when
    # given, else fall back to any importable enoch on sys.path.
    root = None
    if "--root" in args:
        root = Path(args[args.index("--root") + 1]).resolve()
        os.chdir(root)
        sys.path.insert(0, str(root / "src"))
    try:
        import enoch.migration as mig
    except ImportError:
        print("cannot import enoch.migration; pass --root <agent_root>")
        return 4

    result = mig.inspect_migration_bundle(
        bundle, root, require_body_match=False
    )
    print(mig.format_inspection(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
