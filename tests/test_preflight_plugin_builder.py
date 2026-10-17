"""Regression tests for skills/plugin-builder/scripts/preflight_plugin.py.

Run: uv run --with pytest --with pyyaml pytest tests/ -q
Never spawns the `claude` CLI (validate=False everywhere).
"""
import importlib.util
import json
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "plugin-builder" / "scripts" / "preflight_plugin.py"
_spec = importlib.util.spec_from_file_location("preflight_plugin_builder_under_test", SCRIPT)
pf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pf)

MANIFEST_SCHEMA = "https://json.schemastore.org/claude-code-plugin-manifest.json"
MARKET_SCHEMA = "https://json.schemastore.org/claude-code-plugin-marketplace.json"


def make_marketplace(root: Path, entry_name="tally-mod", plugin_name=None, plugin_extra=None):
    """Marketplace with one plugin under plugins/<entry_name>; returns the plugin dir."""
    (root / ".claude-plugin").mkdir(parents=True)
    (root / "LICENSE").write_text("MIT")
    pdir = root / "plugins" / entry_name
    (pdir / ".claude-plugin").mkdir(parents=True)
    manifest = {"$schema": MANIFEST_SCHEMA, "name": plugin_name or entry_name,
                "version": "1.0.0", "license": "MIT", "description": "Counts tool calls",
                "author": {"name": "t"}}
    manifest.update(plugin_extra or {})
    (pdir / ".claude-plugin" / "plugin.json").write_text(json.dumps(manifest))
    (root / ".claude-plugin" / "marketplace.json").write_text(json.dumps(
        {"$schema": MARKET_SCHEMA, "name": "fx-mk", "owner": {"name": "t"},
         "plugins": [{"name": entry_name, "description": "A test mod plugin.",
                      "source": f"./plugins/{entry_name}"}]}))
    return pdir


def errors(issues):
    return [m for lvl, m in issues if lvl == "E"]


def test_mod_plugin_passes(tmp_path):
    pdir = make_marketplace(tmp_path)
    (pdir / "hooks").mkdir()
    (pdir / "hooks" / "hooks.json").write_text(json.dumps({"modules": ["./register.js"]}))
    (pdir / "hooks" / "register.js").write_text(
        "export function register(on) { on('tool.call', async ($, e, next) => next(e)) }\n")
    assert errors(pf.check_repo(tmp_path, validate=False)) == []


def test_mod_with_missing_module_errors(tmp_path):
    pdir = make_marketplace(tmp_path)
    (pdir / "hooks").mkdir()
    (pdir / "hooks" / "hooks.json").write_text(json.dumps({"modules": ["./register.ts"]}))
    errs = errors(pf.check_repo(tmp_path, validate=False))
    assert any("not found relative to hooks/" in e for e in errs)


def test_classic_hooks_without_wrapper_still_errors(tmp_path):
    pdir = make_marketplace(tmp_path, entry_name="classic")
    (pdir / "hooks").mkdir()
    (pdir / "hooks" / "hooks.json").write_text(json.dumps(
        {"PostToolUse": [{"hooks": [{"type": "command", "command": "true"}]}]}))
    errs = errors(pf.check_repo(tmp_path, validate=False))
    assert any("neither the outer" in e for e in errs)


def test_exec_form_args_not_flagged_shell_form_is(tmp_path):
    pdir = make_marketplace(tmp_path, entry_name="hooky")
    (pdir / "hooks").mkdir()
    exec_form = {"type": "command", "command": "node", "args": ["${CLAUDE_PLUGIN_ROOT}/x.js"]}
    (pdir / "hooks" / "hooks.json").write_text(json.dumps(
        {"hooks": {"Stop": [{"hooks": [exec_form]}]}}))
    assert not any("unquoted" in m for _, m in pf.check_repo(tmp_path, validate=False))
    shell_form = {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/x.sh"}
    (pdir / "hooks" / "hooks.json").write_text(json.dumps(
        {"hooks": {"Stop": [{"hooks": [shell_form]}]}}))
    assert any("unquoted" in m for lvl, m in pf.check_repo(tmp_path, validate=False) if lvl == "W")


def test_bom_detected(tmp_path):
    pdir = make_marketplace(tmp_path)
    pj = pdir / ".claude-plugin" / "plugin.json"
    pj.write_bytes(b"\xef\xbb\xbf" + pj.read_bytes())
    errs = errors(pf.check_repo(tmp_path, validate=False))
    assert any("BOM" in e for e in errs)
    # the manifest is still parsed after the BOM, so no spurious parse errors
    assert not any("invalid JSON" in e for e in errs)


def test_cc_plugin_name_rejected(tmp_path):
    make_marketplace(tmp_path, entry_name="tally-mod", plugin_name="cc-plugin-x")
    issues = pf.check_repo(tmp_path, validate=False)
    assert any("cc-plugin-x" in e and "reserved" in e for e in errors(issues))
    assert any("differs from plugin.json name" in m for lvl, m in issues if lvl == "W")


def test_reserved_name_rules():
    assert pf.plugin_name_issue("cc-plugin-x")[0] == "E"
    assert pf.plugin_name_issue("Claude_Code")[0] == "E"
    assert pf.plugin_name_issue("official-claude-tools")[0] == "E"
    assert pf.plugin_name_issue("mcp-for-claude")[0] == "W"
    assert pf.plugin_name_issue("jadlis-search") is None


def test_plugin_dir_mode(tmp_path):
    (tmp_path / ".claude-plugin").mkdir()
    (tmp_path / "LICENSE").write_text("MIT")
    (tmp_path / ".claude-plugin" / "plugin.json").write_text(json.dumps(
        {"$schema": MANIFEST_SCHEMA, "name": "solo", "version": "1.0.0", "license": "MIT"}))
    assert errors(pf.check_repo(tmp_path, validate=False)) == []


def test_mcp_checks(tmp_path):
    uc = {"svc_url": {"type": "string", "title": "t", "description": "d"},
          "mode": {"type": "string", "title": "t", "description": "d",
                   "options": ["a", "b"], "default": "a"}}
    pdir = make_marketplace(tmp_path, entry_name="mcpy", plugin_extra={"userConfig": uc})
    (pdir / ".mcp.json").write_text(json.dumps({"mcpServers": {
        "remote": {"type": "http", "url": "${user_config.svc_url}",
                   "headersHelper": "/bin/echo ${user_config.svc_url}"},
        "local": {"command": "npx", "args": ["x"], "env": {"K": "${SOME_KEY}"}},
        "twin-a": {"type": "http", "url": "http://127.0.0.1:8733/mcp"},
        "twin-b": {"type": "http", "url": "HTTP://127.0.0.1:8733/mcp/"},
    }}))
    issues = pf.check_repo(tmp_path, validate=False)
    msgs = [m for _, m in issues]
    assert any("headersHelper" in e for e in errors(issues))
    assert any("no non-empty default" in m for m in msgs)
    assert any("${SOME_KEY} has no :-default" in m for m in msgs)
    assert any("2.1.271" in m for m in msgs)
    assert any("twin-a" in e and "twin-b" in e for e in errors(issues))
