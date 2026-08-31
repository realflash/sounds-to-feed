# Stage 1: Build Backend Environment
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS backend-builder
WORKDIR /app
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY app/pyproject.toml app/uv.lock* ./
RUN if [ -f uv.lock ]; then uv export --no-dev --format requirements-txt > requirements.txt; else uv pip compile pyproject.toml -o requirements.txt; fi
RUN uv pip install --system --no-cache -r requirements.txt
# Remove pip and build tools to reduce the vulnerability surface of the runtime image
RUN python -m pip uninstall -y pip setuptools wheel || true

# Stage the shared library dependencies of the Python 3.12 runtime + site-packages,
# so the distroless image (which has no Python of its own) can run them.
RUN mkdir -p /stage && \
    { \
      ldd /usr/local/bin/python3.12 2>/dev/null; \
      find /usr/local/lib/python3.12 -name '*.so' 2>/dev/null | while read -r so; do ldd "$so" 2>/dev/null; done; \
    } | awk '/=>/ {print $3}' | sort -u | \
    while read -r lib; do \
      if [ -n "$lib" ] && [ -f "$lib" ]; then \
        mkdir -p "/stage/$(dirname "$lib")"; \
        cp -L "$lib" "/stage/$lib"; \
      fi; \
    done

# Stage 2: Build get_iplayer + native dependencies in a full image
FROM debian:12-slim AS gi-builder
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    perl \
    curl \
    ffmpeg \
    atomicparsley \
    libxml-simple-perl \
    liblwp-protocol-https-perl \
    libmojolicious-perl \
    libcgi-pm-perl && \
    curl -L https://raw.githubusercontent.com/get-iplayer/get_iplayer/master/get_iplayer -o /usr/local/bin/get_iplayer && \
    chmod +x /usr/local/bin/get_iplayer && \
    rm -rf /var/lib/apt/lists/*

# Collect every shared library required at runtime into /stage so the distroless
# image only carries what get_iplayer, perl, ffmpeg and atomicparsley actually need.
RUN mkdir -p /stage && \
    { \
      for bin in /usr/bin/perl /usr/bin/ffmpeg /usr/bin/AtomicParsley; do \
        ldd "$bin" 2>/dev/null; \
      done; \
      find /usr/lib/x86_64-linux-gnu/perl /usr/lib/x86_64-linux-gnu/perl5 /usr/share/perl5 -name '*.so' 2>/dev/null | \
        while read -r so; do ldd "$so" 2>/dev/null; done; \
    } | awk '/=>/ {print $3}' | sort -u | \
    while read -r lib; do \
      if [ -n "$lib" ] && [ -f "$lib" ]; then \
        mkdir -p "/stage/$(dirname "$lib")"; \
        cp -L "$lib" "/stage/$lib"; \
      fi; \
    done

# Pre-create writable data/config dirs owned by the distroless nonroot user (65532).
RUN mkdir -p /data /config && chown -R 65532:65532 /data /config && \
    touch /data/.keep /config/.keep

# Stage 3: Production (Distroless)
# Use the minimal cc base (no Python, no krb5) so the image carries no outdated
# system packages. The full Python 3.12 runtime is provided from the builders.
FROM gcr.io/distroless/cc-debian12

WORKDIR /app

ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Python 3.12 runtime from the backend builder (binaries + libpython + stdlib + site-packages)
COPY --from=backend-builder /usr/local/bin /usr/local/bin
COPY --from=backend-builder /usr/local/lib /usr/local/lib
# Python 3.12 runtime shared library dependencies
COPY --from=backend-builder /stage/ /

# get_iplayer, perl, ffmpeg, atomicparsley and their runtime shared libraries
COPY --from=gi-builder /usr/bin/env /usr/bin/env
COPY --from=gi-builder /usr/bin/perl /usr/bin/perl
COPY --from=gi-builder /usr/local/bin/get_iplayer /usr/local/bin/get_iplayer
COPY --from=gi-builder /usr/bin/ffmpeg /usr/bin/ffmpeg
COPY --from=gi-builder /usr/bin/AtomicParsley /usr/bin/AtomicParsley
COPY --from=gi-builder /usr/share/perl /usr/share/perl
COPY --from=gi-builder /usr/share/perl5 /usr/share/perl5
COPY --from=gi-builder /usr/lib/x86_64-linux-gnu/perl /usr/lib/x86_64-linux-gnu/perl
COPY --from=gi-builder /usr/lib/x86_64-linux-gnu/perl5 /usr/lib/x86_64-linux-gnu/perl5
COPY --from=gi-builder /usr/lib/x86_64-linux-gnu/perl-base /usr/lib/x86_64-linux-gnu/perl-base
# Locale data so C.UTF-8 (used by the poller for get_iplayer) is available
COPY --from=gi-builder /usr/lib/locale /usr/lib/locale
# get_iplayer/perl/ffmpeg shared library dependencies
COPY --from=gi-builder /stage/ /

# Backend source
COPY app/src/backend /app/src/backend

# Writable data/config dirs. Distroless runs as nonroot by default; do not use useradd/USER here.
COPY --from=gi-builder /data /data
COPY --from=gi-builder /config /config

EXPOSE 8000
VOLUME ["/data", "/config"]

ENTRYPOINT ["python", "-m", "src.backend.main"]
