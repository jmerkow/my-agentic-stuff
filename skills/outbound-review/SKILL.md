---
name: outbound-review
description: How to draft, get sign-off on, and send anything that goes out in the user's name — pull request descriptions and review replies, issue and work item text, comments, emails, Teams or Engage messages. Use whenever writing or revising text that will be sent, posted, filed, or pushed on the user's behalf. Covers the explicit approval gate before sending, drafting in chat versus collaborating on a draft file, and always showing the exact final content. Keywords draft, post on my behalf, send as me, act as me, write the PR description, reply to this comment, draft this email, work item text, sign off, approval gate, staged draft file.
---

# Outbound review

Sending, posting, filing, or pushing on the user's behalf speaks in their name. They are
accountable for it and often cannot take it back. Nothing goes out until they have seen the
exact thing that will represent them and said to send it.

Committing locally is not outbound. Pushing is.

## Sign-off

Approval attaches to a specific text, not to a direction. "Make that change" asks for an edit; it
is not permission to send the result.

So the shape of it is "here is the whole thing with your edits — do you approve sending it", and
never "I made those edits and sent it". Show the target and the exact content together, then
wait. A draft that lives in a file is still shown in full here; the path is how it gets edited,
not a substitute for showing what goes out.

Any change after approval — including a typo fix or a recipient resolved on the way out — is a
new text, and needs its own approval. Say plainly when something cannot be cleanly undone.

## Short things stay inline

A comment, a title, a one-line reply can live in chat. The price is that every iteration carries
the whole thing: after every edit, print the complete text and all fields verbatim — not a diff,
not only the changed lines, not a description of what changed.

That is the trade. Inline is only cheap while reprinting everything stays cheap. Once it stops
being cheap, it belongs in a file.

## Longer things go in a file

Anything longer or multi-field gets drafted in a file and edited collaboratively, rather than
renegotiated turn by turn. Everything that is not body text goes in frontmatter, prose goes in
the body, and a second body opens with its own `--- field-name ---` line. Store it somewhere the
user can open and edit, and link the path.

The file is the source of truth and it changes without you — the user edits it directly. Re-read
it from disk before quoting it, before editing it, and before sending it. A stale copy carried in
context will silently overwrite their edits.

`id` says which thing the draft is. Carrying one edits that thing; carrying none creates a new
one. For every other field, blank leaves it as it is and `null` clears it.

When editing, pull the current content into the draft first — otherwise the send replaces what is
there now with a draft that never saw it. Refresh again immediately before sending: if it moved
since the draft was built, or anything it is linked to moved, say so and re-confirm instead of
sending over it.

`references/examples.md` has worked examples for a few surfaces. They are illustrations, not
schemas — no obligation to follow them.
