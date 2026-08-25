#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "json5", "python-frontmatter"]
# ///
"""agent-doctor — keep agent tool-lists correct as plugins install and MCP servers change.

Intent lives in `assignments.yaml` (agent -> tool GROUPS), kept in the STORE separate from the
agent files so a plugin update can't wipe it. A `*.toolsets.jsonc` defines groups (the name
encodes a human-facing tier: read_/write_/write_*_safe/write_*_delete) and `~presets` compose
them. `assign` expands each agent's groups to leaf tool IDs (BFS) and writes them into `tools:`
— but ONLY if every expanded leaf is structurally valid. A dangling/typo'd group reference is a
HARD ERROR and is never written (we fix the config, not hide it).

STORE (a git repo; default ~/.copilot/agent-doctor):
  toolsets.toolsets.jsonc     canonical groups + ~presets
  assignments.yaml            agent -> [groups]
  agent-states/<agent>.json   committed drift baseline + restore source (sorted, one-per-line)
Writes to the store are auto-committed.

Commands:
  assign    Reconcile agents to assignments. Preview by default; --write to apply + commit.
  check     Dry-run assignments and compare them to current tools: and committed state.
  restore   Write an agent's committed state back into its file (undo). --write to apply.
  save      Snapshot current agent tools: into the state baseline and commit.
  get       Print an agent's frontmatter as JSON.

Leaf validity: a leaf is VALID if it is server/tool or is a known builtin bare
group (defaults/builtins.yaml). Anything else is an unresolved group ref → error.
Unknown leaves are never auto-added; declare intentional new tools in the toolset first.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import deque
from pathlib import Path

import frontmatter
import json5
import yaml

DEFAULT_STORE = Path.home() / ".copilot" / "agent-doctor"


# ── frontmatter round-trip (python-frontmatter parse; block tools, compact agents) ──

class FlowList(list):
    """Rendered in YAML flow style: [a, b, c]."""


yaml.SafeDumper.add_representer(
    FlowList, lambda d, data: d.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)
)
FLOW_KEYS = {"tools", "agents"}


def read_agent(path: Path) -> frontmatter.Post:
    return frontmatter.loads(path.read_text(encoding="utf-8"))


def agent_tools(post: frontmatter.Post) -> set[str]:
    return set(post.get("tools") or [])


def write_agent(path: Path, post: frontmatter.Post, tools: list[str]) -> None:
    """Write with sorted block-style tools: and compact agents:, order kept otherwise.
    Parse via python-frontmatter (robust), but dump the YAML ourselves so the FlowList
    representer (registered on SafeDumper) is actually used."""
    meta = dict(post.metadata)
    meta["tools"] = sorted(set(tools))
    if isinstance(meta.get("agents"), list):
        meta["agents"] = FlowList(meta["agents"])  # keep order; render compact
    dumped = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=10**9)
    path.write_text("---\n" + dumped + "---\n" + post.content.lstrip("\n") + "\n", encoding="utf-8")


# ── toolsets + expansion ────────────────────────────────────────────────────

def load_toolsets(path: Path) -> dict:
    """Parse a *.toolsets.jsonc (json5 handles // and /* */ comments + trailing commas)."""
    return json5.loads(path.read_text(encoding="utf-8"))


def expand(toolsets: dict, start_keys: list[str], registry: dict) -> list[str]:
    """BFS over group references, resolving to CONCRETE leaf tool IDs.
      - a defined toolset group          -> recurse
      - a bare builtin group (registry)  -> its concrete leaves
      - anything else                     -> a leaf
    Returns ordered deduped leaves. Cycle-guarded."""
    builtins = registry.get("builtins", {})
    seen_sets: set[str] = set()
    seen_leaves: set[str] = set()
    leaves: list[str] = []
    queue = deque(start_keys)
    while queue:
        item = queue.popleft()
        if item in toolsets:
            if item in seen_sets:
                continue
            seen_sets.add(item)
            queue.extend(toolsets[item].get("tools", []))
        elif item in builtins:
            queue.extend(builtins[item])
        elif item not in seen_leaves:
            seen_leaves.add(item)
            leaves.append(item)
    return leaves


# ── defaults (builtins allow-list + tombstones) ──────────────────────────────

def load_defaults(defaults_dir: Path) -> tuple[set[str], dict]:
    builtins: set[str] = set()
    tombstones: dict = {}
    b = defaults_dir / "builtins.yaml"
    if b.exists():
        data = yaml.safe_load(b.read_text(encoding="utf-8")) or {}
        builtins = set(data.get("vscode_bare_groups", [])) | set(data.get("copilot_bare_groups", []))
    t = defaults_dir / "tombstones.yaml"
    if t.exists():
        data = yaml.safe_load(t.read_text(encoding="utf-8")) or {}
        tomb = data.get("tombstones", {})
        tombstones = tomb if isinstance(tomb, dict) else {k: "" for k in (tomb or [])}
    return builtins, tombstones


def load_registry(defaults_dir: Path) -> dict:
    """Concrete tool members for builtin expansion and known-leaf validation (registry.yaml)."""
    r = defaults_dir / "registry.yaml"
    if not r.exists():
        return {"builtins": {}, "servers": {}}
    data = yaml.safe_load(r.read_text(encoding="utf-8")) or {}
    return {"builtins": data.get("builtins", {}) or {}, "servers": data.get("servers", {}) or {}}


def leaf_is_valid(leaf: str, known_builtins: set[str]) -> bool:
    """A real leaf: server/tool, or a known builtin bare group."""
    if leaf in known_builtins:
        return True
    if "*" in leaf:
        return False
    server, sep, tool = leaf.partition("/")
    return bool(sep and server and tool) and "/" not in tool


# ── config pre-validation ────────────────────────────────────────────────────

def validate_toolsets(toolsets: dict, known_builtins: set[str]) -> list[str]:
    """Validate the JSONC shape and bare references before expansion.
    Toolsets are groups-first, not groups-only: raw leaves are allowed, but bare
    tokens must resolve to a defined group or known builtin."""
    if not isinstance(toolsets, dict):
        return ["toolsets file must be a mapping of group -> {tools: [...]}"]

    errs: list[str] = []
    for group, spec in toolsets.items():
        if not isinstance(group, str) or not group:
            errs.append(f"toolset group name must be a non-empty string, got {group!r}")
            continue
        if not isinstance(spec, dict):
            errs.append(f"{group}: group must be an object with a tools list")
            continue
        tools = spec.get("tools", [])
        if not isinstance(tools, list):
            errs.append(f"{group}: tools must be a LIST, got {type(tools).__name__}")
            continue
        for item in tools:
            if not isinstance(item, str):
                errs.append(f"{group}: non-string tool entry {item!r}")
            elif "*" in item:
                errs.append(f"{group}: wildcard entries are not allowed in tool lists: {item!r}")
            elif item in toolsets or item in known_builtins or leaf_is_valid(item, known_builtins):
                continue
            else:
                errs.append(f"{group}: '{item}' is not a defined group, builtin, or leaf (typo?)")
    return errs


def known_leaf_universe(toolsets: dict, registry: dict, known_builtins: set[str]) -> set[str]:
    """Leaves that are declared by the editable toolset or registry defaults."""
    known = set(known_builtins)
    for spec in toolsets.values():
        if not isinstance(spec, dict):
            continue
        tools = spec.get("tools", [])
        if not isinstance(tools, list):
            continue
        for item in tools:
            if isinstance(item, str) and item not in toolsets and leaf_is_valid(item, known_builtins):
                known.add(item)
    for members in registry.get("servers", {}).values():
        known |= set(members)
    for members in registry.get("builtins", {}).values():
        known |= set(members)
    return known


def leaf_advisories(agent: str, leaves: list[str], tombstones: dict) -> list[str]:
    advisories: list[str] = []
    for leaf in leaves:
        if leaf in tombstones:
            advisories.append(f"{agent}: tombstoned tool '{leaf}' — {tombstones[leaf]}")
    return advisories


def unknown_leaf_errors(agent: str, leaves: list[str], known_leaves: set[str]) -> list[str]:
    unknown = sorted(set(leaves) - known_leaves)
    if not unknown:
        return []
    return [f"{agent}: expanded leaf tool(s) not declared in toolsets or registry: {unknown}"]

def validate_assignments(assignments: dict, toolsets: dict, known_builtins: set[str]) -> list[str]:
    """Structural checks BEFORE expansion. Each agent -> list; each entry a defined group,
    a raw leaf (groups-first, not groups-only), or a known builtin. Else a typo/error."""
    errs: list[str] = []
    if not isinstance(assignments, dict):
        return ["assignments.yaml must be a mapping of agent -> [groups]"]
    for agent, groups in assignments.items():
        if not isinstance(groups, list):
            errs.append(f"{agent}: assignment must be a LIST, got {type(groups).__name__} "
                        f"(did you write `{agent}: {groups}` instead of a list?)")
            continue
        for g in groups:
            if not isinstance(g, str):
                errs.append(f"{agent}: non-string entry {g!r}")
            elif "*" in g:
                errs.append(f"{agent}: wildcard entries are not allowed in assignments: {g!r}")
            elif g in toolsets or leaf_is_valid(g, known_builtins):
                continue
            else:
                errs.append(f"{agent}: '{g}' is not a defined group, builtin, or leaf (typo?)")
    return errs


# ── git ──────────────────────────────────────────────────────────────────────

def git(store: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(store), *args], capture_output=True, text=True)


