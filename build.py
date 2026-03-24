import json
import os
import shutil
from pathlib import Path

from extract_job import to_job_record


DIST_DIR = Path("dist")
PDF_SRC = Path("sample.pdf")
PDF_DST = DIST_DIR / "sample.pdf"


def escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def render_html(rec: dict) -> str:
    title = rec.get("title") or "求人情報"
    company = rec.get("company") or ""
    location = rec.get("location") or ""
    employment_type = rec.get("employment_type") or ""
    salary = rec.get("salary") or ""
    deadline = rec.get("apply_deadline") or ""
    apply_method = rec.get("apply_method") or ""
    description = rec.get("description") or ""

    def row(label: str, value: str) -> str:
        if not value:
            return ""
        return f"<div class=\"row\"><div class=\"label\">{escape_html(label)}</div><div class=\"value\">{escape_html(value)}</div></div>"

    return f"""
<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{escape_html(title)}{(' | ' + escape_html(company)) if company else ''}</title>
  <meta name=\"description\" content=\"{escape_html((description[:140] + '...') if len(description) > 140 else description)}\" />
  <style>
    :root { --fg:#111; --muted:#666; --bg:#fff; --accent:#2563eb; }
    *{box-sizing:border-box} body{{margin:0;background:var(--bg);color:var(--fg);font:16px/1.6 -apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,"Noto Sans JP",sans-serif}}
    .container{{max-width:860px;margin:0 auto;padding:24px}}
    header h1{{margin:0 0 8px;font-size:28px}}
    header .company{{color:var(--muted)}}
    .meta{{margin:16px 0 24px}}
    .row{{display:flex;gap:12px;padding:8px 0;border-bottom:1px solid #eee}}
    .label{{width:10em;color:var(--muted)}}
    .value{{flex:1}}
    .actions{{margin:24px 0;display:flex;gap:12px;flex-wrap:wrap}}
    a.button{{display:inline-block;background:var(--accent);color:#fff;padding:10px 14px;border-radius:8px;text-decoration:none}}
    a.secondary{{background:#f3f4f6;color:#111}}
    pre.desc{{white-space:pre-wrap;background:#fafafa;border:1px solid #eee;border-radius:8px;padding:16px;overflow:auto}}
    footer{{margin:32px 0;color:var(--muted);font-size:14px}}
  </style>
  <link rel=\"preload\" href=\"sample.pdf\" as=\"fetch\" type=\"application/pdf\" crossorigin>
  <meta property=\"og:type\" content=\"website\" />
  <meta property=\"og:title\" content=\"{escape_html(title)}\" />
  <meta property=\"og:description\" content=\"{escape_html((description[:140] + '...') if len(description) > 140 else description)}\" />
</head>
<body>
  <div class=\"container\">
    <header>
      <h1>{escape_html(title)}</h1>
      {f'<div class="company">{escape_html(company)}</div>' if company else ''}
    </header>

    <section class=\"meta\">
      {row('勤務地', location)}
      {row('雇用形態', employment_type)}
      {row('給与', salary)}
      {row('応募期限', deadline)}
      {row('応募方法', apply_method)}
    </section>

    <div class=\"actions\">
      <a class=\"button\" href=\"sample.pdf\" target=\"_blank\" rel=\"noopener\">PDFを開く</a>
      <a class=\"button secondary\" href=\"sample.pdf\" download>PDFをダウンロード</a>
    </div>

    <section>
      <h2>募集要項・詳細</h2>
      <pre class=\"desc\">{escape_html(description)}</pre>
    </section>

    <footer>
      <div>自動抽出のため表記が原文と異なる場合があります。</div>
    </footer>
  </div>
</body>
</html>
"""


def main():
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    rec = to_job_record(str(PDF_SRC))

    html = render_html(rec)
    (DIST_DIR / "index.html").write_text(html, encoding="utf-8")

    if PDF_SRC.exists():
        shutil.copy2(PDF_SRC, PDF_DST)

    # Also emit JSON for debugging/inspection
    (DIST_DIR / "job.json").write_text(
        json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()

