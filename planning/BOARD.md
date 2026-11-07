# [Product Name] Project Board
<!-- Standard Version: 0.2 -->

## 📋 Backlog (Future Work)
- [ ] Example Epic A
  - [ ] Example Story 1
  - [ ] Example Story 2

## 🚀 In Progress (Active)
- [/] [EPIC-001: Managed get_iplayer](epics/EPIC_001_Managed_get_iplayer)
  - [/] [Stories](epics/EPIC_001_Managed_get_iplayer/stories.md)
- [x] BUG-2611061737: The build process does not complete even though the environment now includes the tools needed to run all build stages except those requiring docker.


## ✅ Done (Completed)
- [x] BUG-2611061737 (code-scan): Pin-healthcheck and non-root USER added to Dockerfile + app/scripts/Dockerfile.test so trivy config passes (DS-0002, DS-0026); DS-0001 remains an intentional policy ignore for the rolling base.
- [x] EPIC-002 Time-based Expiry
- [x] BUG-2606020408: Missing show notes and cover art/icon in podcast feed
- [x] tweak-feed-order: Sort feed items by mtime ascending so feedgen renders newest-first
- [x] BUG-2605231738: Poller stops downloading after 21 episodes
- [x] tweak-2605231702: US-003 Remaining criteria
- [x] BUG-2605230620: get_iplayer fails with Wide character error for titles with unicode apostrophes
- [x] tweak-2605222038 (Include publish date in download logs for EPIC-001)
- [x] tweak-2605221314 (EPIC-001 Polling & RSS generation)
- [x] BUG-2605221156: Container exits immediately because `main.py` has no entrypoint
- [x] Initial Repository Setup
- [x] BUG-2611061737 (container-scan): the rejected fix left the base's statically linked `uv`/`uvx` Rust binaries in the final image, so `trivy image --exit-code 1 --ignore-unfixed` failed the build on fixed rustls advisories (GHSA-c8m5-c952-6cm4, GHSA-h2v8-394m-p7vv, GHSA-vp88-798v-h67f, GHSA-w44r-93j7-qv28). The final stage now removes them before `attono-harden`; `app/src/backend/tests/test_build_pipeline_completes.py` pins the contract.
- BUG-2611061737: The code-scan stage still fails, duplicating the already-open and unfixed BUG-2611061737 ("The build process does not complete even though the environment now includes the tools needed to run all buil
  status: fixed