def commit_store(store: Path, message: str) -> tuple[str, bool]:
    if not (store / ".git").exists():
        git(store, "init", "-q")
    git(store, "add", "-A")
    status = git(store, "status", "--porcelain")
    if not status.stdout.strip():
        return "store: nothing to commit", True
    r = git(store, "commit", "-q", "-m", message)
    if r.returncode == 0:
        return "store: committed", True
    return f"store: commit failed ({r.stderr.strip()})", False


# ── diff helper ──────────────────────────────────────────────────────────────

def diff_line(label: str, expected: set[str], current: set[str]) -> tuple[list[str], list[str]]:
    return sorted(expected - current), sorted(current - expected)


def by_server(items: list[str]) -> dict[str, list[str]]:
    """Group tool IDs by server prefix (before '/'); bare builtins under '(builtin)'."""
    groups: dict[str, list[str]] = {}
    for it in items:
        srv, _, leaf = it.partition("/")
        if not leaf:
            srv, leaf = "(builtin)", it
        groups.setdefault(srv, []).append(leaf)
    return groups


def render_delta(added: list[str], removed: list[str], indent: str = "    ") -> list[str]:
    """Human-readable diff: one line per added/removed tool."""
    lines: list[str] = []
    for sign, items in (("+", added), ("-", removed)):
        for item in sorted(items):
            lines.append(f"{indent}{sign} {item}")
    return lines


