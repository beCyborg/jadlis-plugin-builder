#!/usr/bin/env python3
"""Offline authoring guardrail for plugin/marketplace repos (house standard).

Canon validation is `claude plugin validate` — this script runs it first (when
the `claude` binary is on PATH) and then adds what validate can't check (house
rules) or what only shows up at runtime (missing hooks wrapper, unset MCP
variables, endpoint collisions). It never executes plugin code: mod modules
are checked for existence and extension only.

Usage:
    python3 preflight_plugin.py <root>                  # errors -> exit 1
    python3 preflight_plugin.py <root> --json           # machine-readable
    python3 preflight_plugin.py <root> --no-validate    # skip `claude plugin validate`
    python3 preflight_plugin.py --self-test

<root> is a marketplace repo (.claude-plugin/marketplace.json) or a single
plugin directory (.claude-plugin/plugin.json and no marketplace.json).

Checks (E = error, W = warning):
  E `claude plugin validate <dir>` fails (root + each local plugin dir); W binary absent
  E manifest JSON has a UTF-8 BOM (W for other component JSON); E JSON parse
  E version present in plugin.json; not duplicated in marketplace entry (W if equal)
  E $schema present in both manifests
  E LICENSE file at repo root; W license field in plugin.json
  E plugins[] sorted by name (I1); E no duplicate names (I2)
  E description 10-2000 chars (I3); E entry name ~ ^[a-z0-9][a-z0-9-]{1,63}$ (I11)
  E external source URL shape (I4); E external source carries 40-hex sha (I5)
  E no shell metacharacters in source fields (I9); E no invisible Unicode (I10)
  E marketplace name charset / reserved marketplace names
  E plugin name reserved (claude-*, anthropic-*, anthropics-*, cc-plugin-*, ...); W reads as Anthropic's
  W marketplace entry name differs from plugin.json name
  E plugin settings.json keys subset of {agent, subagentStatusLine}
  E dependencies versions are valid semver ranges
  E hooks/hooks.json has `hooks` or `modules`; E each module file exists with a mod extension
  E `types` (mods) is ./-relative, exists, ends in .d.ts
  W unquoted ${CLAUDE_PLUGIN_ROOT} in shell-form hook/monitor commands (exec form with args is fine)
  E ${user_config.X} in an MCP url/headers is undeclared; W url option has no default and is not required
  E ${user_config.*} in MCP headersHelper
  W ${VAR} without :-default in MCP command/args/env/url/headers
  E same MCP url in two servers of one marketplace (one silently disappears)
  W userConfig `options` (needs Claude Code >= 2.1.271); E options rule violations
"""
import json
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")
SEMVER_RANGE_RE = re.compile(
    r"^\s*[~^=]?\s*\d+(\.\d+){0,2}([-.+][0-9A-Za-z.-]+)?(\s*(\|\||\s)\s*[<>=~^]*\s*\d+(\.\d+){0,2}([-.+][0-9A-Za-z.-]+)?)*\s*$"
    r"|^\s*[<>]=?\s*\d+(\.\d+){0,2}\s*$"
)
SHELL_META = re.compile(r"[;&|`$><]")
SHA40_RE = re.compile(r"^[0-9a-f]{40}$")
EXTERNAL_SOURCE_TYPES = {"github", "url", "git-subdir"}
GITHUB_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GIT_URL_RE = re.compile(r"^(https://|ssh://|git@)[^\s]+$")
BOM = b"\xef\xbb\xbf"

# plugins__manifest-reference.md, `name`: reserved plugin names
RESERVED_PLUGIN_PREFIXES = ("claude-", "anthropic-", "anthropics-", "cc-plugin-")
RESERVED_PLUGIN_NAMES = {"claude", "anthropic", "anthropics", "claude-code", "claude-mods"}
# plugins__marketplace-reference.md, Reserved names
RESERVED_MARKETPLACE_NAMES = {
    "claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
    "anthropic-marketplace", "anthropic-plugins", "agent-skills", "anthropic-agent-skills",
    "life-sciences", "knowledge-work-plugins", "claude-for-legal",
    "claude-for-financial-services", "financial-services-plugins", "first-party-plugins",
    "claude-tag-plugins", "claude-community", "claude-plugins-community", "healthcare",
    "anthropic-plugin-directory", "claude-plugin-directory",
    "inline", "builtin", "skills-dir", "synced", "claude-plugin-test",
    "npm", "pip", "uv", "cargo", "github", "gh",
}
MARKETPLACE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
# plugins__mods__reference.md, Files
MOD_EXTS = {".js", ".mjs", ".cjs", ".jsx", ".ts", ".mts", ".cts", ".tsx"}
VAR_RE = re.compile(r"\$\{([^}]*)\}")
PATH_VARS = {"CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_DATA", "CLAUDE_PROJECT_DIR"}
UNQUOTED_ROOT_RE = re.compile(r'(?<!")\$\{CLAUDE_PLUGIN_ROOT\}')
VALIDATE_INVENTORY_RE = re.compile(r" (hooks|calls|env reads|env writes|state reads|state writes): ")


