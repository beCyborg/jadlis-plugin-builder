# Marketplace Operations

> Last audited against Claude Code docs: 2026-09-01 (~v2.1.251, mirror b290425)

Everything about `marketplace.json`: schema, the seven plugin sources, authentication, hosting, org distribution, managed restrictions, version channels, renames, and the marketplace CLI. Canon pointers use these shorthands — `PM` = `plugin-marketplaces.md`, `PR` = `plugins-reference.md`, `P` = `plugins.md`, `PD` = `plugin-dependencies.md`, `DP` = `discover-plugins.md` — followed by the doc's own section anchor.

## 1. Marketplace schema

`.claude-plugin/marketplace.json`. Required: `name`, `owner`, `plugins` (`PM#marketplace-schema`).

- **`name`** — kebab-case; no spaces, control characters, or bidirectional-formatting characters. Public-facing (`/plugin install my-tool@your-marketplace`). **One marketplace per name per user**: adding a second marketplace under the same name *replaces* the first. To publish several plugins under one name, list them all in one `marketplace.json`.
- **`owner`** — object. `name` required; `email` and `url` optional (`PM#owner-fields`).
- **`plugins`** — array of entries (§3).

Optional top level (`PM#optional-fields`):

| Field | Notes |
|---|---|
| `$schema` | Editor autocomplete only — ignored at load time. |
| `description`, `version` | Also accepted under `metadata` for backward compatibility. |
| `metadata.pluginRoot` | Directory that bare plugin source names resolve under. **v2.1.239+**. |
| `allowCrossMarketplaceDependenciesOn` | Array of other marketplaces whose plugins entries here may depend on. Anything else is blocked at install (`PD#depend-on-a-plugin-from-another-marketplace`). |
| `renames` | Former plugin `name` → current name, or `null` if removed. **v2.1.193+**. See §11. |

### Reserved marketplace names

Sixteen names are reserved for Anthropic and rejected for third parties: `claude-code-marketplace`, `claude-code-plugins`, `claude-plugins-official`, `claude-plugins-community`, `claude-community`, `anthropic-marketplace`, `anthropic-plugins`, `agent-skills`, `anthropic-agent-skills`, `knowledge-work-plugins`, `life-sciences`, `claude-for-legal`, `claude-for-financial-services`, `financial-services-plugins`, `first-party-plugins`, `healthcare`. Impersonating variants (`official-claude-plugins`, `anthropic-plugins-v2`) are blocked too.

The check runs **on every marketplace load, not only on add** (`PM#marketplace-schema`). A marketplace registered before a name became reserved stops loading and reports *registered from an untrusted source*; remove and re-add it under a different name. Before v2.1.205, `first-party-plugins` and `healthcare` weren't reserved and an already-registered marketplace kept loading.

## 2. Plugin entries

An entry may carry **any field of the `plugin.json` schema**, plus the marketplace-only fields `source`, `category`, `tags`, `strict`, `relevance`, `headers`, `headersHelper` (`PM#plugin-entries`).

- Required: `name` (kebab-case, no control/bidi characters), `source`.
- Metadata: `displayName` (UI only — never used for namespacing or lookup), `description`, `version`, `author`, `homepage`, `repository`, `license`, `keywords`, `metadata` (free-form; before v2.1.222 the validator flagged it as unrecognized), `category`, `tags`.
- `defaultEnabled` — **overrides the same field in `plugin.json`**.
- `strict` — see §5. `relevance` — install-suggestion signals; only effective for marketplaces an admin allowlists in managed settings (`plugin-relevance`).
- Component fields: `skills`, `commands`, `agents`, `hooks`, `mcpServers`, `lspServers` (string or array/object).
- Archive auth: `headers`, `headersHelper` — both **v2.1.238+**; `headersHelper` additionally requires `"strict": false` on the entry.

## 3. The seven plugin sources

Set in each entry's `source`. Installed plugins are copied into `~/.claude/plugins/cache` — except a `command` source in link mode, which is used in place (`PM#plugin-sources`).

**Marketplace source ≠ plugin source.** The marketplace source (where the catalog lives, set by `marketplace add` / `extraKnownMarketplaces`) supports `ref` but **not** `sha`. A plugin source supports both. When both `ref` and `sha` are set, **`sha` is the effective pin** — the commit is fetched directly, so the install survives deletion of the branch on GitHub/GitLab/Bitbucket. AWS CodeCommit can't fetch by SHA: there the `ref` must still exist and the commit be reachable from it.

