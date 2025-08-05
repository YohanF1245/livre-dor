FROM python:3.12-slim

WORKDIR /app

# Copier les dépendances
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'app Flask
COPY . .

# Lancer Flask
CMD ["python", "app.py"]