def _invisible(s: str) -> bool:
    return any(
        unicodedata.category(ch) in ("Cf", "Co") or ch in "​‌‍⁠﻿"
        for ch in s
    )


def _load_json(path: Path, issues: list, level: str = "E", bom_level: str = "W"):
    """Parse JSON as strict UTF-8. A BOM is reported (never silently accepted),
    then stripped so the remaining checks still run."""
    try:
        raw = path.read_bytes()
    except (FileNotFoundError, IsADirectoryError, NotADirectoryError):
        return None
    if raw.startswith(BOM):
        issues.append((bom_level, f"{path}: starts with a UTF-8 BOM — save as plain UTF-8 "
                                  f"(Claude Code before v2.1.246 failed to install a plugin "
                                  f"whose plugin.json had one)"))
        raw = raw[len(BOM):]
    try:
        return json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        issues.append((level, f"{path}: not UTF-8 — {exc}"))
    except json.JSONDecodeError as exc:
        issues.append((level, f"{path}: invalid JSON — {exc}"))
    return None


def plugin_name_issue(name: str):
    """(level, reason) for a reserved/look-alike plugin name, else None.
    Rule (plugins__manifest-reference.md `name`): case-insensitive, any run of
    separators counts as one."""
    norm = re.sub(r"[-_.\s]+", "-", name.lower()).strip("-")
    words = norm.split("-")
    if norm in RESERVED_PLUGIN_NAMES or norm.startswith(RESERVED_PLUGIN_PREFIXES):
        return "E", "is reserved: it passes as one of Anthropic's own"
    for i, w in enumerate(words):
        if w == "official" and {"claude", "anthropic"} & set(words[max(0, i - 1):i + 2]):
            return "E", "is reserved: 'official' beside claude/anthropic"
    if {"claude", "anthropic", "anthropics"} & set(words):
        return "W", "reads as one of Anthropic's own"
    return None


def _norm_url(url: str):
    """Endpoint identity per mcp.md (dedupe): scheme/host case, default port,
    trailing slash do not make a different endpoint."""
    try:
        p = urlsplit(url.strip())
    except ValueError:
        return url
    scheme = (p.scheme or "").lower()
    host = (p.hostname or "").lower()
    port = p.port if p.port and not ((scheme == "https" and p.port == 443) or
                                     (scheme == "http" and p.port == 80)) else None
    path = p.path.rstrip("/")
    return f"{scheme}://{host}{':' + str(port) if port else ''}{path}{'?' + p.query if p.query else ''}"


def run_validate(target: Path, label: str, issues: list, state: dict):
    """Run `claude plugin validate <target>`; skip gracefully without the binary."""
    exe = shutil.which("claude")
    if not exe:
        if not state.get("warned_no_claude"):
            issues.append(("W", "claude binary not on PATH — `claude plugin validate` skipped; run it before release"))
            state["warned_no_claude"] = True
        return
    try:
        proc = subprocess.run([exe, "plugin", "validate", str(target)],
                              cwd=str(target if target.is_dir() else target.parent),
                              capture_output=True, text=True, timeout=180,
                              stdin=subprocess.DEVNULL)
    except (subprocess.TimeoutExpired, OSError) as exc:
        issues.append(("W", f"{label}: `claude plugin validate` did not finish — {exc}"))
        return
    out = (proc.stdout + proc.stderr).strip()
    # bullet lines are findings; mod inventory lines (hooks:/calls:/env/state) are not
    bullets = [l.strip().lstrip("❯").strip() for l in out.splitlines() if l.strip().startswith("❯")]
    bullets = [b for b in bullets if not VALIDATE_INVENTORY_RE.search(b)]
    detail = " | ".join(bullets)[:600] or " | ".join(l.strip() for l in out.splitlines() if l.strip())[-600:]
    if proc.returncode != 0:
        issues.append(("E", f"{label}: `claude plugin validate` failed — {detail}"))
    elif "with warnings" in out:
        issues.append(("W", f"{label}: `claude plugin validate` warnings — {detail}"))


