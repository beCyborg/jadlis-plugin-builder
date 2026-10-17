# Repo standard — the house GitHub standard for plugin/marketplace repos

> Last audited against Claude Code docs: 2026-10-14 (v2.1.300, mirror 305bb5ef)

Canonical norms for every beCyborg plugin/marketplace repository. Assemble mode scaffolds to this standard; Validate mode checks against it; Migrate mode brings legacy repos up to it. Sources: official Claude Code docs + live anthropics repos (validate-plugins action, claude-plugins-official workflows), verified 2026-09-01.

## Mandatory per repo

1. **Explicit semver in `plugin.json`** — the ONLY place version lives. Never set `version` in the marketplace entry too (plugin.json silently wins; validator warns on mismatch). Bump in the same commit as the content change: version is the update cache key — without a bump recipients get nothing and `/plugin update` says "already at the latest version". `CHANGELOG.md` per plugin.
2. **Release tag per bump**: `{plugin-name}--v{version}` via `claude plugin tag --push` (validates plugin contents, version consistency across both manifests, clean working tree; refuses existing tags). GitHub Release on top of the tag. Tags are mandatory once anything declares `dependencies` on the plugin (semver ranges resolve against tags, not marketplace.json).
3. **`$schema` in both manifests**: `https://json.schemastore.org/claude-code-plugin-manifest.json` and `...-marketplace.json`. Editor autocomplete only — Claude Code ignores the field at load time, and the SchemaStore schemas lag the CLI (community-maintained). Never use them as a CI gate.
4. **LICENSE** at repo root + `license` field in plugin.json.
5. **CI — two layers** (`.github/workflows/plugin-validate.yml`):
   - Layer 1: the official composite action `anthropics/claude-plugins-community/.github/actions/validate-plugins`, pinned to a commit SHA, with `claude-cli-version` pinned. Runs headless with NO `ANTHROPIC_API_KEY` (installs `@anthropic-ai/claude-code` via npm; `permissions: contents: read`; zero secrets — verified against live anthropics repos, 2026-09-01). Enforces invariants I1–I11 + `claude plugin validate`.
   - Layer 2: green `validate` does NOT guarantee the plugin installs and loads: component-path files are checked for existence only, never parsed; a marketplace run never opens the plugins' files; `.lsp.json` is not read at all (`plugins__cli-reference.md §plugin validate`, `plugins__components.md §LSP servers`). MCP entries are checked since v2.1.281 and `outputStyles`/`themes`/`monitors`/`lspServers` paths since v2.1.283. Add: `scripts/preflight_plugin.py` (runs validate per plugin dir plus the invariants below), and a smoke-install into a clean environment with a sentinel-skill invocation. Mods: `claude plugin test`. Plugins with an eval suite: `claude plugin eval --trust-plugin --json` with pinned models (`release-checklist.md §5b`).
   - Fallback if the official action regresses: JSON-schema check + `scripts/preflight_plugin.py`.
6. **`dependencies` with semver ranges** wherever plugins relate (`~2.1.0`, `^2.0`; prereleases opt-in via `-0` suffix). Cross-marketplace deps need `allowCrossMarketplaceDependenciesOn` in the root marketplace.
7. **README install line + auto-update block**:
   - Install line: one command, `claude plugin install <plugin> --marketplace https://<host>/<owner>/<repo>.git` — bare plugin name, no `@marketplace`; it adds the marketplace if needed (user settings, same policy checks as `marketplace add`) and installs (**v2.1.292+**, `plugins__install.md §Add a marketplace and install in one command`; `plugins__cli-reference.md §plugin install`). In a session: `/plugin install <plugin> --marketplace <source>` (v2.1.275+). Directly below it, keep the two-command fallback for older CLIs: `claude plugin marketplace add <url>` then `claude plugin install <plugin>@<marketplace>`. Full URL ⇒ HTTPS without env vars; non-GitHub hosts have no `owner/repo` shorthand.
   - Since v2.1.295 `claude plugin validate` prints a suggested install line when the README has none — advice only, the exit code does not change even with `--strict` (changelog 2.1.295).
   - Auto-update block: for non-Anthropic marketplaces auto-update is OFF by default for recipients — they run `claude plugin update <plugin>@<marketplace>` or enable auto-update once in `/plugin` → Marketplaces.
