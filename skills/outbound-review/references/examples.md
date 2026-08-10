# Draft examples

Shapes that have worked, not a schema. Fields vary by repo, board, and team — take what fits and
ignore the rest.

Text before the first `--- field ---` line is the default body. Once a draft has several bodies,
naming all of them explicitly usually reads better than leaving the first one implicit.

## GitHub PR or issue

```markdown
---
target: owner/repo
id:                     # the existing PR or issue, when editing one
title: Fix the retry backoff
labels: bug, networking
reviewers: alice, bob
---

What changed and why.

--- test-plan ---

- ...
```

Editing one that already exists — `id` names it, and the body starts as whatever is on the PR
right now, not as a blank page:

```markdown
---
target: owner/repo
id: 123
---

The current body, revised.
```

## ADO work item

Different boards and contexts carry different key-value fields; the ones below are only examples.

```markdown
---
target: HLS AI Platform\Ember    # where it gets filed
id:                              # the existing work item, when editing one
parent: `2967286`, [Premium model pre-customer QA](link)   # id and link to parent item
type: Task
title: Premium model pre-customer QA harness
state: New
iteration: HLS AI Platform\FY27
assigned_to: null
---

--- description ---

Lorem ipsum.

--- acceptance-criteria ---

- ...
```

## Email

A saved draft has its own message id, so it is an existing thing you can revise. Reply drafts
arrive pre-filled with the quoted thread — replacing the body wholesale drops it.

```markdown
---
to: alice@example.com
cc: bob@example.com
subject: Retry backoff rollout, Thursday
in_reply_to:            # thread id when replying, blank for a new message
id:                     # the existing draft, when revising one
attachments:
---

Body prose.
```

## Inline, no file

Short things skip the file, not the rule — target and exact text, together, on every pass.

A reply on a PR review thread, `owner/repo#123` on `src/retry.ts:42`:

> Good catch. Switched to exponential backoff with jitter in 1a2b3c4.

A comment on ADO work item `2967286`:

> Parked until the FY27 board is cut over. Picking it back up in Q2.
