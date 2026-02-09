import os
import sys
import io
import argparse
import base64

import fitz  # PyMuPDF
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def image_to_base64(pil_image):
    """Convert PIL Image to base64 string."""
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def extract_text_with_openai(image: Image.Image):
    """Extract text from image using OpenAI Vision model."""
    img_b64 = image_to_base64(image)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are an OCR engine. Extract text exactly as written. Do not explain anything."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all text from this image exactly. Keep line breaks."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}}
                ]
            }
        ],
        temperature=0
    )

    return response.choices[0].message.content.strip()


def extract_data_from_pdf(pdf_path):
    """Extract text from PDF: direct text if available, else OpenAI Vision OCR."""
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        return

    doc = fitz.open(pdf_path)
    extracted = []

    print(f"\nProcessing: {pdf_path}\n")

    for page_number in range(len(doc)):
        page = doc.load_page(page_number)

        # 1) Try direct text extraction
        text = page.get_text("text").strip()

        if text:
            extracted.append(
                f"--- Page {page_number + 1} (Direct Text) ---\n{text}"
            )
        else:
            # 2) Convert PDF page to image
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))

            # 3) Use OpenAI Vision OCR
            print(f"Running OpenAI OCR on page {page_number + 1}...")
            ocr_text = extract_text_with_openai(image)

            extracted.append(
                f"--- Page {page_number + 1} (OpenAI OCR) ---\n"
                f"{ocr_text if ocr_text else '[No text detected]'}"
            )

    doc.close()

    result = "\n\n".join(extracted)

    output_file = "extracted_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(result)

    print("\n✅ Extraction complete")
    print(f"📄 Output saved to: {output_file}\n")
    print(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF OCR Extractor (OpenAI Vision)")
    parser.add_argument("file", help="Path to PDF file")
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY environment variable not set.")
        print("Set it like this:")
        print("setx OPENAI_API_KEY \"your_api_key_here\"")
        sys.exit(1)

    extract_data_from_pdf(args.file)
