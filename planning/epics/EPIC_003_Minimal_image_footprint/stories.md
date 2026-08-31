# EPIC-003: Minimal Image Footprint

## US-001 Static ffmpeg binary

As an administrator I want the container to bundle ffmpeg as a single static binary so that the image does not carry ffmpeg's large shared-library dependency tree (libav*, libsw*, libx264, etc.), reducing both the image size and the number of third-party libraries that form the attack surface.

### Acceptance Criteria

- [ ] The Dockerfile provides ffmpeg as a self-contained static binary instead of installing the `ffmpeg` apt package.
- [ ] The `libav*`, `libsw*`, `libx264` and other shared libraries pulled in by the apt `ffmpeg` package are no longer present in the image.
- [ ] `get_iplayer` can still invoke `ffmpeg` successfully (verified by a download/conversion smoke test).
- [ ] The resulting container image is smaller than the previous build.
- [ ] The trivy container scan still passes with no fixable findings.

## US-002 Minimal Python runtime

As an administrator I want the image to carry only the Python runtime components needed to run the service so that build-only tooling is not shipped in the production image.

### Acceptance Criteria

- [ ] The Dockerfile copies only the interpreter binaries required at runtime (`python`, `python3`, `python3.12`) and the ASGI server (`uvicorn`), rather than the entire `/usr/local/bin`.
- [ ] Build-only tooling (`uv`, `pip`, `setuptools`, `wheel`) is absent from the final image.
- [ ] The service still starts and serves the feed (verified by a startup smoke test).
- [ ] The resulting container image is smaller than the previous build.
- [ ] The trivy container scan still passes with no fixable findings.

## US-003 Minimal perl dependency set

As an administrator I want the image to include only the perl modules that get_iplayer actually requires so that unused perl modules and their native dependencies are not shipped.

### Acceptance Criteria

- [ ] The Dockerfile installs only the perl packages exercised by get_iplayer's runtime download path, not a superset.
- [ ] Perl modules (and their native `.so` dependencies) that get_iplayer does not use are absent from the image.
- [ ] `get_iplayer` can still search for and download a programme successfully (verified by an E2E download).
- [ ] The resulting container image is smaller than the previous build.
- [ ] The trivy container scan still passes with no fixable findings.
