[Русский](README.md) · English

# Build, validate and ship a plugin to the house standard

## Before → after

This section is filled in per the README contract 2026-09.

## How it works

`plugin-creator` assembles, validates, releases and migrates Claude Code plugins and marketplaces: from an empty folder to a tag and a GitHub Release. Four modes — **Assemble** (scaffold a repo to the house standard), **Validate** (offline preflight plus `claude plugin validate --strict`), **Release** (version bump, changelog, tag, release, recipient update path) and **Migrate** (move a legacy repo into a consolidated marketplace without breaking existing installs). It runs inline, with no subagents: `git` and `gh` operations are sequential and depend on working-tree state. `claude plugin validate` is the canon; `skills/plugin-creator/scripts/preflight_plugin.py` only adds offline house-standard checks on top of it.

## Install and first run

```bash
claude plugin marketplace add https://github.com/beCyborg/jadlis-start.git
claude plugin install plugin-creator@jadlis
```

First run: invoke `/plugin-creator` with a task, e.g. `/plugin-creator validate the plugin before release`.

## Limits, cost, updating

- No API keys and no paid services: it runs on the Claude Code subscription.
- Needs `git`, `gh` (authenticated) and `claude plugin` — release and smoke-install fail without them.
- It does not write or improve skill content: that is the `skill-builder` plugin's job.
- Edit the working clone only: files under `~/.claude/plugins/marketplaces/<name>/` are wiped by the background refresh.

Auto-update is off by default for third-party marketplaces:

```bash
claude plugin marketplace update jadlis
claude plugin update plugin-creator@jadlis
```

What changed between versions — [CHANGELOG.md](CHANGELOG.md). License: Apache-2.0, [LICENSE](LICENSE).
