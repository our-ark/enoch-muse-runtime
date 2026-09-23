#!/bin/bash
# round_lock.sh <acquire|release|check|heartbeat> [round-name] [owner-token]
#
# 轮次锁：group discussion / 私聊跑轮次时独占 chat_outbox，
# 防止后台 consumer 并发抢走回复（consumer 见锁必须跳过 chat_outbox 投递）。
#
# 真互斥 + owner token：
# - acquire: 原子创建锁文件（O_EXCL），含 owner token；若锁已存在且有效则失败
# - release: 只有 owner token 匹配才能解锁，防止 A worker 误解 B worker 的锁
# - check:   有有效锁返回 0（consumer 跳过 chat_outbox），无锁/过期返回 1
# - heartbeat: owner 续期，防止长轮次（如 30 分钟编剧会）被误判过期
#
# 锁文件格式：<timestamp> <owner-token> <round-name>
# 锁文件位置：${MUSE_GROUP_HOME:-$HOME/workspace/muse-group}/.round-active
# （live 状态，不进版本库）
#
# 用法：
#   TOKEN=$(round_lock.sh acquire my-round)   # 抢锁，拿到 owner token
#   round_lock.sh check                        # consumer 用：0=有轮次在跑，跳过
#   round_lock.sh heartbeat "$TOKEN"           # 长轮次中续期
#   round_lock.sh release "$TOKEN"            # 只能自己解自己的锁
set -euo pipefail
GROUP_HOME="${MUSE_GROUP_HOME:-$HOME/workspace/muse-group}"
LOCK="$GROUP_HOME/.round-active"
STALE_SECS=3600   # 1 小时：覆盖最长轮次 + 缓冲；过期锁视为死亡，可被接管

case "${1:-check}" in
  acquire)
    name="${2:-round}"
    token="${3:-$(date +%s)-$$-$RANDOM}"
    mkdir -p "$GROUP_HOME"
    # 原子创建：若文件已存在则失败
    if ( set -o noclobber; printf '%s %s %s\n' "$(date +%s)" "$token" "$name" > "$LOCK" ) 2>/dev/null; then
      echo "$token"
      exit 0
    fi
    # 文件已存在：检查是否过期
    started=$(cut -d' ' -f1 "$LOCK" 2>/dev/null || echo 0)
    now=$(date +%s)
    case "$started" in ''|*[!0-9]*) started=0 ;; esac
    if [ $((now - started)) -gt "$STALE_SECS" ]; then
      # 过期锁：强行接管（持有者已死）
      printf '%s %s %s\n' "$now" "$token" "$name" > "$LOCK.tmp.$$"
      mv "$LOCK.tmp.$$" "$LOCK"
      echo "$token"
      exit 0
    fi
    echo "lock held by another round, refusing" >&2
    exit 1
    ;;
  release)
    token="${2:-}"
    [ -n "$token" ] || { echo "release needs owner token" >&2; exit 1; }
    [ -f "$LOCK" ] || exit 0   # 锁已不在，视为成功
    owner=$(cut -d' ' -f2 "$LOCK" 2>/dev/null || echo "")
    if [ "$owner" = "$token" ]; then
      rm -f "$LOCK"
      exit 0
    else
      echo "not lock owner, refusing to release" >&2
      exit 1
    fi
    ;;
  heartbeat)
    token="${2:-}"
    [ -n "$token" ] || { echo "heartbeat needs owner token" >&2; exit 1; }
    [ -f "$LOCK" ] || { echo "no lock" >&2; exit 1; }
    owner=$(cut -d' ' -f2 "$LOCK" 2>/dev/null || echo "")
    name=$(cut -d' ' -f3- "$LOCK" 2>/dev/null || echo "round")
    if [ "$owner" = "$token" ]; then
      printf '%s %s %s\n' "$(date +%s)" "$token" "$name" > "$LOCK.tmp.$$"
      mv "$LOCK.tmp.$$" "$LOCK"
      exit 0
    else
      echo "not lock owner" >&2
      exit 1
    fi
    ;;
  check)
    [ -f "$LOCK" ] || exit 1   # 无锁 -> 允许 consumer 投递
    started=$(cut -d' ' -f1 "$LOCK" 2>/dev/null || echo 0)
    now=$(date +%s)
    case "$started" in ''|*[!0-9]*) started=0 ;; esac
    if [ $((now - started)) -gt "$STALE_SECS" ]; then
      echo "stale lock, ignoring" >&2
      exit 1
    fi
    exit 0   # 有有效锁 -> consumer 跳过 chat_outbox
    ;;
esac
