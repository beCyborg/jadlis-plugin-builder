# Plugin Components Reference

> Last audited against Claude Code docs: 2026-09-01 (~v2.1.251, mirror b290425)

Every component type a plugin can ship, the constraints that break plugins in practice, and how files are resolved on disk. Manifest fields and path variables: see `manifest-reference.md`.

---

## 1. Skills

**Location:** `skills/` or `commands/` in the plugin root, or a single `SKILL.md` at the plugin root (`plugins-reference.md §Skills`).

- Skills are **directories containing `SKILL.md`**; commands are **flat `.md` files**. Both are discovered automatically on install. Use `skills/` for new plugins.
- **Root `SKILL.md` loads only when all three hold:** no `skills/` directory, no `skills` manifest field, and the file is at the plugin root. Nothing else needs declaring.
- Set frontmatter `name` on a root `SKILL.md`. Without it the fallback is the **install directory name**, which for a marketplace install is a version string that changes on every update — so `name` is effectively mandatory there.
- **Boolean frontmatter literals (v2.1.218+):** `disable-model-invocation` and friends accept `yes`, `no`, `on`, `off`, `1`, `0` in any letter case, plus `true`/`false`. Before v2.1.218 only `true`/`false` parsed.
- Plugin skills are namespaced `plugin-name:skill-name`.

## 2. Agents

**Location:** `agents/` in the plugin root. Markdown with YAML frontmatter.

| Supported frontmatter | Notes |
|---|---|
| `name`, `description` | Namespaced as `my-plugin:code-reviewer` in the @-mention typeahead |
| `model`, `effort`, `maxTurns` | |
| `tools`, `disallowedTools` | |
| `skills`, `memory`, `background` | |
| `isolation` | **Only** valid value is `"worktree"` |

**Not supported for plugin-shipped agents, for security reasons: `hooks`, `mcpServers`, `permissionMode`** (`plugins-reference.md §Agents`). Declaring them does not silently work — do not ship an agent that depends on them.

**Graceful degradation (plugin agents only).** Claude Code loads a plugin agent even when the frontmatter is broken:

| Condition | Result |
|---|---|
| No `name` | Named after the file: `agents/reviewer.md` in `my-plugin` → `my-plugin:reviewer` |
| Frontmatter doesn't parse | Named after the file, description becomes `Agent from my-plugin plugin`, **every field in the file is ignored** |

Project, user, and managed agents are *skipped* in both cases. So a plugin agent with a typo'd frontmatter loads silently with none of its settings applied — find these with `claude plugin validate ./my-plugin` (with a manifest) or `claude plugin validate ./my-plugin/agents` (no manifest, v2.1.233+).

## 3. Hooks

**Location:** `hooks/hooks.json` in the plugin root, or inline in `plugin.json`.

The file needs the **outer `{"hooks": …}` wrapper** — the config is not a bare event map:

```json
{
  "hooks": {
    "PostToolUse": [
      { "matcher": "Write|Edit",
        "hooks": [{ "type": "command", "command": "\"${CLAUDE_PLUGIN_ROOT}\"/scripts/format-code.sh" }] }
    ]
  }
}
```

**Events (33).** Plugin hooks respond to the same lifecycle events as user hooks (`plugins-reference.md §Hooks`):

| Group | Events |
|---|---|
| Session | `SessionStart`, `Setup`, `SessionEnd`, `InstructionsLoaded`, `ConfigChange` |
| Prompt | `UserPromptSubmit`, `UserPromptExpansion`, `MessageDisplay` |
| Tools | `PreToolUse`, `PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`, `PostToolBatch` |
| Agents / tasks | `SubagentStart`, `SubagentStop`, `TaskCreated`, `TaskCompleted`, `TeammateIdle` |
| Turn | `Stop`, `StopFailure`, `Notification` |
| Environment | `CwdChanged`, `DirectoryAdded`, `FileChanged`, `WorktreeCreate`, `WorktreeRemove` |
| Context | `PreCompact`, `PostCompact` |
| Model | `PreModelSwitch`, `PostModelSwitch` |
| MCP | `Elicitation`, `ElicitationResult` |

`FileChanged` uses `matcher` for filenames to watch. `Setup` fires only under `--init-only`, or `--init`/`--maintenance` in `-p` mode.

