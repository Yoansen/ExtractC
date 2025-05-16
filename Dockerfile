FROM python:3.9-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-fra \
    libgl1-mesa-glx \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requis dans l'image
COPY requirements.txt ./
COPY app.py ./

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Définir la variable d’environnement du port pour Render
ENV PORT=10000
EXPOSE $PORT

# Lancer l'application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]
