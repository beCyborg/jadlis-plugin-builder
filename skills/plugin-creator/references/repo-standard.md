# Repo standard — the house GitHub standard for plugin/marketplace repos

> Last audited against Claude Code docs: 2026-09-01 (~v2.1.251, mirror b290425)

Canonical norms for every beCyborg plugin/marketplace repository. Assemble mode scaffolds to this standard; Validate mode checks against it; Migrate mode brings legacy repos up to it. Sources: official Claude Code docs + live anthropics repos (validate-plugins action, claude-plugins-official workflows), verified 2026-09-01.

## Mandatory per repo

1. **Explicit semver in `plugin.json`** — the ONLY place version lives. Never set `version` in the marketplace entry too (plugin.json silently wins; validator warns on mismatch). Bump in the same commit as the content change: version is the update cache key — without a bump recipients get nothing and `/plugin update` says "already at the latest version". `CHANGELOG.md` per plugin.
2. **Release tag per bump**: `{plugin-name}--v{version}` via `claude plugin tag --push` (validates plugin contents, version consistency across both manifests, clean working tree; refuses existing tags). GitHub Release on top of the tag. Tags are mandatory once anything declares `dependencies` on the plugin (semver ranges resolve against tags, not marketplace.json).
3. **`$schema` in both manifests**: `https://json.schemastore.org/claude-code-plugin-manifest.json` and `...-marketplace.json`. Editor autocomplete only — Claude Code ignores the field at load time, and the SchemaStore schemas lag the CLI (community-maintained). Never use them as a CI gate.
4. **LICENSE** at repo root + `license` field in plugin.json.
5. **CI — two layers** (`.github/workflows/plugin-validate.yml`):
   - Layer 1: the official composite action `anthropics/claude-plugins-community/.github/actions/validate-plugins`, pinned to a commit SHA, with `claude-cli-version` pinned. Runs headless with NO `ANTHROPIC_API_KEY` (installs `@anthropic-ai/claude-code` via npm; `permissions: contents: read`; zero secrets — verified against live anthropics repos, 2026-09-01). Enforces invariants I1–I11 + `claude plugin validate`.
   - Layer 2: green `validate` does NOT guarantee the plugin installs and loads (validator and runtime loader accept different schemas; component-path files are checked for existence only, never parsed — plugin-marketplaces.md §validate). Add: JSON-parse of `.mcp.json` / `hooks/hooks.json` / `.lsp.json`, path-existence checks, and a smoke-install into a clean environment with a sentinel-skill invocation.
   - Fallback if the official action regresses: JSON-schema check + `scripts/preflight_plugin.py`.
6. **`dependencies` with semver ranges** wherever plugins relate (`~2.1.0`, `^2.0`; prereleases opt-in via `-0` suffix). Cross-marketplace deps need `allowCrossMarketplaceDependenciesOn` in the root marketplace.
7. **README auto-update block**: for non-Anthropic marketplaces auto-update is OFF by default for recipients — they run `claude plugin update <plugin>@<marketplace>` or enable auto-update once in `/plugin` → Marketplaces. Give the HTTPS slash-command install line (`/plugin marketplace add https://github.com/<owner>/<repo>`; full URL ⇒ HTTPS without env vars).
8. **Semver for OWN plugins, SHA-pins for FOREIGN sources**: a curator marketplace pins every external source to a full 40-hex `sha` (invariant I5); own plugins release by semver. Anthropic's own catalog runs SHA-mode as curator — copy its CI, not its version discipline.
9. **`name` is an immutable slug**: never rename a published plugin (breaks installs with `plugin-not-found`); change `displayName` for UI, use the append-only `renames` map for true renames (validator rejects cycles/unfinished chains).
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
  README.md                         # install line + auto-update block
```

One repo per product family; `plugins/<name>/` subdirs with full relative-path sources (`"./plugins/<name>"` — portable to pre-2.1.239 clients; `metadata.pluginRoot` is optional sugar, see pitfalls.md §2). Root-as-plugin (`"source": "./"`) is acceptable for single-plugin repos and can coexist with a `plugins/` dir for later additions.

## preflight_plugin.py invariants (offline authoring guardrail)

Canon validation is `claude plugin validate` — preflight only catches what validate can't or what the house standard adds:

- version present in plugin.json AND absent from the marketplace entry (or equal, warning);
- `$schema` present in both manifests; LICENSE file exists; `license` field set;
- `plugins[]` sorted by name (I1), no duplicate names (I2);
- description 10–2000 chars (I3); name matches `^[a-z0-9][a-z0-9-]{1,63}$` (I11);
- source URL shape (I4); every external source carries a 40-hex `sha` (I5);
- no shell metacharacters (I9), no invisible Unicode (I10);
- plugin `settings.json` contains only `agent` / `subagentStatusLine` keys;
- `dependencies` version strings are valid semver ranges;
- `.mcp.json` / `hooks/hooks.json` / `.lsp.json` parse as JSON; hooks.json has the outer `{"hooks":…}` wrapper;
- `"${CLAUDE_PLUGIN_ROOT}"` quoted in shell-form hook/monitor commands.

## Rollout order (5B)

jadlis-plugins (add version!), youtube-tldr-plugin, swot-news-plugin, skill-creator-plugin, adv-psy-plugin, annas-archive-plugin, claude-desktop-plugins. Per repo: version → $schema → LICENSE → CI → first tag+Release. Bad release recovery: patch-release forward only, never force-push (recipients may have auto-update on).
