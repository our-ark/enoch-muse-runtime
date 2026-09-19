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
*muse_instance.py*daemon*) exit 0 ;;
*) exit 1 ;;
esac
