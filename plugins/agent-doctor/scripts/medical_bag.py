#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml", "json5", "python-frontmatter"]
# ///
"""agent-doctor — keep agent tool-lists correct as plugins install and MCP servers change.

Intent lives in `assignments.yaml` (`agents:` records with `filepath` + tool GROUPS), kept in the
STORE separate from the agent files so a plugin update can't wipe it. A `*.toolsets.jsonc` defines groups (the name
encodes a human-facing tier: read_/write_/write_*_safe/write_*_delete) and `~presets` compose
them. `assign` expands each agent's groups to leaf tool IDs (BFS) and writes them into `tools:`
— but ONLY if every expanded leaf is structurally valid. A dangling/typo'd group reference is a
HARD ERROR and is never written (we fix the config, not hide it).

STORE (a git repo; default ~/.copilot/agent-doctor):
  toolsets.toolsets.jsonc     canonical toolset (also deployed to VS Code prompts/)
    assignments.yaml            agents: [{filepath, groups}]
  agent-states/<agent>.json   committed drift baseline + restore source (sorted, one-per-line)
Writes to the store are auto-committed.

Commands:
  assign    Reconcile agents to assignments. Preview by default; --write to apply + commit.
  check     Compare each agent's file to its assignment (and note baseline drift). Read-only.
    discover  Scan configured/overridden dirs and print only UNASSIGNED filepath stubs.
  restore   Write an agent's committed state back into its file (undo). --write to apply.
  save      Snapshot current agent tools: into the state baseline and commit.
  reconcile Diff the live tool-picker roster (--ui/stdin) vs the store toolset, per server
            (exact-case): NEW (in picker, not store) / GONE (in store, not picker). Read-only.
  fmt       Reflow the toolset jsonc to canonical per-group form (drops comments; names carry structure).

Leaf validity: a leaf is VALID if it contains "/" (server/tool) or is a slash-less token named
by an underscore-prefixed allow-list group in the toolset store. Anything else bare is an
unresolved group ref → error. A genuinely new tool is added deliberately to a toolset group, so a
typo can never silently become a "valid" tool.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import deque
from pathlib import Path

import frontmatter
import json5
import yaml

DEFAULT_STORE = Path.home() / ".copilot" / "agent-doctor"
AGENT_FILE_SUFFIX = ".agent.md"


# ── frontmatter round-trip (python-frontmatter parse; compact tools: via FlowList) ──

class FlowList(list):
    """Rendered in YAML flow style: [a, b, c]."""


yaml.SafeDumper.add_representer(
    FlowList, lambda d, data: d.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)
)


def read_agent(path: Path) -> frontmatter.Post:
    return frontmatter.loads(path.read_text(encoding="utf-8"))


def agent_tools(post: frontmatter.Post) -> set[str]:
    return set(post.get("tools") or [])


def write_agent(path: Path, post: frontmatter.Post, tools: list[str]) -> None:
    """Write with sorted compact tools:/agents: (flow) and everything else block, order kept.
    Parse via python-frontmatter (robust), but dump the YAML ourselves so the FlowList
    representer (registered on SafeDumper) is actually used."""
    meta = dict(post.metadata)
    meta["tools"] = FlowList(sorted(set(tools)))
    if isinstance(meta.get("agents"), list):
        meta["agents"] = FlowList(meta["agents"])  # keep order; render compact
    dumped = yaml.safe_dump(meta, sort_keys=False, allow_unicode=True, width=10**9)
    path.write_text("---\n" + dumped + "---\n" + post.content.lstrip("\n") + "\n", encoding="utf-8")


# ── toolsets + expansion ────────────────────────────────────────────────────

def load_toolsets(path: Path) -> dict:
    """Parse a *.toolsets.jsonc (json5 handles // and /* */ comments + trailing commas)."""
    return json5.loads(path.read_text(encoding="utf-8"))


def bare_allow_list(toolsets: dict) -> set[str]:
    """Union of slash-less tokens declared by underscore-prefixed allow-list groups."""
    allowed: set[str] = set()
    for name, body in toolsets.items():
        if not name.startswith("_"):
            continue
        tools = body.get("tools", []) if isinstance(body, dict) else []
        allowed.update(tool for tool in tools if isinstance(tool, str))
    return allowed


def expand(toolsets: dict, start_keys: list[str]) -> tuple[list[str], list[str]]:
    """Pure flatten of group composition to leaf tool IDs.
      - a defined toolset group -> recurse into its `tools`
      - anything else           -> a leaf (kept as-is)
    Ordered, deduped, cycle-guarded. No wildcard/registry resolution: builtins and servers
    are ordinary leaf-listing groups in the toolset. Underscore-prefixed groups are allow-lists
    only and may not be referenced from normal groups."""
    seen_sets: set[str] = set()
    seen_leaves: set[str] = set()
    leaves: list[str] = []
    errs: list[str] = []
    queue = deque(start_keys)
    while queue:
        item = queue.popleft()
        if item in toolsets:
            if item.startswith("_"):
                errs.append(f"'{item}' is an allow-list group and cannot be referenced from a group's tools")
                continue
            if item in seen_sets:
                continue
            seen_sets.add(item)
            queue.extend(toolsets[item].get("tools", []))
        elif item not in seen_leaves:
            seen_leaves.add(item)
            leaves.append(item)
    return leaves, errs


def leaf_is_valid(leaf: str, allowed_bare: set[str]) -> bool:
    """A real leaf: `server/tool` (one slash, both sides non-empty, no wildcard) or a bare
    token allow-listed by underscore-prefixed groups."""
    if leaf in allowed_bare:
        return True
    parts = leaf.split("/")
    return len(parts) == 2 and all(parts) and "*" not in parts


# ── assignment pre-validation ────────────────────────────────────────────────

def agent_stem_from_path(path: Path) -> str:
    name = path.name
    if not name.endswith(AGENT_FILE_SUFFIX):
        raise ValueError(f"filepath must end with {AGENT_FILE_SUFFIX}: {path}")
    return name[: -len(AGENT_FILE_SUFFIX)]


def home_relative_path(path: Path) -> str:
    expanded = path.expanduser()
    try:
        return "~/" + str(expanded.relative_to(Path.home()))
    except ValueError:
        return str(expanded)


def discover_agents(agents_dirs: list[str]) -> list[Path]:
    discovered: list[Path] = []
    seen_paths: set[Path] = set()
    for agents_dir in agents_dirs:
        root = Path(agents_dir).expanduser()
        if not root.exists():
            continue
        for path in sorted(root.glob(f"*{AGENT_FILE_SUFFIX}")):
            resolved = path.resolve()
            if resolved in seen_paths:
                continue
            seen_paths.add(resolved)
            discovered.append(path)
    return discovered


def load_discover_dirs(assignments: dict) -> tuple[list[str], list[str]]:
    discover_dirs = assignments.get("discover_dirs")
    if discover_dirs is None:
        return [], []
    if not isinstance(discover_dirs, list):
        return [], ["assignments.yaml field `discover_dirs` must be a LIST of directory paths"]

    errs: list[str] = []
    normalized: list[str] = []
    for index, value in enumerate(discover_dirs):
        if not isinstance(value, str):
            errs.append(f"discover_dirs[{index}]: directory path must be a STRING")
            continue
        normalized.append(value)
    return normalized, errs


def validate_assignments(assignments: dict, toolsets: dict, allowed_bare: set[str]) -> tuple[list[str], dict[str, dict]]:
    """Structural checks BEFORE expansion. assignments.yaml must have an `agents:` list with
    `{filepath, groups}` records. Agent identity is the filepath stem."""
    errs: list[str] = []
    agents_by_stem: dict[str, dict] = {}
    if not isinstance(assignments, dict):
        return ["assignments.yaml must be a mapping with an `agents:` list"], agents_by_stem
    _discover_dirs, discover_dir_errs = load_discover_dirs(assignments)
    errs.extend(discover_dir_errs)
    if "agents" not in assignments:
        non_discover_keys = [key for key in assignments if key != "discover_dirs"]
        if non_discover_keys and all(isinstance(assignments[key], list) for key in non_discover_keys):
            return [
                "assignments.yaml uses the legacy `name: [groups]` format; migrate to `agents:` records with `filepath` and `groups`"
            ], agents_by_stem
        return ["assignments.yaml must be a mapping with an `agents:` list"], agents_by_stem

    entries = assignments.get("agents")
    if not isinstance(entries, list):
        return ["assignments.yaml field `agents` must be a LIST of `{filepath, groups}` records"], agents_by_stem

    for index, entry in enumerate(entries):
        label = f"agents[{index}]"
        if not isinstance(entry, dict):
            errs.append(f"{label}: entry must be a mapping with `filepath` and `groups`")
            continue

        filepath = entry.get("filepath")
        groups = entry.get("groups")
        if not isinstance(filepath, str):
            errs.append(f"{label}: filepath must be a STRING")
            continue

        agent_path = Path(filepath).expanduser()
        try:
            agent = agent_stem_from_path(agent_path)
        except ValueError as exc:
            errs.append(f"{label}: {exc}")
            agent = None

        if not isinstance(groups, list):
            target = agent or filepath
            errs.append(f"{target}: groups must be a LIST, got {type(groups).__name__}")
            continue

        target = agent or filepath
        for group in groups:
            if not isinstance(group, str):
                errs.append(f"{target}: non-string entry {group!r}")
            elif group in toolsets and group.startswith("_"):
                errs.append(f"{target}: '{group}' is an allow-list group and cannot be assigned directly")
            elif group in toolsets or "/" in group or group in allowed_bare:
                continue
            else:
                errs.append(f"{target}: '{group}' is not a defined group or valid leaf (typo?)")

        if agent is None:
            continue
        if agent in agents_by_stem:
            errs.append(
                f"{label}: duplicate agent stem '{agent}' also used by {agents_by_stem[agent]['filepath']}"
            )
            continue
        agents_by_stem[agent] = {"filepath": filepath, "path": agent_path, "groups": list(groups)}

    return errs, agents_by_stem


# ── git ──────────────────────────────────────────────────────────────────────

def git(store: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(store), *args], capture_output=True, text=True)


