# jadlis-plugin-creator

Мысль: выпуск плагина идёт по одному списку — задача уходит в один из четырёх режимов, префлайт и валидация закрывают путь к бампу версии, дальше тег, релиз и установка в чистое окружение, а получателю остаётся строка обновления.

## hero

- Картинка: `docs/img/hero-jadlis-plugin-creator.webp`
- Заголовок: «От папки с работой до строки у получателя»
- Слева: папка с готовой работой; подпись «Папка с работой»
- Посередине: одна дорожка из шагов, у каждого своя отметка о проверке; подпись «каждый шаг закрыт проверкой»
- Справа: опубликованный релиз; подпись «Релиз опубликован»
- Последняя стрелка уходит дальше вправо — к рабочему месту того, у кого плагин уже установлен; подпись «У получателя»
- Названия сервисов в картинку не идут: только категории

```
Style: clean flat infographic on a light off-white background (#fdfbf7), two accent colors — deep teal (#1a7174) and warm orange (#f37d2c), thin dark-gray (#2f3333) line art, generous whitespace, geometric shapes, a modern geometric sans-serif look. Short Russian labels rendered as crisp, correctly spelled Cyrillic text. No robots, no glowing AI sparkles or glitter, no stock-photo people, no watermark. Wide 2:1 composition, 1280x640.

Hero illustration for a GitHub README about packaging and releasing a plugin. Bold Russian headline across the top «От папки с работой до строки у получателя». Below it a single horizontal track runs left to right. At the left end a teal folder outline holding three short sheets, labeled «Папка с работой». Along the middle of the track sit four flat outlined rounded chips of exactly equal height, drawn as thin line art with no 3D depth and no solid fill — they must read as a sequence of steps on one track, never as a bar chart; each chip carries a small numeral 1, 2, 3, 4 and a small orange tick badge on its upper right corner, and one Russian caption under the row reads «каждый шаг закрыт проверкой». A thick orange arrow ends the track at an orange card showing a package box with a small tag on a string, labeled «Релиз опубликован». From that card one more thin orange arrow continues further right to a plain teal monitor frame with a single monospace-looking command bar inside it, labeled «У получателя». No logos, no brand names, no service names. Text must be spelled exactly.
```

## scheme

- Картинка: `docs/img/how-jadlis-plugin-creator.webp`
- Блоки: «Задача» → «Выбор режима» → «Префлайт и валидация» → «Версия, changelog, тег, релиз» → «Установка в чистое окружение» → «Строка обновления у получателя»
- Под вторым блоком четыре варианта режима: «собрать», «проверить», «выпустить», «перенести»
- Стрелка из третьего блока в четвёртый перекрыта воротцами с подписью «дальше только после проверок»
- Названия сервисов в картинку не идут: только категории

```
Style: clean flat infographic on a light off-white background (#fdfbf7), two accent colors — deep teal (#1a7174) and warm orange (#f37d2c), thin dark-gray (#2f3333) line art, generous whitespace, geometric shapes, a modern geometric sans-serif look. Short Russian labels rendered as crisp, correctly spelled Cyrillic text. No robots, no glowing AI sparkles or glitter, no stock-photo people, no watermark. Wide 2:1 composition, 1280x640.

Cause-and-effect diagram with six rounded boxes in a row connected left to right by arrows, alternating teal and orange label plates, a simple geometric icon on top of each box: a task card with two short lines; a switch plate whose path fans into four short branches; a clipboard with pass and fail marks; a tag label on a string above a short list of lines; an empty open container with a small puzzle piece dropping into it; a monitor frame holding one monospace-looking command bar. Russian labels under the icons: «Задача» → «Выбор режима» → «Префлайт и валидация» → «Версия, changelog, тег, релиз» → «Установка в чистое окружение» → «Строка обновления у получателя»; the fourth label mixes Cyrillic with the Latin word changelog and must be spelled exactly as written. Under the second box the four branches end in four small flat outlined pills of equal size, drawn as thin line art with no 3D depth and no solid fill, reading as four alternative routes and never as a bar chart, labeled «собрать», «проверить», «выпустить», «перенести». The arrow from the third box to the fourth passes through a small closed gate bar with a short Russian caption above it «дальше только после проверок». No logos, no brand names, no service names. Text must be spelled exactly.
```

## alt

- hero (`docs/img/hero-jadlis-plugin-creator.webp`): Одна дорожка от папки с работой до опубликованного релиза, и последняя стрелка уходит к тому, кто плагин уже поставил
  Текстом: слева папка с готовой работой, справа опубликованный релиз, между ними шаги, каждый из которых закрыт проверкой, а последняя стрелка ведёт к человеку, у которого плагин уже установлен.
- scheme (`docs/img/how-jadlis-plugin-creator.webp`): Задача уходит в один из четырёх режимов, префлайт и валидация закрывают путь к бампу версии, дальше тег, релиз и проверочная установка
  Текстом: задача → выбор режима (собрать, проверить, выпустить, перенести) → префлайт и валидация → версия, changelog, тег, релиз → установка в чистое окружение → строка обновления у получателя.
