#!/usr/bin/env bash
# Build and run the get_iplayer smoke test on the standard base image pattern.
set -euo pipefail

cd "$(dirname "$0")/.."

cat << 'DOCKERFILE' > Dockerfile.test
# syntax=docker/dockerfile:1
# Smoke test for the standard base image pattern used by Sounds to Feed.
FROM registry.digitalocean.com/attono/attono-base:latest AS deps

ARG GETIPLAYER_VERSION=v3.36

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

RUN curl -fsSL "https://raw.githubusercontent.com/get-iplayer/get_iplayer/${GETIPLAYER_VERSION}/get_iplayer" \
        -o /usr/local/bin/get_iplayer && \
    chmod +x /usr/local/bin/get_iplayer

FROM deps
RUN /usr/local/bin/attono-harden

ENTRYPOINT ["/usr/bin/perl", "/usr/local/bin/get_iplayer", "--version"]
DOCKERFILE

docker build --load -t test-attono-base -f Dockerfile.test .
docker run --rm test-attono-base
