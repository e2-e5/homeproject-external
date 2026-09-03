#!/usr/bin/env python3
"""Guard for published pages.

Runs on every push to main. Looks at the *.html files the push touched and
repairs anything the publishing tool got wrong:

  * garbage content (an unexpanded `$(cat ...)`, a bare file path, empty file,
    no HTML at all)  -> restored from the last valid committed version, or
    replaced with an explicit "publication failed" placeholder page;
  * a bare HTML fragment (no <!DOCTYPE>/<html>/<head>) -> wrapped into a full
    document with charset, viewport and title, content untouched;
  * a JSON data file with an .html extension -> left alone on purpose.

Set ALL=1 to scan every *.html instead of only the changed ones.
"""
import html
import json
import os
import re
import subprocess
import sys

ROOT = os.getcwd()
SITE = "https://e2-e5.github.io/homeproject-external/"

def sh(*args, check=False):
    return subprocess.run(args, capture_output=True, text=True, check=check)

def classify(text):
    """Return one of: ok, data, fragment, garbage."""
    s = text.strip()
    if not s:
        return "garbage"
    if s[0] in "{[":
        try:
            json.loads(s)
            return "data"
        except ValueError:
            pass
    if "$(cat " in s[:300] or "${" == s[:2]:
        return "garbage"
    head = s[:4000].lower()
    if "<!doctype" in head or "<html" in head:
        return "ok"
    if re.search(r"<(div|section|main|article|nav|header|body|h1|p|table|style|link|script)\b", head):
        return "fragment"
    return "garbage"

def extract_title(text, slug):
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    if not m:
        m = re.search(r"<h1[^>]*>(.*?)</h1>", text, re.I | re.S)
    if m:
        t = re.sub(r"<[^>]+>", "", m.group(1))
        t = html.unescape(re.sub(r"\s+", " ", t)).strip()
        if t:
            return t
    return slug.replace("-", " ")

def wrap_fragment(text, slug):
    title = extract_title(text, slug)
    # Fragments that begin with <link>/<style> belong in <head>; the rest in <body>.
    head_part, body_part = "", text
    m = re.search(r"</style>\s*", text, re.I)
    if m and not re.search(r"<(div|section|main|nav|header|h1|p)\b", text[: m.start()], re.I):
        head_part, body_part = text[: m.end()], text[m.end():]
    return (
        "<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        f"<title>{html.escape(title)}</title>\n"
        f"{head_part.rstrip()}\n</head>\n<body>\n{body_part.strip()}\n</body>\n</html>\n"
    )

def placeholder(slug, raw):
    sample = html.escape(raw.strip()[:300]) or "(пустой файл)"
    return (
        "<!DOCTYPE html>\n<html lang=\"ru\">\n<head>\n<meta charset=\"utf-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
        "<meta name=\"robots\" content=\"noindex,nofollow\">\n"
        "<title>Страница не опубликована — Home Project</title>\n</head>\n"
        "<body style=\"font-family:system-ui;max-width:640px;margin:80px auto;padding:0 20px;color:#333\">\n"
        "<h1>Страница не опубликована</h1>\n"
        f"<p>Слаг <code>{html.escape(slug)}</code> был опубликован с некорректным содержимым, "
        "и автоматическая защита заменила его этой заглушкой. Переопубликуйте страницу "
        "через <code>publish_external_page</code>, передав полный HTML-документ.</p>\n"
        f"<p style=\"color:#888;font-size:13px\">Полученное содержимое:</p>\n<pre style=\"white-space:pre-wrap;"
        f"background:#f5f5f5;padding:12px;font-size:12px;color:#666\">{sample}</pre>\n"
        f"<p><a href=\"{SITE}\">Home Project</a></p>\n</body>\n</html>\n"
    )

def previous_valid_version(path):
    """Walk back through history and return the last committed content that passes."""
    log = sh("git", "log", "--format=%H", "-n", "6", "--", path).stdout.split()
    for commit in log[1:]:
        r = sh("git", "show", f"{commit}:{path}")
        if r.returncode == 0 and classify(r.stdout) == "ok":
            return r.stdout, commit[:7]
    return None, None

def changed_files():
    if os.environ.get("ALL"):
        return sorted(f for f in os.listdir(ROOT) if f.endswith(".html"))
    before = os.environ.get("BEFORE", "")
    if not before or set(before) == {"0"}:
        r = sh("git", "diff-tree", "--no-commit-id", "--name-only", "-r", "--diff-filter=AM", "HEAD")
    else:
        r = sh("git", "diff", "--name-only", "--diff-filter=AM", before, "HEAD")
    return sorted(f for f in r.stdout.split("\n") if f.endswith(".html") and os.path.isfile(f))

def main():
    report = []
    for path in changed_files():
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
        kind = classify(raw)
        slug = os.path.basename(path)
        if kind in ("ok", "data"):
            continue
        if kind == "fragment":
            fixed = wrap_fragment(raw, slug)
            note = "фрагмент без <html>/<head> обёрнут в полный документ"
        else:
            prev, commit = previous_valid_version(path)
            if prev is not None:
                fixed, note = prev, f"мусорное содержимое, восстановлена версия из {commit}"
            else:
                fixed, note = placeholder(slug, raw), "мусорное содержимое, поставлена заглушка"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(fixed)
        report.append((path, note))
        print(f"::warning file={path}::{note}")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if report:
        lines = ["## Guard: исправлены страницы", ""] + [f"- `{p}` — {n}" for p, n in report]
        text = "\n".join(lines)
        print(text)
        if summary:
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write(text + "\n")
    else:
        print("guard: all published pages are valid")
    return 0

if __name__ == "__main__":
    sys.exit(main())