def commit_store(store: Path, message: str) -> tuple[str, bool]:
    if not (store / ".git").exists():
        git(store, "init", "-q")
    git(store, "add", "-A")
    status = git(store, "status", "--porcelain")
    if status.returncode != 0:
        return f"store: git error — {status.stderr.strip() or 'not a usable git store'}", False
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
    """Human-readable grouped diff: one line per server, listing the leaf names."""
    lines: list[str] = []
    for sign, items in (("+", added), ("-", removed)):
        if not items:
            continue
        groups = by_server(items)
        for srv in sorted(groups):
            names = ", ".join(sorted(groups[srv]))
            lines.append(f"{indent}{sign} {srv} ({len(groups[srv])}): {names}")
    return lines


def by_server_set(tools) -> dict[str, set[str]]:
    d: dict[str, set[str]] = {}
    for t in tools:
        srv = t.split("/", 1)[0] if "/" in t else "(builtin)"
        d.setdefault(srv, set()).add(t)
    return d


def render_by_server(current: set[str], expected: set[str], indent: str = "  ") -> list[str]:
    """Per-server view: only servers that changed, showing count now→proposed + leaf +/-."""
    cur, exp = by_server_set(current), by_server_set(expected)
    lines: list[str] = []
    for srv in sorted(set(cur) | set(exp)):
        c, e = cur.get(srv, set()), exp.get(srv, set())
        if c == e:
            continue
        added = sorted(x.split("/", 1)[-1] for x in e - c)
        removed = sorted(x.split("/", 1)[-1] for x in c - e)
        seg = f"{indent}{srv:<26} {len(c):>3} → {len(e):<3}"
        if added:
            seg += "  +" + ",".join(added)
        if removed:
            seg += "  -" + ",".join(removed)
        lines.append(seg)
    return lines


