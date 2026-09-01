# Pitfalls — field-tested traps in plugin authoring and distribution

> Last audited against Claude Code docs: 2026-09-01 (~v2.1.251, mirror b290425)

Battle-tested lessons from operating 10+ marketplaces (beCyborg, 2026-07..09). Each entry: symptom → cause → rule.

## 1. Marketplace clone is NOT a working tree (autoUpdate wipe)

The background marketplace refresh hard-resets `~/.claude/plugins/marketplaces/<name>/` to origin without warning. It wipes uncommitted edits mid-session AND deletes local branches (observed 2026-09-01: a freshly created branch vanished within the hour). Any `claude` start can trigger the refresh — including headless `claude -p` runs (verifiers, cron, subagent bridges).

**Rule:** all editing happens in a separate dev clone (convention: `~/<repo-name>`). Push the working branch immediately after creating it. Touch the marketplace clone only via `claude plugin update` after the release is pushed. Never run `/plugin` operations while unpushed work exists anywhere.

## 2. `metadata.pluginRoot` — version-gated

Before v2.1.239 the runtime did not prepend `pluginRoot` to bare source names (`Source path does not exist`) even though docs promised it; the workaround was full `"./plugins/<name>"` paths. Fixed in v2.1.239 (changelog): bare names now resolve under `pluginRoot`. Caveats that remain: a bare name containing `/` is not treated as a pluginRoot bareword, and org-synced distribution rejects barewords entirely (plugin-marketplaces.md §Organization settings). Full relative paths (`"./plugins/<name>"`) work everywhere — prefer them when the repo must serve pre-2.1.239 clients.

## 3. `--strict` vs commit-SHA versioning

Omitting `version` is the only way to get per-commit updates (version becomes the git SHA), but `--strict` promotes the `No version specified` warning to an error. Pick one per repo: explicit semver + `--strict` in CI (the standard for published plugins — see repo-standard.md), or SHA-mode + plain `validate` with the expected warning documented. `claude plugin tag` requires explicit version (tag = `{name}--v{version}`).

## 4. MCP tool names change inside a plugin

A skill moved from `~/.claude/skills/` into a plugin sees its MCP tool names rewritten: `mcp__brave-search__brave_web_search` → `mcp__plugin_<plugin>_<server>__<tool>`. Fix EVERY occurrence, not just `allowed-tools`: skill bodies, protocol/reference files the agent reads and calls literally, `--allowedTools` of nested `claude -p` calls, hook matchers in hooks.json, workflow prompts. A real migration hit 55 occurrences across 19 files. Missed-spot symptom: nested run returns `is_error: true`, `stop_reason: "tool_use"`, empty `permission_denials` — it "called" a tool that doesn't exist.

## 5. `${CLAUDE_PLUGIN_ROOT}` substitutes only where documented

It substitutes in SKILL.md / agent bodies and the documented config fields — NOT inside `references/`/`protocols/` files read via the Read tool. There, use your own placeholder (e.g. `{PLUGIN_ROOT}`) and have the prompt pass the value as a string. In bash scripts resolve the root from `$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)`. `${user_config.KEY}` (non-sensitive) substitutes in skill text only when the plugin is installed with the value set — under `--plugin-dir` it stays a literal.

## 6. `installLocation` is pinned to the config dir

With two profiles sharing `~/.claude/plugins` via symlink, marketplaces added from one `CLAUDE_CONFIG_DIR` report "corrupted installLocation" in the other. Do NOT follow the CLI's `remove` + `re-add` advice — it flips the breakage to the other profile (the file is shared). Update the clone directly (`git pull --ff-only`) and reinstall the plugin; the error is cosmetic (only auto-refresh dies).

## 7. Plugin skills are cached per session

The harness resolves a skill's path once, at session start. Reinstalling a plugin mid-session keeps serving the OLD version to that session — edits look broken (or falsely verified). Verify plugin-skill changes from a fresh process: `cd /tmp && claude -p "<prompt>" < /dev/null` — it reloads plugins and shows substituted `${user_config.*}` / `${CLAUDE_PLUGIN_ROOT}` values.

## 8. HTTPS distribution: skip `CLAUDE_CODE_PLUGIN_PREFER_HTTPS` when you give a full URL

The env var only affects `owner/repo` shorthands (which default to SSH). A full `https://github.com/.../repo.git` resolves as `"source": "git"` over HTTPS without it — so recipient instructions can be a plain slash command (`/plugin marketplace add https://…`), no terminal needed. Declarative equivalent: `extraKnownMarketplaces` with `source: "git"` + `url` (HTTPS) vs `source: "github"` + `repo` (SSH).

## 9. Auto-update is opt-in for recipients

Third-party and local marketplaces have auto-update disabled by default (discover-plugins.md). "Every push reaches users automatically" is false: recipients either run `/plugin update <plugin>@<marketplace>` or enable auto-update once in `/plugin` → Marketplaces. Put this in every marketplace README. Also: bumping `version` is what makes an update visible at all (version = cache key; see release-checklist.md).

## 10. hooks.json needs the outer wrapper

`hooks/hooks.json` must be `{"hooks": {...}}` — without the wrapper the hooks silently never register. Quote `"${CLAUDE_PLUGIN_ROOT}"` in shell-form commands (breaks on spaces otherwise); prefer exec-form with `args`. A hook matching the plugin's own MCP server must use the scoped name (`mcp__plugin_<plugin>_<server>__<tool>`) — a bare server name never fires (plugins-reference.md §Hooks).
