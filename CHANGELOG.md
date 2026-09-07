# Changelog — plugin-creator

## [1.1.0] — 2026-09-07 — собственный репозиторий / own repository
### Для человека
- Выделен в собственный репо `jadlis-plugin-creator` (root-as-plugin), команда `/plugin-creator`, маркетплейс `jadlis`; история до 1.1.0 — в `skill-creator-plugin`.
### For agents
- Changed: layout `plugins/plugin-creator/` → root-as-plugin; skill moved to `skills/plugin-creator/SKILL.md` with `references/` and `scripts/` alongside.
- Changed: `.claude-plugin/plugin.json` — version 1.0.2 → 1.1.0, `homepage`/`repository` → `https://github.com/beCyborg/jadlis-plugin-creator`.
- Changed: install path is now `claude plugin install plugin-creator@jadlis` from `https://github.com/beCyborg/jadlis-start.git`; the command is `/plugin-creator` (single-skill plugin).
- Changed: CI calls the shared reusable workflow `beCyborg/jadlis-start/.github/workflows/plugin-ci.yml@main` with `mode: plugin`.
- Migration: reinstall from the `jadlis` marketplace; skill behaviour unchanged.