# ── commands ──────────────────────────────────────────────────────────────────

def resolve_paths(args):
    store = Path(args.store).expanduser()
    ts = getattr(args, "toolsets", None)
    asg = getattr(args, "assignments", None)
    toolsets_path = Path(ts).expanduser() if ts else store / "toolsets.toolsets.jsonc"
    assignments_path = Path(asg).expanduser() if asg else store / "assignments.yaml"
    states_dir = store / "agent-states"
    return store, toolsets_path, assignments_path, states_dir


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


def cmd_assign(args) -> int:
    store, toolsets_path, assignments_path, states_dir = resolve_paths(args)
    for label, pth in (("toolsets", toolsets_path), ("assignments", assignments_path)):
        if not pth.exists():
            print(f"✗ {label} file not found: {pth}")
            return 2
    toolsets = load_toolsets(toolsets_path)
    allowed_bare = bare_allow_list(toolsets)
    assignments = yaml.safe_load(assignments_path.read_text(encoding="utf-8")) or {}

    # 1) pre-validate assignments structurally
    errs, agent_specs = validate_assignments(assignments, toolsets, allowed_bare)
    if errs:
        print("ASSIGNMENT ERRORS (fix before running):")
        for e in errs:
            print(f"  ✗ {e}")
        return 2

    only = set(args.agents) if args.agents else None
    if only:
        unknown = only - set(agent_specs)
        if unknown:
            print(f"✗ unknown agent name(s) not in assignments.yaml: {sorted(unknown)}")
            return 2
    plans, hard_errors = [], []
    for agent, spec in agent_specs.items():
        if only and agent not in only:
            continue
        groups = spec["groups"]
        agent_path = spec["path"]
        if not agent_path.exists():
            hard_errors.append(f"{agent}: no agent file at {agent_path}")
            continue
        leaves, expand_errs = expand(toolsets, list(groups))
        hard_errors.extend(f"{agent}: {err}" for err in expand_errs)
        invalid = [l for l in leaves if not leaf_is_valid(l, allowed_bare)]
        if invalid:
            hard_errors.append(f"{agent}: unresolved leaf/group refs (typo?): {invalid}")
        post = read_agent(agent_path)
        current = agent_tools(post)
        plans.append((agent, agent_path, post, leaves, current))

    # 2) report plan, grouped by server (changed servers only)
    for agent, _p, _post, leaves, current in plans:
        expected = set(leaves)
        rows = render_by_server(current, expected)
        groups_str = ", ".join(agent_specs[agent]["groups"])
        if rows:
            print(f"{agent}: {len(expected)} tools (was {len(current)})   [{groups_str}]")
            for r in rows:
                print(r)
        else:
            print(f"{agent}: no change ({len(expected)} tools)   [{groups_str}]")

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
        save_state(states_dir, agent, leaves, assignment=agent_specs[agent]["groups"])
    msg, ok = commit_store(store, f"assign: {len(plans)} agent(s)")
    print("\n" + msg)
    return 0 if ok else 4


