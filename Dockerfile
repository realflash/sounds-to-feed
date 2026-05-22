# Stage 1: Build Backend Environment
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS backend-builder
WORKDIR /app
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY app/pyproject.toml app/uv.lock* ./
RUN if [ -f uv.lock ]; then uv export --no-dev --format requirements-txt > requirements.txt; else uv pip compile pyproject.toml -o requirements.txt; fi
RUN uv pip install --system --no-cache -r requirements.txt

# Stage 2: Production (Distroless-like Python Slim)
# We use python slim to be able to install perl and get_iplayer, then we purge package managers
FROM python:3.12-slim

WORKDIR /app

# Install get_iplayer dependencies
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
    # Clean up to make it as "distroless" as possible
    apt-get purge -y curl && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/apt/archives/*

# Set runtime environment
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1

# Copy Python site-packages and binaries from builder
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Remove pip and build tools to reduce vulnerabilities and make it more distroless-like
RUN python -m pip uninstall -y pip setuptools wheel || true

# Copy backend source
COPY app/src/backend /app/src/backend

# Create a non-root user
RUN useradd -m -s /usr/sbin/nologin appuser && \
    mkdir -p /data /config && \
    chown appuser:appuser /data /config

USER appuser

VOLUME ["/data", "/config"]

ENTRYPOINT ["python", "-m", "src.backend.main"]