def by_server_set(tools) -> dict[str, set[str]]:
    d: dict[str, set[str]] = {}
    for t in tools:
        srv = t.split("/", 1)[0] if "/" in t else "(builtin)"
        d.setdefault(srv, set()).add(t)
    return d


def render_by_server(current: set[str], expected: set[str], indent: str = "  ") -> list[str]:
    """Per-server view: only servers that changed, with one line per changed tool."""
    cur, exp = by_server_set(current), by_server_set(expected)
    lines: list[str] = []
    for srv in sorted(set(cur) | set(exp)):
        c, e = cur.get(srv, set()), exp.get(srv, set())
        if c == e:
            continue
        lines.append(f"{indent}{srv} ({len(c)} -> {len(e)})")
        for item in sorted(e - c):
            lines.append(f"{indent}  + {item}")
        for item in sorted(c - e):
            lines.append(f"{indent}  - {item}")
    return lines


# ── commands ──────────────────────────────────────────────────────────────────

def resolve_paths(args):
    store = Path(args.store).expanduser()
    ts = getattr(args, "toolsets", None)
    asg = getattr(args, "assignments", None)
    dfl = getattr(args, "defaults", None)
    toolsets_path = Path(ts).expanduser() if ts else store / "toolsets.toolsets.jsonc"
    assignments_path = Path(asg).expanduser() if asg else store / "assignments.yaml"
    defaults_dir = Path(dfl).expanduser() if dfl else store / "defaults"
    states_dir = store / "agent-states"
    return store, toolsets_path, assignments_path, defaults_dir, states_dir