def cmd_check(args) -> int:
    """Compare each agent's file (ACTUAL) against its assignment (DESIRED); note where it also
    differs from the committed state (BASELINE). Out-of-sync-with-intent is the primary signal;
    the fix is `assign --write`. Read-only."""
    store, toolsets_path, assignments_path, states_dir = resolve_paths(args)
    if not toolsets_path.exists():
        print(f"✗ toolsets file not found: {toolsets_path}")
        return 2
    toolsets = load_toolsets(toolsets_path)
    allowed_bare = bare_allow_list(toolsets)
    assignments = {}
    assigned_agents: dict[str, dict] = {}
    if assignments_path.exists():
        assignments = yaml.safe_load(assignments_path.read_text(encoding="utf-8")) or {}
        errs, assigned_agents = validate_assignments(assignments, toolsets, allowed_bare)
        if errs:
            print("ASSIGNMENT ERRORS (fix before running):")
            for e in errs:
                print(f"  ✗ {e}")
            return 2

    # agents to check = everything we know about: assignments ∪ committed states
    agents = set(assigned_agents)
    if states_dir.exists():
        agents |= {p.stem for p in states_dir.glob("*.json")}
    if not agents:
        print("nothing to check — no assignments or committed states found")
        return 0

    problems = 0
    for agent in sorted(agents):
        spec = assigned_agents.get(agent)
        groups = spec["groups"] if spec is not None else None
        agent_path = spec["path"] if spec is not None else None
        actual = agent_tools(read_agent(agent_path)) if agent_path and agent_path.exists() else None
        state = load_state(states_dir, agent)
        baseline = set(state.get("tools", [])) if state else None

        # anomalies — the "something weird" cases
        if groups is None:
            problems += 1
            print(f"{agent}: NO ASSIGNMENT (found in committed state) — intent unknown; add it to assignments.yaml")
            continue
        if actual is None:
            problems += 1
            print(f"{agent}: assigned but NO agent file at {agent_path} — run `assign --write`")
            continue
        leaves, expand_errs = expand(toolsets, list(groups))
        if expand_errs:
            problems += 1
            print(f"{agent}: INVALID TOOLSET REFERENCES — fix the toolset before running `assign --write`")
            for err in expand_errs:
                print(f"    ✗ {err}")
            continue
        desired = set(leaves)

        # primary — does the file match intent?
        missing, extra = diff_line(agent, desired, actual)  # in desired-not-file / in file-not-desired
        if missing or extra:
            problems += 1
            print(f"{agent}: OUT OF SYNC with assignments (+{len(missing)} / -{len(extra)}) — fix: `assign --write`")
            for line in render_delta(missing, extra):
                print(line)
        else:
            print(f"{agent}: in sync")

        # secondary — informational note about the committed baseline
        if baseline is None:
            print("    (no committed baseline yet — `assign --write` or `save` to set one)")
        elif actual != baseline:
            print(f"    (note: agent file differs from committed baseline — `restore {agent}` reverts)")

    print(f"\n{problems} agent(s) need attention")
    return 1 if problems else 0


