import os
from PIL import Image
import pytesseract
import pypdf
import pyheif


def extract_file_text(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _extract_pdf_text(file_path)
    elif ext in (".png", ".jpg", ".jpeg"):
        return _extract_image_text(file_path)
    elif ext == ".heic":
        return _extract_heic_text(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def _extract_pdf_text(file_path: str) -> str:
    reader = pypdf.PdfReader(file_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n".join(pages)


def _extract_image_text(file_path: str) -> str:
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)


def _extract_heic_text(file_path: str) -> str:
    heif_file = pyheif.read_heif(file_path)
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
        heif_file.mode,
        heif_file.stride,
    )
    return pytesseract.image_to_string(image)
