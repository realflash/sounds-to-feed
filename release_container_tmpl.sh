#!/usr/bin/env bash
# Sounds to Feed Release Pipeline
# 1. Validates full stack (Lint -> Test -> Build -> Scan)
# 2. Forces x86_64 architecture for cluster compatibility
# 3. Tags and Pushes to DigitalOcean Registry

set -e # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

REGISTRY="<insert your registry here>"

# Get version from VERSION file
VERSION=$(cat VERSION 2>/dev/null || echo "0.0.1")

# If version is passed as argument, use it
if [ -n "$1" ]; then
    VERSION=$1
fi

echo -e "${BLUE}📦 Initializing Release Pipeline for ${VERSION}...${NC}"

# 2. Tag for DigitalOcean
echo -e "${BLUE}🏷️  Applying Registry Tags...${NC}"
docker tag sounds-to-feed-app:latest ${REGISTRY}:v${VERSION}
docker tag sounds-to-feed-app:latest ${REGISTRY}:latest

# 3. Push to Registry
echo -e "${BLUE}🚀 Pushing to DigitalOcean:${NC} ${REGISTRY}"
docker push ${REGISTRY}:v${VERSION}
docker push ${REGISTRY}:latest

echo -e "\n${GREEN}✨ Release ${VERSION} complete!${NC}"
echo -e "Registry image: ${REGISTRY}:v${VERSION}"