def cmd_restore(args) -> int:
    store, toolsets_path, assignments_path, states_dir = resolve_paths(args)
    agent = args.agent
    assigned_agents: dict[str, dict] = {}
    if assignments_path.exists() and toolsets_path.exists():
        assignments = yaml.safe_load(assignments_path.read_text(encoding="utf-8")) or {}
        toolsets = load_toolsets(toolsets_path)
        errs, assigned_agents = validate_assignments(assignments, toolsets, bare_allow_list(toolsets))
        if errs:
            print("ASSIGNMENT ERRORS (fix before running):")
            for e in errs:
                print(f"  ✗ {e}")
            return 2
    state = load_state(states_dir, agent)
    if state is None:
        print(f"{agent}: no committed state to restore from")
        return 2
    spec = assigned_agents.get(agent)
    if spec is None:
        print(f"{agent}: no assignment record in assignments.yaml")
        return 2
    agent_path = spec["path"]
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
    store, toolsets_path, assignments_path, states_dir = resolve_paths(args)
    assignments = {}
    assigned_agents: dict[str, dict] = {}
    if assignments_path.exists():
        assignments = yaml.safe_load(assignments_path.read_text(encoding="utf-8")) or {}
        if not toolsets_path.exists():
            print(f"✗ toolsets file not found: {toolsets_path}")
            return 2
        toolsets = load_toolsets(toolsets_path)
        errs, assigned_agents = validate_assignments(assignments, toolsets, bare_allow_list(toolsets))
        if errs:
            print("ASSIGNMENT ERRORS (fix before running):")
            for e in errs:
                print(f"  ✗ {e}")
            return 2
    if not args.all and not args.agent:
        print("save: specify an agent name or --all")
        return 2
    if args.all:
        agents = list(assigned_agents)
    else:
        agents = [args.agent]
    if not agents:
        print("save: no assigned agents found in assignments.yaml")
        return 2
    saved = 0
    for agent in agents:
        spec = assigned_agents.get(agent)
        if spec is None:
            print(f"{agent}: no assignment record — skipped")
            continue
        agent_path = spec["path"]
        if not agent_path.exists():
            print(f"{agent}: no agent file at {agent_path} — skipped")
            continue
        tools = sorted(agent_tools(read_agent(agent_path)))
        assignment = spec.get("groups")
        save_state(states_dir, agent, tools, assignment=assignment)
        print(f"{agent}: saved {len(tools)} tools")
        saved += 1
    msg, ok = commit_store(store, f"save: {saved} agent(s) baseline")
    print("\n" + msg)
    return 0 if ok else 4