def _check_name_field(name, where: str, issues: list):
    if not isinstance(name, str) or not name:
        issues.append(("E", f"{where}: name missing or not a string"))
        return
    if re.search(r"[\s@:/\\]", name):
        issues.append(("E", f"{where}: name '{name}' has a space, '@', ':' or path separator"))
    res = plugin_name_issue(name)
    if res:
        issues.append((res[0], f"{where}: plugin name '{name}' {res[1]}"))


def check_repo(root: Path, validate: bool = True):
    issues: list = []  # (level, message)
    state: dict = {}

    mk_path = root / ".claude-plugin" / "marketplace.json"
    pj_path = root / ".claude-plugin" / "plugin.json"
    if not mk_path.exists():
        if pj_path.exists():
            # single-plugin mode (root-as-plugin repo, --plugin-dir mod)
            if not (root / "LICENSE").exists() and not (root / "LICENSE.txt").exists():
                issues.append(("E", "repo root: LICENSE file missing"))
            if validate:
                run_validate(root, root.name, issues, state)
            pj = _load_json(pj_path, [], "E")
            name = pj.get("name", root.name) if isinstance(pj, dict) else root.name
            urls: dict = {}
            issues.extend(check_plugin_dir(root, name, {}, urls))
            _report_url_dupes(urls, issues)
            return issues
        issues.append(("E", f"{mk_path} missing — not a marketplace repo or plugin dir?"))
        return issues

    mk = _load_json(mk_path, issues, bom_level="E")
    if mk is None:
        return issues

    if validate:
        run_validate(root, "marketplace", issues, state)

    if "$schema" not in mk:
        issues.append(("E", "marketplace.json: missing $schema"))
    if not (root / "LICENSE").exists() and not (root / "LICENSE.txt").exists():
        issues.append(("E", "repo root: LICENSE file missing"))

    mk_name = mk.get("name", "")
    if isinstance(mk_name, str) and mk_name:
        if not MARKETPLACE_NAME_RE.match(mk_name) or ".." in mk_name:
            issues.append(("E", f"marketplace name '{mk_name}': only letters, digits, '.', '_', '-', "
                                f"starting alphanumeric, no '..'"))
        low = mk_name.lower()
        canon = re.sub(r"[^a-z0-9_]+", "-", low).strip("-")
        if low in RESERVED_MARKETPLACE_NAMES or canon in RESERVED_MARKETPLACE_NAMES or low.startswith("claudeai-"):
            issues.append(("E", f"marketplace name '{mk_name}' is reserved"))

    entries = mk.get("plugins", [])
    names = [e.get("name", "") for e in entries]
    if names != sorted(names):
        issues.append(("E", "marketplace.json: plugins[] not sorted by name (I1)"))
    dupes = {n for n in names if names.count(n) > 1}
    if dupes:
        issues.append(("E", f"marketplace.json: duplicate plugin names {sorted(dupes)} (I2)"))

    urls: dict = {}  # normalized url -> list of "plugin:server"
    for entry in entries:
        name = entry.get("name", "<unnamed>")
        if not NAME_RE.match(name):
            issues.append(("E", f"{name}: name fails ^[a-z0-9][a-z0-9-]{{1,63}}$ (I11)"))
        if not isinstance(entry.get("source"), str):  # local sources: plugin.json name is checked below
            res = plugin_name_issue(name)
            if res:
                issues.append((res[0], f"{name}: marketplace entry name {res[1]}"))
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
        if src_type == "github":
            if not GITHUB_REPO_RE.match(str(source.get("repo", ""))):
                issues.append(("E", f"{name}: github source repo must be 'owner/repo' (I4)"))
        elif src_type in ("url", "git-subdir"):
            url = str(source.get("url", ""))
            ok = GIT_URL_RE.match(url) or (src_type == "git-subdir" and GITHUB_REPO_RE.match(url))
            if not ok:
                issues.append(("E", f"{name}: {src_type} source url must be https://, ssh:// or git@ (I4)"))
        elif src_type == "archive":
            if not str(source.get("url", "")).startswith("https://"):
                issues.append(("E", f"{name}: archive source url must be https:// (I4)"))
        if isinstance(source, dict):
            for v in source.values():
                if isinstance(v, str) and SHELL_META.search(v):
                    issues.append(("E", f"{name}: shell metacharacters in source field (I9)"))

        # locate local plugin dir for relative-path sources
        if isinstance(source, str):
            pdir = (root / source).resolve()
            if pdir.exists():
                if validate:
                    # a marketplace run never opens plugin files; validate each plugin too.
                    # Root-as-plugin: the directory resolves to the marketplace, so name the manifest file.
                    target = pdir if pdir != root.resolve() else pdir / ".claude-plugin" / "plugin.json"
                    if target.exists():
                        run_validate(target, name, issues, state)
                issues.extend(check_plugin_dir(pdir, name, entry, urls))
            else:
                issues.append(("E", f"{name}: source path {source} does not exist"))

    _report_url_dupes(urls, issues)
    return issues


