# plugin.json Manifest Reference

> Last audited against Claude Code docs: 2026-09-01 (~v2.1.251, mirror b290425)

Complete reference for `.claude-plugin/plugin.json` — every field, path resolution, user configuration, dependencies, and path variables.

**The manifest is optional.** Without it, Claude Code auto-discovers components in their default locations and derives the plugin name from the directory name (`plugins-reference.md §Plugin manifest schema`). Write one when you need metadata, custom component paths, `userConfig`, `channels`, or `dependencies`. `plugin.json` lives in `.claude-plugin/`; **every other directory** (`skills/`, `agents/`, `hooks/`, …) lives at the plugin root, not inside `.claude-plugin/` (`plugins-reference.md §Standard plugin layout`).

---

## 1. Complete schema

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "plugin-name",
  "displayName": "Plugin Name",
  "version": "1.2.0",
  "description": "Brief plugin description",
  "author": { "name": "Author Name", "email": "a@example.com", "url": "https://github.com/author" },
  "homepage": "https://docs.example.com/plugin",
  "repository": "https://github.com/author/plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"],
  "metadata": { "catalogId": "cat-123", "tier": "pro" },
  "defaultEnabled": true,
  "skills": "./custom/skills/",
  "commands": ["./custom/commands/special.md"],
  "agents": ["./custom/agents/reviewer.md"],
  "workflows": "./custom/workflows/",
  "hooks": "./config/hooks.json",
  "mcpServers": "./mcp-config.json",
  "outputStyles": "./styles/",
  "lspServers": "./.lsp.json",
  "experimental": { "themes": "./themes/", "monitors": "./monitors.json" },
  "userConfig": { },
  "channels": [ ],
  "dependencies": ["helper-lib", { "name": "secrets-vault", "version": "~2.1.0" }]
}
```

---

## 2. Required field and namespacing

| Field | Type | Required | Rules |
|---|---|---|---|
| `name` | string | **Yes** (the only one) | kebab-case; no spaces, control characters, or bidirectional-formatting characters |

`name` is the component namespace: agent `agent-creator` in plugin `plugin-dev` shows as `plugin-dev:agent-creator` (`plugins-reference.md §Required fields`).

**A marketplace entry can rename the plugin.** When the entry lists a different `name`, that entry name — not the manifest name — is what keys `enabledPlugins` and what `/plugin` displays (`plugins-reference.md §Required fields`).

---

## 3. Metadata fields

| Field | Type | Notes |
|---|---|---|
| `$schema` | string | `https://json.schemastore.org/claude-code-plugin-manifest.json`. Editor autocomplete only — **Claude Code ignores it at load time**, and it is not a CI gate. Use `claude plugin validate --strict` for that. |
| `displayName` | string | UI name in the `/plugin` picker. May contain spaces and any casing. Falls back to `name`. **Never used for namespacing or lookup.** |
| `version` | string | Semver. Setting it **pins** the plugin: users get updates only when you bump it. Exception: a `command` source always derives its version from the command output hash and ignores this pinning behavior. If the marketplace entry also sets `version`, `plugin.json` wins. |
| `description` | string | Plugin purpose. |
| `author` | object | `{ name, email, url }`. |
| `homepage` / `repository` / `license` | string | Docs URL / source URL / SPDX-style identifier. |
| `keywords` | array | Discovery tags. A string here instead of an array is a **load error**. |
| `metadata` | object | Free-form; Claude Code never reads it, so values cannot affect behavior. Non-object value → ignored + warning. Before v2.1.222 the key counted as unrecognized. |
| `defaultEnabled` | boolean | Default `true`. See §4. |

Version fallback chain when `plugin.json` sets no `version`: marketplace entry → git commit SHA (`github` / `url` / `git-subdir` / relative path in a git marketplace) → SHA-256 digest, first 12 chars (`archive`) → `unknown` (`npm`, local dirs outside git) (`plugins-reference.md §Version management`).

## 4. defaultEnabled precedence

