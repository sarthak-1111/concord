import os, pathlib, re
from typing import List, Dict, Any

from pypdf import PdfReader  # Concord: replaces PyMuPDF (AGPL) with pypdf (BSD)


def extract_texts_from_pdfs(
    pdf_paths: List[str],
    output_dir: str = "papers/extracted_texts"
) -> Dict[str, Any]:
    """
    Extract plain text from a list of local PDF files and save as .txt files.

    Args:
        pdf_paths: List of local PDF file paths (e.g., results from download_pdfs).
        output_dir: Directory to write extracted .txt files.

    Returns:
        dict with:
          - status: "ok"
          - saved: list of {"pdf","text_path","pages","chars"}
          - skipped: list of {"pdf","reason"}
    """
    out = pathlib.Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    saved, skipped = [], []

    for p in pdf_paths:
        try:
            if not os.path.exists(p):
                skipped.append({"pdf": p, "reason": "file not found"})
                continue

            doc = PdfReader(p)
            if doc.is_encrypted and not doc.decrypt(""):
                skipped.append({"pdf": p, "reason": "encrypted, cannot authenticate"})
                continue
            raw_text = "\n".join(page.extract_text() or "" for page in doc.pages)

            text = _normalize_extracted_text(raw_text)

            base = os.path.splitext(os.path.basename(p))[0]
            txt_path = str(out / f"{base}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"[SOURCE_PDF_PATH]: {p}\n\n")
                f.write(text)

            saved.append({
                "pdf": p,
                "text_path": txt_path,
                "pages": len(doc.pages),
                "chars": len(text)
            })

        except Exception as e:
            skipped.append({"pdf": p, "reason": str(e)})

    return {"status": "ok", "saved": saved, "skipped": skipped}


def _normalize_extracted_text(text: str) -> str:
    """
    Clean up PDF-extracted text to avoid single-word lines and excessive newlines.

    Steps:
    - Unify newlines (\r\n, \r -> \n)
    - Fix cross-line hyphenation: "co-\nprecipitation" -> "coprecipitation"
    - Collapse soft line breaks within paragraphs to single spaces
    - Preserve paragraph boundaries by keeping blank-line separations (\n\n)
    - Trim trailing spaces and collapse runs of spaces
    """
    if not text:
        return text

    s = text.replace("\r\n", "\n").replace("\r", "\n")

    s = re.sub(r"(\w)-\n(\w)", r"\1\2", s)

    s = re.sub(r"\n{3,}", "\n\n", s)

    paragraphs = re.split(r"\n\n", s)
    normalized_paragraphs = []
    for p in paragraphs:
        p_clean = p.replace("\n", " ")
        p_clean = re.sub(r"[ \t]+", " ", p_clean).strip()
        if p_clean:
            normalized_paragraphs.append(p_clean)
    s = "\n\n".join(normalized_paragraphs)

    return s