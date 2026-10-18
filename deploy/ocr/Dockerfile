FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
COPY deploy/ocr/apt-package-closure.lock /opt/apt-package-closure.lock
RUN apt-get update && xargs apt-get install -y --no-install-recommends < /opt/apt-package-closure.lock && rm -rf /var/lib/apt/lists/*
COPY deploy/ocr/requirements.lock /opt/requirements.lock
RUN pip install --no-cache-dir --only-binary=:all: --require-hashes -r /opt/requirements.lock && useradd --uid 10002 --create-home --shell /usr/sbin/nologin ocr
RUN python -m pip uninstall -y pip setuptools
WORKDIR /opt/app
COPY LICENSE NOTICE ./
COPY LICENSES ./LICENSES
RUN mkdir -p /opt/app/nsai
COPY src/nsai/ocr_geometry.py src/nsai/upload_limits.py src/nsai/ingestion.py src/nsai/ocr_worker.py src/nsai/ocr_server.py /opt/app/nsai/
RUN touch /opt/app/nsai/__init__.py && dpkg-query -W > /opt/package-versions.txt
ENV PYTHONPATH=/opt/app PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_THREAD_LIMIT=1
USER 10002:10002
EXPOSE 8091
ENTRYPOINT ["python", "-m", "nsai.ocr_server"]
