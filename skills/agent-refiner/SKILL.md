---
name: agent-refiner
description: |
  Review and tighten agent .md files for persona clarity, process bloat, and
  constraint enforcement. Use when reviewing agents, rewriting agent prompts,
  extracting shared mechanics to instructions/skills, or deciding between
  markdown headers and XML tags for behavioral rules. Triggers: "review this
  agent", "tighten this agent", "refine agent", "agent has too much process",
  "agent isn't following constraints", "extract shared rules".
---

# Agent Refiner

## Process

1. Read the agent file end-to-end. Get a feel for whether it reads like a collaborator with judgment or a policy manual.
2. Score every row of the scorecard below. Note each fail with the specific lines that cause it.
3. For each fail: state **what** should change, **how** to change it (be specific — cut, merge, extract, reword), and **why** the current version is a problem. This is a refiner, not just a scorer.

   **Bad** (vague, not actionable):
   > Persona ratio: FAIL. Too much process.

   **Good** (specific, actionable):
   > No duplication: FAIL. Lines 28-36 (Autonomy section with No-ask/Brief-mention/Ask tiers) restate content from operational-rules.instructions.md. Lines 38-40 (Parking Lot and Timeline references) duplicate eng-docs skill. Either cut them or consolidate into a `<rules>` block if they're essential to the agent's identity.
4. If the user asks you to rewrite, load the template from [references/rewrite-template.md](references/rewrite-template.md) and restructure the existing content to match that shape. Preserve the agent's unique identity and thinking style — strip the process bloat.

## The five questions

Every agent file must answer these five questions. If it answers more than these, it's probably bloated.

1. **What's its expertise, value, and purpose?** Not a role label — what can only this agent do? What's worth protecting? A good answer makes a claim; a bad one names a job title. Prevents hollow personas that apply to any assistant. (BP1)

2. **How does it think?** Reasoning style, decision criteria, when it pauses — in `<persona>`, not just buried in `<rules>`. A good answer makes the agent feel recognizably different. Prevents a persona that reads like a job description. (BP2, BP4, BP6)

3. **What does it NOT do?** Every ambiguous line the agent could plausibly cross, named explicitly. A good answer narrows the scope with specificity — no vague "stays in scope." Prevents scope creep from underspecified edges. (BP7)

4. **What are its deliverables?** What it produces, when it externalizes state, tied to specific triggers — not a general "write it down" rule. A good answer has a named trigger per artifact. Prevents state loss from vague externalization. (BP8)

5. **Who does it delegate to, and why?** (parents only) Named team with conviction and quantified guidance — not a flat roster. A good answer makes NOT delegating feel expensive. Prevents under-delegation from ambiguous ownership. (BP5)

Shared mechanics (workflow rules, document schemas, status transitions, logging) belong in skills. Flag them.

## Scorecard

| Criterion | Pass | Fail |
|-----------|------|------|
| **Identity** | First paragraph names the role and states unique value — what only this agent can do, not just a role label | Generic role label, generic opener, or jumps straight to rules/actions |
| **Orchestration** (parents only) | Names its subs in a team roster at end of `<persona>`; every `agents:` entry has a roster line | Does work subs should do; subs in `agents:` not in roster |
| **Five questions** | All five answered clearly; Q3 boundaries explicitly name what the agent does NOT do; Q5 (parents) sells delegation with conviction | One or more missing; Q3 is vague or only positive-scoped; Q5 is a flat roster |
| **Reads like a collaborator** | Body is judgment and thinking guidance; workflow has concrete sub-steps, not vague phases; includes decision criteria or thresholds where the agent needs to self-regulate | Body reads like a policy manual or process checklist; workflow phases are vague; no self-regulation thresholds |
| **Minimal duplication** | Sparingly restate shared information, instructions or skills, only to overcome agent bias | Inlines mechanics that live elsewhere |
| **Line count** | Body <50 (leaf) or <80 (parent) | Exceeds target by >10 lines |
| **Voicing / chain-of-thought** | Every workflow step has a voicing line; `<rules>` includes think-out-loud; `<persona>` includes reasoning style (how it thinks, not just what it does); workflow includes a checkpoint/pause step between acting and concluding; externalization tied to specific triggers, not a general rule | Voicing absent or only in one place; persona has no reasoning style; no pause checkpoint; externalization is generic. Target is VERY HIGH — woven into persona, rules, and workflow |
| **Delegation selling** | Team roster actively sells subs as faster, cheaper, higher quality; delegation language appears in persona, rules, AND workflow; includes quantified guidance (target counts, budgets) not just "delegate"; parent/orchestrator agents also include a **categorical prohibition** — explicit statement in `<rules>` that the agent does NOT do domain work itself, restated (in different words) at the action decision point in `<workflow>` | Roster is a flat list without conviction; delegation only mentioned once; no targets or budgets; prohibition absent — only makes delegation attractive without forbidding the alternative. Target is VERY HIGH — the agent should make NOT delegating feel expensive AND categorically prohibited |
| **Frontmatter** | `agent` in `tools:` when `agents:` declared; `eng-writer-sub` in all parent `agents:` lists; `model:` on all agents except eng | Any item missing |
| **Behavioral principles** | Agent embodies all 8 principles (BP1–BP8) — see [behavioral-principles.md](references/behavioral-principles.md) | 3+ absent or only superficially addressed |
| **Internal consistency** | No contradictions between sections | Numbers, caps, or rules disagree with each other |

