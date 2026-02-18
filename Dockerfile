# CoRec Tracker - includes Chromium for web scraping
FROM python:3.11-slim

# Install Chromium and ChromeDriver (required for Selenium)
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium \
    chromium-driver \
    libnss3 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libpango-1.0-0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway sets PORT at runtime - use ENV to set default, then CMD uses it
ENV PORT=8080
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
