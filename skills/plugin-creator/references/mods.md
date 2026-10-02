# Mods — a plugin that runs code inside Claude Code

> Last audited against Claude Code docs: 2026-10-02 (v2.1.287, mirror 934d35c9)

A mod is a plugin whose `hooks/hooks.json` lists a hooks module under `modules`. Claude Code loads that JavaScript/TypeScript module in its own process and calls its functions on events: it can draw panes and bands, add a `/command` that runs with no model turn, rewrite tool calls, prompts and requests, and share state between hooks (`plugins__mods__overview.md`). **Mods require Claude Code v2.1.287 or later** (`plugins__mods__overview.md §Turn mods on or off`). What an older CLI does with a `hooks.json` that has only `modules` is not documented — state the minimum version in the README.

This page is what plugin-creator needs to package, validate and ship a mod. **Writing the mod's code is the job of Claude Code's built-in `plugin-authoring` skill** (`plugins__mods__create.md §Ask Claude for a mod`) — route there, do not duplicate the API here. When to pick a mod at all: `components.md §0`.

## 1. Files

| File | Required | Contents (`plugins__mods__reference.md §Files`) |
|---|---|---|
| `.claude-plugin/plugin.json` | Yes | Ordinary manifest. Mods add no required fields |
| `hooks/hooks.json` | Yes | `"modules": ["./register.js"]` — an array with one path, **relative to `hooks.json`**. May also hold classic hooks under `hooks` |
| the hooks module | Yes | ES module exporting `register(on, options)`; extension `.js .mjs .cjs .jsx .ts .mts .cts .tsx` |
| `types/index.d.ts`, named by manifest `types` | When the mod uses `$.state` or adds a namespace | `PluginState` values and namespaces |
| `*.test.ts` / `*.test.tsx` | No | Tests for `claude plugin test` |

- The `modules` key is what makes a plugin a mod. Without it `claude plugin validate` passes but prints no `hooks:` line (`plugins__mods__troubleshoot.md`).
- The classic-hook rule "hooks.json needs the outer `{"hooks": …}` wrapper" applies only to classic hooks: a mod-only `hooks.json` is `{"modules": [...]}` and is valid.
- `options` passed to `register` are the manifest's `userConfig` values with defaults filled in. A value that doesn't fit its field stops the module from loading: `options do not fit plugin.json userConfig`.
- Manifest `dependencies` also order mods: a mod runs before the plugins it depends on (`plugins__mods__events.md §The order mods run in`).
- Plugin name: `claude plugin validate` fails names that pass as Anthropic's own — `cc-plugin-*`, `claude-*`, `claude-mods`, … (`plugins__manifest-reference.md §name`). The built-in mods are themselves named `cc-plugin-*`.

### Generated files

Loading a mod from `--plugin-dir` (or one Claude wrote) writes TypeScript declarations into `.claude-plugin/types/` and, when the mod has none, a `tsconfig.json` at the mod root (`plugins__mods__create.md §Get type definitions for your version`). So for a mod, `.claude-plugin/` holds more than `plugin.json`. The docs do not say whether to commit these files; decide per repo (they describe the CLI version that wrote them).

## 2. Rules static analysis enforces

`claude plugin validate` must read every hook and API call statically, and Claude Code refuses to load a mod whose API use it can't read (`plugins__mods__create.md §Check what Claude Code reads from your mod`, `plugins__mods__admin.md`):

- Spell each call in full (`$.store.get(...)`); never assign, destructure or computed-index `$` or a namespace (`const ui = $.ui` fails).
- Event names in `on(...)` are string literals.
- Don't redeclare `on` inside `register`.
- Import only relative files inside the plugin; the one bare import is `claude-code`.
- No dynamic `import()`, no `require` — ES modules only.

preflight does not re-implement this; it runs `claude plugin validate` first and only checks that each module file exists with a mod extension. **It never executes mod code.**

## 3. Develop, validate, test

