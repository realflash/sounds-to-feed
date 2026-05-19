# EPIC-001: Managed get_iplayer

## US-001 get_iplayer kept up-to-date

As a user I want get_iplayer to be kept up-to-date automatically so that I always have the latest version. As an administrator I want to be able to simply rebuild the container to pick up the latest get_iplayer.

### Acceptance Criteria

- [x] When the container is built, the latest version of get_iplayer is installed.
- [x] The container is distroless
- [x] Any configuration needed by get_iplayer is included in the container image
- [x] The service should be designed to run constantly, so that a player can pick up the latest episodes on demand.

## US-002 Managing episodes

As a user I want the service to download programmes I'm interested in and make them available to me before I want to listen to them. It should retain episodes I have not yet listened to, and discard those I have. The service could use get_iplayer's PVR functionality rather than re-implementing that logic, if it makes sense.

### Acceptance Criteria

- [ ] The container is run as a service. It will run indefinitely and poll for new programmes every hour. 
- [ ] For each programme defined in the configuration the following steps are taken by the service:
   - The programmes are searched for. If episodes are found that are newer than the start from date then:
      - The episodes are downloaded if they have not previously been downloaded. 
      - The episodes are named "YYYY-MM-DD_HHMM_<display name>_<episode_name>.<ext>" or similar.
- [ ] The service's operation is logged to the console using a structured format (JSON).
- [ ] The service should not re-download episodes that have already been downloaded.
- [ ] The service should not re-download episodes that have been downloaded previously, and then intentionally deleted from the filesystem by the service itself. These episodes should be considered "served", and no longer required. 
- [ ] The service should re-download an episode if it has been deleted for any other reason (such as infrastructure failure)

## US-003 Configurable feed management

As an administrator I want to be able to update to easily specify the programmes the service should download and manage.

### Acceptance Criteria

- [ ] A JSON file mounted inside the container is checked for programmes to download and other configuration. The file contains an array of programmes:
   - A programme name as get_iplayer knows it
   - A start from date (optional)
   - A display name (optional)
     It may contain additional configuration.
- [ ] The configuration file is re-read by the service on each poll, so changes will take effect without a rebuild of the container.
- [ ] The directory for storing the downloaded files is defined in the configuration.
- [ ] The directory for storing the downloaded files should be a volume mount.

## US-004 Podcast feed conversion

As a user I want the service to convert the programme files it downloads into podcast feeds so that I can consume them in a podcast player.

### Acceptance Criteria

- [ ] A podcast feed is generated consisting of a single RSS feed for all programmes, with one entry per episode.
- [ ] The feed is ordered by date and time of the broadcast (oldest first).
- [ ] Each feed entry includes a link to the audio file.
- [ ] The podcast feed is served over HTTP on a port number defined an environment variable.
- [ ] The podcast feed is generated in a format that is compatible with the podcast player AntennaPod running on Android.
- [ ] The metadata added to the feed includes all of the metadata about the programme that is available from get_iplayer, embedded within the podcast feed.
- [ ] The podcast feed should be updated in place, so that the feed is always up to date.
- [ ] Once the first client has successfully downloaded an episode, it should no longer be available in the podcast feed for download, and the audio file should be deleted from the filesystem if a global config property "delete_on_download" is set to true.
- [ ] Any subsequent attempts to download the same episode should be replied to with an HTTP 404.