def _report_url_dupes(urls: dict, issues: list):
    for url, owners in sorted(urls.items()):
        if len(owners) > 1:
            issues.append(("E", f"MCP url {url} is declared by {', '.join(owners)} — Claude Code dedupes "
                                f"plugin servers by endpoint, so all but one silently disappear with their "
                                f"tool names (plugin-vs-plugin case observed 2026-10-02, not documented)"))


def _iter_mcp_servers(pdir: Path, pj: dict, issues: list, label: str):
    """Yield (server_name, config) from .mcp.json and plugin.json mcpServers."""
    def from_map(data):
        if not isinstance(data, dict):
            return []
        m = data.get("mcpServers", data)
        return [(k, v) for k, v in m.items() if isinstance(v, dict)] if isinstance(m, dict) else []

    out = from_map(_load_json(pdir / ".mcp.json", issues))
    decl = pj.get("mcpServers")
    for item in (decl if isinstance(decl, list) else [decl] if decl is not None else []):
        if isinstance(item, dict):
            out.extend(from_map({"mcpServers": item}))
        elif isinstance(item, str):
            low = item.lower()
            if low.endswith((".mcpb", ".dxt")):
                continue  # bundle: config lives inside the bundle
            if low.endswith(".json") and not low.startswith("http"):
                out.extend(from_map(_load_json((pdir / item).resolve(), issues)))
            else:
                issues.append(("E", f"{label}: mcpServers entry '{item}' — a bundle must end in .mcpb or .dxt"))
    return out


def _check_mcp(pdir: Path, pj: dict, label: str, urls, issues: list):
    uc = pj.get("userConfig") if isinstance(pj.get("userConfig"), dict) else {}
    for server, cfg in _iter_mcp_servers(pdir, pj, issues, label):
        where = f"{label}: MCP server '{server}'"
        hh = cfg.get("headersHelper")
        if isinstance(hh, str) and "${user_config." in hh:
            issues.append(("E", f"{where}: headersHelper references ${{user_config.*}} — the server is "
                                f"reported misconfigured; put it in headers or read a file in the helper"))
        fields = {k: cfg.get(k) for k in ("command", "args", "env", "url", "headers")}
        blob = json.dumps(fields)
        for var in sorted(set(VAR_RE.findall(blob))):
            if var.startswith("user_config."):
                key = var.split(".", 1)[1]
                if key not in uc:
                    issues.append(("E", f"{where}: ${{user_config.{key}}} is not declared in userConfig"))
                continue
            if var in PATH_VARS or ":-" in var:
                continue
            issues.append(("W", f"{where}: ${{{var}}} has no :-default — unset, Claude Code warns and uses the "
                                f"literal text; for a plugin server a probe (2026-10-02) saw '✘ Failed to connect — "
                                f"Missing environment variables'"))
        url = cfg.get("url")
        if isinstance(url, str):
            for key in VAR_RE.findall(url):
                if not key.startswith("user_config."):
                    continue
                opt = uc.get(key.split(".", 1)[1])
                if isinstance(opt, dict) and not opt.get("required") and not opt.get("default"):
                    issues.append(("W", f"{where}: url uses ${{{key}}} with no non-empty default and no "
                                        f"required:true — unset, /mcp shows 'URL is unset or invalid'"))
            if urls is not None and "${" not in url:
                urls.setdefault(_norm_url(url), []).append(f"{label}:{server}")
            elif urls is not None:
                # resolve user_config defaults so two plugins defaulting to one daemon are caught
                def sub(m):
                    v = m.group(1)
                    if v.startswith("user_config."):
                        opt = uc.get(v.split(".", 1)[1])
                        return str(opt.get("default", "")) if isinstance(opt, dict) else ""
                    if ":-" in v:
                        return v.split(":-", 1)[1]
                    return ""
                resolved = VAR_RE.sub(sub, url)
                if "://" in resolved and urlsplit(resolved).hostname:
                    urls.setdefault(_norm_url(resolved), []).append(f"{label}:{server}")