`defaultEnabled` is only the fallback. Precedence, highest first (`plugins-reference.md §Default enablement`):

1. **Marketplace entry `defaultEnabled`** — overrides the value in `plugin.json`.
2. **The user's setting** — any `enabledPlugins` entry at any scope. It persists across updates and reinstalls, so changing `defaultEnabled` in a later release never flips an existing user.
3. **A dependency requirement** — when an active plugin requires this one, Claude Code writes an explicit `true` at install/enable time, which beats a `defaultEnabled: false` of its own (`plugin-dependencies.md §Enable or disable a plugin with dependencies`).
4. **`defaultEnabled` in `plugin.json`**, else `true`.

Ship `defaultEnabled: false` for plugins that add cost or scope the user should opt into (external-service connectors).

## 5. Unrecognized fields, wrong types, `--strict`

| Situation | Runtime | `claude plugin validate` |
|---|---|---|
| Unrecognized top-level field | Ignored; plugin loads | Warning, with a did-you-mean suggestion when the name is 1–2 characters off |
| Recognized field, wrong type (most fields) | **Plugin fails to load** | Error |
| `experimental` or `metadata`, wrong type | Value ignored | Warning |

Ignoring unknown keys is deliberate: one manifest can double as a VS Code/Cursor extension manifest, an npm `package.json`, or an MCPB/DXT bundle manifest (`plugins-reference.md §Unrecognized fields`).

`--strict` turns **every** warning into an error — not just unrecognized fields. Run it in CI:

```bash
claude plugin validate ./my-plugin --strict
```

---

## 6. Component path fields

| Field | Type | Default dir it relates to | Merge |
|---|---|---|---|
| `skills` | string \| array | `skills/` | **adds** |
| `commands` | string \| array | `commands/` | replaces |
| `agents` | string \| array | `agents/` | replaces |
| `workflows` | string \| array | `workflows/` | replaces |
| `outputStyles` | string \| array | `output-styles/` | replaces |
| `experimental.themes` | string \| array | `themes/` | replaces |
| `experimental.monitors` | string \| array | `monitors/monitors.json` | replaces |
| `hooks` | string \| array \| object | `hooks/hooks.json` | own merge rules |
| `mcpServers` | string \| array \| object | `.mcp.json` | own merge rules |
| `lspServers` | string \| array \| object | `.lsp.json` | own merge rules |
| `userConfig` | object | — | §7 |
| `channels` | array | — | §8 |
| `dependencies` | array | — | §9 |

`themes` and `monitors` are **experimental**: their schema may change between releases, and declaring them at the top level still works but warns — a future release will require `experimental.*` (`plugins-reference.md §Experimental components`).

### Path behavior rules

(`plugins-reference.md §Path behavior rules`)

- **Replace:** `commands`, `agents`, `workflows`, `outputStyles`, `experimental.themes`, `experimental.monitors`. Declaring the key stops the default directory from being scanned. To keep the default and add more, list it: `"commands": ["./commands/", "./extras/"]`.
- **Add:** `skills` only. `skills/` is **always** scanned and the listed directories load alongside it. One exception: for a marketplace entry whose `source` resolves to the **marketplace root**, listing specific subdirectories *replaces* the default `skills/` scan (`plugin-marketplaces.md §Advanced plugin entries`).
- **Own merge rules:** `hooks`, `mcpServers`, `lspServers` — each combines its manifest value with the default file rather than replacing it.
- **Default-folder conflict:** with both a default folder and its manifest key present, Claude Code warns about the ignored folder in `claude plugin list` and the `/plugin` detail view; the plugin still loads from the manifest paths. No warning when the manifest path points *into* the default folder (`"commands": ["./commands/deploy.md"]`).
- **All paths are relative to the plugin root and must start with `./`.** Only `skills` also accepts `"."`. `"."` and `"./"` both mean the plugin root; before v2.1.221 `"."` failed validation and the plugin didn't load, so use `"./"` for backward compatibility.
- A skill path may point straight at a directory holding a `SKILL.md` (`"skills": ["."]`). The invocation name comes from the frontmatter `name`, falling back to the directory basename.
- A plugin with a root `SKILL.md`, **no `skills/` directory, and no `skills` manifest key** loads automatically as a single-skill plugin — do not add `"skills": ["./"]` for that layout.
- Paths resolving outside the plugin root (`../shared-utils`) are rejected with `path escapes plugin directory`; the plugin loads without that component (`plugins-reference.md §Path traversal limitations`).

