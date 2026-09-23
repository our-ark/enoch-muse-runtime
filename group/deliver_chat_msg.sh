#!/bin/bash
# deliver_chat_msg.sh <agent-root> <text>
# 原子投递 chat_inbox 消息：在同一个 flock 临界区内完成
#   seq 分配 → .tmp 写入 → chmod 0600 → rename
#
# 为什么需要这个工具：
# daemon 的 receive() 只认纯数字文件名，且只返回 seq > 持久化 cursor 的文件。
# 若"先算号、后写文件"分成两步，并发投递会撞号、丢消息。
# 本工具把"读目录最大号、读 cursor、取 max+1、写文件"全部放在同一把
# 文件锁内，保证 seq 绝不复用、绝不跳过 cursor。
#
# 实现 Group Discussion 协议 §7 的投递规则：
# 纯数字文件名 <seq>.json，内容 {"seq":N,"text":"...","created_at":...}，
# .tmp → rename 原子写入，权限 0600。
#
# 输出分配到的 seq（纯数字）。
set -euo pipefail
ROOT="$1"
TEXT="$2"
INBOX="$ROOT/mailbox/chat_inbox"
CURSOR="$ROOT/.enoch/channels/muse/cursor.json"
LOCK="$ROOT/mailbox/chat_inbox/.seq.lock"

mkdir -p "$INBOX"
exec 9>"$LOCK"
flock -x 9

dir_max=0
for f in "$INBOX"/[0-9]*.json; do
  [ -e "$f" ] || continue
  base=$(basename "$f" .json)
  case "$base" in
    ''|*[!0-9]*) continue ;;
  esac
  [ "$base" -gt "$dir_max" ] 2>/dev/null && dir_max="$base"
done

cursor=0
if [ -f "$CURSOR" ]; then
  v=$(CURSOR_PATH="$CURSOR" python3 -c "
import json, os
try:
    d = json.load(open(os.environ['CURSOR_PATH']))
    print(d['cursor'] if isinstance(d, dict) else d)
except Exception:
    print(0)
" 2>/dev/null || echo 0)
  case "$v" in ''|*[!0-9]*) v=0 ;; esac
  cursor="$v"
fi

# 删文件不回退 cursor：若目录最大号 <= cursor，必须跳号到 cursor+1
if [ "$dir_max" -gt "$cursor" ]; then
  seq=$((dir_max + 1))
else
  seq=$((cursor + 1))
fi

# 锁内原子写：tmp → chmod 0600 → rename
tmp="$INBOX/.$seq.tmp.$$"
python3 -c "
import json, sys, time
d = {'seq': $seq, 'text': sys.argv[1], 'created_at': time.time()}
open('$tmp', 'w').write(json.dumps(d, ensure_ascii=False))
" "$TEXT"
chmod 0600 "$tmp"
mv "$tmp" "$INBOX/$seq.json"

echo "$seq"
# flock 随 fd 9 关闭自动释放
