# EPIC-002 Time-based Expiry

## US-001 Automatic Episode Expiry

As a user I have observed that the previous strategy of marking an episode downloaded once the user appears to have completely downloaded it is not working. Large gaps have appeared in the list of episodes successfully by the client, and the client's built-in functionality to-reattempt downloads does not work because the episodes have been deleted from the service. I would like the service to automatically expire episodes after a configurable period of time so that they are moved to a "served" state and no longer required for download management instead.

### Acceptance Criteria

- [x] The service implements a time-based expiry mechanism to automatically mark episodes as "served" after a configurable duration (e.g., 7 days).
- [x] The expiry check runs at regular intervals (e.g., every hour) alongside the existing hourly polling for new content.
- [x] The service maintains a record of when each episode was first downloaded to calculate the expiry timestamp.
- [x] Once an episode expires, it is moved to a "served" state and no longer required for download management. The episode file is deleted from the filesystem.
- [x] The service logs expiry events to the console using structured JSON format, including the episode ID and expiry timestamp.
- [x] The expiry duration is configurable via the existing JSON configuration file (e.g., `expiry_days` field).
- [x] The service no longer expires episodes when it thinks the user has successfully completed the download.