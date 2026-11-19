import logging
import re

import pymupdf

from cmj.utils import clean_text

logger = logging.getLogger(__name__)

PRIVATE_USE_PATTERN = re.compile(r"[-]")

# Acima desta proporção de caracteres de uso privado, o texto embutido da
# página é considerado ilegível e a página passa por OCR.
PRIVATE_USE_OCR_THRESHOLD = 0.1


def extract_pdf_text(doc):
    """Texto das páginas de um documento pymupdf, com OCR nas ilegíveis."""
    text_parts = []

    for page in doc:
        try:
            page_text = page.get_text()
            private_use_count = len(PRIVATE_USE_PATTERN.findall(page_text))

            if private_use_count > len(page_text) * PRIVATE_USE_OCR_THRESHOLD:
                rect = pymupdf.Rect(0, 80, page.rect.width - 45, page.rect.height - 55)
                pix = page.get_pixmap(clip=rect, dpi=300)
                bpdf = pymupdf.open(stream=pix.pdfocr_tobytes())
                page_text = bpdf[0].get_textpage_ocr().extractText()

            text_parts.append(page_text)

        except Exception as e:
            logger.warning(f"Erro ao extrair texto da página: {e}")
            text_parts.append("")

    return " ".join(text_parts)


def extract_clean_text_from_path(path):
    """Texto limpo (`clean_text`) do PDF em `path`."""
    with pymupdf.open(path) as doc:
        return clean_text(extract_pdf_text(doc))
