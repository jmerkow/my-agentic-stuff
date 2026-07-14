---
name: collect
description: 'Collect Copilot Chronicle session-store SQLite databases from local machine, WSL, and remote SSH hosts into a single staging directory, then query them with sqlite3. Use when the user wants to inspect, search, or export their Copilot chat history (sessions, turns, files, refs) across machines. Triggers: chronicle, session-store.db, copilot history, session history, search past sessions, what did I ask, find prompt.'
argument-hint: '[hosts...] - optional SSH host names to include (e.g. my-host)'
---

# Sessions Collect

Gather Copilot Chronicle (`session-store.db`) databases from every place they live, stage them locally, and run SQL queries against them.

## When to Use

- User asks about past chat sessions, prompts, or files touched
- User wants to search Copilot history across machines
- User wants raw data, not the built-in `/chronicle` summaries
- Built-in `/chronicle:tips` returns nothing useful (not enough local data)

## Known DB Locations

| Source | Path |
|---|---|
| Copilot CLI (any host) | `~/.copilot/session-store.db` |
| VS Code (Windows) | `%APPDATA%\Code\User\globalStorage\github.copilot-chat\session-store.db` |
| VS Code Server (Linux/WSL/SSH) | `~/.vscode-server/data/User/globalStorage/github.copilot-chat/session-store.db` |
| VS Code Insiders Server | `~/.vscode-server-insiders/data/User/globalStorage/github.copilot-chat/session-store.db` |

Each DB has sidecar `*.db-shm` and `*.db-wal` files. **Always copy all three** — the WAL often holds most recent data.

## Procedure

### 1. Collect

Run [collect.sh](./scripts/collect.sh) with optional SSH host args:

```bash
bash ~/.copilot/skills/collect/scripts/collect.sh my-host
```

Output goes to `/tmp/chronicle/<host>/<source>/session-store.db*`.

**Private hosts:** if `~/.copilot/skills/collect/hosts.md` exists, use the SSH host names listed there as the collect.sh args instead of the placeholder above.

### 2. Verify schema

Schemas differ between CLI and VS Code stores. Check before querying:

```bash
sqlite3 /tmp/chronicle/<host>/<source>/session-store.db ".schema sessions"
sqlite3 ... ".tables"
```

See [schema.md](./references/schema.md) for both variants.

### 3. Query

See [queries.md](./references/queries.md) for ready-to-run example queries (overview, search by keyword, find files touched, list references, etc.).

Basic search example:

```bash
DB=/tmp/chronicle/local/vscode/session-store.db
sqlite3 -header -column "$DB" \
  "SELECT s.updated_at, s.summary, t.user_message
   FROM turns t JOIN sessions s ON s.id=t.session_id
   WHERE t.user_message LIKE '%KEYWORD%'
   ORDER BY s.updated_at DESC LIMIT 20;"
```

## Notes

- DBs are SQLite WAL-mode. Copying just `.db` misses recent activity — use the script.
- Do **not** modify the live DB. Always copy first.
- `sqlite3` binary may not be installed on remote hosts; copy the file back and query locally.
