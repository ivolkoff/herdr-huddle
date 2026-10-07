# herdr-huddle

[English](README.md) · **Русский**

Плагин для [herdr](https://herdr.dev): агент задаёт вопрос не строкой в терминале, а страницей.
Страница открывается в [terminal-browser](https://github.com/zenbu-labs/terminal-browser) зумом поверх
панели самого агента, ответ возвращается агенту JSON-ом в stdout.

![Страница с вопросом huddle](docs/screenshot.png)

Варианты с подзаголовками, рекомендацией, плюсами и минусами; превью (диаграммы, графики, макеты, цвета);
слайдеры с живым превью для значений на вкус; несколько вопросов на одной странице со сводкой; поле для
своего текста под каждым вопросом. Всё работает с клавиатуры.

## Что нужно

- herdr 0.9.0 или новее, macOS или Linux
- `terminal-browser` в `PATH`
- Python 3 (только стандартная библиотека)
- `jq` для команды установки ниже

## Установка

```bash
herdr plugin install ivolkoff/herdr-huddle
```

Плагин регистрирует одну панель, `page`. CLI, который вызывают агенты, лежит в папке плагина:

```bash
HUDDLE="$(herdr plugin list --json --plugin ivolkoff.huddle | jq -r '.result.plugins[0].plugin_root')"
"$HUDDLE/bin/huddle" q "Выкатываем сегодня?" "*Да|тесты зелёные" "Нет|ждём ревью"
```

### Как скил агента

`SKILL.md` в корне репозитория объясняет агенту формат спеки и когда звать huddle. Для Claude Code
подключите папку плагина как скил:

```bash
ln -s "$HUDDLE" ~/.claude/skills/huddle
```

Скил вызывает `~/.claude/skills/huddle/bin/huddle`. Другим агентам дайте `SKILL.md` и путь `bin/huddle`
рядом с ним. Текст скила на английском.

## Использование

```bash
huddle q "Где хранить сессии?" "*Redis|уже крутится для очереди задач" "Таблица в Postgres|одна таблица, индекс по expiry"
huddle spec.json            # полная JSON-спека или `huddle - < spec.json`
huddle templates            # заготовки в templates/
huddle demo [NAME]          # открыть демо из комплекта
huddle render spec.json -o page.html   # собрать страницу без показа
```

Ответ:

```json
{"status": "answered", "answers": {"answer": {"selected": ["o1"], "labels": ["Redis"], "text": "только для прода"}}}
```

Коды выхода: `0` — ответ получен (или `status: "chat"`, если пользователь хочет обсудить в терминале),
`2` — страницу закрыли без ответа, `3` — показать негде, `4` — вышло время, `1` — ошибка.

Вне herdr или с `--browser` страница открывается в браузере по умолчанию. Справочник спеки (блоки,
раскладки, слайдеры, стили) — в `SKILL.md`; полные спеки — в шаблонах и демо.

## Настройка

- `~/.config/huddle/defaults.json` (или `HUDDLE_CONFIG`): личные значения по умолчанию, например
  `{"style": "minimal", "review": "always"}`.
- `PIXEL_DISPLAY_SCALE`: масштаб страницы, по умолчанию `1`. Без него terminal-browser берёт масштаб экрана
  под курсором, и при мониторах с разной плотностью страница скачет между 1x и 2x.
- `HUDDLE_NO_BROWSER=1`: вне herdr выйти с кодом 3 вместо открытия браузера.

Mermaid скачивается один раз в `~/.cache/huddle/`; без сети диаграммы показываются исходником.

## Происхождение

Рантайм страницы, шаблоны и демо взяты из huddle в
[skkap/claude-skills](https://github.com/skkap/claude-skills) (MIT). Здесь транспорт заменён на панель
плагина herdr. Лицензия MIT, см. [LICENSE](LICENSE).
