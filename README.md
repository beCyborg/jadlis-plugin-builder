Русский · [English](README.en.md)

# Собрать, проверить и выпустить плагин по стандарту

## Было → стало

Раздел заполняется по контракту README 2026-09.

## Как это работает

`plugin-creator` собирает, проверяет, выпускает и переносит плагины и маркетплейсы Claude Code: от пустой папки до тега и GitHub Release. Четыре режима — **Assemble** (каркас репозитория по домашнему стандарту), **Validate** (офлайн-preflight плюс `claude plugin validate --strict`), **Release** (бамп версии, CHANGELOG, тег, релиз, путь обновления у получателей) и **Migrate** (перенос старого репозитория в общий маркетплейс без поломки уже сделанных установок). Работа идёт инлайн, без субагентов: операции с `git` и `gh` последовательные и завязаны на состояние рабочего дерева. Канон валидации — `claude plugin validate`; `skills/plugin-creator/scripts/preflight_plugin.py` только добавляет офлайн-проверки домашнего стандарта поверх него.

## Установка и первый запуск

```bash
claude plugin marketplace add https://github.com/beCyborg/jadlis-start.git
claude plugin install plugin-creator@jadlis
```

Первый запуск — командой `/plugin-creator` с задачей, например: `/plugin-creator проверь плагин перед релизом`.

## Границы, стоимость, обновление

- Своих ключей и платных сервисов не требует: работает на подписке Claude Code.
- Нужны `git`, `gh` (авторизованный) и `claude plugin` — релиз и smoke-install без них не проходят.
- Содержание скиллов не пишет и не улучшает: это работа плагина `skill-builder`.
- Правки только в рабочем клоне: файлы в `~/.claude/plugins/marketplaces/<имя>/` стирает фоновое обновление.

Автообновление у сторонних маркетплейсов выключено по умолчанию:

```bash
claude plugin marketplace update jadlis
claude plugin update plugin-creator@jadlis
```

Что изменилось между версиями — [CHANGELOG.md](CHANGELOG.md). Лицензия — Apache-2.0, [LICENSE](LICENSE).
