FROM python:3.13-slim

# System dependencies for WeasyPrint PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 \
    libffi-dev libcairo2 libglib2.0-0 shared-mime-info && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data

EXPOSE 8000

# Use a start script to handle PORT variable
RUN echo '#!/bin/sh\nuvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"' > /app/start.sh && chmod +x /app/start.sh
CMD ["/app/start.sh"]
