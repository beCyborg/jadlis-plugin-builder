# Mods — a plugin that runs code inside Claude Code

> Last audited against Claude Code docs: 2026-11-04 (v2.1.318, mirror 8f02c497)

A mod is a plugin whose `hooks/hooks.json` lists a hooks module under `modules`. Claude Code loads that JavaScript/TypeScript module in its own process and calls its functions on events: it can draw panes and bands, add a `/command` that runs with no model turn, rewrite tool calls, prompts and requests, and share state between hooks (`plugins__mods__overview.md`). **Mods need Claude Code v2.1.287 or later in the terminal; the Desktop app's bundled Claude Code runs them from v2.1.286; the VS Code extension runs their hooks and draws them from extension 2.1.299** (`plugins__mods__overview.md §Turn mods on or off`, `§Where mods run`). What an older CLI does with a `hooks.json` that has only `modules` is not documented — state the minimum version in the README, and raise it when the mod uses a newer API (§8).

This page is what plugin-builder needs to package, validate and ship a mod. **Writing the mod's code is the job of Claude Code's built-in `plugin-authoring` skill** (`plugins__mods__create.md §Ask Claude for a mod`) — route there, do not duplicate the API here. When to pick a mod at all: `components.md §0`.

## 1. Files

| File | Required | Contents (`plugins__mods__reference.md §Files`) |
|---|---|---|
| `.claude-plugin/plugin.json` | Yes | Ordinary manifest. Mods add no required fields |
| `hooks/hooks.json` | Yes | `"modules": ["./register.js"]` — an array with one path, **relative to `hooks.json`**. May also hold classic hooks under `hooks` |
| the hooks module | Yes | ES module exporting `register(on, options)`; extension `.js .mjs .cjs .jsx .ts .mts .cts .tsx` |
| `types/index.d.ts` — the default path; manifest `types` names another | When the mod uses `$.state` or adds a namespace | `PluginState` values and namespaces. Leaving `types` out of the manifest needs v2.1.299+ (`plugins__mods__reference.md:24`) |
| `*.test.ts` / `*.test.tsx` | No | Tests for `claude plugin test` |

- The `modules` key is what makes a plugin a mod. Without it `claude plugin validate` passes but prints no `hooks:` line (`plugins__mods__troubleshoot.md §validate passes and lists no hooks line`).
- The classic-hook rule "hooks.json needs the outer `{"hooks": …}` wrapper" applies only to classic hooks: a mod-only `hooks.json` is `{"modules": [...]}` and is valid.
- `options` passed to `register` are the manifest's `userConfig` values with defaults filled in. A value that doesn't fit its field stops the module from loading: `options do not fit plugin.json userConfig`.
- Manifest `dependencies` also order mods: a mod runs before the plugins it depends on (`plugins__mods__events.md §The order mods run in`).
- Plugin name: `claude plugin validate` fails names that pass as Anthropic's own — `cc-plugin-*`, `claude-*`, `claude-mods`, … (`plugins__manifest-reference.md §name`). The built-in mods are themselves named `cc-plugin-*`.
- **One hooks module per plugin name.** When two enabled plugins from different marketplaces share a manifest name, only one copy loads its hooks module (and only one registers its `hooks.json` hooks); the other gets `Its hooks module does not load` in `/plugin` → Errors (note v2.1.296+) and `another plugin of that name loads first` in the debug log (`plugins__loading.md §Hooks when two enabled plugins share a name`, `plugins__mods__troubleshoot.md §Refusal messages`). A fork of a mod needs its own name.
- A hooks-module file may nest scopes at most 2,000 deep (`code nested too deep to scan`, `plugins__mods__reference.md §Limits`). Since v2.1.309 a module nested too deep to load gets an error that names the file instead of a bare stack-overflow message (changelog.md:649; `plugins__mods__troubleshoot.md:105–116`).

### Generated files

Loading a mod from `--plugin-dir` **in an interactive session** (or one Claude wrote) writes TypeScript declarations into `.claude-plugin/types/` and, when the mod has none, a `tsconfig.json` at the mod root (`plugins__mods__create.md §Get type definitions for your version`); since v2.1.295 `-p` and SDK sessions no longer write them (changelog 2.1.295). So for a mod, `.claude-plugin/` holds more than `plugin.json`. The docs do not say whether to commit these files; decide per repo (they describe the CLI version that wrote them).

