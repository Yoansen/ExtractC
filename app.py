from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_bytes
import unicodedata
import re

app = FastAPI()

# Supprimer les accents
def remove_accents(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

# OCR fallback si aucun texte brut n’est trouvé
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

    # Fallback OCR si texte brut vide
    if not text.strip():
        text = extract_text_with_ocr(content)

    # Nettoyage : minuscules, accents et espaces multiples
    text_cleaned = remove_accents(text.lower())
    text_cleaned = re.sub(r"\s+", " ", text_cleaned)  # remplacer les espaces multiples par un seul

    # Liste des expressions à détecter
    motifs_commande = [
        r"reference[\s:-]*commande[\s:-]*client",
        r"commande[\s:-]*client",
        r"n[\s:-]*commande[\s:-]*client",
        r"purchase[\s:-]*order",
        r"bon[\s:-]*de[\s:-]*commande",
        r"\bpo\b",
        r"\bpo#\b",
        r"commande[\s:-]*45"
    ]

    # Détection des motifs dans le texte nettoyé
    commande_detectee = any(re.search(motif, text_cleaned) for motif in motifs_commande)

    return {
        "text": text,
        "commande_detectee": commande_detectee
    }