**Hook types (5):** `command` (shell), `http` (POSTs the event JSON), `mcp_tool` (calls a tool on a configured MCP server), `prompt` (LLM evaluation, `$ARGUMENTS` placeholder), `agent` (agentic verifier with tools).

**Targeting the plugin's own MCP server requires scoped names** (`plugins-reference.md §Hooks`) — the single most common silent failure:

| Field | Value |
|---|---|
| Tool `matcher` / `if` | `mcp__plugin_<plugin-name>_<server-name>__<tool>` |
| `mcp_tool` hook `server` | `plugin:<plugin-name>:<server-name>` |

A matcher written against the bare server key **never fires**.

## 4. MCP servers

**Location:** `.mcp.json` in the plugin root, or inline `mcpServers` in `plugin.json`. Standard MCP server configuration.

- Plugin MCP servers start automatically when the plugin is enabled and appear as normal tools.
- They are configured independently of the user's own MCP servers.
- `/reload-plugins` **keeps live connections** for servers whose configuration is unchanged.
- Path variables resolve only in `command`/`args`/`env` (stdio) and `url`/`headers`/`headersHelper` (http/sse/ws) — see `manifest-reference.md §10`.

## 5. LSP servers

**Location:** `.lsp.json` in the plugin root, or inline `lspServers` in `plugin.json`. Maps server name → config.

**Required:** `command` (binary, must be in PATH) and `extensionToLanguage` (extension → language id).

**Optional:** `args`, `transport`, `env`, `initializationOptions`, `settings`, `workspaceFolder`, `startupTimeout`, `shutdownTimeout`, `restartOnCrash` (default `true`), `maxRestarts`, `diagnostics` (default `true`).

- `transport` accepts `socket`, but **every server actually runs over stdio**, so the stdout rules below apply universally.
- `restartOnCrash` and `shutdownTimeout` require **v2.1.205+**. Before that the schema accepted them but setting either made Claude Code skip the server entirely, visible only in `claude --debug`.
- **Extension collisions:** when several enabled servers claim the same extension — same plugin or not — the **first registered wins** and the others never start; `/plugin` warns and names the active plugin.
- An **invalid** server (missing `command` or `extensionToLanguage`) is skipped, doesn't claim its extensions, and the others still start. `claude --debug` says why.
- **Log to stderr, never stdout.** stdout is read as protocol: headers ≤ **64 KiB**, body ≤ **32 MiB**. Exceeding either, or writing non-protocol output, disconnects the server and **counts as a crash** against `restartOnCrash` / `maxRestarts`.
- The language-server binary is **not** bundled — users install it themselves (`Executable not found in $PATH` in the `/plugin` Errors tab).

## 6. Monitors (experimental)

Background commands started automatically while the plugin is active; every stdout line reaches Claude as a notification.

**Location:** `monitors/monitors.json` (a JSON array), or `experimental.monitors` in `plugin.json` as the same array **or** a relative path string (`"./config/monitors.json"`).

