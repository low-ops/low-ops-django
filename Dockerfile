FROM python:3.13-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh \
    && DEBUG=true POSTGRES_HOST=localhost POSTGRES_PORT=5432 POSTGRES_DATABASE=low_ops \
       POSTGRES_USER=postgres POSTGRES_PASSWORD=postgres \
       python manage.py collectstatic --noinput \
    && python -c "import compileall; compileall.compile_dir('.', quiet=1)"

ENV PORT=8000
ENV METRICS_PORT=8001
ENV METRICS_BIND_HOST=127.0.0.1
EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
