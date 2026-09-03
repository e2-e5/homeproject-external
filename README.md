# homeproject-external

Auto-published external pages for Home Project agents — briefs, KPs, landings, anything client-facing that should live on a public URL but not on the storefront.

**DO NOT EDIT MANUALLY.** Files here are written by agents on the VPS via the `publish_external_page` MCP tool. Manual edits will be overwritten.

URL pattern: `https://e2-e5.github.io/homeproject-external/<slug>`

## Защита от битых публикаций

Workflow `.github/workflows/guard-pages.yml` запускается на каждый пуш в `main`
и проверяет изменённые `*.html` (скрипт `.github/scripts/guard_pages.py`):

- мусор вместо HTML (неисполненный `$(cat …)`, путь к файлу, пустой файл) —
  восстанавливается последняя валидная версия из истории, а если её нет,
  ставится заглушка «Страница не опубликована» с текстом того, что пришло;
- фрагмент без `<!DOCTYPE>/<html>/<head>` — оборачивается в полный документ
  с charset, viewport и title, контент не меняется;
- JSON с расширением `.html` (данные для калькуляторов) — не трогается.

Исправления коммитятся обратно в `main` от `pages-guard[bot]`. Полную проверку
всех файлов можно запустить вручную через «Run workflow» (workflow_dispatch).

Контракт для `publish_external_page`: содержимое страницы должно быть полным
HTML-документом, начинающимся с `<!DOCTYPE html>`.