- **Interactive CLI sessions only**, unsandboxed, at the same trust level as hooks; skipped where the Monitor tool is unavailable.
- Required: `name` (unique within the plugin — prevents duplicate processes on reload), `command` (persistent background process in the session cwd), `description` (shown in the task panel and notification summaries).
- Optional `when`: `"always"` (default — session start and plugin reload) or `"on-skill-invoke:<skill-name>"` (first dispatch of that skill).
- `command` supports `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, `${CLAUDE_PROJECT_DIR}` and any `${ENV_VAR}`. Prefix `cd "${CLAUDE_PLUGIN_ROOT}" && ` when the script must run from the plugin directory.
- **`${user_config.*}` is rejected** in monitor commands, and monitor processes get **no** `CLAUDE_PLUGIN_OPTION_*` variables — have the script read a config file it owns.
- Disabling the plugin mid-session does **not** stop already-running monitors; they end with the session.

## 7. Themes (experimental)

JSON files in `themes/`: a `base` preset plus a sparse `overrides` map of color tokens. Selecting one saves `custom:<plugin-name>:<slug>` in the user's config. Plugin themes are read-only — `Ctrl+E` in `/theme` copies one into `~/.claude/themes/` for editing.

## 8. Workflows, bin/, settings.json

- **`workflows/`** — workflow script files. The `workflows` manifest key *replaces* this default.
- **`bin/`** — executables added to the Bash tool's `PATH`, callable as bare commands while the plugin is enabled. **Forbidden in org distribution:** claude.ai rejects any plugin with a top-level `bin/` whether it arrives by marketplace sync or direct upload, with `Plugin contains a top-level bin/ directory` (marketplace sync rejects that plugin and syncs the rest). Put executables in `scripts/` and reference them as `${CLAUDE_PLUGIN_ROOT}/scripts/<name>` (`plugin-marketplaces.md §Keep executables out of the top-level bin directory`).
- **`settings.json`** at the plugin root — only `agent` and `subagentStatusLine`; see `manifest-reference.md §11`.

---

## 9. Reference layout

```text
enterprise-plugin/
├── .claude-plugin/
│   └── plugin.json           # the ONLY file that belongs in .claude-plugin/
├── skills/<name>/SKILL.md    # + optional reference.md, scripts/
├── commands/*.md             # flat-file skills
├── agents/*.md
├── workflows/*.js
├── output-styles/*.md
├── themes/*.json
├── monitors/monitors.json
├── hooks/hooks.json          # plus additional hook files
├── bin/                      # PATH executables — not for org distribution
├── settings.json             # agent, subagentStatusLine only
├── .mcp.json
├── .lsp.json
├── scripts/                  # hook and utility scripts
├── LICENSE
└── CHANGELOG.md
```

| Component | Default location |
|---|---|
| Manifest | `.claude-plugin/plugin.json` (optional) |
| Skills | `skills/` (`<name>/SKILL.md`) |
| Commands | `commands/` (flat `.md`) |
| Agents | `agents/` |
| Workflows | `workflows/` |
| Output styles | `output-styles/` |
| Themes | `themes/` |
| Hooks | `hooks/hooks.json` |
| MCP servers | `.mcp.json` |
| LSP servers | `.lsp.json` |
| Monitors | `monitors/monitors.json` |
| Executables | `bin/` |
| Settings | `settings.json` |

**A `CLAUDE.md` at the plugin root is not loaded as context.** Ship instructions as a skill instead (`plugins-reference.md §Standard plugin layout`).

## 10. Cache, orphaned directories, traversal, symlinks

**Cache.** Marketplace plugins are **copied** into `~/.claude/plugins/cache` rather than used in place — the exception is a `command` source in link mode, used in place through links in the cache entry. Each installed version is its own directory, grouped by marketplace and plugin and named for the resolved version, with its own file copy and Node dependencies. A tag-resolved dependency gets a commit-SHA suffix on the directory name.

**Orphaned directories.** On update or uninstall the previous version directory is marked orphaned and swept in the background roughly **14 days** later — the grace period keeps concurrent sessions that already loaded it running. The sweep runs only while at least one plugin is installed, so after uninstalling your last plugin the orphans stay until you install another. Glob and Grep **skip orphaned directories**, so searches don't surface stale plugin code.

A plugin or marketplace folder is removed from the cache only when it holds no directory or symlink. A development checkout symlinked in as a version entry is never marked orphaned, never removed, and never has version-tracking files written inside it.

**Path traversal.** A component path resolving outside the plugin root (`../shared-utils`) is rejected with `path escapes plugin directory`, whether declared in `plugin.json` or in a marketplace entry; the plugin loads without that component. Files outside the plugin directory are also **not copied** into the cache, so a bundled script can't read them at runtime either.

**Symlinks** at copy time (`plugins-reference.md §Share files within a marketplace with symlinks`):

| Target resolves | Behavior |
|---|---|
| Within the plugin's own directory | Preserved as a relative symlink |
| Elsewhere in the same marketplace | **Dereferenced** — content copied in its place (this is how a meta-plugin's `skills/` links to sibling plugins' skills) |
| Outside the marketplace | **Skipped** for security |

For `--plugin-dir`, local-path, and copy-mode `command` installs, **only** links resolving inside the plugin's own directory survive; all others are skipped.

## 11. Node.js dependencies

Claude Code installs a plugin's own npm/Bun packages into each cached version directory it creates — on install, on update, and at session start when an enabled plugin isn't cached yet. It runs **only** when the plugin root has both a `package.json` and a supported lockfile:

| Lockfile | Command |
|---|---|
| `bun.lock` or `bun.lockb` | `bun install --frozen-lockfile --ignore-scripts` |
| `npm-shrinkwrap.json` or `package-lock.json` | `npm ci --ignore-scripts` |
| `yarn.lock`, `pnpm-lock.yaml` | **Skipped** — Yarn and pnpm support resolution-time hooks that bypass `--ignore-scripts` |

With several lockfiles present the first match wins, checked in the order above. Constraints: frozen resolution (fails rather than re-resolving when `package.json` and the lockfile disagree), **no lifecycle scripts**, and a **60-second timeout** — a timeout can leave a partial `node_modules`. The install cannot be disabled by any setting or env var. Failures never block the plugin: they are logged as warnings in `--debug` output, and a `package.json` with no lockfile is skipped with no log entry at all.

Ship an npm lockfile for widest reach; for an **npm-source** plugin ship `npm-shrinkwrap.json`, since npm excludes `package-lock.json` from published packages. For anything this can't cover — packages needing lifecycle scripts, Python dependencies, Yarn/pnpm locks — install from a hook into `${CLAUDE_PLUGIN_DATA}`.

## 12. Installation scopes

| Scope | Settings file | Use case |
|---|---|---|
| `user` | `~/.claude/settings.json` | Personal plugins across all projects (default) |
| `project` | `.claude/settings.json` | Team plugins shared via version control |
| `local` | `.claude/settings.local.json` | Project-specific, gitignored |
| `managed` | Managed settings | Org-managed, read-only (update only) |

## 13. Skills-directory plugins (`<name>@skills-dir`)

Any folder under a skills directory containing `.claude-plugin/plugin.json` loads as a plugin named `<name>@skills-dir` on the next session — **no marketplace, no install step**, discovered in place rather than copied into the cache. Scaffold with `claude plugin init`.

| What you have | What it is |
|---|---|
| `<skills-dir>/foo/SKILL.md`, no manifest | A plain skill `foo` |
| `<skills-dir>/foo/.claude-plugin/plugin.json` | Plugin `foo@skills-dir` with its own skills, agents, hooks, … |
| `<plugin>/skills/bar/SKILL.md` | Skill `bar` inside a plugin |

| Skills directory | Scope | Loads |
|---|---|---|
| `~/.claude/skills/` | personal | Everywhere; no extra restrictions |
| `<cwd>/.claude/skills/` | project | Only after the workspace trust dialog for that folder |

Project scope is restricted further: MCP servers go through the same per-server approval as a project `.mcp.json`, LSP servers start only after trust, and **background monitors do not load at all**.

Project-scope `@skills-dir` plugins load **only from the session's primary working directory** — they do not walk up to the repo root the way plain skills do, so launching from a subdirectory misses a plugin at the repo root. Launch from the repo root, or move the session with `/cd` (v2.1.246+).

Edits to a skill's `SKILL.md` take effect immediately; changes to `hooks/`, `.mcp.json`, `agents/`, `output-styles/` need `/reload-plugins` or a restart. Stop one by deleting the folder or `claude plugin disable my-tool@skills-dir` — there is no uninstall.

## 14. Plugins synced from claude.ai (`<name>@synced`)

In Cowork and cloud sessions, plugins enabled for the claude.ai account are downloaded into `~/.claude/plugins/synced/` in that session's environment and loaded as `<name>@synced`. **They never load in a terminal session you start yourself.** `claude plugin list` shows them under `Synced from claude.ai`.

- `install` / `update` / `uninstall` don't apply — manage the plugin on claude.ai. Turning it off for the account keeps it out of every future synced session.
- Per-environment off switch: `claude plugin disable <name>@synced` (writes `"<name>@synced": false` to that environment's user `enabledPlugins`); per-project: the same key in the committed `.claude/settings.json`.
- **Name conflicts:** an enabled plugin from any other source — marketplace install, `@skills-dir`, `--plugin-dir` — wins, and the synced copy is reported as not loaded. Disable your own copy to use the claude.ai one. Before v2.1.239 the synced copy won instead, and synced plugins loaded as `<name>@inline`.
