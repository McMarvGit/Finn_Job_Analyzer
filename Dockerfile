# Basis-Image
FROM python:3.11-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Requirements kopieren
COPY requirements.txt .

# Abhängigkeiten installieren
RUN pip install --no-cache-dir -r requirements.txt

# Restlichen Code kopieren
COPY . .

# Startbefehl
CMD ["streamlit", "run", "main.py", "--server.address=0.0.0.0", "--server.port=8501"]