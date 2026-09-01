#!/usr/bin/env python3
"""Offline authoring guardrail for plugin/marketplace repos (house standard).

Canon validation is `claude plugin validate` — this script only catches what
validate can't (house-standard rules) or what only shows up at runtime
(unparseable component JSON, missing hooks wrapper, unquoted PLUGIN_ROOT).

Usage:
    python3 preflight_plugin.py <repo-root>          # errors -> exit 1
    python3 preflight_plugin.py <repo-root> --json   # machine-readable
    python3 preflight_plugin.py --self-test

Checks (E = error, W = warning):
  E version present in plugin.json; not duplicated in marketplace entry (W if equal)
  E $schema present in both manifests
  E LICENSE file at repo root; W license field in plugin.json
  E plugins[] sorted by name (I1); E no duplicate names (I2)
  E description 10-2000 chars (I3); E name ~ ^[a-z0-9][a-z0-9-]{1,63}$ (I11)
  E external source (github/url/git-subdir) carries 40-hex sha (I5)
  E no shell metacharacters in string fields (I9); E no invisible Unicode (I10)
  E plugin settings.json keys subset of {agent, subagentStatusLine}
  E dependencies versions are valid semver ranges
  E .mcp.json / hooks/hooks.json / .lsp.json parse; hooks.json has {"hooks":...} wrapper
  W unquoted ${CLAUDE_PLUGIN_ROOT} in shell-form hook/monitor commands
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
SEMVER_RANGE_RE = re.compile(
    r"^\s*[~^=]?\s*\d+(\.\d+){0,2}([-.+][0-9A-Za-z.-]+)?(\s*(\|\||\s)\s*[<>=~^]*\s*\d+(\.\d+){0,2}([-.+][0-9A-Za-z.-]+)?)*\s*$"
    r"|^\s*[<>]=?\s*\d+(\.\d+){0,2}\s*$"
)
SHELL_META = re.compile(r"[;&|`$><]")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
EXTERNAL_SOURCE_TYPES = {"github", "url", "git-subdir"}


def _invisible(s: str) -> bool:
    return any(
        unicodedata.category(ch) in ("Cf", "Co") or ch in "​‌‍⁠﻿"
        for ch in s
    )


def _load_json(path: Path, issues: list, level: str = "E"):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        issues.append((level, f"{path}: invalid JSON — {exc}"))
        return None


def check_repo(root: Path):
    issues: list[tuple[str, str]] = []  # (level, message)

    mk_path = root / ".claude-plugin" / "marketplace.json"
    mk = _load_json(mk_path, issues)
    if mk is None and not mk_path.exists():
        issues.append(("E", f"{mk_path} missing — not a marketplace repo?"))
        return issues
    if mk is None:
        return issues

    if "$schema" not in mk:
        issues.append(("E", "marketplace.json: missing $schema"))
    if not (root / "LICENSE").exists() and not (root / "LICENSE.txt").exists():
        issues.append(("E", "repo root: LICENSE file missing"))

    entries = mk.get("plugins", [])
    names = [e.get("name", "") for e in entries]
    if names != sorted(names):
        issues.append(("E", "marketplace.json: plugins[] not sorted by name (I1)"))
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        issues.append(("E", f"marketplace.json: duplicate plugin names {sorted(dupes)} (I2)"))

    for entry in entries:
        name = entry.get("name", "<unnamed>")
        if not NAME_RE.match(name):
            issues.append(("E", f"{name}: name fails ^[a-z0-9][a-z0-9-]{{1,63}}$ (I11)"))
        desc = entry.get("description", "")
        if desc and not (10 <= len(desc) <= 2000):
            issues.append(("E", f"{name}: description length {len(desc)} outside 10-2000 (I3)"))
        for field in ("name", "description", "category"):
            val = entry.get(field)
            if isinstance(val, str) and _invisible(val):
                issues.append(("E", f"{name}: invisible Unicode in {field} (I10)"))

        source = entry.get("source")
        src_type = source.get("source") if isinstance(source, dict) else None
        if src_type in EXTERNAL_SOURCE_TYPES:
            sha = source.get("sha", "")
            if not SHA40_RE.match(sha or ""):
                issues.append(("E", f"{name}: external source ({src_type}) without full 40-hex sha (I5)"))
        if isinstance(source, dict):
            for v in source.values():
                if isinstance(v, str) and SHELL_META.search(v):
                    issues.append(("E", f"{name}: shell metacharacters in source field (I9)"))

        # locate local plugin dir for relative-path sources
        if isinstance(source, str):
            pdir = (root / source).resolve()
            if pdir.exists():
                issues.extend(check_plugin_dir(pdir, name, entry))
            else:
                issues.append(("E", f"{name}: source path {source} does not exist"))
    return issues


def check_plugin_dir(pdir: Path, mk_name: str, mk_entry: dict):
    issues: list[tuple[str, str]] = []
    pj_path = pdir / ".claude-plugin" / "plugin.json"
    pj = _load_json(pj_path, issues)
    if pj is None:
        if not pj_path.exists():
            issues.append(("W", f"{mk_name}: no plugin.json (name falls back to install dir — set one)"))
        return issues

    if "$schema" not in pj:
        issues.append(("E", f"{mk_name}: plugin.json missing $schema"))
    if "version" not in pj:
        issues.append(("E", f"{mk_name}: plugin.json missing version (house standard: explicit semver)"))
    elif "version" in mk_entry:
        lvl = "W" if mk_entry["version"] == pj["version"] else "E"
        issues.append((lvl, f"{mk_name}: version set in BOTH plugin.json and marketplace entry "
                            f"({'equal' if lvl == 'W' else 'DIFFERENT — plugin.json silently wins'})"))
    if "license" not in pj:
        issues.append(("W", f"{mk_name}: plugin.json missing license field"))

    deps = pj.get("dependencies", [])
    for dep in deps if isinstance(deps, list) else []:
        if isinstance(dep, dict) and "version" in dep:
            if not SEMVER_RANGE_RE.match(str(dep["version"])):
                issues.append(("E", f"{mk_name}: dependency {dep.get('name')}: "
                                    f"'{dep['version']}' is not a valid semver range"))

    settings = _load_json(pdir / "settings.json", issues)
    if isinstance(settings, dict):
        extra = set(settings) - {"agent", "subagentStatusLine"}
        if extra:
            issues.append(("E", f"{mk_name}: settings.json unknown keys {sorted(extra)} "
                                f"(only agent/subagentStatusLine are read)"))

    for comp in (".mcp.json", ".lsp.json"):
        _load_json(pdir / comp, issues)  # parse errors recorded as E

    hooks_path = pdir / "hooks" / "hooks.json"
    hooks = _load_json(hooks_path, issues)
    if hooks is not None:
        if "hooks" not in hooks:
            issues.append(("E", f"{mk_name}: hooks/hooks.json lacks the outer {{\"hooks\":...}} "
                                f"wrapper — hooks will silently never register"))
        else:
            blob = json.dumps(hooks)
            if "${CLAUDE_PLUGIN_ROOT}" in blob and '\\"${CLAUDE_PLUGIN_ROOT}' not in blob:
                issues.append(("W", f"{mk_name}: ${{CLAUDE_PLUGIN_ROOT}} appears unquoted in "
                                    f"hooks.json commands — breaks on paths with spaces"))
    return issues


def self_test() -> int:
    import tempfile
    ok = True
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".claude-plugin").mkdir()
        (root / "LICENSE").write_text("MIT")
        (root / "plugins" / "aaa" / ".claude-plugin").mkdir(parents=True)
        (root / "plugins" / "aaa" / ".claude-plugin" / "plugin.json").write_text(json.dumps(
            {"$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
             "name": "aaa", "version": "1.0.0", "license": "MIT"}))
        (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(
            {"$schema": "https://json.schemastore.org/claude-code-plugin-marketplace.json",
             "name": "test-mk", "owner": {"name": "t"},
             "plugins": [{"name": "aaa", "description": "A valid test plugin.",
                          "source": "./plugins/aaa"}]}))
        issues = check_repo(root)
        errors = [i for i in issues if i[0] == "E"]
        if errors:
            print("self-test FAIL: clean fixture produced errors:", errors)
            ok = False

        # bad fixture: dup version, missing sha, bad name
        mk = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
        mk["plugins"].append({"name": "ZZ bad", "description": "short",
                              "version": "2.0.0",
                              "source": {"source": "github", "repo": "x/y"}})
        (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(mk))
        issues = check_repo(root)
        msgs = "\n".join(m for _, m in issues)
        for expected in ("not sorted", "fails ^", "40-hex sha", "outside 10-2000"):
            if expected not in msgs:
                print(f"self-test FAIL: expected finding containing '{expected}'")
                ok = False
    print("self-test:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if args[0] == "--self-test":
        return self_test()
    root = Path(args[0]).resolve()
    as_json = "--json" in args
    issues = check_repo(root)
    errors = [m for lvl, m in issues if lvl == "E"]
    warnings = [m for lvl, m in issues if lvl == "W"]
    if as_json:
        print(json.dumps({"errors": errors, "warnings": warnings}, ensure_ascii=False, indent=1))
    else:
        for m in errors:
            print(f"ERROR   {m}")
        for m in warnings:
            print(f"warning {m}")
        print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