---

## 7. userConfig

Declares values Claude Code prompts for when the plugin is enabled, instead of asking users to hand-edit `settings.json`. Keys must be valid identifiers.

| Option field | Required | Description |
|---|---|---|
| `type` | Yes | `string`, `number`, `boolean`, `directory`, or `file` |
| `title` | Yes | Label in the configuration dialog |
| `description` | Yes | Help text under the field |
| `sensitive` | No | Masks input and stores in secure storage instead of `settings.json` |
| `required` | No | Validation fails when empty |
| `default` | No | Used when the user provides nothing |
| `multiple` | No | `string` type only — allow an array of strings |
| `min` / `max` | No | Bounds for `number` |

**Substitution.** `${user_config.KEY}` resolves in MCP and LSP server configs and in hook commands; **non-sensitive** values also resolve in skill and agent content. All values reach hook processes as `CLAUDE_PLUGIN_OPTION_<KEY>` environment variables (key uppercased).

**Shell-executed fields reject `${user_config.*}`** — substituting into a shell command would let the shell run whatever the value contains, so the component fails with an error instead (v2.1.207+; earlier versions did substitute):

| Rejected field | Pass the value instead by |
|---|---|
| Shell-form hook commands | exec form with `args`, or reading `CLAUDE_PLUGIN_OPTION_<KEY>` from the hook environment |
| Monitor commands | reading it from a config file in the script (monitors get **no** `CLAUDE_PLUGIN_OPTION_*` either) |
| MCP `headersHelper` | reading it from a config file in the script |

**Storage.** Non-sensitive → `pluginConfigs[<plugin-id>].options` in user `settings.json`. Sensitive → macOS Keychain, falling back to `~/.claude/.credentials.json` when the Keychain rejects the write; on platforms with no supported keychain, always the credentials file. Keychain storage is shared with OAuth tokens and capped at roughly **2 KB total** — keep sensitive values small.

**Which settings sources are read** (precedence: managed → `--settings` → user): `pluginConfigs` is read from **user settings, `--settings`, and managed settings only**. Project `.claude/settings.json` and `.claude/settings.local.json` entries are **ignored**, so a cloned repository can't feed values into hook commands or server configs (v2.1.207+). The restriction is specific to `pluginConfigs` — `enabledPlugins` still honors project and local settings.

## 8. channels

`channels` is an array of message-injection channel declarations (Telegram/Slack/Discord style). Each entry:

- `server` — **required**; must match a key in the plugin's own `mcpServers`.
- `userConfig` — optional, per-channel, same schema as §7 (bot tokens, owner IDs prompted at enable time).

## 9. dependencies (plugin → plugin)

An entry is a bare name string, or an object (`plugin-dependencies.md §Declare a dependency with a version constraint`):

| Field | Type | Description |
|---|---|---|
| `name` | string | Required. Resolves in the declaring plugin's own marketplace by default. |
| `version` | string | semver range: `~2.1.0`, `^2.0`, `>=1.4`, `=2.1.0`. Fetched at the **highest tagged version** satisfying it. |
| `marketplace` | string | Resolve `name` in a different marketplace. Blocked unless allowlisted (below). |