def _check_user_config(pj: dict, label: str, issues: list):
    uc = pj.get("userConfig")
    if not isinstance(uc, dict):
        return
    for key, opt in uc.items():
        if not isinstance(opt, dict) or "options" not in opt:
            continue
        where = f"{label}: userConfig.{key}.options"
        issues.append(("W", f"{where} — recipients on Claude Code < 2.1.271 can't load the plugin"))
        opts = opt.get("options")
        if opt.get("type") != "string" or opt.get("multiple") or opt.get("sensitive"):
            issues.append(("E", f"{where}: only for a string field that isn't multiple or sensitive"))
        if not isinstance(opts, list) or not all(isinstance(o, str) and 1 <= len(o) <= 64 for o in opts):
            issues.append(("E", f"{where}: each option must be a 1-64 character string"))
        elif not opt.get("required") and opt.get("default") not in opts:
            issues.append(("E", f"{where}: set default to one of the options, or required: true"))


def _check_hook_quoting(hooks_obj, label: str, issues: list):
    if not isinstance(hooks_obj, dict):
        return
    for groups in hooks_obj.values():
        for group in groups if isinstance(groups, list) else []:
            for h in (group.get("hooks", []) if isinstance(group, dict) else []):
                if not isinstance(h, dict) or h.get("type", "command") != "command":
                    continue
                if "args" in h or h.get("shell") == "powershell":
                    continue  # exec form: no shell, no quoting needed
                if UNQUOTED_ROOT_RE.search(str(h.get("command", ""))):
                    issues.append(("W", f"{label}: ${{CLAUDE_PLUGIN_ROOT}} unquoted in a shell-form hook "
                                        f"command — breaks on paths with spaces (or use exec form with args)"))
                    return