## 2. Rules static analysis enforces

`claude plugin validate` must read every hook and API call statically, and Claude Code refuses to load a mod whose API use it can't read (`plugins__mods__create.md §Check what Claude Code reads from your mod`, `plugins__mods__admin.md`):

- Spell each call in full (`$.store.get(...)`); never assign, destructure or computed-index `$` or a namespace (`const ui = $.ui` fails). `$` may be passed to a function declared at the top level of the same file, not to a method, an inner function or an imported function (`plugins__mods__create.md §Check what Claude Code reads from your mod`).
- Event names in `on(...)` are string literals.
- Don't redeclare `on` inside `register`; don't redeclare or reassign a top-level `var` that `$.state` is read through (refused since v2.1.292).
- Import only relative files inside the plugin; the one bare import is `claude-code`.
- No dynamic `import()`, no `require` — ES modules only.

preflight does not re-implement this; it runs `claude plugin validate` first and only checks that each module file exists with a mod extension. **It never executes mod code.**

## 3. Develop, validate, test

| Step | Command | Notes |
|---|---|---|
| Inner loop | `claude --plugin-dir ./my-mod` | Hot-reloads the module on save; each reload runs `register` again. A save that breaks the module keeps the previous version loaded (`reload failed, the previous version stays loaded:`) |
| Review what it does | `claude plugin validate ./my-mod` | Prints `hooks:`, `calls:`, and `env reads/writes`, `state reads/writes` lines, plus **one line per hook that can refuse an action**, such as `gating hook without .catch: tool.call` (v2.1.290+, `gatingHooks` under `--json`; `plugins__mods__create.md §Check what Claude Code reads from your mod`). Since v2.1.299 it also names hooks that are skipped where an organization manages Claude Code (changelog 2.1.299). Since v2.1.304 validate no longer predicts where the mod's hooks run (changelog.md:875); where the built-in guard skips a hook, `/plugin` says so in the plugin's details and **Errors** tab instead (v2.1.299+, §5). This is also the security review |
| Tests | `claude plugin test` (in the mod dir) | Runs every `*.test.ts(x)`; no session, sign-in or network; exit 1 on failure → CI-ready. Each test has 5 s unless it sets `timeoutMs` (`plugins__mods__reference.md §Limits`) |
| Can mods load here? | `claude plugin test` in a dir without a mod | `no hooks module to load` = yes; `turned off here` = `disableAllHooks` or org policy; `turned off in this process` = disabled remotely (`plugins__mods__troubleshoot.md §Check whether mods can load`). It does not report `allowManagedModsOnly` |

`claude plugin test` behaviour that changed (changelog):

- **v2.1.299**: every mod's `Box`/`Text` root in a `ui.render` tree carries `part: { plugin }` naming the mod — **exact-tree assertions written earlier fail until they include it**; a call to a served `$` method that hasn't answered in 10 s fails, as in a session.
- **v2.1.293**: `mock.session(on)` reads back rows added with `$.session.append` (`plugins__mods__test.md`).
- **v2.1.292**: a failed `expect` inside a hook the test registered, or a stub answer the engine refuses, fails the test instead of passing silently — older green suites can turn red after the upgrade.

- Develop against the directory, not an installed copy: the cache is keyed by version, so edits reach an install only after a version bump (`plugins__mods__create.md §Share your mod`).
- Mods Claude writes for you live in `~/.claude/dev-mods/<session-id>/` and load only in that session; copy the directory out to keep it. Since v2.1.318 Claude Code records the user's answer when it asks to turn those mods on (changelog.md:19); since v2.1.317 the built-in `plugin-authoring` skill offers once, after a mod works, to help share it (changelog.md:135).
- Since v2.1.304, when a plugin that runs first skips one of your mod's hooks, the transcript gets a line naming the event and that plugin (changelog.md:854) — check it before debugging a hook that never fires.
- The README says which Claude Code version the mod was tested with — events and methods can change between releases.

## 4. Failure behaviour — a mod is a seatbelt, not a lock