1. **Relative path** — `"./my-plugin"`. Resolves against the **marketplace root** (the directory containing `.claude-plugin/`), not against `.claude-plugin/`. `../` is rejected. A *bare name* (single segment, no `/`, e.g. `"formatter"`) is allowed only when `metadata.pluginRoot` is set (v2.1.239+): with `"pluginRoot": "./plugins"`, `"formatter"` → `./plugins/formatter`. `pluginRoot` must itself be a relative path inside the marketplace, is ignored for sources that already start with `./`, and does **not** apply to a source containing a `/` (`team-a/formatter` still needs `./`). Relative paths do **not** work in URL-based marketplaces — only `marketplace.json` is downloaded (`PM#plugins-with-relative-paths-fail-in-url-based-marketplaces`).
2. **`github`** — `repo` (required, `owner/repo`), `ref?` (branch/tag), `sha?` (full 40-character SHA).
3. **`url`** — `url` (required, full `https://` or `git@`; the `.git` suffix is optional, so Azure DevOps and AWS CodeCommit URLs work), `ref?`, `sha?`.
4. **`git-subdir`** — `url` (full URL, `owner/repo` shorthand, or SSH), `path` (required subdirectory), `ref?`, `sha?`. Uses a sparse partial clone, so it's the right source for monorepos.
5. **`npm`** — `package` (required, scoped names fine), `version?` (exact or range), `registry?` (private registry URL). Installed via `npm install`.
6. **`archive`** (**v2.1.224+**) — `url` (required, HTTPS only; `http://`, loopback, link-local, and cloud-metadata hosts are rejected, and every redirect hop must satisfy the same rules), `sha256?` (64 hex, either case; mismatch → `Plugin archive integrity check failed`). Both zip layouts install — content at the archive root, or one single top-level folder; anything nested deeper fails. **Limit: 256 MiB.** With no `version` declared anywhere the digest *is* the version, so if you declare a `version`, bump it when you rebuild the zip or users keep the cached copy. On v2.1.120–v2.1.223 the install fails with *source type your Claude Code version does not support*; older versions fail to load the whole marketplace.
7. **`command`** (**v2.1.229+**) — `command` (required; printable ASCII ≤ 500 chars, no run of 4+ spaces, so the user can review it; prints exactly one line — the absolute path of a directory holding the complete plugin — and exits 0), `timeout?` (whole seconds, default 60, max 600), `mode?` (`copy` | `link`). Run through `sh` / `cmd.exe` from the user's home directory. The printed path is **refused** when the directory has no plugin content at its top level (`.claude-plugin/`, `skills/`, `commands/`, `agents/`, `hooks/`), when it is the directory Claude Code was started in or one of its parents, or when it is a Windows UNC path.
   - **copy** (default): copied into the versioned cache, version = content hash; refused above 256 MiB or 20,000 entries.
   - **link**: entries linked in place — nothing copied, contents not hashed, size limits don't apply, **npm dependency install is skipped** (ship `node_modules` yourself), and the version derives from the printed directory's real path plus its top-level entries, so print a *different path* to signal new content. Not supported on Windows. A top-level symlink pointing outside the printed directory fails the install.
   - **Acceptance**: the user sees and accepts the exact command string on install/update from `/plugin` details or `claude plugin install|update` in an interactive terminal; `--yes` accepts non-interactively. Every other path runs only the already-accepted command. Changing `command` or `mode` freezes users at their current version until they re-accept via `claude plugin update <plugin>@<marketplace>`. Command-sourced plugins are **never** installed as another plugin's dependency.
   - **Re-runs**: on every install/update; once per session in the background shortly after start (independent of the marketplace auto-update setting); and at startup or `/reload-plugins` when the installed version is missing from the cache. `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` skips the two background runs. A changed hash installs a new version and reloads it in-session (or prompts for `/reload-plugins` when reloading would invalidate the prompt cache).

## 4. headersHelper — authenticating archive downloads

`PM#authenticate-archive-downloads`. Where you declare it decides both scope and timing:

