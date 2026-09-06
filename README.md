Русский · [English](README.en.md)

# plugin-creator

Плагин Claude Code, который собирает, проверяет, выпускает и переносит другие плагины и маркетплейсы: от пустой папки до тега и GitHub Release.

## Зачем

Готовый скилл ещё не инструмент: пока он лежит в личной папке, его нельзя ни поставить одной командой, ни обновить у получателя. Ручная упаковка каждый раз повторяет одни и те же ошибки — версия в двух местах, забытый `$schema`, тег без релиза, правка в кеше маркетплейса, которую стирает фоновое обновление.

Плагин закрывает четыре режима: **Assemble** (собрать репозиторий по стандарту), **Validate** (проверить до релиза), **Release** (выпустить версию), **Migrate** (перенести старый репозиторий в общий маркетплейс).

## Как выглядит

Работа идёт инлайн, без субагентов: операции с `git` и `gh` последовательные и завязаны на состояние рабочего дерева.

<details>
<summary>Синтетический пример: Validate перед релизом</summary>

```
> /plugin-creator:plugin-creator проверь плагин перед релизом

1/3 preflight (офлайн, инварианты домашнего стандарта)
    ✔ version только в plugin.json      ✔ $schema в обоих манифестах
    ✔ LICENSE на месте                  ✔ hooks.json разбирается
    ⚠ README без блока обновления

2/3 claude plugin validate --strict
    ✔ manifest ok    ✔ skills 2    ✔ marketplace ok

3/3 smoke-install во временное окружение
    ✔ скилл виден как /demo-plugin:demo

Итог: 0 ошибок, 1 предупреждение.
Правка: добавить в README блок «Обновление» с командой claude plugin update.
```

</details>

## Как поставить

Основной путь — через хаб `jadlis`. Вставь этот блок агенту:

> Ты — установщик. Выполни ровно эти шаги и ничего сверх них:
> 1. Bash: `claude plugin marketplace add https://github.com/beCyborg/jadlis-plugins.git`
> 2. Bash: `claude plugin install plugin-creator@jadlis`
> 3. Bash: `claude plugin list`
> 4. Скажи мне: появился ли `plugin-creator` в списке и с какой версией.

Руками — те же команды:

```bash
claude plugin marketplace add https://github.com/beCyborg/jadlis-plugins.git
claude plugin install plugin-creator@jadlis
```

Альтернатива — маркетплейс этого репозитория, без хаба:

```bash
claude plugin marketplace add https://github.com/beCyborg/skill-creator-plugin.git
claude plugin install plugin-creator@skill-creator-plugin
```

## Как пользоваться

Три сценария, командами:

1. Собрать плагин из готовой работы: `/plugin-creator:plugin-creator упакуй ~/skills/<имя> в плагин` — короткое интервью, каркас репозитория, перенос компонентов, валидация.
2. Проверить перед релизом: `/plugin-creator:plugin-creator проверь плагин` — офлайн-preflight, `claude plugin validate --strict`, smoke-install, находки с разбивкой на ошибки и предупреждения.
3. Выпустить версию: `/plugin-creator:plugin-creator зарелизь плагин` — бамп `version` в `plugin.json`, запись в CHANGELOG, коммит, тег `<плагин>--v<версия>`, GitHub Release и команда обновления для получателей.

Четвёртый режим — `/plugin-creator:plugin-creator перенеси репо в маркетплейс` — переносит старый репозиторий в общий маркетплейс, не ломая уже сделанные установки.

## Границы и стоимость

- Своих ключей и платных сервисов не требует: работает на подписке Claude Code.
- Нужны `git`, `gh` (авторизованный) и `claude plugin` — релиз и smoke-install без них не проходят.
- Содержание скиллов не пишет и не улучшает: это работа `skill-creator`.
- Канон валидации — `claude plugin validate`; `scripts/preflight_plugin.py` только добавляет офлайн-проверки домашнего стандарта.
- Правки только в рабочем клоне: файлы в `~/.claude/plugins/marketplaces/<имя>/` стирает фоновое обновление.

## Обновление

Автообновление у сторонних маркетплейсов выключено по умолчанию:

```bash
claude plugin update plugin-creator@jadlis
```

Что изменилось между версиями — [CHANGELOG.md](CHANGELOG.md).

## Лицензия

Apache-2.0, [LICENSE](../../LICENSE). Соседний плагин репозитория — [skill-creator](../../README.md).
