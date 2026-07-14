---
name: work-search
description: Search and retrieve work information across M365 activity, internal engineering knowledge, and official Microsoft documentation. Use when gathering meeting summaries, email threads, chat messages, calendar events, internal docs, technical support guidance, or Microsoft/Azure product documentation. Covers tool selection, query strategies, and data-quality rules.
---

# Work Search

Search across three work-information domains:

1. **Personal activity** — meetings, emails, chats, calendar
2. **Internal engineering knowledge** — EngHub docs, TSGs, internal support knowledge
3. **Official Microsoft knowledge** — Microsoft Learn docs and code samples

These tool families have different strengths. Pick the source first, then the tool.

## Tool Landscape

## Personal Activity

### WorkIQ (`mcp_workiq_ask_work_iq`)

Cross-source semantic search. Ask natural language questions spanning meetings, emails, and chats.

**Best for:** Discovery, cross-source queries ("What happened with X this week?"), transcript-based meeting summaries, broad activity sweeps.

**Unique capability:** Only tool that can access **meeting transcripts** and produce grounded summaries of what was discussed.

**Limitations:** Can truncate long result sets. Break large date ranges into ≤10-day chunks. Results are summarized, not raw — drill into specific items with the targeted tools below.

### Calendar (`mcp_calendar_*`)

Direct calendar API access.

| Tool | Use |
|------|-----|
| `ListCalendarView` | List events in a date range (structured, complete) |
| `ListEvents` | List events with filtering |
| `FindMeetingTimes` | Find available meeting slots |
| `GetRooms` | List meeting rooms |
| `GetUserDateAndTimeZoneSettings` | User's timezone |

**Best for:** Complete event lists for a date range (no truncation), confirming attendance, getting organizer/attendee lists, structured data.

**Pair with WorkIQ:** Use Calendar to get the full event list, then WorkIQ to get transcript-based summaries for specific meetings.

### Mail (`mcp_mail_*`)

Direct email access.

| Tool | Use |
|------|-----|
| `SearchMessages` | Search emails by keyword, sender, date range |
| `GetMessage` | Get a specific email by ID |
| `GetAttachments` | List attachments on a message |
| `DownloadAttachment` | Download a specific attachment |

**Best for:** Finding specific email threads, getting exact recipients (To/CC), retrieving attachments, keyword-based search.

### Teams (`mcp_teams_*`)

Direct Teams chat and channel access.

| Tool | Use |
|------|-----|
| `ListChats` | List all chats |
| `GetChat` | Get a specific chat |
| `ListChatMessages` | List messages in a chat |
| `GetChatMessage` | Get a specific message |
| `SearchTeamsMessages` | Search across Teams messages |
| `ListChannels` / `GetChannel` | Channel info |
| `ListChannelMessages` | Messages in a channel |
| `ListTeams` / `GetTeam` | Team info |
| `ListChatMembers` / `ListChannelMembers` | Membership |

**Best for:** Getting exact chat messages, monitoring specific channels/chats over time, getting message history for a named chat.

## Internal Engineering Knowledge

### ES Chat (`mcp_es-chat_*`)

Internal engineering assistant over engineering systems, knowledge bases, incidents, wikis, and other internal sources.

**Best for:** Broad technical questions, onboarding questions, internal system troubleshooting, and finding likely threads before drilling into EngHub or ADO.

**Use first when:** The question is technical and you do not yet know which service, doc set, or system contains the answer.

**Pair with EngHub:** Use ES Chat to orient quickly, then use EngHub to fetch the underlying docs or TSGs when you need precise grounding.

### EngHub (`mcp_enghub_*`)

Internal documentation search and fetch for eng.ms content.

| Tool | Use |
|------|-----|
| `mcp_enghub_search` | Search docs, TSGs, onboarding guides, team docs |
| `mcp_enghub_fetch` | Fetch full content from an eng.ms URL |

**Best for:** Internal docs, technical support guides, service-specific onboarding, and grounded internal references.

**Use when:** You know the question is about an internal Microsoft engineering service, team doc, or TSG and need the actual source content.

## Official Microsoft Knowledge

### Microsoft Learn (`mcp_msft-learn_*`)

Official Microsoft documentation and code samples.

| Tool | Use |
|------|-----|
| `mcp_msft-learn_microsoft_docs_search` | Search official Microsoft docs |
| `mcp_msft-learn_microsoft_docs_fetch` | Fetch the full content of a docs page |
| `mcp_msft-learn_microsoft_code_sample_search` | Search official code samples |

**Best for:** Azure, M365, Copilot, Foundry, and other Microsoft product documentation; SDK/API guidance; official examples.

**Use when:** The question is product or platform guidance rather than personal activity or internal team knowledge.

**Required pattern:** Search first, then fetch the most relevant page when details matter.

## Query Strategy: The Funnel

```
WorkIQ (broad discovery) → Calendar/Mail/Teams (targeted detail)
```

