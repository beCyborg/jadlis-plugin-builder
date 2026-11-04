# Changelog — jadlis-plugin-builder

## [3.1.0] — 2026-11-04 — сверка с Claude Code 2.1.318, основной дом на GitHub / audit to Claude Code 2.1.318, GitHub becomes the primary home

### Для человека

- Я сверил справочники с Claude Code 2.1.318. Скилл теперь знает новые лимиты хуков, правила для мониторов и MCP-серверов, новые поля и события модов. Где документация и changelog расходятся, в справочнике стоят оба утверждения со ссылками.
- Предварительная проверка (preflight) теперь отклоняет имена маркетплейса `constructor`, `toString` и ещё пять имён из JavaScript. Claude Code такой маркетплейс не добавит.
- Основной репозиторий теперь на GitHub: https://github.com/becyb-org/jadlis-plugin-builder. Ссылка стоит в README. Команда установки не изменилась.

### For agents

- Changed: `.claude-plugin/plugin.json` version 3.0.0 → 3.1.0, `homepage`/`repository` → `https://github.com/becyb-org/jadlis-plugin-builder`. README.md / README.en.md gain a repository link after the intro (no new H2). Hub install URL stays `https://gitlab.com/beCyborg/jadlis-hub.git`.
- Added: `scripts/preflight_plugin.py` — `JS_OBJECT_MEMBER_NAMES` (`constructor`, `hasOwnProperty`, `isPrototypeOf`, `propertyIsEnumerable`, `toLocaleString`, `toString`, `valueOf`), checked case-sensitively against the original marketplace name, kept apart from the lowercased `RESERVED_MARKETPLACE_NAMES` (`plugins__marketplace-reference.md:50`). Test `test_js_object_member_marketplace_names_rejected` in `tests/test_preflight_plugin_builder.py`.
- Changed: `components.md` — monitors on Bedrock/Vertex/Foundry and with telemetry off from 2.1.310 (`plugins__components.md:588`), `allowManagedHooksOnly` blocks monitors of non-force-enabled plugins (`settings-reference.md:3583`), exit no longer asks about monitors (2.1.317), Bash hooks and `Monitor(tail *)` `if` conditions see monitor commands (2.1.314); `autoCompactWindow` vs `CLAUDE_CODE_AUTO_COMPACT_WINDOW` — docs (`sub-agents.md:1197`, no effect) and changelog 2.1.312 (lowers, never raises) both kept; fork mode text follows `sub-agents.md §Turn fork mode off` (on by default from 2.1.302, `Agent(fork)` deny); agent `disallowedTools` `mcp__reports` also withholds `reports__v2` (`sub-agents.md:494-499`, `permissions.md:581-583`); agent `name` > 256 chars → file name (`plugins__components.md:326`); subagent effort (`CLAUDE_CODE_SUBAGENT_EFFORT` 2.1.316, other-model effort 2.1.317, "Ask each time" stops subagents 2.1.318 vs `model-config.md:569`); hook concurrency — docs 12 per event (`hooks.md:398`) and changelog 2.1.312 24 per session both kept; PreCompact output cut at 10,000 chars (2.1.314); skill hooks 1,024 / 16,384 per source, a plugin = one source (`hooks.md:691`); `allowed-tools` loss under the hooks lock (2.1.304, `settings-reference.md:4168`) and for Desktop path-mounted `@inline` plugins under `allowManagedPermissionRulesOnly` (2.1.305, `settings-reference.md:819-830`); MCP `readOnlyHint`/`idempotentHint` retry (2.1.307), MCP tasks (2.1.304), `alwaysLoad` for synced plugins' stdio servers (2.1.304), `headersHelper` `CLAUDE_PLUGIN_ROOT` fix (2.1.316); `bin/` on the PATH of unsandboxed PowerShell commands; `@skills-dir` plugins silently blocked by `strictPluginOnlyCustomization` / `strictKnownMarketplaces` without `skills-dir` (`plugins__loading.md:95-102`).
- Changed: `mods.md` — validate no longer predicts where hooks run (2.1.304), the note lives in `/plugin` → Errors (`plugins__mods__admin.md:119`); with the built-in guard a user's mod can't approve past `deny`/`ask` rules or any `PreToolUse` block (`plugins__mods__admin.md:66`); guard trigger (Team/Enterprise `/login`, `CLAUDE_CODE_OAUTH_TOKEN` doesn't count) and the guard-skipped events table; `types/index.d.ts` default path; `disableSideloadFlags` also refuses SDK `addPlugins` (`plugins__org.md:185`); `§8` extended to 2.1.318 (`$.model.fork` `effort`, `prompt.submit` attachment in the user's turn, `turn.step` headless success fixes, `DISABLE_COMPACT`, `turn.step` alias, `refused:` before 2.1.307, 45% pane, `decider: "person"`, `e.isReadOnly`, `settings.read` `e.layers`, calls refused after an interrupt, VS Code drawing without feature flags) plus docs-only `plugin_notification`, `Button` `variant`/`role`, tree size limits; an older release doesn't draw a tree with new props; † dropped on `Input` `rows`.
- Changed: `mcp-patterns.md` — stdio restart rules per run mode (`mcp.md:397-405`), plugin stdio failure skipped 15 min (`errors.md:4473-4490`), 2.1.318 version-probe pinning; empty `${VAR:-default}` expands to empty (`mcp.md:861`).
- Changed: `marketplace-ops.md` — deprecated `claude-code-plugins` demo marketplace, no askpass for marketplace clones, submodule fetch only of plugin files (2.1.295), skills-dir block under managed restrictions. `release-checklist.md` — `validate --json` `advice`, custom-named marketplace file fix (2.1.318), `Version: unknown` needs ≥ 2.1.302. `manifest-reference.md §10` — Windows exec-form/PowerShell hooks keep backslashes. `pitfalls.md §14` — deny/ask rules cover `reports__v2` (corrected); `§15` concurrency per docs and changelog.
- Changed: section cites re-pointed to mirror 8f02c497 (`§Frontmatter reference`, `§Turn fork mode off`, `§Get type definitions for your version`, `` §`Text` typography props ``, `` §`Box` spacing steps ``, `hooks.md` ~902–955, `lspServers` ~line 340, `skills.md` ~289, `CLI §plugin validate` ~line 620); audit markers → 2026-11-04 (v2.1.318, mirror 8f02c497) in every reference except `repo-standard.md`.
- Unchanged: modes, other `preflight_plugin.py` behaviour, `repo-standard.md`.

