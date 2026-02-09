import os
import sys
import io
import argparse

import fitz  # PyMuPDF
from PIL import Image
import pytesseract


# -----------------------------
# CONFIGURE TESSERACT (WINDOWS)
# -----------------------------
def configure_tesseract():
    """
    Ensure Tesseract OCR is available.
    """
    try:
        pytesseract.get_tesseract_version()
        return True
    except pytesseract.TesseractNotFoundError:
        pass

    possible_paths = [
 
        r"C:\Program Files\Tesseract-OCR\tesseract.exe"
 
    ]

    for path in possible_paths:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return True

    return False


# -----------------------------
# PDF TEXT + OCR EXTRACTOR
# -----------------------------
def extract_data_from_pdf(pdf_path):
    """
    Extracts text from:
    - Searchable PDFs (direct text)
    - Scanned PDFs (OCR via page rendering)
    """

    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    doc = fitz.open(pdf_path)
    extracted = []

    print(f"\nProcessing: {pdf_path}\n")

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)

        # 1️⃣ Try direct text extraction
        text = page.get_text("text").strip()

        if text:
            extracted.append(
                f"--- Page {page_number + 1} (Direct Text) ---\n{text}"
            )
        else:
            # 2️⃣ OCR scanned page
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))

            ocr_text = pytesseract.image_to_string(
                image, config="--psm 6"
            ).strip()

            extracted.append(
                f"--- Page {page_number + 1} (OCR Scanned Page) ---\n"
                f"{ocr_text if ocr_text else '[No text detected]'}"
            )

    doc.close()

    result = "\n\n".join(extracted)

    # Save output
    output_file = "extracted_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)

    print("✅ Extraction complete")
    print(f"📄 Output saved to: {output_file}\n")
    print(result)


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="PDF Text + OCR Extractor (Scanned + Normal PDFs)"
    )
    parser.add_argument("file", help="Path to PDF file")
    args = parser.parse_args()

    print("PDF OCR Extractor")
    print("-----------------")

    if not configure_tesseract():
        print("❌ Tesseract OCR not found.")
        print("Install Tesseract and add it to PATH.")
        sys.exit(1)

    extract_data_from_pdf(args.file)