- **Fail-open by default.** A hook with no `.catch` that throws, times out, or returns the wrong shape **before calling `next`** is skipped and the next handler runs; if it fails **after `next` resolved**, that result stands and nothing runs twice (`plugins__mods__events.md §Handle a hook that fails`).
- **Fail closed with `.catch`.** `on(...)` returns a registration; `.catch(handler)` answers in the hook's place. Since v2.1.301 the handler runs **only when the hook itself throws or times out** (changelog 2.1.301). In the handler, test `next.called`: `true` → `return next(e)` (resolves to what the hook's own `next` call produced, without running the action again); `false` → return the event's refusal — `{ deny }` on `tool.call` and `config.set`, `{ drop }` on `prompt.submit`. On `tool.check` (`{ decision: 'deny', reason }`) and `plugin.register` (`{ refuse }`) a refusal after `next` still holds, so no `next.called` test is needed (`plugins__mods__events.md §Handle a hook that fails`). The handler gets 1 s; if it throws or times out too, the hook is skipped as if it had no handler — open again.
- **What a `.catch` does not cover (v2.1.301).** An event raised beneath the hook's own calls — for example a tool call, process or prompt that another mod's hook starts while your guard awaits `$.process.run` — **skips your hook without asking its `.catch`** (changelog 2.1.301; v2.1.292 had briefly made the handler answer those). So a guard never sees what its own `$` calls cause; don't build a check that depends on it. The mirror still documents `next.error.kind: 're-entry'` with `cause` `rewritten`/`lent` for that case (`plugins__mods__reference.md §The hook function`) — per the 2.1.301 changelog the handler is no longer asked, so don't branch on `re-entry` in new code.
- **Transport failures fail closed (v2.1.299).** An action a plugin hook can block is refused, not let through, when the hook can't be handed the event or can't hand back its answer; a tool that already ran has its result withheld (changelog 2.1.299).
- **`deny` after the tool ran.** On `tool.call`, `{ deny: reason }` returned after `await next(e)` withholds the result from Claude; it undoes nothing the tool did, and Claude reads `<Tool> ran, and a plugin withheld its result:` before the reason (`plugins__mods__events.md §Guard or change a tool call`; wording since v2.1.295). A `deny` after `next` on `config.set`, `state.set`, `env.set` or `agent.spawn` is reported as a failed hook, by name (v2.1.292).
- Limits (`plugins__mods__reference.md §Limits`): 10 s per hook per event, excluding time in `next` and API calls (50 ms for `prompt.edit`); `.catch` 1 s; all `session.end` hooks share the SessionEnd budget (1.5 s by default); `$.process.run` 30 s default, 10 min max; `$.store` 4 MiB; `$.http.fetch` bodies 4 MiB; a `drop`/`deny` reason 4,096 chars (cut since v2.1.292).
- If the hooks worker crashes three times without a single culprit, every non-built-in mod is unloaded for the session, organization mods included (`plugins__mods__troubleshoot.md §mods that run in the hooks worker are off for this session`); `/reload-plugins` loads them again.
- Owner's probe notes from 2.1.287 (not from the docs): the `tool.call`-on-Bash breakage of `isolation: "worktree"` subagents (#92533) is fixed in 2.1.288 ("a plugin's `tool.call` hook making Bash fail … in subagents that run in a worktree", changelog 2.1.288). The undelivered `skill.prompt` event (anthropics/claude-code#96831) has no fix entry in the changelog; 2.1.299 added fields to that event, so re-probe before relying on it.

## 5. Security