def cmd_discover(args) -> int:
    store, toolsets_path, assignments_path, _states_dir = resolve_paths(args)
    assignments = {}
    configured_dirs: list[str] = []
    assigned_agents: dict[str, dict] = {}

    if assignments_path.exists():
        assignments = yaml.safe_load(assignments_path.read_text(encoding="utf-8")) or {}
        configured_dirs, discover_dir_errs = load_discover_dirs(assignments)
        if discover_dir_errs:
            print("ASSIGNMENT ERRORS (fix before running):")
            for err in discover_dir_errs:
                print(f"  ✗ {err}")
            return 2

        if not toolsets_path.exists():
            print(f"✗ toolsets file not found: {toolsets_path}")
            return 2
        toolsets = load_toolsets(toolsets_path)
        allowed_bare = bare_allow_list(toolsets)
        errs, assigned_agents = validate_assignments(assignments, toolsets, allowed_bare)
        if errs:
            print("ASSIGNMENT ERRORS (fix before running):")
            for err in errs:
                print(f"  ✗ {err}")
            return 2

    scan_dirs = configured_dirs + (args.dir or [])
    seen_dirs: set[Path] = set()
    normalized_scan_dirs: list[str] = []
    for directory in scan_dirs:
        expanded = Path(directory).expanduser()
        key = expanded.resolve(strict=False)
        if key in seen_dirs:
            continue
        seen_dirs.add(key)
        normalized_scan_dirs.append(str(expanded))

    if not normalized_scan_dirs:
        print("no discover dirs configured — add `discover_dirs:` to assignments.yaml or pass --dir")
        return 0

    discovered = discover_agents(normalized_scan_dirs)
    if not discovered:
        print("no agent files found")
        return 0

    assigned_paths = {spec["path"].resolve(): agent for agent, spec in assigned_agents.items()}
    assigned_stems = {agent: spec["path"].resolve() for agent, spec in assigned_agents.items()}
    unassigned: list[Path] = []
    collisions: list[tuple[str, Path, Path]] = []

    for path in discovered:
        resolved = path.resolve()
        if resolved in assigned_paths:
            continue
        unassigned.append(path)
        stem = agent_stem_from_path(path)
        if stem in assigned_stems:
            collisions.append((stem, path, assigned_stems[stem]))

    if not unassigned:
        print(f"all {len(discovered)} discovered agent file(s) are already assigned")
        return 0

    print(f"{len(unassigned)} unassigned agent file(s):")
    print()
    for path in sorted(unassigned):
        print(f"  - filepath: {home_relative_path(path)}")
        print("    groups: []")

    if collisions:
        print()
        print("duplicate stem collisions:")
        for stem, discovered_path, assigned_path in sorted(collisions, key=lambda item: (item[0], str(item[1]))):
            print(
                f"  {stem}: discovered {home_relative_path(discovered_path)} conflicts with assigned {home_relative_path(assigned_path)}"
            )
    return 0


def cmd_reconcile(args) -> int:
    """Diff the live tool-picker roster against the store toolset, EXACT-CASE. Reports
    CASING (store id differs from the live tool only by case — VS Code silent-fails on it),
    then real NEW (in picker, not store) and GONE (in store, not picker), per server. The
    CLI can't see the session, so paste/pipe the Configure-Tools list via --ui <file> or
    stdin (DrAgent runs with all tools — `tools:` omitted — so it can enumerate the live roster). Read-only."""
    store, toolsets_path, _a, _s = resolve_paths(args)
    if not toolsets_path.exists():
        print(f"✗ toolsets file not found: {toolsets_path}")
        return 2
    toolsets = load_toolsets(toolsets_path)
    store_leaves = {t for g in toolsets.values() for t in (g.get("tools") or [])
                    if "/" in t and not t.endswith("/*")}
    raw = Path(args.ui).read_text(encoding="utf-8") if args.ui else sys.stdin.read()
    ui_leaves = set(re.findall(r"[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+", raw))
    if not ui_leaves:
        print("no server/tool ids found — paste the Configure-Tools list into --ui or stdin")
        return 2

    # Case-insensitive pairing: a store id equal to a live id only up to case is a CASING
    # bug (VS Code fails to resolve it silently), not a real add/remove. The live id wins.
    ui_lower = {l.lower(): l for l in ui_leaves}
    store_lower = {l.lower(): l for l in store_leaves}
    casing = sorted((store_lower[k], ui_lower[k]) for k in set(ui_lower) & set(store_lower)
                    if store_lower[k] != ui_lower[k])
    real_new = {l for l in ui_leaves if l.lower() not in store_lower}
    real_gone = {l for l in store_leaves if l.lower() not in ui_lower}

    issues = 0
    if casing:
        issues += len(casing)
        print("CASING MISMATCH — store id differs from the live tool only by case (fix the toolset to the live id):")
        for store_id, live_id in casing:
            print(f"  store: {store_id}")
            print(f"  live:  {live_id}")
        print()

    def by_server(leaves):
        d: dict[str, set[str]] = {}
        for leaf in leaves:
            d.setdefault(leaf.split("/", 1)[0], set()).add(leaf)  # exact case
        return d

    picker_by, store_by = by_server(real_new), by_server(real_gone)
    ui_srv = {l.split("/", 1)[0].lower() for l in ui_leaves}
    store_srv = {l.split("/", 1)[0].lower() for l in store_leaves}
    for srv in sorted(set(picker_by) | set(store_by)):
        new = sorted(picker_by.get(srv, set()))
        gone = sorted(store_by.get(srv, set()))
        issues += len(new) + len(gone)
        if srv.lower() not in store_srv:
            print(f"{srv}: SERVER only in picker ({len(new)}) — new; onboard it")
        elif srv.lower() not in ui_srv:
            print(f"{srv}: SERVER only in store ({len(gone)}) — gone? (down / renamed / removed)")
        else:
            print(f"{srv}:")
        for t in new:
            print(f"  + NEW  {t}")
        for t in gone:
            print(f"  - GONE {t}")
    print(f"\n{issues} issue(s)" if issues else "\nin sync — picker matches the store toolset (exact case)")
    return 0


