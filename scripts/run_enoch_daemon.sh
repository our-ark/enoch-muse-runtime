#!/usr/bin/env bash
# Start Enoch's own daemon (python -m enoch.agent) for a muse-enoch agent root.
#
# The daemon's poll loop owns the S direction end-to-end (receive ->
# handle_event -> run_conversation -> runtime.muse -> chat_outbox). The R
# direction (answering mailbox runtime requests) is still served by the
# Muse-side bridge (cron + inline fast path).
#
# Paths are overridable via environment; defaults match the original
# single-instance layout:
#   ENOCH_AGENT_ROOT  agent root (default ~/workspace/muse-enoch-agent)
#   ENOCH_MUSE_MAILBOX mailbox dir (default ~/workspace/muse-enoch/mailbox)
#   ENOCH_MUSE_REPO    this repo (default ~/workspace/muse-enoch)
#   ENOCH_SRC          enoch source tree (default ~/workspace/enoch-experiment)
#
# Supervision: the minutely cron checks the pidfile and restarts this script
# if the daemon died. Daemon epoch is last-writer-wins, so a duplicate start
# safely retires the older process via StaleDaemonEpoch.
set -u

AGENT_ROOT="${ENOCH_AGENT_ROOT:-$HOME/workspace/muse-enoch-agent}"
MAILBOX="${ENOCH_MUSE_MAILBOX:-$HOME/workspace/muse-enoch/mailbox}"
REPO_ROOT="${ENOCH_MUSE_REPO:-$HOME/workspace/muse-enoch}"
ENOCH_SRC_DIR="${ENOCH_SRC:-$HOME/workspace/enoch-experiment}"
PIDFILE="$MAILBOX/enoch-daemon.pid"
LOG="$MAILBOX/enoch-daemon.log"

mkdir -p "$MAILBOX"
cd "$AGENT_ROOT" || exit 1

export ENOCH_CHAT_PROVIDER=muse
export ENOCH_RUNTIME_PROVIDER=muse
export ENOCH_MUSE_MAILBOX="$MAILBOX"
export ENOCH_MUSE_POLL_SECONDS="${ENOCH_MUSE_POLL_SECONDS:-5}"
export ENOCH_MUSE_TIMEOUT="${ENOCH_MUSE_TIMEOUT:-1800}"
export PYTHONPATH="$REPO_ROOT/src:$ENOCH_SRC_DIR/src:$(ls -d "$ENOCH_SRC_DIR"/libraries/*/src | tr '\n' ':')"

echo $$ > "$PIDFILE"
echo "=== daemon start $(date -u +%FT%TZ) pid=$$ root=$AGENT_ROOT ===" >> "$LOG"
exec >>"$LOG" 2>&1
exec python3 -u -m enoch.agent
