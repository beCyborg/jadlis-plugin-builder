---
name: plugin-creator
description: >-
  Assemble, validate, release, and migrate Claude Code plugins and plugin
  marketplaces: scaffold a plugin repo to the house GitHub standard, run
  offline preflight + claude plugin validate, ship releases (version bump,
  changelog, tag, GitHub Release, recipient update path), and migrate legacy
  repos into a consolidated marketplace. TRIGGER when: user says "создай
  плагин", "собери плагин", "упакуй в плагин", "новый маркетплейс", "провали
  дируй плагин", "проверь плагин", "зарелизь плагин", "выпусти версию
  плагина", "обнови маркетплейс", "перенеси плагин", "мигрируй репо",
  "make a plugin", "package as a plugin", "validate plugin", "release the
  plugin", "publish plugin version", "plugin marketplace", "migrate plugin
  repo". DO NOT TRIGGER when: creating or improving a SKILL itself — its
  content, description, evals, benchmarks (use skill-creator; this skill
  packages finished work), general git/GitHub work unrelated to plugins
  (use /github), installing third-party plugins for daily use (use /plugin).
license: Apache-2.0
allowed-tools:
  - Read
  - Grep
  - Glob
  - Edit
  - Write
  - Bash(git:*)
  - Bash(gh:*)
  - Bash(claude plugin:*)
  - Bash(python3:*)
  - Bash(ls:*)
  - Bash(mkdir:*)
---

# plugin-creator — assemble, validate, release, migrate

Companion to skill-creator: that one authors skills; this one packages finished
work into plugins/marketplaces and operates their lifecycle. Orchestration is
inline — git/gh operations are sequential and state-heavy; no subagents in v1.

## Ground rules (read before ANY mode)

1. **Never edit `~/.claude/plugins/marketplaces/<name>/`.** The background
   refresh resets it (wipes edits AND local branches; any `claude` start —
   headless included — can trigger it). Work in a dev clone (`~/<repo-name>`),
   push branches early, run `/plugin`-operations only after push.
   Details: references/pitfalls.md §1.
2. **Canon validation is `claude plugin validate`** — `scripts/preflight_plugin.py`
   is an offline house-standard guardrail on top, never a replacement.
3. **House standard** (semver, $schema, LICENSE, CI, tags, README auto-update
   block) lives in references/repo-standard.md — every mode targets it.
4. Facts about manifests/components/marketplaces: do not answer from memory —
   open the matching reference (below) or the official docs mirror.

| Question about… | Reference |
|---|---|
| plugin.json schema, userConfig, dependencies, path vars | references/manifest-reference.md |
| component types and their limits (skills/agents/hooks/MCP/LSP/…) | references/components.md |
| marketplace.json, 7 source types, hosting, managed limits, renames | references/marketplace-ops.md |
| shipping a version, validate matrix, tags, CI | references/release-checklist.md |
| field-tested traps (autoUpdate wipe, MCP prefixes, caches…) | references/pitfalls.md |
| repo layout norms, CI recipe, preflight invariants | references/repo-standard.md |

## Mode routing

| User intent | Mode |
|---|---|
| "создай/собери/упакуй плагин", new marketplace, scaffold | **Assemble** |
| "проверь/провалидируй", pre-release check, CI failed | **Validate** |
| "зарелизь/выпусти/обнови у получателей", version bump | **Release** |
| "перенеси/мигрируй/консолидируй" legacy repo | **Migrate** |

Ambiguous → ask one question with the four options.

## Assemble

Goal: existing work (skills/hooks/MCP/agents) → a repo matching repo-standard.md.

1. Interview (short): what components; one plugin or a family (monorepo
   `plugins/<name>/` is the default — repo-standard.md §layout); new repo or an
   entry in an existing marketplace; public/private.
2. Scaffold: `.claude-plugin/marketplace.json` (+`$schema`, owner, sorted
   `plugins[]`), per-plugin `.claude-plugin/plugin.json` (`$schema`, name,
   `version: 1.0.0`, description 10–2000 chars, license), LICENSE, README with
   the install line and the auto-update block (recipients have auto-update OFF
   by default), CI workflow from repo-standard.md §CI, CHANGELOG.md.
3. Move components in; check path behavior rules (manifest-reference.md §Path
   behavior: `skills` ADDS, `commands`/`agents`/`workflows` REPLACE) and the
   MCP tool-name prefix change (`mcp__plugin_<plugin>_<server>__<tool>` —
   pitfalls.md §4: fix bodies and references, not just allowed-tools).
4. Run Validate mode. Then suggest Release mode for the first tag.

## Validate

1. `python3 "{PLUGIN_ROOT}/scripts/preflight_plugin.py" <repo-root>` — offline
   house-standard invariants (version placement, $schema, LICENSE, I1–I11,
   settings.json keys, semver deps, JSON parse of .mcp.json/hooks.json,
   hooks wrapper, PLUGIN_ROOT quoting).
2. `claude plugin validate <repo-root> --strict` — the canon. Also run the
   narrower modes that apply (plugin dir, bare skills dir — the matrix in
   release-checklist.md; NB: a root `SKILL.md` is only checked when the named
   directory is literally called `skills`).
3. Runtime layer (validate ≠ loader): smoke-install into a clean env
   (`cd /tmp && claude -p` with `--plugin-dir`), invoke a sentinel skill,
   `claude plugin details <name>` for the token inventory.
4. Report findings grouped E/W with the fix per finding; do not auto-fix
   without being asked.

`{PLUGIN_ROOT}` = this plugin's root; when running from a dev clone use the
relative `scripts/` path.

## Release

Follow references/release-checklist.md top to bottom. Spine: preflight +
validate green → bump `version` in plugin.json ONLY (version = update cache
key; never duplicate it in the marketplace entry) → CHANGELOG → commit+push →
`claude plugin tag --push` (`{plugin-name}--v{version}`; needs clean tree and
consistent manifests) → `gh release create` → smoke-install → tell the user
what recipients must run (`claude plugin update <plugin>@<marketplace>` —
auto-update is off by default for third-party marketplaces). Bad release:
patch-release forward only, never force-push.

## Migrate

Importer for legacy repos into a consolidated marketplace (the executor for
marketplace-consolidation plans).

1. Inventory the source repo: `claude plugin validate`, manifest diff against
   repo-standard.md, list of installed recipients if known.
2. Plan the move: target marketplace + `plugins/<name>/` dir; if the plugin
   name changes, use the append-only `renames` map (marketplace-ops.md
   §renames; remote-source plugins will hit `plugin-cache-miss` and need a
   reinstall — say so in the release notes).
3. Execute in a dev clone; run Validate; Release in the TARGET marketplace;
   archive the source repo (README pointer + GitHub archive) only after the
   target release is live.
4. Never break existing installs silently: keep the old marketplace readable
   until recipients are notified.

## Non-goals

Skill content authoring, descriptions, evals → skill-creator. Publishing to
Anthropic's official/community catalogs → their web forms (release-checklist.md
notes). Marketplace UI walkthroughs → official docs.