def state_path(states_dir: Path, agent: str) -> Path:
    return states_dir / f"{agent}.json"


def save_state(states_dir: Path, agent: str, tools: list[str], assignment=None) -> None:
    states_dir.mkdir(parents=True, exist_ok=True)
    payload = {"name": agent, "tools": sorted(set(tools))}
    if assignment is not None:
        payload["assignment"] = list(assignment)
    state_path(states_dir, agent).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                                             encoding="utf-8")


def load_state(states_dir: Path, agent: str) -> dict | None:
    p = state_path(states_dir, agent)
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def cmd_get(args) -> int:
    post = read_agent(Path(args.agent))
    print(json.dumps(post.metadata, indent=2, ensure_ascii=False))
    return 0


def cmd_assign(args) -> int:
    store, toolsets_path, assignments_path, defaults_dir, states_dir = resolve_paths(args)
    for label, pth in (("toolsets", toolsets_path), ("assignments", assignments_path)):
        if not pth.exists():
            print(f"✗ {label} file not found: {pth}")
            return 2
    toolsets = load_toolsets(toolsets_path)
    assignments = yaml.safe_load(assignments_path.read_text(encoding="utf-8")) or {}
    known_builtins, tombstones = load_defaults(defaults_dir)
    registry = load_registry(defaults_dir)
    agents_dir = Path(args.agents_dir)

    # 1) pre-validate config structurally
    errs = validate_toolsets(toolsets, known_builtins) + validate_assignments(assignments, toolsets, known_builtins)
    if errs:
        print("CONFIG ERRORS (fix before running):")
        for e in errs:
            print(f"  ✗ {e}")
        return 2

    only = set(args.agents) if args.agents else None
    unknown_requested = sorted((only or set()) - set(assignments))
    plans, hard_errors, advisories = [], [], []
    for agent in unknown_requested:
        hard_errors.append(f"{agent}: requested but not present in assignments.yaml")
    known_leaves = known_leaf_universe(toolsets, registry, known_builtins)
    for agent, groups in assignments.items():
        if only and agent not in only:
            continue
        agent_path = agents_dir / f"{agent}.agent.md"
        if not agent_path.exists():
            hard_errors.append(f"{agent}: no agent file at {agent_path}")
            continue
        leaves = expand(toolsets, list(groups), registry)
        invalid = [l for l in leaves if not leaf_is_valid(l, known_builtins)]
        if invalid:
            hard_errors.append(f"{agent}: unresolved leaf/group refs (typo?): {invalid}")
        hard_errors.extend(unknown_leaf_errors(agent, leaves, known_leaves))
        advisories.extend(leaf_advisories(agent, leaves, tombstones))
        post = read_agent(agent_path)
        current = agent_tools(post)
        plans.append((agent, agent_path, post, leaves, current))

    # 2) report plan, grouped by server (changed servers only)
    for agent, _p, _post, leaves, current in plans:
        expected = set(leaves)
        rows = render_by_server(current, expected)
        groups_str = ", ".join(assignments[agent])
        if rows:
            print(f"{agent}: assignment would change tools")
            print(f"  groups: {groups_str}")
            print(f"  tools: {len(current)} current -> {len(expected)} assigned")
            for r in rows:
                print(r)
        else:
            print(f"{agent}: no change")
            print(f"  groups: {groups_str}")
            print(f"  tools: {len(expected)}")
    for a in advisories:
        print(f"  ⚠ {a}")

    # 3) hard errors block the write entirely — no partial application
    if hard_errors:
        print("\nHARD ERRORS — nothing written:")
        for e in hard_errors:
            print(f"  ✗ {e}")
        return 2

    if not args.write:
        print("\npreview only — rerun with --write to apply")
        return 0

    # 4) write + post-verify + save state
    for agent, agent_path, post, leaves, _current in plans:
        write_agent(agent_path, post, leaves)
        verify = agent_tools(read_agent(agent_path))
        if verify != set(leaves):
            print(f"  ✗ {agent}: POST-VERIFY FAILED (written tools != expected); aborting")
            return 3
        save_state(states_dir, agent, leaves, assignment=assignments[agent])
    msg, ok = commit_store(store, f"assign: {len(plans)} agent(s)")
    print("\n" + msg)
    return 0 if ok else 4


