---
name: ledger
description: >
  Create, update, and check small Markdown ledgers with stable IDs, scoped
  lookup, file-local rules, and maintained entry templates. Use when tracking
  questions, decisions, findings, or inventories across edits and sessions.
  Keywords: ledger, ledger ID, namespace, entry slug, stable references.
---

# Ledger

Keep each ledger self-describing and follow repository conventions for location
and additional metadata. Frontmatter, identity, and entry-table rules are mandatory;
the remaining layout and example are starting points. Each ledger defines its
additional entry fields, states, and sections.

## Hard Rules

- **Frontmatter:** Require `type: ledger`, `ledger_id`, and `created` in `YYYY-MM-DD` format. Set `created` to the original ledger creation date; preserve it through edits and moves. Additional repository metadata may coexist.
- **Ledger ID (namespace):** `<readable-name>-<suffix>`, e.g. `premium-examples-d6f1`. Generate the suffix once with `openssl rand -hex 2` (four random lowercase hexadecimal characters), not a hand-picked value. Accept probabilistic uniqueness; no global registry or collision scan.
- **Entry slug:** readable lowercase kebab-case, e.g. `client-strategy`. Check uniqueness only within the ledger, including retired entries. Do not add another random suffix.
- **Entry table:** Every entry must have a two-column key/value metadata table directly below its heading, with at least an `ID` row containing its entry slug. Additional rows are ledger-specific.
- **Full reference:** `<ledger-id>:<entry-slug>`. Resolve the ledger first, then search for the slug within it. Frontmatter is the single source of the ledger ID; do not duplicate its declaration in Rules.
- Preserve IDs through wording, title, order, status, and file-location changes. Never reuse retired IDs. Independent new ledgers get new ledger IDs; preserve existing formats unless an explicit migration is requested.
- Keep retired IDs addressable. Record explicit old-to-new references when splitting, merging, or superseding items.

## Starting Layout

After frontmatter, start with `Rules`, a fenced `Template` under Rules, then entries.
Follow each entry's metadata table with content sections as needed. Adapt headings,
additional fields, and sections to the collection. Document their purpose and which
are required or conditional in the ledger's rules and template; entries must follow
that chosen schema.

For longer text, prefer named sections with headings and paragraphs over long
`**Label:** ...` blocks. Keep table values concise.

## Maintain

1. Read the rules, template, and entries; find an existing matching item before adding one.
2. Follow any applicable file-ownership/locking protocol before editing. Respect other writers' claims, reread after acquiring a required claim, and release only your own claim afterward. Ownership is not a lock; do not invent a locking mechanism here.
3. Update entries in place. Keep recommendations distinct from confirmed decisions.
4. Keep the ledger's rules, template, and affected entries consistent when the schema changes. Replace generic template placeholders with the actual field definitions for this collection.
5. Check required frontmatter, a metadata table with an ID row on every entry, entry-slug uniqueness, locally required fields, consistency with the chosen template, and reference targets in scope. Do not treat these checks as a global ledger-ID search.

## Length Guidance

Aim for a ledger ID of up to 24 characters including its suffix, entry slugs up
to 40, and full references up to 65. Use a short, one-line title and a summary
that makes sense without following links. Keep entry bodies around one screen;
link extended detail. Review the layout when scanning or finding duplicates
becomes difficult. These are soft targets: never rename IDs, truncate useful
content, or split/archive a ledger automatically to meet them.

## Starter Example

The ID table is required; its additional fields and the content sections are choices for this question ledger.

````markdown
---
type: ledger
ledger_id: premium-examples-d6f1
created: 2026-09-13
---

# Client Questions

## Rules
- Entry IDs are permanent slugs, unique within this ledger, including retired entries.
- Required fields: ID, State. States: open, answered, retired. Use the question as the item heading.
- Context and Resolution are required; retain the Resolution guidance comment until answered.
- Template markers: `<add-blank>` requires the section to be present, retaining its guidance comment or placeholder until filled. `<optional>` sections may be omitted entirely. Remove these markers from instantiated entry headings.

### Template
```markdown
## <Question being tracked>

| Field | Value |
| --- | --- |
| ID | `<entry-slug>` |
| State | <open, answered, or retired> |

### Context
<Required: describe the constraints and options needed to answer the question.>

### Resolution <add-blank>
<!-- When answered: record the confirmed answer and its supporting evidence -->

### Some Option Section <optional>
<use under these conditions, but you don't need to copy it in.>
```

## Should premium endpoints use the existing clients or separate clients?

| Field | Value |
| --- | --- |
| ID | `client-strategy` |
| State | open |

### Context
Existing clients handle common request setup, but premium endpoints use different payloads.

### Resolution
<!-- When answered: record the confirmed answer and its supporting evidence -->
````