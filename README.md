# homeproject-external

Auto-published external pages for Home Project agents — briefs, KPs, landings, anything client-facing that should live on a public URL but not on the storefront.

**DO NOT EDIT MANUALLY.** Files here are written by agents on the VPS via the `publish_external_page` MCP tool. Manual edits will be overwritten.

URL pattern: `https://e2-e5.github.io/homeproject-external/<slug>`

## Защита от битых публикаций

Workflow `.github/workflows/guard-pages.yml` проверяет опубликованные `*.html`
(скрипт `.github/scripts/guard_pages.py`):

- мусор вместо HTML (неисполненный `$(cat …)`, путь к файлу, пустой файл) —
  восстанавливается последняя валидная версия из истории, а если её нет,
  ставится заглушка «Страница не опубликована» с текстом того, что пришло;
- фрагмент без `<!DOCTYPE>/<html>/<head>` — оборачивается в полный документ
  с charset, viewport и title, контент не меняется;
- JSON с расширением `.html` (данные для калькуляторов) — не трогается.

Запускается тремя способами:

- на каждый пуш в `main` — проверяются только изменённые файлы;
- раз в час по расписанию — полная проверка всех файлов. Это подстраховка:
  пуш, сделанный токеном, который не порождает событий (например, GitHub App),
  иначе остался бы непроверенным;
- вручную через «Run workflow» — тоже полная проверка.

Исправления коммитятся обратно в `main` от `pages-guard[bot]`.

Контракт для `publish_external_page`: содержимое страницы должно быть полным
HTML-документом, начинающимся с `<!DOCTYPE html>`. Если инструмент передаёт
строку вида `$(cat …)` или путь к файлу, значит подстановка не выполнилась —
такую публикацию guard откатит.