def cmd_check(args) -> int:
    store, toolsets_path, assignments_path, defaults_dir, states_dir = resolve_paths(args)
    agents_dir = Path(args.agents_dir)
    states = {}
    if states_dir.exists():
        for sp in sorted(states_dir.glob("*.json")):
            states[sp.stem] = json.loads(sp.read_text(encoding="utf-8"))

    toolsets = {}
    assignments = {}
    known_builtins, tombstones = load_defaults(defaults_dir)
    registry = load_registry(defaults_dir)
    have_intent = toolsets_path.exists() and assignments_path.exists()
    if have_intent:
        toolsets = load_toolsets(toolsets_path)
        assignments = yaml.safe_load(assignments_path.read_text(encoding="utf-8")) or {}
        errs = validate_toolsets(toolsets, known_builtins) + validate_assignments(assignments, toolsets, known_builtins)
        if errs:
            print("CONFIG ERRORS (fix before running):")
            for e in errs:
                print(f"  ✗ {e}")
            return 2
    elif not states:
        print("no assignments/toolsets or committed states found — run `assign --write` or `save` first")
        return 0

    drift = 0
    hard_errors: list[str] = []
    advisories: list[str] = []
    known_leaves = known_leaf_universe(toolsets, registry, known_builtins)
    agents = sorted(set(assignments) | set(states))

    for agent in agents:
        baseline = set(states.get(agent, {}).get("tools", []))
        agent_path = agents_dir / f"{agent}.agent.md"
        if not agent_path.exists():
            source = "assigned in assignments.yaml" if agent in assignments else "state exists"
            print(f"{agent}: MISSING agent file at {agent_path} ({source})")
            drift += 1
            continue
        current = agent_tools(read_agent(agent_path))

        if agent in assignments:
            leaves = expand(toolsets, list(assignments[agent]), registry)
            invalid = [l for l in leaves if not leaf_is_valid(l, known_builtins)]
            if invalid:
                hard_errors.append(f"{agent}: unresolved leaf/group refs (typo?): {invalid}")
            hard_errors.extend(unknown_leaf_errors(agent, leaves, known_leaves))
            advisories.extend(leaf_advisories(agent, leaves, tombstones))

            expected = set(leaves)
            groups_str = ", ".join(assignments[agent])
            changed = False
            if current != expected:
                changed = True
                drift += 1
                print(f"{agent}: file differs from assignment")
                print(f"  groups: {groups_str}")
                print(f"  tools: {len(current)} current -> {len(expected)} assigned")
                for line in render_by_server(current, expected):
                    print(line)
            if states and baseline != expected:
                changed = True
                drift += 1
                print(f"{agent}: saved baseline differs from assignment")
                print(f"  tools: {len(baseline)} saved -> {len(expected)} assigned")
                for line in render_by_server(baseline, expected):
                    print(line)
            elif not states:
                print(f"{agent}: no saved baseline   [{groups_str}]")
            if not changed:
                print(f"{agent}: clean")
                print(f"  groups: {groups_str}")
                print(f"  tools: {len(expected)}")
        else:
            added, removed = diff_line(agent, current, baseline)  # current vs baseline
            if added or removed:
                drift += 1
                print(f"{agent}: FILE != BASELINE +{len(added)} / -{len(removed)}")
                for line in render_delta(added, removed):
                    print(line)
            else:
                print(f"{agent}: clean vs baseline")

    for a in advisories:
        print(f"  ⚠ {a}")
    if hard_errors:
        print("\nHARD ERRORS:")
        for e in hard_errors:
            print(f"  ✗ {e}")
        return 2
    print(f"\n{drift} drift point(s)")
    return 1 if drift else 0


