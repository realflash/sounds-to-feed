---
description: How to carry out a release of the container
---

1. Look at the list of local docker images for this app. If the ID of the latest image that does not include the repository name matches that of the latest image that does include the repository name, then a new version needs to be created. Bearing in mind the semantic versioning in use:
   * bump the VERSION file in the root of the app repository by one patch number
   * Build the container
2. We should now have a local image that has a later semantic version than the one in the registry. Create the relevant alias of this image in preparation for pushing to the repository. The registry path to prepend to the image is 'registry.digitalocean.com/attono/'
3. Run `doctl registry login`
4. Push the new alias to the repository.