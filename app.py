from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_bytes
import unicodedata

app = FastAPI()

# Supprimer les accents
def remove_accents(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

# Fallback OCR si le PDF ne contient pas de texte
def extract_text_with_ocr(pdf_bytes):
    images = convert_from_bytes(pdf_bytes)
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img, lang="fra")
    return text

@app.post("/extract")
async def extract(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        return JSONResponse(content={"error": "Invalid file type"}, status_code=400)

    content = await file.read()

    try:
        doc = fitz.open(stream=content, filetype="pdf")
        text = "".join([page.get_text() for page in doc])
        doc.close()
    except Exception as e:
        return JSONResponse(content={"error": f"PDF reading failed: {str(e)}"}, status_code=500)

    # Si aucun texte détecté, lancer l’OCR
    if not text.strip():
        text = extract_text_with_ocr(content)

    text_cleaned = remove_accents(text.lower())

    # Détection de commandes (élargie)
    commande_detectee = any(
        phrase in text_cleaned
        for phrase in [
            "reference commande client",
            "commande client",
            "n commande client",
            "purchase order",
            "bon de commande",
            "po",
            "po#"
        ]
    )

    return {
        "text": text,
        "commande_detectee": commande_detectee
    }
