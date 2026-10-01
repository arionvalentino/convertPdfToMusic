FROM ubuntu:24.04

ARG AUDIVERIS_VERSION=5.11.0
ENV DEBIAN_FRONTEND=noninteractive

# Dependensi runtime Audiveris + Python
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl python3 python3-venv \
        libasound2t64 libbsd0 libx11-6 libxext6 libxi6 libxrender1 libxtst6 libfreetype6 fontconfig \
    && curl -fsSL -o /tmp/audiveris.deb \
        "https://github.com/Audiveris/audiveris/releases/download/${AUDIVERIS_VERSION}/Audiveris-${AUDIVERIS_VERSION}-ubuntu24.04-x86_64.deb" \
    # Ekstrak langsung: postinst paket .deb mencoba membuat menu desktop dan gagal di container
    && dpkg-deb -x /tmp/audiveris.deb / \
    && rm /tmp/audiveris.deb && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN python3 -m venv /venv && /venv/bin/pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY templates templates

ENV AUDIVERIS_BIN=/opt/audiveris/bin/Audiveris PORT=5000
EXPOSE 5000
CMD ["/venv/bin/gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "660", "app:app"]
