#!/usr/bin/env bash
# Start Enoch's own daemon (python -m enoch.agent) for the muse-enoch-agent root.
#
# This replaces the one-shot chat_turn.py driver: the daemon's poll loop now
# owns the S direction end-to-end (receive -> handle_event -> run_conversation
# -> runtime.muse -> chat_outbox). The R direction (answering mailbox runtime
# requests) is still served by the Muse-side bridge (cron + inline fast path).
#
# Supervision: the minutely cron checks the pidfile and restarts this script
# if the daemon died. Daemon epoch is last-writer-wins, so a duplicate start
# safely retires the older process via StaleDaemonEpoch.
set -u

AGENT_ROOT="$HOME/workspace/muse-enoch-agent"
MAILBOX="$HOME/workspace/muse-enoch/mailbox"
PIDFILE="$MAILBOX/enoch-daemon.pid"
LOG="$MAILBOX/enoch-daemon.log"

cd "$AGENT_ROOT" || exit 1

export ENOCH_CHAT_PROVIDER=muse
export ENOCH_RUNTIME_PROVIDER=muse
export ENOCH_MUSE_MAILBOX="$MAILBOX"
export ENOCH_MUSE_POLL_SECONDS=5
export ENOCH_MUSE_TIMEOUT=1800
export PYTHONPATH="$HOME/workspace/muse-enoch/src:$HOME/workspace/enoch-experiment/src:$(ls -d "$HOME"/workspace/enoch-experiment/libraries/*/src | tr '\n' ':')"

echo $$ > "$PIDFILE"
echo "=== daemon start $(date -u +%FT%TZ) pid=$$ ===" >> "$LOG"
exec >>"$LOG" 2>&1
exec python3 -u -m enoch.agent
