import sys
import json
import re
import hashlib
import pathlib
import datetime

try:
    import pdfplumber
except Exception as e:
    print(json.dumps({"error": "pdfplumber_not_available", "detail": str(e)}, ensure_ascii=False))
    sys.exit(1)

try:
    import pytesseract  # wrapper, needs Tesseract binary installed
except Exception:
    pytesseract = None

try:
    import pypdfium2 as pdfium
except Exception:
    pdfium = None


FIELD_PATTERNS = {
    "title": r"(?:募集職種|職種)\s*[:：]?\s*(.+)",
    "company": r"(?:企業名|社名|会社名)\s*[:：]?\s*(.+)",
    "location": r"(?:勤務地)\s*[:：]?\s*(.+)",
    "employment_type": r"(?:雇用形態)\s*[:：]?\s*(.+)",
    "salary": r"(?:給与|報酬)\s*[:：]?\s*(.+)",
    "apply_deadline": r"(?:応募期限|締切|締め切り)\s*[:：]?\s*(.+)",
    "apply_method": r"(?:応募方法)\s*[:：]?\s*(.+)",
}


def extract_text(pdf_path: str) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        texts = []
        for page in pdf.pages:
            t = page.extract_text() or ""
            texts.append(t)
        return "\n".join(texts).strip()


def parse_fields(text: str) -> dict:
    data = {}
    for key, pat in FIELD_PATTERNS.items():
        m = re.search(pat, text)
        if m:
            data[key] = m.group(1).strip()
    data["description"] = text
    return data


def to_job_record(pdf_path: str, source_url: str | None = None) -> dict:
    pdfp = pathlib.Path(pdf_path)
    text = extract_text(pdf_path)
    rec = parse_fields(text)
    rec.update({
        "source_pdf_path": str(pdfp.resolve()),
        "source_pdf_url": source_url,
        "extracted_text_length": len(text),
        "parse_confidence": 0.5,
        "posted_at": datetime.date.today().isoformat(),
        "hash": hashlib.md5(pdfp.read_bytes()).hexdigest(),
        "status": "draft",
    })
    if len(text) < 100:
        # Try OCR fallback if available
        ocr_note = []
        if pytesseract is not None and pdfium is not None:
            try:
                # Check if tesseract binary is available
                _ = pytesseract.get_tesseract_version()
                # Render pages to PIL using pypdfium2 (avoid external poppler)
                doc = pdfium.PdfDocument(str(pdfp))
                scale = 300/72  # ~300dpi
                images = pdfium.render_pdf_topil(doc, scale=scale)
                ocr_texts = []
                for img in images:
                    t = pytesseract.image_to_string(img, lang="jpn+eng", config="--oem 1 --psm 4")
                    if t:
                        ocr_texts.append(t)
                ocr_text = "\n".join(ocr_texts).strip()
                if len(ocr_text) > len(text):
                    text = ocr_text
                    rec.update({
                        "description": text,
                        "extracted_text_length": len(text),
                        "ocr_used": True,
                        "parse_confidence": 0.35,
                    })
                else:
                    ocr_note.append("OCR実行済みだがテキスト量は増えませんでした")
            except Exception as e:
                ocr_note.append(f"OCR未実行: {type(e).__name__}: {e}")
        else:
            if pytesseract is None:
                ocr_note.append("pytesseract未インストール")
            if pdfium is None:
                ocr_note.append("pypdfium2未利用")
        if ocr_note:
            rec["note"] = "; ".join(ocr_note) + "。スキャンPDFの可能性あり（OCR推奨）。"
    return rec


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_job.py <pdf_path>")
        sys.exit(2)
    pdf_path = sys.argv[1]
    rec = to_job_record(pdf_path)
    print(json.dumps(rec, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
