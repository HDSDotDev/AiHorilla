FROM python:3.11-slim-bullseye

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y libcairo2-dev gcc g++ build-essential libpq-dev python3-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app/

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

CMD ["gunicorn", "horilla.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