1. **Start broad with WorkIQ** — ask cross-source questions to discover what happened
2. **Drill down with targeted tools** — use Calendar for event lists, Mail for email threads, Teams for chat messages
3. **Back to WorkIQ for transcripts** — if you need meeting discussion summaries, only WorkIQ has transcript access

## Query Strategy: Choose by Domain

### Personal Activity

```
WorkIQ (broad discovery) → Calendar/Mail/Teams (targeted detail)
```

- Start with `work_iq` for cross-source discovery
- Use `calendar`, `mail`, and `teams` for exact records
- Return to `work_iq` for transcript-based meeting summaries

### Internal Technical Questions

```
ES Chat (orient) → EngHub search (find source) → EngHub fetch (read source)
```

- Start with `es-chat` when the question is broad or system-oriented
- Use `enghub_search` when you need the actual doc or TSG
- Use `enghub_fetch` to read the source before citing or acting on it

### Microsoft Product Questions

```
Microsoft Docs Search → Microsoft Docs Fetch → Code Sample Search
```

- Start with `microsoft_docs_search` for official guidance
- Fetch the full page when details or steps matter
- Use `microsoft_code_sample_search` when writing or reviewing Microsoft-specific code

### Example: Weekly Activity Sweep

```
1. Calendar.ListCalendarView(startDate, endDate)     → complete event list
2. WorkIQ("meetings I attended from X to Y, with summaries")  → transcript summaries
3. WorkIQ("emails I sent from X to Y with decisions")         → email activity
4. Teams.SearchTeamsMessages("keyword")               → specific chat threads
5. WorkIQ("activity with [customer] from X to Y")     → per-customer cross-source
```

### Example: Investigate a Specific Meeting

```
1. Calendar.ListCalendarView(date, date)  → find the event, get organizer + attendees
2. WorkIQ("summarize the [meeting name] meeting on [date]")  → transcript summary
```

### Example: Find an Email Thread

```
1. Mail.SearchMessages(query="subject:keyword")  → find the thread
2. Mail.GetMessage(id)                            → full content with recipients
```

### Example: Investigate an Internal Engineering Question

```
1. ES Chat("How does X service handle Y?")        → orient and identify systems/docs
2. EngHub.search("X service Y")                   → find TSG or team doc
3. EngHub.fetch(url)                              → read the underlying source
```

### Example: Investigate a Microsoft Product Question

```
1. MicrosoftDocs.search("Azure AI Foundry model packaging")
2. MicrosoftDocs.fetch(url)
3. MicrosoftCodeSamples.search("Azure AI Foundry packaging", language)
```

## Data-Quality Rules

Apply these during and after all queries:

1. **WorkIQ truncates** — if results seem incomplete, break into smaller date ranges or use targeted tools to fill gaps
2. **Resolve relative dates** — "yesterday" or "last Thursday" → convert to absolute dates immediately
3. **Meeting names must match calendar** — don't rename meetings. Add disambiguation in parentheses: `**Project Sync** *(Acme)*`
4. **Flag meeting-name misclassification** — WorkIQ sometimes merges or splits meetings incorrectly. Cross-check with Calendar.ListCalendarView
5. **Organizer ≠ attendee** — being the organizer doesn't confirm attendance. Flag uncertain attendance with ⚠️
6. **Request full detail** — always include attendees, organizer, recipients (To/CC). Bare topic names are useless
7. **Disambiguate colliding abbreviations** — when one abbreviation maps to two different entities, never use the bare abbreviation; tag every occurrence so they can't be conflated. E.g. if "GT" could mean Globex Tech or Gamma Therapeutics, always write `**GT** *(Globex)*` vs `**GT** *(Gamma)*`.
8. **Only WorkIQ has transcript access** — Calendar, Mail, Teams, EngHub, ES Chat, and Microsoft Learn do not provide meeting transcript summaries
9. **EngHub and Microsoft Learn are source systems** — prefer fetching the underlying page before quoting specific guidance
10. **ES Chat is an orienting tool** — useful for discovery, but fetch the underlying doc when precision matters

## Categorization

After collecting items, categorize by project:

Customize this mapping to your own projects. If `~/.copilot/skills/work-search/config.md` exists, use the categorization table there instead.

| Signal | Project |
|--------|---------|
| compliance, security, vulnerability | Compliance |
| Customer name, partner meeting, workshop, hackathon, eval, engagement | CustomerEngagements |
| Agent, prompt, skill, eng tooling | AgentTooling |
| Org meeting, 1:1, general discussion, cross-cutting | Other |

For **CustomerEngagements**, also tag the specific customer: `[CUSTOMER: name]`.

## Exclusion Rules

Skip unless user says otherwise:
- Internal 1:1s (manager syncs) — unless a decision was made
- Research reading groups / journal clubs — unless action taken
- All-hands / org broadcasts — unless directly involved in a decision
- Calendar holds / no-shows
