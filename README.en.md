[Русский](README.md) · English

# plugin-creator

A Claude Code plugin that assembles, validates, releases and migrates other plugins and marketplaces: from an empty folder to a tag and a GitHub Release.

## Why

A finished skill is not yet a tool: while it sits in a personal folder, nobody can install it with one command or update it later. Hand-packaging repeats the same mistakes every time — a version stored in two places, a missing `$schema`, a tag with no release, an edit inside the marketplace cache that the background refresh wipes.

The plugin covers four modes: **Assemble** (scaffold a repo to the house standard), **Validate** (check before shipping), **Release** (ship a version), **Migrate** (move a legacy repo into a shared marketplace).

## What it looks like

Everything runs inline, without subagents: `git` and `gh` operations are sequential and depend on the state of the working tree.

<details>
<summary>Synthetic example: Validate before a release</summary>

```
> /plugin-creator:plugin-creator check the plugin before release

1/3 preflight (offline, house-standard invariants)
    ✔ version only in plugin.json      ✔ $schema in both manifests
    ✔ LICENSE present                  ✔ hooks.json parses
    ⚠ README has no update block

2/3 claude plugin validate --strict
    ✔ manifest ok    ✔ skills 2    ✔ marketplace ok

3/3 smoke-install into a throwaway environment
    ✔ skill visible as /demo-plugin:demo

Result: 0 errors, 1 warning.
Fix: add an “Update” block with the claude plugin update command to the README.
```

</details>

## Install

The main path goes through the `jadlis` hub. Paste this block to your agent:

> You are an installer. Do exactly these steps and nothing more:
> 1. Bash: `claude plugin marketplace add https://github.com/beCyborg/jadlis-plugins.git`
> 2. Bash: `claude plugin install plugin-creator@jadlis`
> 3. Bash: `claude plugin list`
> 4. Tell me: did `plugin-creator` appear in the list, and at which version.

By hand — the same commands:

```bash
claude plugin marketplace add https://github.com/beCyborg/jadlis-plugins.git
claude plugin install plugin-creator@jadlis
```

Alternative — this repository's own marketplace, no hub:

```bash
claude plugin marketplace add https://github.com/beCyborg/skill-creator-plugin.git
claude plugin install plugin-creator@skill-creator-plugin
```

## Usage

Three scenarios, as commands:

1. Package finished work: `/plugin-creator:plugin-creator package ~/skills/<name> as a plugin` — short interview, repo scaffold, components moved in, validation.
2. Check before shipping: `/plugin-creator:plugin-creator validate the plugin` — offline preflight, `claude plugin validate --strict`, smoke-install, findings split into errors and warnings.
3. Ship a version: `/plugin-creator:plugin-creator release the plugin` — bump `version` in `plugin.json`, changelog entry, commit, `<plugin>--v<version>` tag, GitHub Release, and the update command recipients must run.

A fourth mode — `/plugin-creator:plugin-creator migrate this repo into the marketplace` — moves a legacy repo into a shared marketplace without breaking existing installs.

## Limits and cost

- No API keys and no paid services: it runs on the Claude Code subscription.
- Requires `git`, an authenticated `gh`, and `claude plugin` — release and smoke-install fail without them.
- It does not write or improve skill content: that is `skill-creator`'s job.
- `claude plugin validate` is the canon; `scripts/preflight_plugin.py` only adds offline house-standard checks on top.
- Edit the dev clone only: files under `~/.claude/plugins/marketplaces/<name>/` are wiped by the background refresh.

## Update

Third-party marketplaces have auto-update off by default:

```bash
claude plugin update plugin-creator@jadlis
```

What changed between versions: [CHANGELOG.md](CHANGELOG.md).

## License

Apache-2.0, [LICENSE](../../LICENSE). The repository's companion plugin: [skill-creator](../../README.en.md).
