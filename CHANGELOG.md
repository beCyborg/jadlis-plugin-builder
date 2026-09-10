# Changelog — jadlis-plugin-creator

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
