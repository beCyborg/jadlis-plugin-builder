# Plugin Release Checklist

> Last audited against Claude Code docs: 2026-10-17 (v2.1.302, mirror da8a6ce9)

Ordered checklist for shipping a version of a plugin or a marketplace. Canon shorthands for the docs mirror: `CLI` = `plugins__cli-reference.md`, `D` = `plugins__dependencies.md`, `T` = `plugins__troubleshooting.md`, `PE` = `plugin-evals.md`, followed by the section heading. Steps 4–9 are the ones that silently ship nothing when skipped.

## Rule 0 — where you are allowed to edit

**Never edit inside `~/.claude/plugins/marketplaces/<name>/`.** That clone is owned by the background marketplace refresh, which resets it to origin and has been observed deleting a local *branch*, not just uncommitted changes. Any `claude` start can trigger the refresh, **including headless `claude -p`** — so a parallel agent session is enough to lose work.

- Keep a **dev clone** somewhere else (`~/<plugin>-plugin`) and do all editing there.
- Push the working branch early; treat an unpushed commit as at risk.
- Run **no `/plugin` or `claude plugin` mutation before the push** — install, update, and marketplace refresh all read from origin, so pre-push runs test the old code and can wipe the new.

## 1. Confirm the docs mirror is fresh

```bash
git -C ~/.claude-code-docs log -1 --format=%cs
```

Skim `changelog.md` for releases newer than the audit markers in your references, and update any `> Last audited …` line you touch. Doc-derived claims carry version gates (`v2.1.233+`, `v2.1.239+`, …); a stale gate is a bug report from a user on an older CLI.

## 2. Make the content changes