## [3.0.0] — 2026-10-17 — переименование в `jadlis-plugin-builder` и сверка с Claude Code 2.1.302 / renamed to `jadlis-plugin-builder`, audit to Claude Code 2.1.302

### Для человека

- Плагин теперь называется `jadlis-plugin-builder`. Команда тоже новая: `/plugin-builder`. Старая `/plugin-creator` больше не работает.
- Новая установка: `claude plugin install jadlis-plugin-builder --marketplace https://gitlab.com/beCyborg/jadlis-hub.git`.
- Если у тебя стоял `jadlis-plugin-creator`, сначала обнови маркетплейс: `claude plugin marketplace update jadlis`. Claude Code покажет строку `Renamed to "jadlis-plugin-builder"` и сам перепишет имя в настройках.
- Ты добавил маркетплейс из git, поэтому дальше нужен один шаг руками. Выполни один раз в сессии: `/plugin install jadlis-plugin-builder@jadlis`. До этого плагин покажет ошибку `not cached`.
- Я сверил справочник по модам с Claude Code 2.1.302. Главное изменение: обработчик `.catch` у хука-охранника срабатывает только при сбое самого хука. События от собственных вызовов охранника его обходят. Ещё в справочнике новые поля и события модов с версиями, с которых они работают.
- В разделе о хуках три новых правила. Хук с фоновым процессом должен сначала вывести решение. Неверный `updatedInput` теперь отклоняет вызов. На одно событие одновременно работают не больше 12 хуков `prompt` и `agent`.
- Я исправил описание переименования: шаг `/plugin install` нужен всем, кто добавил маркетплейс из git или по ссылке. Тип источника плагина тут ни при чём.

