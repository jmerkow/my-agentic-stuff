# Rewrite Template

Target structure for a refined agent body (below YAML frontmatter). Every section is wrapped in an XML tag. No bare markdown headers. Include only the tags the agent needs — `<persona>` and `<rules>` are required, the rest are optional.

```markdown
---
name: ...
description: ...
tools: [...]
agents: [...]
...
---

<persona>
{Identity — prose, second person. Who you are, what you hold in your head, what your value is.
For parents: who does the work, why you don't do it yourself. 2-4 sentences.}

{Think out loud — state reasoning before every action.}

{How you think — judgment guidance as verb-phrase bullets:
- **Understand the plan first.** Read decisions before touching anything.
- **Delegate with clarity.** Give subs everything they need.}
</persona>

<rules>
- {Operational constraints — .eng/ hygiene, journal, mistake capture}
- {Stop conditions, escalation triggers}
- {Things the agent must always or never do}
</rules>

<capabilities>                    ← optional
- {Concrete things this agent is good at — task types, examples}
- {Reference skills where they give the agent a specific capability}
</capabilities>

<workflow>                        ← optional
{Process phases. Can be strict (numbered gates) or loose (general approach).
Use nested markdown headers for multi-step phases:}

## 1. {Phase name}
{Description, sub-steps, skill references where they apply.}

## 2. {Phase name}
{...}
</workflow>

<{name}_guide>                    ← optional
{Template for a structured output — response format, findings doc, plan, etc.
Name after the deliverable: plan_style_guide, findings_guide, response_guide.}
</{name}_guide>
```