| Step | Command | Notes |
|---|---|---|
| Inner loop | `claude --plugin-dir ./my-mod` | Hot-reloads the module on save; each reload runs `register` again |
| Review what it does | `claude plugin validate ./my-mod` | Prints `hooks:`, `calls:`, and `env reads/writes`, `state reads/writes` lines — this is also the security review |
| Tests | `claude plugin test` (in the mod dir) | Runs every `*.test.ts(x)`; no session, sign-in or network; exit 1 on failure → CI-ready. Each test has 5 s unless it sets `timeoutMs` (`plugins__mods__reference.md §Limits`) |
| Can mods load here? | `claude plugin test` in a dir without a mod | `no hooks module to load` = yes; `turned off here` = `disableAllHooks` or org policy; `turned off in this process` = disabled remotely (`plugins__mods__troubleshoot.md §Check whether mods can load`) |

- Develop against the directory, not an installed copy: the cache is keyed by version, so edits reach an install only after a version bump (`plugins__mods__create.md §Share your mod`).
- Mods Claude writes for you live in `~/.claude/dev-mods/<session-id>/`.
- The README says which Claude Code version the mod was tested with — events and methods can change between releases.

## 4. Failure behaviour — a mod is a seatbelt, not a lock

- **Fail-open by default.** A hook that throws, times out, or returns the wrong shape before calling `next` is skipped and the next handler runs (`plugins__mods__events.md §Handle a hook that fails`). For a guard that must fail closed, attach `.catch(...)` returning `{ deny }` — the handler gets 1 s.
- Limits: 10 s per hook per event (excluding time in `next` and API calls), 1.5 s for all `session.end` hooks, `$.store` 4 MiB (`plugins__mods__reference.md §Limits`).
- If the hooks worker crashes three times without a single culprit, every non-built-in mod is unloaded for the session (`plugins__mods__troubleshoot.md`).
- Known bugs on 2.1.287 (from the owner's probe notes, not from the docs): the `skill.prompt` event is not delivered (anthropics/claude-code#96831), and a `tool.call` hook on Bash breaks `isolation: "worktree"` subagents (#92533).

## 5. Security

- **Mods aren't sandboxed.** A mod runs as the user, with the user's files, processes and network (`plugins__mods__admin.md`). Never install someone else's mod without reading it; read `claude plugin validate`'s `calls:` line first.
- A mod can approve a tool call that an `ask` rule would prompt for or that a `PreToolUse` hook blocked (`plugins__mods__overview.md`). It can't restyle the permission prompt.
- A mod can spend the user's usage (`$.model.complete`) and send prompts to other sessions — say so in the README when it does.

## 6. Distribution and organization control

- A mod ships like any plugin: version in `plugin.json`, marketplace entry, `claude plugin update`.
- **A mod from a GitHub, git, URL or npm source counts as a user's mod** even when managed `enabledPlugins` enables it: it is copied into the cache, runs among users' mods, and is skipped by `prependPlugins` / `appendPlugins`, `allowManagedModsOnly` and `allowManagedHooksOnly` (`plugins__mods__admin.md §Install your organization's mods and set the order`). An organization's own mod must come from a **directory marketplace on the user's machine, named by absolute path in managed settings, listing the plugin by a relative path** (loaded in place). The house "GitHub marketplace" standard therefore does not fit org policy mods.
- Admin keys (managed settings only): `allowManagedModsOnly` and `allowModsToOverrideDenyRules` are options of the built-in guard `cc-plugin-sec-default@builtin` under `pluginConfigs`; `prependPlugins` / `appendPlugins` set the order. `disableAllHooks` and `--safe-mode` stop installed mods but not built-in ones.

## 7. Checklist for a mod release

1. `claude plugin validate <mod>` — passed, and the `hooks:` line lists every event you meant.
2. `claude plugin test` — green.
3. preflight — `modules` file exists, name not reserved, `types` path valid.
4. README: minimum Claude Code version (2.1.287+), tested version, what the mod can see/change/approve, how to turn it off.
5. Release as any plugin (`release-checklist.md`).
