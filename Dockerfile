FROM python:3.12-slim

# fonts for rendering tables (Latin + CJK) to PNG
RUN apt-get update && apt-get install -y --no-install-recommends fonts-noto-cjk fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY panel/requirements.txt .
COPY factors/requirements.txt ./factors-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r factors-requirements.txt
COPY panel/backend ./panel/backend
COPY web ./web
COPY panel/web ./panel/web
COPY news/web ./news/web
COPY news/data/news.json ./news/data/news.json
COPY factors ./factors
COPY macro ./macro
COPY panel/data/sectors.json ./panel/data/sectors.json

ENV PORT=8765
EXPOSE 8765
CMD ["sh", "-c", "python -m uvicorn server:app --app-dir panel/backend --host 0.0.0.0 --port ${PORT}"]
