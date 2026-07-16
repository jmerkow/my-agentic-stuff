#!/usr/bin/env bash
# Collect Chronicle session-store DBs from local + given SSH hosts into /tmp/chronicle/.
# Usage: collect.sh [ssh-host ...]
set -uo pipefail

DEST="${CHRONICLE_DEST:-/tmp/chronicle}"
mkdir -p "$DEST"

# Local source paths to try (label:path)
LOCAL_SOURCES=(
  "cli:$HOME/.copilot/session-store.db"
  "vscode:$HOME/.vscode-server/data/User/globalStorage/github.copilot-chat/session-store.db"
  "vscode-insiders:$HOME/.vscode-server-insiders/data/User/globalStorage/github.copilot-chat/session-store.db"
)

copy_local() {
  local host_label="$1"; shift
  for entry in "${LOCAL_SOURCES[@]}"; do
    local label="${entry%%:*}"
    local path="${entry#*:}"
    if [[ -f "$path" ]]; then
      local out="$DEST/$host_label/$label"
      mkdir -p "$out"
      cp -f "$path" "$out/" 2>/dev/null
      [[ -f "$path-shm" ]] && cp -f "$path-shm" "$out/" 2>/dev/null
      [[ -f "$path-wal" ]] && cp -f "$path-wal" "$out/" 2>/dev/null
      echo "  [ok] $label -> $out/"
    fi
  done
}

copy_remote() {
  local host="$1"
  # Resolve remote $HOME once. Modern scp uses the SFTP protocol and does NOT
  # run a remote shell, so a literal "$HOME" in the path never expands. We must
  # pass an absolute path instead.
  local remote_home
  remote_home="$(ssh "$host" 'printf %s "$HOME"' 2>/dev/null)"
  if [[ -z "$remote_home" ]]; then
    echo "  [fail] $host: cannot resolve remote \$HOME (ssh failed)"
    return 1
  fi
  for entry in "${LOCAL_SOURCES[@]}"; do
    local label="${entry%%:*}"
    local rel="${entry#*:}"
    rel="${rel#$HOME/}"
    local remote_path="$remote_home/$rel"
    if ssh "$host" "test -f '$remote_path'" 2>/dev/null; then
      local out="$DEST/$host/$label"
      mkdir -p "$out"
      if scp -q "$host:$remote_path" "$out/"; then
        # -shm/-wal are optional; their absence is not a failure.
        scp -q "$host:${remote_path}-shm" "$out/" 2>/dev/null
        scp -q "$host:${remote_path}-wal" "$out/" 2>/dev/null
        echo "  [ok] $host:$label -> $out/"
      else
        echo "  [fail] $host:$label scp failed for $remote_path"
      fi
    fi
  done
}

echo "Collecting Chronicle DBs into $DEST"
echo "== local =="
copy_local "local"

for host in "$@"; do
  echo "== $host =="
  copy_remote "$host"
done

echo
echo "Collected files:"
find "$DEST" -name 'session-store.db' -printf '  %p (%s bytes)\n'