| Declared on | Gets the headers | When the command runs |
|---|---|---|
| Marketplace `url` source | Archive downloads on the marketplace URL's **origin** (same scheme, host, port) | Before each `marketplace.json` fetch and each archive download on that origin; one run's output is reused for up to **60 s** |
| Plugin entry | That entry's download only | Only on a **single-plugin** install/update that the user accepts |

Where both set the same header name, the entry's value wins; within one place, command output overrides a listed `headers` value.

**Writing the command**: printable ASCII ≤ 500 chars, no run of 4+ spaces; print **one JSON object** of string header values on stdout and exit 0 within **10 s**; run through `sh` (`cmd.exe` on Windows) **from the config directory** (`~/.claude` or `CLAUDE_CONFIG_DIR`) — so use an absolute path or a `PATH` command, never a project-relative one. For a command declared in `marketplace.json` or a project's `.claude/settings*.json`, Claude Code **strips every env var whose name contains `TOKEN`, `SECRET`, `KEY`, or `AUTH`** (including `ANTHROPIC_API_KEY`); user settings, `--settings`, and managed settings are exempt. Claude Code supplies `CLAUDE_CODE_MARKETPLACE_URL` / `CLAUDE_CODE_MARKETPLACE_NAME` (url source) or `CLAUDE_CODE_PLUGIN_NAME` / `CLAUDE_CODE_PLUGIN_ARCHIVE_URL` (entry); `MARKETPLACE_NAME` is unset on the first fetch after an add-by-URL.

**Not run, or output dropped**: non-zero exit / >10 s / non-JSON output (the fetch itself is abandoned); marketplace URL not `https://`; a redirect off the archive URL's origin (drops both places' headers); routing/identity header names (`Host`, `Cookie`, `X-Forwarded-*`) — stripped, while `Authorization` is kept; a command declared in an `--add-dir` directory's settings; managed `disableCommandPluginSources: true`, or `allowManagedHooksOnly` unless `disableCommandPluginSources` is explicitly `false`.

**Refused instead of prompted** (plugin stays at its installed version): bulk install, install from a plugin suggestion, install as another plugin's dependency, background auto-update, and session start for an archive never downloaded — the last two surface in the `/plugin` **Errors** tab. Before v2.1.238 the entry's archive downloaded without headers at all → `HTTP 401 while downloading plugin archive from …`.

## 5. Strict mode

`PM#strict-mode`. Default `true`.

- **`true`** — `plugin.json` is the authority; the marketplace entry *supplements* it and both are merged.
- **`false`** — the entry is the plugin's **entire** definition. If `plugin.json` also declares components, that is a conflict and the plugin fails to load: `Plugin my-plugin has conflicting manifests: both plugin.json and marketplace entry specify components.` (`PR#example-error-messages`).

Use `false` when the marketplace operator curates or restructures a plugin's components, or when an entry needs `headersHelper` (which requires it, so users can review what the plugin contains before accepting the command).

## 6. Marketplace-root `skills`

`PM#advanced-plugin-entries`. Normally `skills` **adds** to the default `skills/` scan. The one exception: when several entries share one `skills/` folder at the marketplace root (`"source": "./"`), listing specific subdirectories makes that list the **complete set** for the entry and other directories don't load:

```json
"source": "./",
"skills": ["./skills/code-review", "./skills/docs"]
```

Listing `./skills/` itself, or the plugin root, keeps the full scan. If none of the listed paths exist, the default scan runs anyway.

## 7. Hosting and private repositories

- **GitHub is recommended** (`PM#host-on-github-recommended`); users add with `/plugin marketplace add owner/repo`. Any other git host works via the full URL (`/plugin marketplace add https://gitlab.com/company/plugins.git`).
- **Commands the user runs** (`marketplace add`, `plugin install|update`, `marketplace update`) use their existing git credential helpers — `gh auth login`, macOS Keychain, `git-credential-store`. SSH works when the host is in `known_hosts` and the key is in `ssh-agent` (interactive SSH prompts are suppressed). GitHub `owner/repo` shorthand clones over **SSH** by default; `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1` switches to HTTPS.
- **The background refresh disables git credential helpers** for its `git pull`, so HTTPS private pulls fail even with a helper configured; SSH remotes with a loaded key are unaffected. A failed pull triggers a full re-clone, which *does* use stored credentials but can hit the 120 s git timeout. Mitigations: `CLAUDE_CODE_PLUGIN_KEEP_MARKETPLACE_ON_FAILURE=1` (keep the existing clone instead of re-cloning — also the fix for offline/airgapped loops), a configured helper (`gh auth setup-git`), `CLAUDE_CODE_PLUGIN_GIT_TIMEOUT_MS`, or a **scoped** git URL rewrite that embeds a read-only token (`x-access-token` for GitHub, `oauth2` for GitLab, `x-token-auth` for Bitbucket). Never scope a rewrite to the bare host — it overrides normal credentials for every fetch and push there. Setting `GITHUB_TOKEN` alone does nothing; tokens take effect only through a helper.