- **Mods aren't sandboxed.** A mod runs as the user, with the user's files, processes and network (`plugins__mods__admin.md`); a process a mod starts runs outside the Bash sandbox even when sandboxing is on (`plugins__mods__overview.md §Try a sample mod`). Never install someone else's mod without reading it; read `claude plugin validate`'s `calls:` line first.
- A mod's `tool.check` hook can approve a call. **Where the built-in guard loads**, a user's mod by default **can't** approve a call that a `deny` rule refuses or an `ask` rule prompts for, whichever settings file holds the rule, nor a call that **any** `PreToolUse` hook blocked (`plugins__mods__admin.md §Know what happens by default`, :66; `permissions.md §Precedence among rules, hooks, and mods`, :631–637); `allowModsToOverrideDenyRules` lifts only the deny part (`plugins__mods__admin.md:78`). Without the guard the mod can approve a call that a `deny` rule refuses or a `PreToolUse` hook blocked, and the user isn't prompted for one an `ask` rule would prompt for (`permissions.md:639–641`). In plan mode it can only tighten the decision for a call that isn't read-only (`plugins__mods__events.md §Approve or refuse a tool call before the user is asked`, :220). None of this covers the mod's own `$.fs` / `$.process` calls (`plugins__mods__admin.md:68`). It can't restyle the permission prompt.
- **When the built-in guard loads** (`plugins__mods__admin.md:58–63`): the machine has managed settings, or the session runs on `/login` credentials for a Team or Enterprise plan. A session on an API key, Bedrock, Agent Platform or Foundry gets it only with managed settings, and a session on a long-lived `CLAUDE_CODE_OAUTH_TOKEN` doesn't count as that login even when a Team or Enterprise login is stored. Test a gating mod both with and without the guard.
- **Hooks the guard skips.** Where the guard loads, a user's mod's hooks on these events never run: `classic.<Event>`, `prompt.compose`, `prompt.section`, `prompt.context`, `prompt.attachment`, `skill.prompt`, `attribution.text`, `session.compact`, `settings.read`, and `session.append` for `door` `attachment`, `hook-context` and `compaction` (`plugins__mods__admin.md §Know which hooks of a user's mod don't run`, :98–116). `/plugin` notes it in the plugin's details and the **Errors** tab (v2.1.299+, :119). A mod built on these events works there only as the organization's own mod (§6) or with the guard removed from `prependPlugins`.
- `$.http.fetch` is not stopped by a `WebFetch` deny rule or `CLAUDE_CODE_DISABLE_WEB_FETCH`; `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` stops only built-in mods and requests that carry the session's Anthropic credentials; an org policy that disallows WebFetch refuses every mod's request (`plugins__mods__admin.md §Know which controls still apply`).
- A mod can spend the user's usage (`$.model.complete`) and send prompts to other sessions, subagents and teammates (`$.session.send`) — say so in the README when it does.
- Managed-only APIs (v2.1.299): `$.prompt.media` (bytes of an attached image/document in `prompt.submit`) and `$.session.identity()` (sign-in kind, organization, email) work only for a mod installed by managed settings (changelog 2.1.299; not yet in the mirror). A user-installed mod can't rely on them.

## 6. Distribution and organization control

- A mod ships like any plugin: version in `plugin.json`, marketplace entry, `claude plugin update`. The docs list four routes: a directory or `.zip` for a few people, your own marketplace for a team, managed settings for an organization, a public marketplace or Anthropic's directory for anyone (`plugins__mods__create.md §Share your mod`).
- **A mod from a GitHub, git, URL or npm source counts as a user's mod** even when managed `enabledPlugins` enables it: it is copied into the cache, runs among users' mods, and is skipped by `prependPlugins` / `appendPlugins`, refused by `allowManagedModsOnly`, and kept from loading by `allowManagedHooksOnly` (`plugins__mods__admin.md §Install your organization's mods and set the order`). An organization's own mod must come from a **directory marketplace on the user's machine, named by absolute path in managed settings, listing the plugin by a relative path** (loaded in place). The house "git marketplace" standard therefore does not fit org policy mods.
- Admin keys (managed settings only): `allowManagedModsOnly` and `allowModsToOverrideDenyRules` are options of the built-in guard under `pluginConfigs` keyed exactly `cc-plugin-sec-default@builtin`; `prependPlugins` / `appendPlugins` set the order; `disableSideloadFlags` rejects `--plugin-dir` / `--plugin-url` and mods Claude writes in a session (`plugins__mods__admin.md §Allow only your organization's mods`), as well as the Agent SDK `plugins` option, `CLAUDE_CODE_PLUGIN_DIRS` folders and plugin folders an SDK application adds mid-session with `addPlugins` (`plugins__org.md:185`). `disableAllHooks` and `allowManagedModsOnly` stop the mod but **leave the rest of its plugin loaded** — skills, agents, MCP servers keep working (`plugins__mods__overview.md §Turn mods on or off`). `disableAllHooks` and `--safe-mode` stop installed mods but not built-in ones.

## 7. Checklist for a mod release