In the dev clone only (Rule 0). Keep component files at the **plugin root** — only `plugin.json` (and `marketplace.json`, when the repo is also the marketplace) belong in `.claude-plugin/` (a mod's generated `.claude-plugin/types/` is the exception — `mods.md §1`).

Agents or skills that set `model:` / `effort:` — model/effort choice: see skill-builder `references/model-routing.md`.

## 3. Offline preflight

Run the local guardrail before invoking the CLI — it catches the cheap mistakes without a Claude Code process:

```bash
python3 "{PLUGIN_ROOT}/scripts/preflight_plugin.py" <repo-root>    # {PLUGIN_ROOT} = plugin-builder's skill dir; add --json for CI
```

It runs `claude plugin validate` on the root and on every local plugin dir first (skipped with a warning when `claude` isn't on PATH; `--no-validate` skips it on purpose), then the house checks listed in `repo-standard.md §preflight_plugin.py invariants`: manifests without a **UTF-8 BOM** (before v2.1.246 a BOM in `plugin.json` failed the install), reserved plugin names, entry name = manifest name, version in exactly one place, `hooks.json` wrapper or mod `modules`, MCP variable and endpoint checks. It accepts a marketplace repo or a single plugin directory. Preflight is an authoring guardrail; `claude plugin validate` is the canon.

## 4. `claude plugin validate` — every mode that applies

One run does **not** cover everything. Pick the rows that match your layout (`CLI §plugin validate`); the rows for directories without a manifest require **v2.1.233+**.

| To check | Run | Covered |
|---|---|---|
| Marketplace catalog | `claude plugin validate .` (from the marketplace root) | schema, **duplicate plugin names**, `source` path traversal, and — per entry with a local `source` — that plugin's own `plugin.json`, with a warning when the entry's `version` disagrees. Findings prefixed `plugins[2] plugin.json →`. Since v2.1.196 this also covers `source: "."`, works when `marketplace.json` sits outside `.claude-plugin/`, and reports entry problems even when the file has schema errors. **It never opens the plugins' skill/agent/command/hook files.** |
| A plugin with a `plugin.json` | `claude plugin validate ./plugins/my-plugin` | `plugin.json`, `hooks/hooks.json` (for a mod also the module's `hooks:` / `calls:` inventory), MCP server entries (v2.1.281+), and the `skills`, `agents`, `commands` directories **at the plugin root** |
| A root-as-plugin repo (`.claude-plugin/` holds both `marketplace.json` and `plugin.json`) | `claude plugin validate .` | the marketplace **and** the plugin's manifest and component files — **v2.1.289+**; earlier versions skipped the plugin (`CLI §plugin validate`, ~line 612; changelog 2.1.289) |
| A mod's tests | `claude plugin test` (in the mod dir) | every `*.test.ts(x)`; exit 1 on failure, no session or network (`mods.md §3`) |
| A plugin with no manifest yet, or one component directory | `claude plugin validate ./my-plugin/agents` | every skill/agent/command file in that directory — the way to catch unparseable frontmatter |
| A plugin whose skill is a root `SKILL.md` | `claude plugin validate ./skills` (name the holding dir) | each folder's root `SKILL.md`. The holding directory must literally be named `skills`; under any other name (`plugins/`) **no run checks it** |
| A project / your user dirs | `claude plugin validate .claude` or `~/.claude` | `skills`, `agents`, and `commands` under it |

**Symlinks are not followed.** A linked `skills`/`agents`/`commands` directory warns that nothing in it was read; a linked entry inside one is skipped with a per-directory count; naming a symlinked directory (or one whose parent `.claude` is a symlink) is an **error** — name the real directory. A plugin whose `skills/` links to a sibling plugin's skills passes with warnings; validate the sibling separately.

**Reading the result**: a clean run ends `✔ Validation passed`, or `✔ Validation passed with warnings`. Add `--strict` in CI — it turns **all** warnings into errors, including the Claude Desktop name checks. Typical findings:

- `No manifest found in directory` — no `plugin.json`/`marketplace.json` and no component files under the probed paths. Name the `skills`/`agents`/`commands` directory instead.
- `YAML frontmatter failed to parse: …` — until fixed, a session reads **no** frontmatter fields from that file.
- `Invalid JSON syntax: …` on `hooks/hooks.json` — reported only in a plugin run; a session loads the plugin without those hooks.
- `Duplicate plugin name "x" found in marketplace`, `plugins[0].source: Path contains ".."`, `… cannot contain control or bidirectional-formatting characters` (the last check added v2.1.247).
- Warnings worth heeding: `Plugin name "x" is not kebab-case` and the Claude Desktop name rules (≤128 chars of letters, digits, `.`, `_`, `-`, starting alphanumeric; `org`/`org-provisioned`/`unknown` are reserved there) — Claude Code accepts these names, but claude.ai / Claude Desktop managed sync rejects the marketplace or silently drops the entry. A root `CLAUDE.md` also warns: it is not loaded as context.
- For paths set through component path fields, only **existence** and containment are checked — the files are never read (`outputStyles`, `themes`, `monitors`, `lspServers` paths only since v2.1.283). `.lsp.json` is not read by validate at all.
- **README install-line advice** (v2.1.295+, changelog 2.1.295): when a plugin's README has no install line, validate prints the line to paste. It is advice only — it **never changes the exit code, even with `--strict`**, so CI stays green either way; fix the README by hand (house format: `repo-standard.md` item 7).

## 5. `claude plugin details` — token inventory

```bash
claude plugin details <plugin>@<marketplace>
```

Shows the component inventory (Skills — including `commands/` entries — Agents, Hooks, MCP, LSP) and two cost figures: **always-on** tokens added to every session by listing text, and **on-invoke** per component. The always-on total comes from the `count_tokens` API for the active model (character-estimate fallback when unreachable); per-component numbers are scaled from it. Check this before shipping anything that grows the roster — always-on cost is paid by every user in every session.

## 5b. `claude plugin eval` — behaviour, when the plugin has a suite

```bash
claude plugin eval . --trust-plugin --model <pinned model id> --judge-model <pinned model id> --max-cost-usd <ceiling> --json results.json
```

Requires v2.1.269+ (and git 2.31+ when git is installed). Every run and judge call is billed to the account, so set a ceiling. Pin `--model`/`--judge-model` so a model rollout isn't read as a regression; `--threshold` (default 1.0) sets the pass score; add `evals/results/` to `.gitignore`. A suite lives in `evals/` (or the manifest's `experimental.evals`); `claude plugin eval init` drafts one (`PE §Run evals in CI`). Evals for one skill's wording/triggering → skill-builder; `claude plugin eval` and skill-creator-style `evals/evals.json` don't read each other's files (`PE`).

**Keeping built-in tools out of a run** (v2.1.299+, changelog 2.1.299; confirmed in `claude plugin eval --help` on 2.1.300 — not yet in `PE`): `--disallow-tools <tools...>` removes built-in tools from Claude in every case, even if granted (e.g. `--disallow-tools Agent TaskStop`); the per-case field `disallowed_tools` (a list, next to `allowed_tools` in `prompt.md` frontmatter or `case.yaml`) does the same for one case, and the two lists are combined. Only built-in tools are accepted — any other name fails the case with `… cannot be disallowed: it is not a built-in tool` (strings in the 2.1.300 binary). Use it when a skill must be scored without delegating to subagents. Since v2.1.302 fork subagents are on by default in `claude -p` and the SDK too (changelog 2.1.302), so a run can fork the conversation where it used to answer inline; add `Agent` to `--disallow-tools`, or set `CLAUDE_CODE_FORK_SUBAGENT=0` in the run's environment, when the score must not depend on that (`components.md §2`).

**API errors now fail the suite** (v2.1.299+, `PE §"ended on an API error and scored 0 without grading"`): a run that ends on an API error scores 0 without grading and makes the command exit 1. Before v2.1.299 such a run was graded on what it had produced, so an older green result can hide refused runs.

## 6. Bump `version` — the step that decides whether anyone gets the release

**The version is the cache key.** If the resolved version matches what a user has, `/plugin update` and auto-update skip the plugin entirely: editing a `SKILL.md` without bumping ships nothing.

- Set `version` in **exactly one place**. When both `plugin.json` and the marketplace entry declare it, **`plugin.json` wins silently**, so a stale manifest masks the catalog value.
- Omitting `version` everywhere falls back to the commit SHA (or an archive digest) — every push ships. That's the right choice for internal, actively developed plugins; explicit versions are for published release cycles.
- **Exception**: a `command` source is never pinned by `version` — its version always includes a 12-character hash of the produced directory, and the marketplace entry's `version` is ignored.
- For `archive` sources, a rebuilt zip needs a bumped `version` too when one is declared, otherwise users keep the cached copy despite a new digest.

## 7. CHANGELOG

One entry per released version, newest first: what changed, and any user-visible migration (renamed skill or command, a new `userConfig` option, a raised minimum Claude Code version). Anything that requires action from a recipient belongs here **and** in the release notes of step 10.

## 8. Commit and push

Conventional commit, English message, no unrelated files. Push before touching any `/plugin` command (Rule 0).

## 9. Tag the release

```bash
claude plugin tag --push          # from the plugin directory; --dry-run first
```

Convention: **`{plugin-name}--v{version}`**, where the version matches that commit's `plugin.json`. Without such tags, semver dependency constraints cannot resolve (`no-matching-tag`) — so tag whenever anything may depend on this plugin (`D §Release a plugin that others depend on`).

Preconditions the command enforces before creating the tag: the plugin contents validate, `plugin.json` and the marketplace entry **agree on the version**, the working tree under the plugin directory is **clean**, and the tag does not already exist. Options: `--push` (to `origin`; `--remote` for another), `--dry-run`, `-f/--force` (dirty tree or existing tag), `-m` with `%s` as the version placeholder. If the push fails the tag still exists locally and the command exits non-zero. Tags are read from the repository hosting the plugin — or the marketplace repository for a relative-path plugin (local-folder marketplaces need **v2.1.196+**). `git tag <name>--v<version>` by hand is equivalent if you keep the two versions in sync yourself.

## 10. GitHub release

```bash
gh release create <plugin>--v<version> --title "…" --notes-file <changelog excerpt>
```

Only after the tag is pushed. Notes = the CHANGELOG entry plus the upgrade command from step 12.

## 11. Smoke-install in a clean environment

**A green validator is not a green load.** `claude plugin validate` checks schema and frontmatter parsing; it never starts an MCP server, never runs a hook, and never reads files behind component path fields. Prove the release actually loads:

```bash
CFG=$(mktemp -d)
CLAUDE_CONFIG_DIR=$CFG claude plugin install <plugin> --marketplace <owner>/<repo-or-url>   # v2.1.292+
# older CLI: CLAUDE_CONFIG_DIR=$CFG claude plugin marketplace add <owner>/<repo>
#            CLAUDE_CONFIG_DIR=$CFG claude plugin install <plugin>@<marketplace>
```

Use **one** config dir for both steps (two separate `mktemp -d` calls install into a directory that has no marketplace). The one-command form is the same line recipients get from the README (`repo-standard.md` item 7), so the smoke test also proves that line. Since v2.1.295 `install`, `enable`, `disable` and `marketplace add` print a **warning when the settings file they write to does not load** (changelog 2.1.295) — in a smoke run treat that warning as a failure and fix the settings file before trusting the result.

Then, in a session against that config dir: invoke a **sentinel skill** (a cheap, deterministic skill of the plugin) by its namespaced name `/<plugin>:<skill>` and confirm the output; check `claude plugin list --json` has no `errors` field on your plugin; and run `claude --debug` to see plugin load, skill/agent/hook registration, and MCP init. Faster inner loop during development: `claude --plugin-dir ./my-plugin` (accepts a `.zip`, repeatable, and since v2.1.265 a folder of plugins; a local copy overrides an installed plugin of the same name except where managed settings force the state) plus `/reload-plugins`.

## 12. Tell the recipients

**Auto-update is disabled by default for third-party and local marketplaces** — only official Anthropic marketplaces default to on. Nobody receives this release until they run:

```bash
claude plugin marketplace update <marketplace> && claude plugin update <plugin>@<marketplace>
```

Keep that line in the README and repeat it in the release notes. Point users at `/plugin → Marketplaces → Enable auto-update` for the one-time fix; org admins can set `"autoUpdate": true` on the `extraKnownMarketplaces` entry in managed settings.

## CI: the official validate-plugins action

*(verified against live anthropics repos, 2026-09-01)* Anthropic ships a composite action at **`anthropics/claude-plugins-community/.github/actions/validate-plugins`**. It runs **headless and needs no `ANTHROPIC_API_KEY`** — it installs `@anthropic-ai/claude-code` from npm and runs `claude plugin validate`, then a set of catalog invariants **I1–I11**:

- `plugins[]` sorted by `name`, and no duplicate names
- `description` length between **10 and 2000** characters
- `source` URLs well-formed; external `source`s pinned to a **full 40-hex SHA**
- no shell metacharacters and no hidden/invisible Unicode anywhere in the entry
- `name` matching `^[a-z0-9][a-z0-9-]{1,63}$`

*(verified against live anthropics repos, 2026-09-01)* **Pin both the action SHA and the `claude-cli-version` input.** An unpinned action is an unreviewed executable in your release path, and an unpinned CLI turns a Claude Code release into a surprise CI break — or a surprise pass.

Also *(verified against live anthropics repos, 2026-09-01)*: **the validator is not the loader.** These invariants and `claude plugin validate` can both be green while the plugin fails to load in a session. Add to CI, after the action: `scripts/preflight_plugin.py` (it covers JSON parse, `.lsp.json` and mods, which validate skips or reads only partly — validate itself checks MCP entries since v2.1.281), and the step-11 smoke install against a throwaway `CLAUDE_CONFIG_DIR` with one sentinel skill invocation.

## Debugging a failed release

`claude --debug` prints plugin loading, manifest errors, skill/agent/hook registration, and MCP initialization. `claude plugin list --json` exposes an `errors` field on plugins that failed (absent when clean) — the programmatic check for dependency errors `dependency-unsatisfied`, `range-conflict`, `dependency-version-unsatisfied`, `no-matching-tag` (`T §Plugin installed but not working`). Common causes:

| Symptom | Cause | Fix |
|---|---|---|
| Plugin not loading | invalid `plugin.json` (or a BOM, pre-v2.1.246) | `claude plugin validate ./my-plugin` |
| Skills not appearing | wrong structure | `skills/` at the plugin **root**, not inside `.claude-plugin/` |
| Hook not firing | script not executable / wrong event name | `chmod +x`, check the shebang, quote `"${CLAUDE_PLUGIN_ROOT}"`, verify the case-sensitive event name and matcher |
| MCP server fails | missing `${CLAUDE_PLUGIN_ROOT}` | use the variable for every plugin path; `claude --debug` shows init errors |
| `path escapes plugin directory` | absolute or `../` path | relative, starting `./` (the `skills` field also accepts `"."`, v2.1.221+) |
| `conflicting manifests: both plugin.json and marketplace entry specify components` | `strict: false` with components in both | remove the duplicates, or drop `strict: false` |
| Files missing after install | referenced outside the plugin dir | plugins are **copied** to the cache; keep everything inside the plugin root |