def cmd_restore(args) -> int:
    store, _t, _a, _d, states_dir = resolve_paths(args)
    agents_dir = Path(args.agents_dir)
    agent = args.agent
    state = load_state(states_dir, agent)
    if state is None:
        print(f"{agent}: no committed state to restore from")
        return 2
    agent_path = agents_dir / f"{agent}.agent.md"
    if not agent_path.exists():
        print(f"{agent}: no agent file at {agent_path}")
        return 2
    post = read_agent(agent_path)
    baseline = state.get("tools", [])
    added, removed = diff_line(agent, set(baseline), agent_tools(post))
    print(f"restore {agent}: +{len(added)} / -{len(removed)}")
    for line in render_delta(added, removed):
        print(line)
    if not (added or removed):
        print("  already matches baseline; nothing to do")
        return 0
    if not args.write:
        print("\npreview only — rerun with --write to restore")
        return 0
    write_agent(agent_path, post, baseline)
    if agent_tools(read_agent(agent_path)) != set(baseline):
        print(f"  ✗ {agent}: POST-VERIFY FAILED")
        return 3
    print("restored")
    return 0


def cmd_save(args) -> int:
    store, _t, assignments_path, _d, states_dir = resolve_paths(args)
    agents_dir = Path(args.agents_dir)
    assignments = {}
    if assignments_path.exists():
        assignments = yaml.safe_load(assignments_path.read_text(encoding="utf-8")) or {}
    if args.all:
        agents = [p.stem.replace(".agent", "") for p in agents_dir.glob("*.agent.md")]
    else:
        agents = [args.agent]
    saved = 0
    for agent in agents:
        agent_path = agents_dir / f"{agent}.agent.md"
        if not agent_path.exists():
            print(f"{agent}: no agent file — skipped")
            continue
        tools = sorted(agent_tools(read_agent(agent_path)))
        save_state(states_dir, agent, tools, assignment=assignments.get(agent))
        print(f"{agent}: saved {len(tools)} tools")
        saved += 1
    msg, ok = commit_store(store, f"save: {saved} agent(s) baseline")
    print("\n" + msg)
    return 0 if ok else 4


def _add_common(pr, need_agents_dir=True):
    pr.add_argument("--store", default=str(DEFAULT_STORE), help=f"store dir (default {DEFAULT_STORE})")
    if need_agents_dir:
        pr.add_argument("--agents-dir", required=True, help="dir containing <agent>.agent.md files")


def main() -> int:
    p = argparse.ArgumentParser(prog="agent-doctor", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("assign", help="reconcile agents to assignments (preview; --write to apply)")
    _add_common(a)
    a.add_argument("--toolsets"); a.add_argument("--assignments"); a.add_argument("--defaults")
    a.add_argument("--write", action="store_true", help="actually write files + save state + commit")
    a.add_argument("agents", nargs="*", help="limit to these agent names (default: all)")
    a.set_defaults(func=cmd_assign)

    c = sub.add_parser("check", help="dry-run assignments against current tools and baseline (read-only)")
    _add_common(c)
    c.add_argument("--toolsets"); c.add_argument("--assignments"); c.add_argument("--defaults")
    c.set_defaults(func=cmd_check)

    r = sub.add_parser("restore", help="write an agent's committed state back into its file")
    _add_common(r)
    r.add_argument("agent")
    r.add_argument("--write", action="store_true")
    r.set_defaults(func=cmd_restore)

    s = sub.add_parser("save", help="snapshot current agent tools into the baseline + commit")
    _add_common(s)
    s.add_argument("agent", nargs="?"); s.add_argument("--all", action="store_true")
    s.add_argument("--assignments")
    s.set_defaults(func=cmd_save)

    g = sub.add_parser("get", help="print an agent's frontmatter as JSON")
    g.add_argument("agent")
    g.set_defaults(func=cmd_get)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