1. `claude plugin validate <mod>` — passed; the `hooks:` line lists every event you meant; every `gating hook without .catch` line is either fixed with a `.catch` or a deliberate fail-open guard named in the README.
2. `claude plugin test` — green on the CLI version you state (exact-tree tests include `part: { plugin }` on 2.1.299+).
3. preflight — `modules` file exists, name not reserved, `types` path valid.
4. README: minimum Claude Code version (2.1.287+, higher when §8 applies), tested version, what the mod can see/change/approve, which guards fail open, how to turn it off.
5. Release as any plugin (`release-checklist.md`).

## 8. API changes 2.1.288 – 2.1.318 that change what you ship

From the changelog; rows marked † are not yet in the docs mirror 8f02c497. The docs state for the 2.1.299 `Text` props and `Box` step names that on an earlier release a tree that uses them **doesn't draw** (`plugins__mods__reference.md §`Text` typography props`, :364, :370; `§`Box` spacing steps`, :351). Assume the same for other new props and events, and make the newest row a mod uses its README minimum.

| Version | Change | What it means for the author |
|---|---|---|
| 2.1.318 | `$.model.fork` takes an `effort` option; the result reports the effort sent † (changelog.md:21) | A side job can run at `low` whatever the session's effort; min version 2.1.318 if used |
| 2.1.318 | What a mod attaches at `prompt.submit` stays in the user's turn instead of going out as a system message † (changelog.md:37) | Claude reads the attachment as part of the user's message — word it that way |
| 2.1.318 | A `turn.step` hook no longer makes a stopped reply, or one an API error cut off, finish as a success in `claude -p` / SDK runs (changelog.md:78, :98) | On older releases a headless run of a mod that hooks `turn.step` can report false success |
| 2.1.311 | `DISABLE_COMPACT` set through `$.env.set` (or a settings file) can only turn compaction off, not back on (changelog.md:498) | A mod can't re-enable compaction |
| 2.1.309 | A `turn.step` `model` given as an alias such as `haiku` resolves; before, every request failed with a model error (changelog.md:691; `plugins__mods__events.md:318`) | Use a full model id to support older releases |
| 2.1.307 | A `ui.render (<site>) refused:` line now means a size limit; before 2.1.307 it reported any tree that didn't validate (`plugins__mods__troubleshoot.md:249`, :257) | On older releases fix whatever the reason names |
| 2.1.305 | A docked pane stays within 45% of the terminal's width, also when the width was kept from a wider terminal (changelog.md:810; `plugins__mods__interface.md:309`, :553) | Design a side pane for ≤ 45% |
| 2.1.304 | `decider: "person"` on a `tool.check` answer: only the permission dialog or a host's callback can approve the ask; where nobody can be asked it is refused with the mod's reason † (changelog.md:855) | Use it for asks a mod must never auto-approve |
| 2.1.304 | `e.isReadOnly` on `tool.check` — `true` when the tool reports the call read-only, otherwise absent (changelog.md:856; `plugins__mods__reference.md:71–75`) | Filter with `isReadOnly: true` in the matcher; `isReadOnly: false` in a matcher means the hook never runs (`plugins__mods__events.md:248–249`) |
| 2.1.304 | `settings.read` hooks receive each settings layer in `e.layers` and rewrite the merged settings; the event also fires on Claude Code's own read (changelog.md:867; `plugins__mods__events.md:332–341`). `$.settings.read({ key })` / `({ key, source })` read one key (`plugins__mods__api.md:439–446`) | A managed mod can make an organization setting a ceiling; the guard skips a user mod's `settings.read` (§5) |
| 2.1.304 | After the user interrupts a turn, calls that start new work are refused with `the session was stopped and nobody has sent input since` until the next input (`plugins__mods__api.md §Calls and background work after the user interrupts a turn`, :261–265) | Retry from `turn.complete`; apart from `$.prompt.submit` and `$.command.run` this handling needs 2.1.304 |
| 2.1.304 | VS Code draws mods in sessions that don't fetch feature flags (Bedrock, Vertex, Foundry, an LLM gateway, telemetry off) from extension 2.1.304 (changelog.md:861; `plugins__mods__overview.md:194`) | Older extensions draw nothing there |
| 2.1.304 | `claude plugin validate` stops predicting where hooks run (changelog.md:875) | §3 |
| 2.1.301 | `.catch` runs only on throw/timeout; events beneath the hook's own calls skip it | Guards don't see effects of their own `$` calls (§4) |
| 2.1.301 | `$.env.set` resolves `{}` once set/unset, or `{ deny }` saying why † | Check the result; a refused write no longer looks like success |
| 2.1.301 | `rows` on `Input` — a multi-line field in the terminal (Enter submits, Shift+Enter / `\`+Enter = new line); VS Code ignores it (`plugins__mods__reference.md:280`, :315) | Min version 2.1.301 if used |
| 2.1.301 | A tree above the question dialog holds Markdown and up to 48 rows in VS Code / desktop / mobile; the terminal keeps 12 plain rows | Design for the 12-row terminal case |
| 2.1.300 | `virtualText` in prompt decorations — drawn in the prompt box, never enters the draft † | Min version 2.1.300 |
| 2.1.300 | New event `prompt.change` — box text changed without a typed edit (history recall, clear, undo, a plugin's fill) † | Hook it next to `prompt.edit` if you mirror the draft |
| 2.1.300 | `agent.spawn` can rewrite a workflow agent's `prompt` and `model` (before: refuse only) † | Spawn guards now see rewrites from other mods too |
| 2.1.300 | `$.ui.view({ agentId })` shows an agent's transcript in the main view; `$.ui.view({})` goes back † | Min version 2.1.300 |
| 2.1.300 | `dir` on `Text` for right-to-left text † | Min version 2.1.300 |
| 2.1.299 | `Text` `size`, `weight`, `mono`, `tabular`; **`bold` deprecated** → `weight: 'semibold'` | Older CLIs don't draw a tree that sets them — min version 2.1.299 (`plugins__mods__reference.md §`Text` typography props`, :364) |
| 2.1.299 | `Box` spacing steps `xs`…`xl` for `gap` / `padding` / `margin` | Same min-version rule (`plugins__mods__reference.md §`Box` spacing steps`, :351) |
| 2.1.299 | **`turn.start` also hears subagents' and teammates' turns**; `e.agentId` is absent on the main loop | A main-loop-only hook must filter on `e.agentId`, or it now fires per subagent |
| 2.1.299 | `skill.prompt` receives `e.source`, `e.pluginName`, `e.path`, `e.frontmatter`, `e.frontmatterProblem` | `plugins__mods__reference.md §Source and frontmatter fields on skill.prompt` |
| 2.1.299 | `session.append` gets a `queue` door — transcript queue records may differ from the prompt as sent † | |
| 2.1.299 | `$.prompt.media`, `$.session.identity()` — managed-installed mods only † | §5 |
| 2.1.299 | `claude plugin test`: `part: { plugin }` on render roots; 10 s limit on served `$` methods | §3 |
| 2.1.295 | `$.ui.notify` (native notification); `Button` children (strings, `Text`) | |
| 2.1.293 | `isDeferred` on `$.tool.register` (`false` = schema in the prompt from the start); `mock.session` | |
| 2.1.292 | `prompt.autocomplete` event; prompt caching in `$.model.complete` (`cache: true` on a block); `agent.spawn` sees workflow agents | |
| 2.1.290 | `turn.step` result `serverToolUses` (API-side tool calls such as the advisor — no `tool.call`/`tool.check` fires for them); `ceiling` on `tool.check`; `agentId` on `tool.check` | |
| 2.1.289 | `agent.spawn` for teammates; one agent id across plugin hook events | |
| 2.1.288 | `$.ui.selection()` (last fullscreen selection) | |

Documented in the mirror without a changelog version — check before relying on them:

- `$.ui.notify` runs the user's `Notification` hooks with type `plugin_notification`; the hook's `title` is the mod's name unless the mod set one (`hooks.md:297`, :2491; `plugins__mods__api.md:231`).
- `Button` `variant` (`primary` | `secondary`) and `role` (`dismiss`); any other value throws, and the VS Code extension ignores both (`plugins__mods__reference.md:293–294`, :313).
- Tree size limits: the first 100,000 characters of text are drawn; at most 32 levels below the root, 20,000 elements and text children, 262,144 `Raster` cells and 2 MiB of `Image` bytes per tree — a tree over a limit isn't drawn (`plugins__mods__reference.md §Limits`, :374, :390–396).
