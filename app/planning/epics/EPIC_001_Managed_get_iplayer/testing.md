# Testing Strategy: EPIC-001

## Unit Tests
- `test_config_manager.py`: Verify JSON parsing, handling of optional fields, and error handling for malformed config.
- `test_downloader.py`: Mock `subprocess.run` to verify `get_iplayer` is called with correct arguments and correct file naming conventions.
- `test_rss_generator.py`: Verify XML generation meets AntennaPod compatibility requirements and correctly embeds metadata.

## Integration Tests
- `test_api.py`: Use FastAPI `TestClient` to verify the RSS feed endpoint returns valid XML and correct HTTP status codes.
- `test_file_serving.py`: Verify that downloading a file via the API succeeds, and that the file is deleted afterward if the global config `delete_on_download` is set.
- `test_state_management.py`: Verify that the service does not re-download intentionally deleted files, but does re-download files deleted by infrastructure failure.

## End-to-End (E2E) Tests
- Spin up the container with a mock `get_iplayer` script to simulate downloads.
- Verify the service polls and "downloads" files based on a mounted `config.json`.
- Request the podcast feed via HTTP, parse the RSS, and request an audio file URL.
- Verify the audio file is successfully downloaded by the client and subsequently deleted from the mounted volume.
