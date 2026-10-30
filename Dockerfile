FROM python:3.12-slim

# fonts for rendering tables (Latin + CJK) to PNG
RUN apt-get update && apt-get install -y --no-install-recommends fonts-noto-cjk fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY web ./web
COPY data/sectors.json ./data/sectors.json

ENV PORT=8765
EXPOSE 8765
CMD ["sh", "-c", "python -m uvicorn server:app --app-dir backend --host 0.0.0.0 --port ${PORT}"]