def check_plugin_dir(pdir: Path, mk_name: str, mk_entry: dict, urls=None):
    issues: list = []
    pj_path = pdir / ".claude-plugin" / "plugin.json"
    pj = _load_json(pj_path, issues, bom_level="E")
    if pj is None:
        if not pj_path.exists():
            issues.append(("W", f"{mk_name}: no plugin.json (name falls back to install dir — set one)"))
        return issues

    _check_name_field(pj.get("name"), f"{mk_name}: plugin.json", issues)
    if mk_entry and isinstance(pj.get("name"), str) and mk_entry.get("name") != pj.get("name"):
        issues.append(("W", f"{mk_name}: marketplace entry name differs from plugin.json name "
                            f"'{pj.get('name')}' — enabledPlugins uses the entry name, components are "
                            f"namespaced under the manifest name"))

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

    _load_json(pdir / ".lsp.json", issues)  # parse errors recorded as E
    _check_mcp(pdir, pj, mk_name, urls, issues)
    _check_user_config(pj, mk_name, issues)

    types = pj.get("types")
    if types is not None:
        if not (isinstance(types, str) and types.startswith("./") and types.endswith(".d.ts")
                and (pdir / types).is_file()):
            issues.append(("E", f"{mk_name}: plugin.json types must be a ./-relative existing .d.ts file"))

    hooks_path = pdir / "hooks" / "hooks.json"
    hooks = _load_json(hooks_path, issues)
    if isinstance(hooks, dict):
        if "hooks" not in hooks and "modules" not in hooks:
            issues.append(("E", f"{mk_name}: hooks/hooks.json has neither the outer {{\"hooks\":...}} "
                                f"wrapper nor a mod's \"modules\" — hooks will silently never register"))
        if "modules" in hooks:
            mods = hooks["modules"]
            if not isinstance(mods, list) or not mods:
                issues.append(("E", f"{mk_name}: hooks.json modules must be an array with one path"))
            else:
                if len(mods) > 1:
                    issues.append(("W", f"{mk_name}: hooks.json modules lists {len(mods)} paths; "
                                        f"the docs describe an array with one path"))
                for m in mods:
                    mpath = (hooks_path.parent / str(m)).resolve() if isinstance(m, str) else None
                    if mpath is None or not mpath.is_file():
                        issues.append(("E", f"{mk_name}: mod module {m!r} not found relative to hooks/"))
                    elif mpath.suffix not in MOD_EXTS:
                        issues.append(("E", f"{mk_name}: mod module {m} must be one of {sorted(MOD_EXTS)}"))
                    elif pdir.resolve() not in mpath.parents:
                        issues.append(("E", f"{mk_name}: mod module {m} escapes the plugin directory"))
        _check_hook_quoting(hooks.get("hooks"), mk_name, issues)
    elif hooks is not None:
        issues.append(("E", f"{mk_name}: hooks/hooks.json must be a JSON object"))

    monitors = _load_json(pdir / "monitors" / "monitors.json", issues)
    for mon in monitors if isinstance(monitors, list) else []:
        if isinstance(mon, dict) and UNQUOTED_ROOT_RE.search(str(mon.get("command", ""))):
            issues.append(("W", f"{mk_name}: ${{CLAUDE_PLUGIN_ROOT}} unquoted in monitor "
                                f"'{mon.get('name')}' command — breaks on paths with spaces"))
    return issues


def self_test() -> int:
    import tempfile
    ok = True

    def expect(issues, needle, level=None):
        nonlocal ok
        if not any(needle in m and (level is None or lvl == level) for lvl, m in issues):
            print(f"self-test FAIL: expected {level or ''} finding containing '{needle}'")
            ok = False

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / ".claude-plugin").mkdir()
        (root / "LICENSE").write_text("MIT")
        pdir = root / "plugins" / "aaa"
        (pdir / ".claude-plugin").mkdir(parents=True)
        (pdir / ".claude-plugin" / "plugin.json").write_text(json.dumps(
            {"$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
             "name": "aaa", "version": "1.0.0", "license": "MIT"}))
        (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(
            {"$schema": "https://json.schemastore.org/claude-code-plugin-marketplace.json",
             "name": "test-mk", "owner": {"name": "t"},
             "plugins": [{"name": "aaa", "description": "A valid test plugin.",
                          "source": "./plugins/aaa"}]}))
        issues = check_repo(root, validate=False)
        errors = [i for i in issues if i[0] == "E"]
        if errors:
            print("self-test FAIL: clean fixture produced errors:", errors)
            ok = False

        # mod: modules only -> clean; missing module -> E
        (pdir / "hooks").mkdir()
        (pdir / "hooks" / "hooks.json").write_text(json.dumps({"modules": ["./register.js"]}))
        (pdir / "hooks" / "register.js").write_text("export function register(on) {}\n")
        if [i for i in check_repo(root, validate=False) if i[0] == "E"]:
            print("self-test FAIL: mod fixture produced errors")
            ok = False
        (pdir / "hooks" / "register.js").unlink()
        expect(check_repo(root, validate=False), "not found relative to hooks/", "E")
        (pdir / "hooks" / "hooks.json").write_text(json.dumps({"PreToolUse": []}))
        expect(check_repo(root, validate=False), "neither the outer", "E")
        (pdir / "hooks" / "hooks.json").unlink()

        # bad fixture: dup version, missing sha, bad name
        mk = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
        mk["plugins"].append({"name": "ZZ bad", "description": "short",
                              "version": "2.0.0",
                              "source": {"source": "github", "repo": "x/y"}})
        (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(mk))
        msgs = check_repo(root, validate=False)
        for needle in ("not sorted", "fails ^", "40-hex sha", "outside 10-2000"):
            expect(msgs, needle)
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
    issues = check_repo(root, validate="--no-validate" not in args)
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
