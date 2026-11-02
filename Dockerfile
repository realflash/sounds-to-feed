# syntax=docker/dockerfile:1

# ============================================================================
# Sounds to Feed — production image built on the Attono standard base image.
# The final image IS the dependency stage, hardened in place with attono-harden.
#
# Company standard: /workspace/product_standards/base/README.md
#   FROM registry.digitalocean.com/attono/attono-base:latest AS deps
#   ... install product deps ...
#   FROM deps
#   RUN /usr/local/bin/attono-harden
#   ENTRYPOINT [<JSON array>]
#
# The base ships current-stable Debian + Python 3.13 + Node/npm + uv +
# attono-harden. We never hardcode a Python minor version or a distro path.
# ============================================================================

# Stage 1: product dependency stage on the shared rolling standard base (has
# shell + apt, which is exactly why dependencies are installed here).
FROM registry.digitalocean.com/attono/attono-base:latest AS deps

WORKDIR /app

# Accepted so `make build-container`'s --build-arg VITE_BUILD_ID=... is not an
# error. This product has no frontend/Vite build; the value is intentionally unused.
ARG VITE_BUILD_ID=unused

# Pin get_iplayer to a real upstream release tag (not master) for reproducibility.
ARG GETIPLAYER_VERSION=v3.36

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Product-specific toolchain (installed in the deps stage — the full-filesystem
# design guarantees their shared libraries carry into the final image):
#  - perl + the Perl modules get_iplayer requires
#    (XML::Simple, LWP::Protocol::https, Mojo, CGI)
#  - ffmpeg (download/remux), AtomicParsley (MP4 tagging)
#  - ca-certificates (TLS to BBC / GitHub)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        perl \
        libxml-simple-perl \
        liblwp-protocol-https-perl \
        libmojolicious-perl \
        libcgi-pm-perl \
        ffmpeg \
        atomicparsley \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# get_iplayer, PINNED to a tagged release (NOT master) so image rebuilds are
# reproducible and auditable.
RUN curl -fsSL "https://raw.githubusercontent.com/get-iplayer/get_iplayer/${GETIPLAYER_VERSION}/get_iplayer" \
        -o /usr/local/bin/get_iplayer && \
    chmod +x /usr/local/bin/get_iplayer

# Python dependencies. Re-resolve on every build so container rebuilds pick up
# security fixes automatically (local dev keeps using the committed uv.lock),
# export to a requirements file, then install into the base's system Python.
# System Python is PEP 668 externally-managed, hence --break-system-packages.
COPY app/pyproject.toml app/uv.lock* ./
RUN uv lock --upgrade && \
    uv export --no-dev --format requirements-txt > /tmp/requirements.txt && \
    uv pip install --system --break-system-packages --no-cache -r /tmp/requirements.txt && \
    rm -f /tmp/requirements.txt

# Backend source. This product does not install its own package, so PYTHONPATH
# above points the interpreter at /app.
COPY app/src/backend /app/src/backend

# The base's system Python may only be exposed as `python3`; the ENTRYPOINT and
# the app invoke `python`. Link it WITHOUT hardcoding a Python minor version.
RUN ln -sf "$(command -v python3)" /usr/local/bin/python && \
    python --version

# Writable runtime dirs (SQLite state under /data, config under /config).
RUN mkdir -p /data /config

# Record product-specific components and the justification for each pin in the
# image's inherited /attono/manifest.json so the image stays interrogable.
RUN python3 - <<'PY'
import json, os

path = "/attono/manifest.json"
try:
    with open(path) as fh:
        manifest = json.load(fh)
except (FileNotFoundError, ValueError):
    manifest = {}

manifest["product"] = "sounds-to-feed"
components = manifest.get("product_components", [])
components.extend([
    {
        "name": "get_iplayer",
        "version": os.environ.get("GETIPLAYER_VERSION", "v3.36"),
        "pin_reason": "Pinned to a tagged upstream release (not master) so image "
                      "rebuilds are reproducible and auditable.",
    },
    {
        "name": "perl",
        "version": "debian-current-stable",
        "pin_reason": "Runtime interpreter for get_iplayer.",
    },
    {
        "name": "libxml-simple-perl",
        "version": "debian-current-stable",
        "pin_reason": "get_iplayer XML parsing; from current-stable Debian for security updates.",
    },
    {
        "name": "liblwp-protocol-https-perl",
        "version": "debian-current-stable",
        "pin_reason": "get_iplayer HTTPS downloads; from current-stable Debian for security updates.",
    },
    {
        "name": "libmojolicious-perl",
        "version": "debian-current-stable",
        "pin_reason": "get_iplayer dependency; from current-stable Debian for security updates.",
    },
    {
        "name": "libcgi-pm-perl",
        "version": "debian-current-stable",
        "pin_reason": "get_iplayer dependency; from current-stable Debian for security updates.",
    },
    {
        "name": "ffmpeg",
        "version": "debian-current-stable",
        "pin_reason": "Media download/remux used by get_iplayer; from current-stable Debian.",
    },
    {
        "name": "atomicparsley",
        "version": "debian-current-stable",
        "pin_reason": "MP4 metadata tagging used by get_iplayer; from current-stable Debian.",
    },
])
manifest["product_components"] = components

with open(path, "w") as fh:
    json.dump(manifest, fh, indent=2, sort_keys=True)
PY

# ============================================================================
# Stage 2: final image — the deps stage itself, hardened IN PLACE.
# No COPY --from=<builder>: every resolved file (incl. .so) is inherited.
# After attono-harden there is no shell/apt/curl/wget, so no further RUN that
# needs them and the ENTRYPOINT must be a JSON array.
# ============================================================================
FROM deps
RUN /usr/local/bin/attono-harden

EXPOSE 8000
VOLUME ["/data", "/config"]

ENTRYPOINT ["python", "-m", "src.backend.main"]