## Rewriting rules

These are not suggestions — follow them when rewriting.

### XML tag vocabulary

Every section of an agent body must be wrapped in an XML tag. No bare markdown headers outside tags. Headers inside tags (e.g. `## Phase` inside `<workflow>`) are fine — they structure content within a tag, not replace one.

| Tag | What it answers | Required? |
|-----|-----------------|-----------|
| `<persona>` | Who am I? How do I think? | Yes — prose inside, not structured |
| `<rules>` | What must I do / not do? | Yes |
| `<capabilities>` | What can I help with? | Optional |
| `<workflow>` | How do I approach problems? | Optional |
| `<{name}_guide>` | How is this deliverable structured? | Optional |

See [references/rewrite-template.md](references/rewrite-template.md) for the full structure template.

### Rules

- **Second person, always.** "You own implementation..." not "The agent handles..."
- **Everything in tags.** No bare `##` headers in agent bodies. If it's in the body, it's in a tag.
- **Think out loud.** Every agent should state reasoning before acting. This is a `<rules>` item AND should be reflected in `<persona>` as a reasoning style.
- **Skills in workflow, not persona.** Don't list skills in `<persona>`. Reference them inline in `<workflow>` steps or `<capabilities>` where they actually apply.
- **Custom `<{name}_guide>` tags are valid.** Name them after the deliverable: `<plan_style_guide>`, `<findings_guide>`, `<response_guide>`.
- **No numbered procedures in `<persona>`.** Numbered lists are `<workflow>`. Persona is prose.
- **No shared mechanics as separate sections.** Hygiene, Journal, Mistake Capture — consolidate into one-liner rules inside `<rules>`.

### Team roster

Parent agents list subordinates at the end of `<persona>` — bold names, one-line descriptions. Every `agents:` frontmatter entry must have a corresponding roster line.

Example for `agents: ['agent-a', 'agent-b', 'agent-c-sub']`:
```
Your team:

Specialists — multi-step, full-scope tasks. Not delegating costs you velocity:
- **agent-a** — investigation expert. More thorough, better sourced, and keeps your context clean.
- **agent-b** — coding workhorse. Every code change goes here, even one-liners. Doing it yourself is slower and burns context.

Workers — dirt cheap, high accuracy. No task is too small:
- **agent-c-sub** — writing specialist. Any markdown. More consistent and polished than inline writing.
```

Self-referencing (e.g. agent-a listing agent-a) is valid for cold reads.

### Common missteps

- **Mixing rules and workflow.** "Think out loud" is a rule (always true). "Read the situation first" is workflow step 1 (specific moment). For each line: always true regardless of task → rule; happens at a specific point → workflow.
- **Skills in persona.** List skills in `<capabilities>` or inline in `<workflow>` steps — not at the bottom of `<persona>`.
- **Domain-specific rules.** "Stop at objective boundaries" is too eng-specific. Reframe as universal: "Don't get ahead of yourself."
- **Flat workflow.** A numbered list reads like a checklist. Use nested `##` headers with judgment guidance under each phase.
- **Cutting things the agent needs.** Cold readers may flag content that looks like duplication — not everything in a skill should be stripped. Some things are the agent's core operating procedure. Push back when the cut would remove identity.
- **Forgetting frontmatter after rewrites.** After rewriting the body, recheck the frontmatter checklist (Frontmatter row above).
- **Capabilities restating rules/workflow.** If `<capabilities>` mirrors what other tags already say, cut it. Only use it for domain scoping.
- **No decision criteria in workflow.** An agent that has to make judgment calls (when to stop, when to escalate, when to delegate) needs concrete thresholds — not open-ended "use your judgment."
- **Missing the categorical prohibition.** Selling delegation (team roster, conviction language) is not enough for parent/orchestrator agents. They also need a hard prohibition: an explicit statement that doing domain work inline is not allowed. Selling makes delegation attractive; the prohibition closes the escape hatch. The prohibition must appear in `<rules>` and be restated (in different words) at the action decision point in `<workflow>` so it fires when the agent actually needs it, not just at load time.
