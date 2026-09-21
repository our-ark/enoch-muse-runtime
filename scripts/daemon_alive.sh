#!/usr/bin/env bash
# Exit 0 if the Enoch daemon supervisor is alive, 1 otherwise.
#
# Guards against stale pidfiles and PID reuse: a live PID alone is not
# enough, the process's cmdline must match our daemon supervisor
# (muse_instance.py ... daemon). Used by the mailbox-consumer supervision
# step instead of a bare `kill -0` on the pidfile.
set -uo pipefail

MAILBOX="${1:-${ENOCH_MUSE_MAILBOX:-$HOME/workspace/muse-enoch/mailbox}}"
pidfile="$MAILBOX/enoch-daemon.pid"

[ -f "$pidfile" ] || exit 1
pid="$(tr -d '[:space:]' < "$pidfile" 2>/dev/null)"
case "$pid" in '' | *[!0-9]*) exit 1 ;; esac
[ -d "/proc/$pid" ] || exit 1

cmdline="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null)"
case "$cmdline" in
*muse_instance.py*daemon*) ;;
*) exit 1 ;;
esac

# Identity check (2026-09-21): a live pid with a matching cmdline is not
# enough. After a mass restart the kernel recycles pids quickly, and the
# number in a stale pidfile may now belong to a *different* agent's daemon
# (observed: 白晶晶's pidfile kept her dead supervisor's pid 1744, which
# 唐三藏's new supervisor then recycled; this script still reported "alive").
# The supervisor is always launched as `muse_instance.py --root <root> ...`,
# so require its cmdline to name the root this mailbox belongs to (recorded
# by claim_mailbox in .enoch-instance.json). Fail closed (report dead) when
# the marker is missing or the roots differ: a false "dead" only triggers a
# restart attempt that the per-instance lock rejects while the real
# supervisor still holds it.
#
# Deliberately NOT based on /proc/<pid>/environ: on this host, variables the
# supervisor sets later via os.environ (e.g. ENOCH_MUSE_MAILBOX when launched
# without --mailbox) do not appear in its /proc environ — only exec-inherited
# variables do (verified 2026-09-21: 青霞's supervisor 1773 lacked it while
# its child 1777, spawned after the setenv, had it).
expected_root="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("root") or "")' \
    "$MAILBOX/.enoch-instance.json" 2>/dev/null)"
[ -n "$expected_root" ] || exit 1
printf '%s' "$cmdline" | grep -F -q -- "--root $expected_root " || exit 1
exit 0
