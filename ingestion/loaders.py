import re

_MIN_TEXT_CHARS = 50   # below this, assume a scanned document


def load_document(path: str) -> str:
    """Return cleaned full text of one corpus PDF."""
    text = _extract_text_layer(path)
    if len(text.strip()) < _MIN_TEXT_CHARS:
        from ingestion.ocr import extract_scanned
        text = extract_scanned(path)
    return _clean(text)


def _extract_text_layer(path: str) -> str:
    import pdfplumber
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages)


def _clean(text: str) -> str:
    """Normalise extraction artifacts without touching legal wording."""
    text = text.replace("­", "")                 # soft hyphens
    text = re.sub(r"[ \t]+", " ", text)               # collapse runs of spaces
    text = re.sub(r"\n{3,}", "\n\n", text)            # collapse blank-line runs
    # Gazette page furniture like "3—PL 012345—..." print codes tends to slip
    # into extraction; drop lines that are only digits/dashes/whitespace.
    lines = [ln for ln in text.split("\n")
             if not re.fullmatch(r"[\s\d—\-–—]*", ln)]
    return "\n".join(lines).strip()