8. **Semver for OWN plugins, SHA-pins for FOREIGN sources**: a curator marketplace pins every external source to a full 40-hex `sha` (invariant I5); own plugins release by semver. Anthropic's own catalog runs SHA-mode as curator — copy its CI, not its version discipline.
9. **`name` is an immutable slug**, never reserved (`claude-*`, `anthropic-*`, `anthropics-*`, `cc-plugin-*`, `claude-code`, `claude-mods`, `official` beside claude/anthropic — `manifest-reference.md §2`), and equal in `plugin.json` and the marketplace entry: never rename a published plugin (breaks installs with `plugin-not-found`); change `displayName` for UI, use the append-only `renames` map for true renames (validator rejects cycles/unfinished chains).
10. **Working-tree rule**: dev work in a separate clone (`~/<repo-name>`), never in `~/.claude/plugins/marketplaces/` (background refresh wipes edits AND local branches; any `claude` start triggers it, headless included). Push the branch early; `/plugin` operations only after push. See pitfalls.md §1.

## Repo layout (monorepo, the Anthropic model)

```
<repo>/
  .claude-plugin/marketplace.json   # name, owner, plugins[]
  plugins/<plugin-name>/            # or "./" for a root-as-plugin repo
    .claude-plugin/plugin.json      # name, version, description, license, $schema
    skills/…  agents/…  hooks/…  .mcp.json  CHANGELOG.md
  .github/workflows/plugin-validate.yml
  LICENSE
  README.md                         # one-command install line (+ two-command fallback) + auto-update block
```

One repo per product family; `plugins/<name>/` subdirs with full relative-path sources (`"./plugins/<name>"` — portable to pre-2.1.239 clients; `metadata.pluginRoot` is optional sugar, see pitfalls.md §2). Root-as-plugin (`"source": "./"`) is acceptable for single-plugin repos and can coexist with a `plugins/` dir for later additions.

## preflight_plugin.py invariants (offline authoring guardrail)

Canon validation is `claude plugin validate` — preflight runs it first (root + each local plugin dir; skipped with a warning when the binary is absent, or on `--no-validate`) and then checks what validate can't or what the house standard adds. Accepts a marketplace repo or a single plugin directory. Never executes plugin code.

- no UTF-8 BOM in `plugin.json` / `marketplace.json` (error; warning in other component JSON); every component JSON parses;
- version present in plugin.json AND absent from the marketplace entry (or equal, warning);
- `$schema` present in both manifests; LICENSE file exists; `license` field set;
- `plugins[]` sorted by name (I1), no duplicate names (I2);
- description 10–2000 chars (I3); entry name matches `^[a-z0-9][a-z0-9-]{1,63}$` (I11);
- source URL shape (I4: `github` repo is `owner/repo`; `url` / `git-subdir` use `https://`, `ssh://` or `git@`; `archive` uses `https://`); every external source carries a 40-hex `sha` (I5);
- no shell metacharacters (I9), no invisible Unicode (I10);
- marketplace name charset and reserved marketplace names;
- plugin name not reserved (error) or Anthropic-looking (warning); marketplace entry name = `plugin.json` name (warning);
- plugin `settings.json` contains only `agent` / `subagentStatusLine` keys;
- `dependencies` version strings are valid semver ranges;
- `hooks/hooks.json` has the outer `{"hooks":…}` wrapper or a mod's `modules`; each module file exists, stays inside the plugin, and has a mod extension; manifest `types` is a `./`-relative existing `.d.ts`;
- `"${CLAUDE_PLUGIN_ROOT}"` quoted in shell-form hook commands (exec form with `args` needs no quoting) and in monitor commands;
- MCP (`.mcp.json` + manifest `mcpServers`): `${user_config.X}` declared; a `url` option has a non-empty `default` or `required: true`; `${VAR}` carries `:-default`; no `${user_config.*}` in `headersHelper`; no URL repeated across servers of one marketplace (`mcp-patterns.md §3`);
- `userConfig.options`: warning (recipients need v2.1.271+), error when the documented option rules are broken.

## Rollout order (5B)

jadlis-plugins (add version!), youtube-tldr-plugin, swot-news-plugin, skill-creator-plugin, adv-psy-plugin, annas-archive-plugin, claude-desktop-plugins. Per repo: version → $schema → LICENSE → CI → first tag+Release. Bad release recovery: patch-release forward only, never force-push (recipients may have auto-update on).