### For agents

- Breaking: `.claude-plugin/plugin.json` — `name` `jadlis-plugin-creator` → `jadlis-plugin-builder`, version 2.2.0 → 3.0.0, `homepage`/`repository` → `https://gitlab.com/beCyborg/jadlis-plugin-builder`.
- Breaking: skill folder `skills/plugin-creator/` → `skills/plugin-builder/`, frontmatter `name: plugin-builder`; commands `/plugin-builder` and `/jadlis-plugin-builder:plugin-builder`. Trigger list keeps every RU/EN phrase and adds "plugin builder".
- Migration (recipients): the hub `jadlis` needs `"renames": {"jadlis-plugin-creator": "jadlis-plugin-builder"}` plus the renamed entry; recipients then run `claude plugin marketplace update jadlis` and once `/plugin install jadlis-plugin-builder@jadlis` (`plugins__host-marketplace.md §Migrate users with a renames map`: a git/URL marketplace reports `Plugin "<name>" not cached at <path>` until that install).
- Changed: README.md / README.en.md, `docs/img/prompts/jadlis-plugin-builder.md`, images `docs/img/{hero,how}-jadlis-plugin-builder.webp`, `tests/test_preflight_plugin_builder.py`, `evals/ru-trigger-make-plugin/*` — all on the new names. READMEs gain a rename note in the update section. `preflight_plugin.py` keeps its name; old `jadlis-plugin-creator--v*` tags stay.
- Fixed: `marketplace-ops.md §11` and SKILL.md Migrate step 2 — the post-rename `not cached` error depends on how the marketplace was added (git repo or URL), not on the plugin source type; recipient command is `/plugin install <new>@<marketplace>`. Added a rename checklist for the house marketplace.
- Changed: `mods.md` fully re-audited (mirror 934d35c9 → da8a6ce9, changelog 2.1.288–2.1.302): `.catch` runs only on throw/timeout and is skipped for events raised beneath the hook's own calls (2.1.301; mirror still documents `next.error.kind: 're-entry'`); `next.called` handler pattern and per-event refusals; transport failures fail closed (2.1.299); `deny` after the tool ran withholds the result (2.1.295); validate `gating hook without .catch` lines (2.1.290) and managed-skip note (2.1.299); `claude plugin test` changes (2.1.292, 2.1.293, 2.1.299: `part: { plugin }`, 10 s served-`$` limit); one hooks module per plugin name; Desktop 2.1.286 / VS Code 2.1.299 support; security notes on `tool.check`, `$.http.fetch`, managed-only `$.prompt.media` / `$.session.identity()`; new `§8` version table (`$.env.set` result, `Input` `rows`, `virtualText`, `prompt.change`, `agent.spawn` rewrite, `$.ui.view`, `Text` `dir`, `Text` typography with `bold` deprecated, `Box` spacing steps, `turn.start` hears subagents, `skill.prompt` fields, `session.append` `queue`, and older 2.1.288–2.1.295 additions). The #92533 worktree bug is marked fixed in 2.1.288.
- Added: `components.md §3` — hooks that start a background process (`refusing to honor the suspect capture`, `hooks.md §Hooks that start a background process`), `updatedInput` validation (2.1.300), at most 12 `prompt`/`agent` hooks of one event at a time (2.1.302), matching failures block (2.1.288), `UserPromptSubmit` before skill expansion (2.1.299), plugin `UserPromptSubmit` missing-file exit 2 is non-blocking, agent hooks honour `model` (2.1.300).
- Changed: `components.md §2` — `autoCompactWindow` is now documented (`sub-agents.md`, `plugins__components.md` plugin-agent fields; 100000–1000000, plain integer); unknown-field debug string `does not recognize or apply`; fork subagents on by default in `-p`/SDK/desktop/VS Code (2.1.302; mirror `sub-agents.md` not yet updated).
- Changed: `manifest-reference.md §2` skill-name rows now follow `skills.md §Characters a skill name can't hold` (plugin skill folders: characters become hyphens; refused frontmatter `name`; `[names]` in the debug log).
- Changed: `pitfalls.md §12` mods guard semantics; added `§15` guard hooks after 2.1.300–2.1.302. `release-checklist.md §5b` fork note for eval runs.
- Changed: audit markers → 2026-10-17 (v2.1.302, mirror da8a6ce9) in `mods.md`, `components.md`, `manifest-reference.md`, `marketplace-ops.md`, `pitfalls.md`, `release-checklist.md`; `mcp-patterns.md` and `repo-standard.md` keep 2026-10-14 (no relevant docs change).
- Unchanged: modes, `preflight_plugin.py` behaviour and its tests.

