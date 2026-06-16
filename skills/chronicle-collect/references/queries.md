# Chronicle Query Cookbook

Set `DB` first:

```bash
DB=/tmp/chronicle/local/vscode/session-store.db
alias sq='sqlite3 -header -column "$DB"'
```

## Overview

```sql
-- Counts and date range
SELECT (SELECT COUNT(*) FROM sessions) AS sessions,
       (SELECT COUNT(*) FROM turns)    AS turns,
       (SELECT COUNT(*) FROM session_files) AS files,
       (SELECT COUNT(*) FROM session_refs)  AS refs,
       (SELECT MIN(updated_at) FROM sessions) AS earliest,
       (SELECT MAX(updated_at) FROM sessions) AS latest;
```

## Recent sessions

```sql
SELECT updated_at, COALESCE(repository,'') AS repo,
       SUBSTR(summary,1,80) AS summary
FROM sessions
ORDER BY updated_at DESC
LIMIT 20;
```

## Search prompts by keyword

```sql
SELECT s.updated_at, SUBSTR(s.summary,1,60) AS summary,
       SUBSTR(t.user_message,1,200) AS msg
FROM turns t JOIN sessions s ON s.id = t.session_id
WHERE t.user_message LIKE '%KEYWORD%'
ORDER BY s.updated_at DESC
LIMIT 20;
```

## Search assistant responses

```sql
SELECT s.updated_at, SUBSTR(s.summary,1,60) AS summary,
       SUBSTR(t.assistant_response,1,200) AS resp
FROM turns t JOIN sessions s ON s.id = t.session_id
WHERE t.assistant_response LIKE '%KEYWORD%'
ORDER BY s.updated_at DESC
LIMIT 20;
```

## Full-text search (FTS5)

The `search_index` virtual table backs Chronicle's own search:

```sql
SELECT * FROM search_index WHERE search_index MATCH 'KEYWORD' LIMIT 20;
```

## Sessions by repo

```sql
SELECT COALESCE(repository,'(none)') AS repo, COUNT(*) AS cnt
FROM sessions
GROUP BY repository
ORDER BY cnt DESC;
```

## Files touched in a session

```sql
SELECT tool_name, file_path, turn_index
FROM session_files
WHERE session_id = 'SESSION_ID'
ORDER BY turn_index;
```

## All sessions that touched a file

```sql
SELECT s.updated_at, SUBSTR(s.summary,1,60) AS summary, sf.tool_name
FROM session_files sf JOIN sessions s ON s.id = sf.session_id
WHERE sf.file_path LIKE '%FILE_PATH%'
ORDER BY s.updated_at DESC;
```

## External references (PRs, issues, commits)

```sql
SELECT ref_type, ref_value, COUNT(*) AS cnt
FROM session_refs
GROUP BY ref_type, ref_value
ORDER BY cnt DESC
LIMIT 50;
```

## Full conversation of a session

```sql
SELECT turn_index, user_message, assistant_response
FROM turns
WHERE session_id = 'SESSION_ID'
ORDER BY turn_index;
```

## Sessions touching the most files (longest/messiest)

```sql
SELECT s.updated_at, SUBSTR(s.summary,1,60) AS summary,
       COUNT(sf.id) AS file_touches
FROM sessions s LEFT JOIN session_files sf ON sf.session_id = s.id
GROUP BY s.id
ORDER BY file_touches DESC
LIMIT 10;
```

## Cross-DB query (UNION across collected DBs)

```bash
sqlite3 :memory: <<SQL
ATTACH '/tmp/chronicle/local/vscode/session-store.db' AS local;
ATTACH '/tmp/chronicle/ssh-my-host/cli/session-store.db' AS gpu;
SELECT 'local' AS host, updated_at, summary FROM local.sessions
UNION ALL
SELECT 'gpu',   updated_at, summary FROM gpu.sessions
ORDER BY updated_at DESC LIMIT 20;
SQL
```
