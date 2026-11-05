from pathlib import Path
from pypdf import PdfReader
from pptx import Presentation


def read_text_file(file_path: Path, max_chars: int = 50000) -> str:
    """Reads raw text or code files with fallback encoding support."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read(max_chars)
    except UnicodeDecodeError:
        with open(file_path, "r", encoding="latin-1") as f:
            content = f.read(max_chars)
    return content


def extract_pdf_pages(file_path: Path) -> list[str]:
    """Extracts text content page-by-page from a PDF."""
    reader = PdfReader(str(file_path))
    pages_text = []
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or f"[Page {idx + 1} has no selectable text / contains only images]"
        pages_text.append(text.strip())
    return pages_text


def extract_pptx_slides(file_path: Path) -> list[dict]:
    """
    Extracts text, titles, and speaker notes slide-by-slide from a .pptx file.
    Returns a list of dicts: {'slide_num': int, 'title': str, 'body': list[str], 'notes': str}
    """
    prs = Presentation(str(file_path))
    slides_data = []

    for idx, slide in enumerate(prs.slides, start=1):
        title = "Untitled Slide"
        body_lines = []

        if slide.shapes.title and slide.shapes.title.text.strip():
            title = slide.shapes.title.text.strip()

        for shape in slide.shapes:
            if shape == slide.shapes.title:
                continue
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    line = paragraph.text.strip()
                    if line:
                        body_lines.append(line)

        notes_text = ""
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            notes_text = slide.notes_slide.notes_text_frame.text.strip()

        slides_data.append({
            "slide_num": idx,
            "title": title,
            "body": body_lines,
            "notes": notes_text
        })

    return slides_data