## [2.2.0] — 2026-10-14 — установка одной командой и сверка с Claude Code 2.1.300 / one-command install, audit to Claude Code 2.1.300

### Для человека

- Плагин теперь ставится одной командой: `claude plugin install jadlis-plugin-creator --marketplace https://gitlab.com/beCyborg/jadlis-hub.git`. Она сама добавляет маркетплейс и ставит плагин. Нужен Claude Code 2.1.292 или новее.
- Если Claude Code старше, работают прежние две команды. Они остались в README сразу под новой строкой.
- Справочники сверены с Claude Code 2.1.300. Скилл теперь знает новые правила: хук может блокировать действие при своём сбое (`onFailure: "block"`), MCP-сервер в `tools:` агента пишется полным именем, у имён скиллов есть запрещённые символы, у `claude plugin eval` появился `--disallow-tools`.
- Скилл советует ту же строку установки для README твоих плагинов. Если строки нет, `claude plugin validate` подскажет её сам, но проверку не провалит.
- В шаге проверочной установки была ошибка: две команды получали два разных временных конфига. Теперь обе работают с одним.

### For agents

- Added: `components.md §2` — agent `autoCompactWindow` (changelog 2.1.296; not yet in the docs mirror, plugin-agent support unconfirmed), `name` ≤ 256 chars (2.1.292), `skills` preload capped at 32 (2.1.295), MCP entries in `tools:`/`disallowedTools` match the whole server name only (2.1.299), `--debug` names unknown agent frontmatter fields (2.1.296); `§3` hooks `onFailure: "block"` for `command`/`http` hooks (2.1.295, `hooks.md §Block the action when a hook fails`), agent/permission row in the scoped-MCP-name table; `§5` LSP `requestTimeout` (2.1.288).
- Added: `manifest-reference.md §2` "Skill, command and agent names" — hidden/direction-changing/blank-like characters, `<`, `>` in skill or command file/folder names (2.1.299), 256-char `name` cap (2.1.292); `§10` LSP placeholders resolve in `initializationOptions`/`settings` (fix in 2.1.288).
- Added: `pitfalls.md §14` — MCP allow rules and agent `tools:` match one server only since 2.1.299.
- Added: `release-checklist.md §4` root-as-plugin repos validate both manifests (2.1.289), README install-line advice (2.1.295, never changes the exit code); `§5b` `--disallow-tools` and the case field `disallowed_tools` (2.1.299, checked in `claude plugin eval --help` 2.1.300), API-error runs score 0 and exit 1 (2.1.299); `§11` one-command smoke install and the settings-file warning (2.1.295).
- Added: `marketplace-ops.md §1` reserved marketplace names — JS object member names (2.1.296) and `<owner>-<repo>` download folders (2.1.290); `§12` `claude plugin install <plugin> --marketplace <source>` (2.1.292) and the settings-file warning (2.1.295).
- Changed: `repo-standard.md` item 7 — README install line is now `claude plugin install <plugin> --marketplace <url>` with the two-command pair below it as the fallback for CC < 2.1.292.
- Changed: README.md / README.en.md install sections use the one-command line, the old pair kept as the fallback.
- Fixed: `release-checklist.md §11` smoke install called `mktemp -d` twice, so `install` ran in a config dir without the marketplace.
- Changed: audit markers → 2026-10-14 (v2.1.300, mirror 305bb5ef) in every reference except `mods.md`, which this pass did not audit; `.claude-plugin/plugin.json` 2.1.1 → 2.2.0.
- Unchanged: command `/plugin-creator`, modes, `preflight_plugin.py` and its tests.

