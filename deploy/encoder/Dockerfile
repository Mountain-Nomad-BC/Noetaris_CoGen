FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 AS builder
WORKDIR /build
COPY requirements.lock requirements-semantic.lock ./
RUN python -m pip install --no-cache-dir --only-binary=:all: --require-hashes --prefix=/install -r requirements.lock -r requirements-semantic.lock

FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
RUN python -m pip uninstall -y pip setuptools && groupadd -g 10001 nsai && useradd -M -u 10001 -g 10001 -s /usr/sbin/nologin nsai
COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=10001:10001 LICENSE NOTICE ./
COPY --chown=10001:10001 LICENSES ./LICENSES
COPY --chown=10001:10001 src ./src
USER 10001:10001
CMD ["uvicorn","nsai.encoder_service:app","--host","0.0.0.0","--port","8092","--no-server-header","--no-access-log"]
