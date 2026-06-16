# Chronicle DB Schema

Two variants exist. Check with `sqlite3 <db> ".schema sessions"` before composing queries.

## Tables (both variants)

- `sessions` — one row per chat session
- `turns` — user/assistant turn pairs (`turn_index` 0-based)
- `session_files` — files touched via tools, keyed by `tool_name`
- `session_refs` — external refs (PRs, issues, commits) extracted from messages
- `search_index*` — FTS5 virtual tables backing full-text search
- `checkpoints`, `schema_version` — internal

## sessions (VS Code variant — newer)

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    cwd TEXT,
    repository TEXT,
    host_type TEXT,
    branch TEXT,
    summary TEXT,
    agent_name TEXT,           -- present
    agent_description TEXT,    -- present
    created_at TEXT,
    updated_at TEXT
);
```

## sessions (Copilot CLI variant — older)

```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    cwd TEXT,
    repository TEXT,
    branch TEXT,
    summary TEXT,
    created_at TEXT,
    updated_at TEXT,
    host_type TEXT
    -- no agent_name, no agent_description
);
```

## turns (both)

```sql
CREATE TABLE turns (
    id INTEGER PRIMARY KEY,
    session_id TEXT REFERENCES sessions(id),
    turn_index INTEGER,
    user_message TEXT,
    assistant_response TEXT,
    timestamp TEXT
);
```

## session_files (both)

```sql
CREATE TABLE session_files (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    file_path TEXT,
    tool_name TEXT,            -- e.g. read_file, edit, create
    turn_index INTEGER,
    first_seen_at TEXT
);
```

## session_refs (both)

```sql
CREATE TABLE session_refs (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    ref_type TEXT,             -- e.g. commit, pr, issue
    ref_value TEXT,
    turn_index INTEGER,
    created_at TEXT
);
```