## 8. Distribution through organization settings

Team/Enterprise, **Organization settings → Plugins** (`PM#distribute-through-organization-settings`):

- The marketplace repository must be **private or internal**; org sync reads it through the Claude GitHub App or the org's GHE App — the maintainer's git credentials are not involved.
- Allowed source types only: `github`, `url`, `git-subdir`, or a relative path starting with `./`. **A bare name under `metadata.pluginRoot` is rejected** as unsupported — write `./plugins/deploy-tools` out in full.
- A plugin source may be private only if it is a github.com source with the marketplace repo's owner, or lives on the org's GHE host with the app installed. Everything else is fetched without credentials and must be public.
- **No top-level `bin/`** in any plugin distributed this way — both marketplace sync and direct upload reject it with `Plugin contains a top-level bin/ directory`. Put executables in `scripts/` and reference `${CLAUDE_PLUGIN_ROOT}/scripts/<name>`.

## 9. Teams, containers, and managed restrictions

- **Team auto-registration**: `extraKnownMarketplaces` + `enabledPlugins` in the repo's `.claude/settings.json` register the marketplace once the user trusts the folder — no separate prompt. Marketplace state itself is per user in `~/.claude/plugins/known_marketplaces.json`, not per project; a relative local source resolves against the repo's main checkout, shared across worktrees (`PM#require-marketplaces-for-your-team`).
- **Containers/CI**: `CLAUDE_CODE_PLUGIN_SEED_DIR` points at a pre-populated mirror of `~/.claude/plugins` (`known_marketplaces.json`, `marketplaces/<name>/`, `cache/<marketplace>/<plugin>/<version>/`); layer several with `:` (`;` on Windows). Build it by installing during image build, or install straight into it with `CLAUDE_CODE_PLUGIN_CACHE_DIR`. The seed is **read-only** (auto-update off), **takes precedence** over the user's configuration on every startup (opt out with `/plugin disable`, not by removing the marketplace), is located by **probing paths at runtime** so it survives being mounted elsewhere, and rejects `marketplace remove` / `marketplace update`. Works in `-p` mode too.
- **Managed restrictions** (`PM#managed-marketplace-restrictions`), all checked **before any network or filesystem operation**, on add and on install/update/refresh/auto-update: `strictKnownMarketplaces` — undefined = no restriction, `[]` = total lockdown including the official Anthropic marketplace, a list = allowlist. Matching is exact except owner-wildcard `github` entries `owner/*` (**v2.1.223+**); `hostPattern` and `pathPattern` match by regex on host / filesystem path and are the right form when one repo is reachable by several URL shapes (a trailing slash, `.git`, or `ssh://` vs `https://` count as different literals). `blockedMarketplaces` enforces the same way and also matches cloned `https://` repo URLs (**v2.1.232+**, ignoring `.git` and a `#ref`). Pair with `disableSideloadFlags` to reject sideload CLI flags, `pluginSuggestionMarketplaces` to allowlist suggestion sources, `disableCommandPluginSources` to block `command` sources (`strictKnownMarketplaces` matches the marketplace, not entries, so it does not block them), and `allowManagedHooksOnly`, which blocks command sources by default. `strictKnownMarketplaces` restricts but doesn't register — pair it with `extraKnownMarketplaces` in the same `managed-settings.json`.

## 10. Version resolution and release channels

The plugin version is the **cache key**: if the resolved version matches what the user already has, `/plugin update` and auto-update skip the plugin. Resolution order for every source type except `command` (`PR#version-management`):

1. `version` in `plugin.json`
2. `version` in the marketplace entry
3. the git commit SHA of the source (`github`, `url`, `git-subdir`, and relative paths in a git-hosted marketplace)
4. the SHA-256 digest for `archive` sources — the `sha256` pin, or the downloaded file's digest — shortened to 12 characters
5. `unknown`, for `npm` sources and local directories not inside a git repository

