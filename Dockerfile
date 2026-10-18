# Starter build. Pin base by immutable digest and use a lockfile before public production deployment.
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1 AS builder
WORKDIR /build
COPY requirements.lock ./
RUN python -m pip install --no-cache-dir --only-binary=:all: --require-hashes --prefix=/install -r requirements.lock

FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app/src
RUN python -m pip uninstall -y pip setuptools
RUN groupadd -g 10001 nsai && useradd -M -u 10001 -g 10001 -s /usr/sbin/nologin nsai
COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=10001:10001 LICENSE NOTICE ./
COPY --chown=10001:10001 LICENSES ./LICENSES
COPY --chown=10001:10001 src ./src
COPY --chown=10001:10001 assets ./assets
COPY --chown=10001:10001 database/migrations ./database/migrations
COPY --chown=10001:10001 database/access-contract.json database/access-contract-pg18.json ./database/
COPY --chown=10001:10001 deploy/init.sql ./deploy/init.sql
USER 10001:10001
EXPOSE 8787
CMD ["uvicorn", "nsai.api:app", "--host", "0.0.0.0", "--port", "8787", "--no-server-header", "--no-access-log"]
