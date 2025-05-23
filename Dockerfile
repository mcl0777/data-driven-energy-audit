FROM python:3.9-slim

WORKDIR /app

# Installiere System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Kopiere die Requirements-Datei
COPY requirements.txt .

# Installiere Python-Abhängigkeiten
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Anwendungscode
COPY . .

# Setze Umgebungsvariablen
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Exponiere den Port
EXPOSE 5000

# Starte die Anwendung
CMD ["flask", "run", "--host=0.0.0.0"] 