def emit_toolset(data: dict) -> str:
    """Canonical toolset text: one group per multi-line object, keys on their own line, the
    tools array inline. Drops comments — the `<type>_<grouping>` names carry the structure."""
    lines = ["{"]
    items = list(data.items())
    for i, (name, body) in enumerate(items):
        tail = "," if i < len(items) - 1 else ""
        lines.append(f"\t{json.dumps(name)}: {{")
        for k in [k for k in body if k != "tools"]:
            lines.append(f"\t\t{json.dumps(k)}: {json.dumps(body[k], ensure_ascii=False)},")
        lines.append(f'\t\t"tools": {json.dumps(body.get("tools", []), ensure_ascii=False)}')
        lines.append(f"\t}}{tail}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def cmd_fmt(args) -> int:
    """Reflow the toolset jsonc to canonical form (json5 parse → re-emit). Drops comments; the
    `<type>_<grouping>` group names carry the structure. Preview by default; --write to commit."""
    store, toolsets_path, _a, _s = resolve_paths(args)
    path = Path(args.file).expanduser() if getattr(args, "file", None) else toolsets_path
    if not path.exists():
        print(f"✗ toolset file not found: {path}")
        return 2
    text = path.read_text(encoding="utf-8")
    reflowed = emit_toolset(load_toolsets(path))
    if reflowed == text:
        print("already canonical — nothing to do")
        return 0
    if not args.write:
        print("would reflow the toolset (preview). Rerun with --write to apply.")
        return 0
    path.write_text(reflowed, encoding="utf-8")
    if path == toolsets_path:
        msg, ok = commit_store(store, "fmt: canonical toolset formatting")
        print(msg)
        return 0 if ok else 4
    print(f"wrote {path}")
    return 0


def _add_common(pr):
    pr.add_argument("--store", default=str(DEFAULT_STORE), help=f"store dir (default {DEFAULT_STORE})")


def main() -> int:
    p = argparse.ArgumentParser(prog="agent-doctor", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("assign", help="reconcile agents to assignments (preview; --write to apply)")
    _add_common(a)
    a.add_argument("--toolsets"); a.add_argument("--assignments")
    a.add_argument("--write", action="store_true", help="actually write files + save state + commit")
    a.add_argument("agents", nargs="*", help="limit to these agent names (default: all)")
    a.set_defaults(func=cmd_assign)

    c = sub.add_parser("check", help="compare agents to assignments (+note baseline drift); read-only")
    _add_common(c)
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

    d = sub.add_parser("discover", help="scan discover dirs and print unassigned assignments.yaml filepath stubs")
    _add_common(d)
    d.add_argument("--toolsets")
    d.add_argument("--assignments")
    d.add_argument("--dir", action="append", metavar="DIR",
                   help="extra dir to scan; repeatable (--dir a --dir b). Added to `discover_dirs`.")
    d.set_defaults(func=cmd_discover)

    rc = sub.add_parser("reconcile", help="diff live picker roster (--ui/stdin) vs store toolset, per server; read-only")
    rc.add_argument("--ui", help="file with the pasted Configure-Tools roster (default: stdin)")
    rc.add_argument("--store", default=str(DEFAULT_STORE), help=f"store dir (default {DEFAULT_STORE})"); rc.add_argument("--toolsets")
    rc.set_defaults(func=cmd_reconcile)

    fm = sub.add_parser("fmt", help="reflow the toolset jsonc to canonical per-group form")
    fm.add_argument("--file", help="toolset file to reflow (default: <store>/toolsets.toolsets.jsonc)")
    fm.add_argument("--write", action="store_true"); fm.add_argument("--store", default=str(DEFAULT_STORE), help=f"store dir (default {DEFAULT_STORE})")
    fm.add_argument("--toolsets")
    fm.set_defaults(func=cmd_fmt)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