## [2.1.1] — 2026-10-08 — репозиторий переехал на GitLab / repository moved to GitLab

### Для человека

- Плагин теперь живёт на GitLab: https://gitlab.com/beCyborg/jadlis-plugin-creator. Аккаунт GitHub beCyborg заблокирован, поэтому старые ссылки открывают 404.
- Каталог ставится новой командой: `claude plugin marketplace add https://gitlab.com/beCyborg/jadlis-hub.git`. Если ты уже ставил его со старой ссылки GitHub, удали каталог командой `claude plugin marketplace remove jadlis` и поставь всё заново по README. Плагины этого каталога при удалении тоже снимутся.
- Работа плагина не изменилась.

### For agents

- Changed: every `github.com/beCyborg/*` link in README pairs now points to `gitlab.com/beCyborg/*`; `marketplace add` uses the full `https://…/jadlis-hub.git` URL (non-GitHub hosts have no `owner/repo` shorthand).
- Changed: `.claude-plugin/plugin.json` `homepage`/`repository` → GitLab; version 2.1.0 → 2.1.1.
- Changed: CI moved from `.github/workflows/ci.yml` (reusable workflow in `beCyborg/jadlis-hub`) to `.gitlab-ci.yml` including `/ci/plugin-ci.yml` from `beCyborg/jadlis-hub` on GitLab — same checks: `claude plugin validate --strict`, gitleaks full history, README parity, privacy grep.

## [2.1.0] — 2026-10-02 — моды, MCP-демоны и сверка с Claude Code 2.1.287
### Для человека
- Предварительная проверка (preflight) больше не падает на плагине-моде: `hooks/hooks.json` вида `{"modules":[...]}` считается нормальным, проверяется только, что файл модуля на месте. Код мода проверка не запускает.
- Preflight первым делом запускает `claude plugin validate` (если `claude` есть в PATH) и теперь работает и на папке одного плагина, не только на маркетплейсе.
- Новые проверки: зарезервированные имена (`cc-plugin-*`, `claude-*` и т. п.), расхождение имени в маркетплейсе и в `plugin.json`, честная проверка BOM, форма адреса источника (I4), MCP-переменные без значения по умолчанию, `${user_config}` в `headersHelper`, один и тот же адрес MCP у двух серверов, `options` в userConfig (нужен Claude Code 2.1.271+).
- Убрано ложное предупреждение про `${CLAUDE_PLUGIN_ROOT}` без кавычек в хуках exec-формы (с `args`).
- Новые главы: «какой компонент когда» (скилл, агент, хук, мод, MCP, монитор…), моды (устройство, тесты, безопасность, раздача в организации), MCP как общий демон (паттерны U / L / C и 10 проверок).
- Справочники сверены с документацией Claude Code 2.1.287: ссылки на удалённые страницы документации заменены, исправлены неверные утверждения (синхронизированные плагины грузятся и в терминале; npm-источник ставится через `npm pack --ignore-scripts`; лимит Keychain «~2 KB» не подтверждён и убран), добавлены `claude plugin eval`, `claude plugin configure`, бандлы `.mcpb`, новые поля агентов.
- Отсылки к skill-creator заменены на skill-builder.
### For agents
- Changed: `skills/plugin-creator/scripts/preflight_plugin.py` — runs `claude plugin validate` on the root and each local plugin dir (root-as-plugin: on `.claude-plugin/plugin.json`) before its own checks; `--no-validate` opts out; missing binary → one warning. Accepts a single plugin dir (no `marketplace.json`).
- Fixed: hooks.json with `modules` and no `hooks` is valid; module files must exist, stay inside the plugin, and use a mod extension. Exec-form hooks (`args`) no longer draw the unquoted-ROOT warning; monitors are checked.
- Fixed: BOM is reported (E for manifests, W for other JSON) instead of being silently accepted by `utf-8-sig`.
- Added: reserved plugin names (E) / Anthropic-looking names (W); entry name ≠ manifest name (W); I4 source URL shape; marketplace name charset and reserved names; manifest `types`; MCP checks (`${user_config.X}` declared, url option default/required, `${VAR}` without `:-default`, `headersHelper` with `${user_config}`, duplicate URL across servers of one marketplace); `userConfig.options` (W: CC ≥ 2.1.271; E: documented rule violations).
- Added: `references/mods.md`, `references/mcp-patterns.md`; `components.md §0` component-choice table; `tests/test_preflight_plugin_creator.py` (9 cases).
- Changed: all references re-pointed from the removed `plugins-reference.md` / `plugin-marketplaces.md` / `plugin-dependencies.md` / `discover-plugins.md` / `plugins.md` to the `plugins__*.md` pages; audit markers → 2026-10-02 (v2.1.287, mirror 934d35c9); `release-checklist.md` §3 real preflight command, new §5b `claude plugin eval`; agents section and release checklist point to skill-builder `references/model-routing.md` for model/effort choice.
- Unchanged: command `/plugin-creator`, modes, the JSON output shape of preflight (`errors` / `warnings`).