A `command` source always derives its version from the produced content: a 12-character hash alone, or `<version>-<hash>` when `plugin.json` sets one; the **marketplace entry's `version` is ignored**. Setting `version` in *both* `plugin.json` and the entry is a trap: **`plugin.json` wins silently**, so a stale manifest masks the marketplace value.

**Release channels**: stable/latest = two marketplaces pointing at different `ref`s of the same repo, assigned per user group through per-group endpoint-managed settings or one Claude apps gateway policy per group (a group policy's `extraKnownMarketplaces` *replaces* the catch-all map rather than merging, so list everything the group needs). Server-managed settings apply org-wide and can't carry per-group assignment. **Each channel must resolve to a different version** — with explicit versions, `plugin.json` must differ at each pinned ref; with none, the distinct commit SHAs already differ. Two refs resolving to the same version string are treated as identical and the update is skipped.

## 11. renames

`PM#rename-or-remove-a-plugin`. A plugin's `name` is its stable identifier (`enabledPlugins`, `pluginConfigs`, install commands). To change only the label, set `displayName` and leave `name` alone. To really rename or remove, add a top-level `renames` entry mapping the former name to the new name or to `null` (**v2.1.193+**; earlier versions ignore the field and report `plugin-not-found`).

At startup Claude Code follows the map: it loads the plugin under the new name, shows a one-line notice (`Renamed to "code-formatter" in the "acme-tools" marketplace`), and rewrites the key in `enabledPlugins` and `pluginConfigs` across user, project, and local scopes — so the notice appears once. A `null` entry drops the key and reports the removal. **A remote-sourced plugin (`github`, `npm`, …) reports `plugin-cache-miss` after a rename and needs one `/plugin install`.** Managed and other read-only scopes can't be rewritten, so the notice recurs until an admin edits them.

Treat the map as **append-only**: keep old entries forever and add a second entry for a second rename rather than editing the first — chains are followed. `claude plugin validate .` rejects a chain that forms a cycle or doesn't terminate at `null` or a listed plugin.

## 12. Marketplace CLI

`PM#manage-marketplaces-from-the-cli` — equivalent to the in-session `/plugin marketplace` commands.

| Command | Notes |
|---|---|
| `claude plugin marketplace add <source>` | `owner/repo`, git URL, URL to a `marketplace.json`, or local path. Pin with `@ref` (shorthand) or `#ref` (URL). A URL **must include its scheme** — since v2.1.196 a bare host is rejected with a fix-it message; earlier versions misread it as a GitHub path. `--scope user\|project\|local` (default `user`), `--sparse <paths…>` for monorepos. |
| `claude plugin marketplace list [--json]` | JSON adds `installLocation` (local cache path) plus source-specific `repo` / `url` / `path`, and `ref` when pinned. |
| `claude plugin marketplace remove <name> [--scope]` | `<name>` is the name from `marketplace.json`, not the source you added. **Removing from the last scope uninstalls the plugins installed from it** — use `update` to refresh instead. |
| `claude plugin marketplace update [name]` | Updates to the latest commit of the pinned `ref` (not the default branch). Seed-managed marketplaces are skipped; `remove`/`update` fail against them outright. |

## 13. Auto-update is OFF by default for your recipients

`claude-plugins-official` and most other official Anthropic marketplaces ship with auto-update **enabled**. **Third-party and local development marketplaces have auto-update disabled by default** (`DP#configure-auto-updates`). Your users therefore get nothing when you publish a new version until they act.

**A README block is mandatory for any marketplace you publish.** Give recipients both paths:

```
# get the new version now
claude plugin marketplace update <marketplace> && claude plugin update <plugin>@<marketplace>

# or turn on auto-update once: /plugin → Marketplaces → <marketplace> → Enable auto-update
```

For org distribution, admins can set `"autoUpdate": true` on the `extraKnownMarketplaces` entry in managed settings instead of asking every user to toggle it. Note also that even with auto-update on, the check runs after session start with a **random delay of up to ten minutes** and the running session keeps its loaded versions until `/reload-plugins` or the next launch; a plugin whose entry declares `headersHelper` is left out of auto-update entirely, and a `command` source follows its own once-per-session cadence, independent of both this setting and `DISABLE_AUTOUPDATER`.
