# Pitfalls — field-tested traps in plugin authoring and distribution

> Last audited against Claude Code docs: 2026-10-17 (v2.1.302, mirror da8a6ce9)

Battle-tested lessons from operating 10+ marketplaces (beCyborg, 2026-07..09). Each entry: symptom → cause → rule.

## 1. Marketplace clone is NOT a working tree (autoUpdate wipe)

The background marketplace refresh hard-resets `~/.claude/plugins/marketplaces/<name>/` to origin without warning. It wipes uncommitted edits mid-session AND deletes local branches (observed 2026-09-01: a freshly created branch vanished within the hour). Any `claude` start can trigger the refresh — including headless `claude -p` runs (verifiers, cron, subagent bridges).

**Rule:** all editing happens in a separate dev clone (convention: `~/<repo-name>`). Push the working branch immediately after creating it. Touch the marketplace clone only via `claude plugin update` after the release is pushed. Never run `/plugin` operations while unpushed work exists anywhere.

## 2. `metadata.pluginRoot` — version-gated

Before v2.1.239 the runtime did not prepend `pluginRoot` to bare source names (`Source path does not exist`) even though docs promised it; the workaround was full `"./plugins/<name>"` paths. Fixed in v2.1.239 (changelog): bare names now resolve under `pluginRoot`. Caveats that remain: a bare name containing `/` is not treated as a pluginRoot bareword, and org-synced distribution rejects barewords entirely (`plugins__host-marketplace.md §Distribute through organization settings`). Full relative paths (`"./plugins/<name>"`) work everywhere — prefer them when the repo must serve pre-2.1.239 clients.

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

Third-party and local marketplaces have auto-update disabled by default (`plugins__install.md §Keep plugins updated`). "Every push reaches users automatically" is false: recipients either run `/plugin update <plugin>@<marketplace>` or enable auto-update once in `/plugin` → Marketplaces. Put this in every marketplace README. Also: bumping `version` is what makes an update visible at all (version = cache key; see release-checklist.md).

## 10. hooks.json needs the outer wrapper — unless it is a mod

Classic hooks in `hooks/hooks.json` must be `{"hooks": {...}}` — without the wrapper the hooks silently never register. A mod's `hooks.json` is `{"modules": ["./register.js"]}` (optionally plus `hooks`) and needs no wrapper; preflight before 2.1.0 wrongly failed it. Quote `"${CLAUDE_PLUGIN_ROOT}"` in shell-form commands (breaks on spaces otherwise); prefer exec-form with `args`. A hook matching the plugin's own MCP server must use the scoped name (`mcp__plugin_<plugin>_<server>__<tool>`) — a bare server name never fires (`plugins__components.md §MCP servers`).

## 11. Official CI action: false I8 warning on root-as-plugin repos

The `validate-plugins` action's invariant I8 warns `vendored source './' has no .claude-plugin/plugin.json` on repos whose marketplace entry uses `source: "./"` — it resolves the manifest relative to the source dir with a nested-layout assumption and does not recognize the root-as-plugin pattern (reproduced on two repos, 2026-09-01; CI still passes). Ignore the warning, or move to `plugins/<name>/` layout. Also expected on a workflow's first run: `git diff failed … treating ALL entries as changed` (no base commit — the action validates everything, which is stricter, not weaker).

## 12. Mods: fail-open, unsandboxed, version-gated

A mod (`mods.md`) runs inside Claude Code with the user's rights: no sandbox, never install one unread. A hook that throws or times out before `next` is skipped and the event proceeds — a guard needs a `.catch` that returns the event's refusal (`{ deny }`, `{ drop }`) when `next.called` is false, or it fails open (`plugins__mods__events.md §Handle a hook that fails`). Since v2.1.301 that `.catch` runs **only when the hook itself throws or times out**: events raised beneath the guard's own `$` calls skip the guard without asking its `.catch` (changelog 2.1.301), so a guard never checks what its own calls cause. `claude plugin validate` lists each gating hook without a `.catch` (v2.1.290+). Mods need Claude Code ≥ 2.1.287 (terminal); new props such as `Text` `weight` need 2.1.299+ or the tree doesn't draw (`mods.md §8`). From the owner's 2.1.287 probes: the worktree breakage (#92533) is fixed in 2.1.288; `skill.prompt` delivery (anthropics/claude-code#96831) has no fix entry — re-probe. A mod shipped from a GitHub/git/URL/npm marketplace counts as the user's, never as the organization's (`plugins__mods__admin.md`).

## 13. Two plugins on one MCP URL — one silently vanishes

Plugin MCP servers are deduplicated by endpoint, not name (`mcp.md §Scope hierarchy and precedence`): a plugin server with the same URL or command as an enabled user/project/local server is not connected, and its tool names disappear with it. Observed on 2026-10-02 (not documented): the same happens between two plugins — which one survives was not established. Give every shared daemon one owner key; preflight errors on a URL repeated inside one marketplace. Patterns: `mcp-patterns.md`.

## 14. MCP names in agent `tools:` and allow rules match one server only (v2.1.299)

Since v2.1.299 an MCP allow rule or an agent `tools:` entry reaches **only the server whose whole normalized name it spells**: `mcp__a` no longer allows a server named `a__b` or `a_` (changelog 2.1.299). An agent or allow-list that worked on 2.1.298 because a short entry happened to cover a second server loses that server's tools after the upgrade — symptom: the subagent reports the tool missing, or fails to launch when no `tools:` entry resolves (`sub-agents.md §Available tools`). Deny and ask rules got the same whole-name matching for servers with `__` in their name (changelog 2.1.299).

**Rule:** list every server by its full name — `mcp__<server>__*` (or `mcp__<server>`) for the whole server, `mcp__<server>__<tool>` for one tool; a server whose name contains `__` only as `mcp__<whole name>__*`. A plugin's own server is `mcp__plugin_<plugin>_<server>__*` (§4). Before a release, check that every `mcp__…` entry in agents and skills' `allowed-tools` spells one whole server name.

## 15. A guard hook that "works" but lets calls through — or blocks everything

Three hook changes turn an old guard into a silent leak or a hard block (`components.md §3`):

- **Background child.** A command hook that forks a helper and exits loses any decision the helper prints later. A hook that prints an allow and then starts a child with stdout/stderr still attached gets the call **blocked** (`refusing to honor the suspect capture`, `hooks.md §Hooks that start a background process`; since v2.1.285 a sync hook ends shortly after its own process exits, changelog 2.1.285 — the refusal's first version is not stated). Rule: decision first, `|| exit $?`, child with `>/dev/null 2>&1 &`.
- **`updatedInput` rewrites** are validated since v2.1.300: unknown keys are dropped, input the tool rejects denies the call (changelog 2.1.300). A misspelled key used to reach the tool; now it is dropped silently, and an object the tool rejects fails the call. Return the full, valid argument object.
- **Many LLM hooks on one event** queue: at most 12 `prompt`/`agent` hooks of one event run at a time (changelog 2.1.302). Expect latency, not errors.

**Rule:** after a CLI upgrade, smoke-test every guard once with a deliberately failing check and once with a passing one, and read the hook error text.
