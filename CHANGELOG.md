# Changelog — jadlis-plugin-creator

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