- Pre-releases (`2.0.0-beta.1`) are excluded unless the range opts in with a pre-release suffix (`^2.0.0-0`).
- **Release tags are what constraints resolve against.** Tag each release `{plugin-name}--v{version}`, with `{version}` matching that commit's `plugin.json`. `claude plugin tag --push` derives the name, validates the plugin, checks that `plugin.json` and the marketplace entry agree, and requires a clean tree. Without tags, no constraint resolves.
- **Bundle pattern:** a manifest of only `name` + `dependencies` installs a curated plugin set behind one `claude plugin install`.
- **Cross-marketplace:** blocked by default. The **root** marketplace (the one hosting the plugin being installed) must list the target in `allowCrossMarketplaceDependenciesOn`; trust does not chain through intermediate marketplaces. Otherwise install fails with a `cross-marketplace` error naming the field.
- **Intersecting ranges:** several plugins constraining the same dependency resolve to the highest version satisfying all. Incompatible ranges → `range-conflict` and the *new* install fails, leaving existing plugins untouched. Uninstalling the last constraining plugin releases the dependency back to tracking its marketplace.
- **Non-git sources** (`npm`, `archive`, `command`): the constraint doesn't select the version, but is checked at load — a mismatch disables the plugin with `dependency-version-unsatisfied`.

| Error | Meaning |
|---|---|
| `dependency-unsatisfied` | Declared dependency not installed, or installed but disabled |
| `range-conflict` | Ranges can't be combined, invalid semver, or too complex to intersect |
| `dependency-version-unsatisfied` | Installed version outside the declared range |
| `no-matching-tag` | No `{name}--v*` tag on the dependency's repo satisfies the range |

Check programmatically with `claude plugin list --json` — the `errors` field lists them; cleanly loaded plugins omit the field.

---

## 10. Path variables

| Variable | Resolves to | Use for |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | Absolute path to the plugin's install directory | Bundled scripts, binaries, config files |
| `${CLAUDE_PLUGIN_DATA}` | `~/.claude/plugins/data/{id}/`, created on first reference | Installed dependencies, generated files, caches that must outlive an update |
| `${CLAUDE_PROJECT_DIR}` | The project root | Project-local scripts and config |

All three are exported as environment variables to hook processes and MCP/LSP subprocesses. **Inline substitution is field-scoped** (`plugins-reference.md §Environment variables`):

| Component | Fields where placeholders resolve |
|---|---|
| Skill and agent content | Anywhere |
| Hook and monitor commands | Anywhere |
| MCP `stdio` servers | `command`, `args`, `env` |
| MCP `http` / `sse` / `ws` servers | `url`, `headers`, `headersHelper` |
| LSP servers | `command`, `args`, `env`, `workspaceFolder` |

**Quoting.** Prefer hook exec form with `args` — each path arrives as one argument with no quoting. In shell-form hooks and monitor commands, wrap in double quotes: `"${CLAUDE_PLUGIN_ROOT}"/scripts/process.sh`.

**ROOT is ephemeral, DATA persists.** `${CLAUDE_PLUGIN_ROOT}` changes on every update; the old directory lingers only as a grace period — never write state there. `${CLAUDE_PLUGIN_DATA}` survives updates; `{id}` is the plugin identifier with characters outside `a-zA-Z0-9_-` replaced by `-` (`formatter@my-marketplace` → `formatter-my-marketplace`). It is deleted when the plugin is uninstalled from its last scope — `--keep-data` preserves it.

**Mid-session updates:** hooks, monitors, MCP, and LSP keep using the old path. `/reload-plugins` switches hooks, MCP, and LSP to the new one; **monitors need a session restart**.

Because the data directory outlives any single version, existence alone can't detect a changed dependency manifest — the documented pattern is a `SessionStart` hook that `diff`s the bundled `package.json` against a copy in `${CLAUDE_PLUGIN_DATA}` and reinstalls when they differ (`plugins-reference.md §Persistent data directory`).

## 11. The plugin's own settings.json

A `settings.json` at the plugin root applies default configuration when the plugin is enabled. **Only `agent` and `subagentStatusLine` are supported**; unknown keys are silently ignored (`plugins-reference.md §File locations reference`, `plugins.md §Ship default settings with your plugin`).

```json
{ "agent": "security-reviewer" }
```

`agent` activates one of the plugin's own agents as the **main thread**, applying its system prompt, tool restrictions, and model. `settings.json` takes priority over a `settings` key declared in `plugin.json`.
