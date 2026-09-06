# Changelog — plugin-creator

## [1.0.2] — 2026-09-06 — README RU/EN, docs/employee, формат CHANGELOG, gitleaks в CI / bilingual READMEs, docs/employee, changelog format, gitleaks in CI
### Для человека
- У плагина появились README на русском и английском: зачем, как выглядит, как поставить, как пользоваться, границы.
- CHANGELOG переписан в общий формат репозиториев, версия поднята под тег.
### For agents
- Added: `plugins/plugin-creator/README.md` + `README.en.md` (5 sections + Обновление/Лицензия, four modes described).
- Changed: `plugins/plugin-creator/CHANGELOG.md` reformatted to the house layout (`## [X.Y.Z] — date — summary` → `### Для человека` / `### For agents`); entries 1.0.0 and 1.0.1 preserved.
- Changed: `.claude-plugin/plugin.json` version 1.0.1 → 1.0.2.
- Related (repo level): `gitleaks` job in `.github/workflows/plugin-validate.yml`, root `CLAUDE.md`, `docs/employee.md`.
- Migration: none — docs and metadata only, skill behaviour unchanged.

## [1.0.1] — 2026-09-01 — ложное I8 на root-as-plugin / false I8 on root-as-plugin repos
### Для человека
- Официальная CI-проверка ругалась на репозитории, где плагин лежит в корне; в справочнике описано, почему это ложная тревога.
### For agents
- Changed: `references/pitfalls.md` §11 — official CI action's false I8 warning on root-as-plugin repos; first-run git-diff note.

## [1.0.0] — 2026-09-01 — первый релиз: сборка, валидация, релиз, миграция / initial release: assemble, validate, release, migrate
### Для человека
- Плагин собирает репозиторий по домашнему стандарту, проверяет его офлайн и официальной командой, выпускает версию с тегом и переносит старые репозитории в общий маркетплейс.
### For agents
- Added: four modes (Assemble / Validate / Release / Migrate) in `SKILL.md`.
- Added: references — `manifest-reference.md`, `components.md`, `marketplace-ops.md`, `release-checklist.md`, `pitfalls.md`, `repo-standard.md`.
- Added: `scripts/preflight_plugin.py` — offline house-standard invariants I1–I11 plus runtime-parse checks; `claude plugin validate` stays the canon.