## [2.0.0] — 2026-09-10 — переименование в `jadlis-plugin-creator`
### Для человека
- Плагин переименован: `plugin-creator` → `jadlis-plugin-creator`. Ставится теперь строкой `claude plugin install jadlis-plugin-creator@jadlis`, маркетплейс `jadlis` добавляется с `https://github.com/beCyborg/jadlis-hub`.
- Короткая команда `/plugin-creator` не изменилась; полная форма стала `/jadlis-plugin-creator:plugin-creator`.
- Совместимости со старым именем нет: переустановите плагин (`claude plugin uninstall plugin-creator@jadlis --keep-data`, затем установка по новой строке).
### For agents
- Breaking: `.claude-plugin/plugin.json` — `name` `plugin-creator` → `jadlis-plugin-creator`, version 1.1.0 → 2.0.0; `homepage`/`repository` already pointed at `https://github.com/beCyborg/jadlis-plugin-creator`.
- Changed: README (RU + EN) — install/update/uninstall lines carry the new plugin name; marketplace source is `https://github.com/beCyborg/jadlis-hub` instead of `jadlis-start.git`.
- Changed: CI calls `beCyborg/jadlis-hub/.github/workflows/plugin-ci.yml@main` with `mode: plugin`.
- Unchanged: skill folder `skills/plugin-creator/`, frontmatter `name: plugin-creator`, the bare `/plugin-creator` command; release tags now use the `jadlis-plugin-creator--v<version>` prefix.

## [1.1.0] — 2026-09-07 — собственный репозиторий / own repository
### Для человека
- Выделен в собственный репо `jadlis-plugin-creator` (root-as-plugin), команда `/plugin-creator`, маркетплейс `jadlis`; история до 1.1.0 — в `skill-creator-plugin`.
### For agents
- Changed: layout `plugins/plugin-creator/` → root-as-plugin; skill moved to `skills/plugin-creator/SKILL.md` with `references/` and `scripts/` alongside.
- Changed: `.claude-plugin/plugin.json` — version 1.0.2 → 1.1.0, `homepage`/`repository` → `https://github.com/beCyborg/jadlis-plugin-creator`.
- Changed: install path is now `claude plugin install plugin-creator@jadlis` from `https://github.com/beCyborg/jadlis-start.git`; the command is `/plugin-creator` (single-skill plugin).
- Changed: CI calls the shared reusable workflow `beCyborg/jadlis-start/.github/workflows/plugin-ci.yml@main` with `mode: plugin`.
- Migration: reinstall from the `jadlis` marketplace; skill behaviour unchanged.
