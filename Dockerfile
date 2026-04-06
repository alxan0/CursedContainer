FROM debian:trixie-slim AS build-env

ENV DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv python3-pip \
 && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv

COPY requirements.txt /tmp/requirements.txt
RUN /opt/venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt
RUN chmod -R 555 /opt/venv

COPY . /app
RUN chmod -R 555 /app

# use python3-debian13:debug-nonroot when you need a busybox shell
FROM gcr.io/distroless/python3-debian13:nonroot

COPY --from=build-env /opt/venv /opt/venv
COPY --from=build-env /app /app

WORKDIR /app
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_BASE_PATH="/app" \
    SYNC_INTERVAL=0 \
    APP_TIMEZONE="UTC" \
    MAX_MOD_FILE_SIZE_MB=1024 \
    DOWNLOAD_TIMEOUT_SECONDS=60 \
    CONNECT_TIMEOUT_SECONDS=10

ENTRYPOINT ["/opt/venv/bin/python3", "src/main.py"]