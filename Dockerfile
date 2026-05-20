FROM python:3.10-slim

# Install system dependencies for Tesseract OCR (required by pytesseract) and psycopg2 (compilation)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port (Hugging Face Spaces requires port 7860)
EXPOSE 7860

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "run:app"]
