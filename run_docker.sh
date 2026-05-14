#!/usr/bin/env bash
# Script to launch the Docker container with build information
# Standard Version: 0.2

# Configuration
PROJECT_NAME="project-name"
IMAGE_NAME="${PROJECT_NAME}:latest"
CONTAINER_NAME="${PROJECT_NAME}-app"
DB_FILE_LOCAL="./data/test-data.db"
DB_FILE_CONTAINER="/app/test-data.db"

# Ensure data directory exists
mkdir -p ./data

# If the database file exists, back it up and start fresh to ensure "clean db"
if [ -f "$DB_FILE_LOCAL" ]; then
    echo "Backing up existing database to ${DB_FILE_LOCAL}.bak"
    mv "$DB_FILE_LOCAL" "${DB_FILE_LOCAL}.bak"
fi

# Create an empty database file
touch "$DB_FILE_LOCAL"

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    export $(grep -v '^#' .env | xargs)
fi

# Get the current Build ID from the source code
CURRENT_BUILD_ID=$(make info 2>/dev/null | grep "Build ID:" | cut -d' ' -f3)

# Check if the 'latest' image actually matches this Build ID
IMAGE_ID_LATEST=$(docker inspect --format='{{.Id}}' "$IMAGE_NAME" 2>/dev/null)
IMAGE_ID_VER=$(docker inspect --format='{{.Id}}' "${PROJECT_NAME}:$CURRENT_BUILD_ID" 2>/dev/null)

if [ "$IMAGE_ID_LATEST" == "$IMAGE_ID_VER" ] && [ -n "$IMAGE_ID_LATEST" ]; then
    DISPLAY_VERSION="$CURRENT_BUILD_ID"
else
    # Fallback: if they differ or versioned image doesn't exist, detectives from tags
    DETECTED_BUILD_ID=$(docker inspect --format='{{range .RepoTags}}{{.}} {{end}}' "$IMAGE_NAME" 2>/dev/null | tr ' ' '\n' | grep -v ':latest' | head -n 1 | cut -d':' -f2)
    DISPLAY_VERSION=${DETECTED_BUILD_ID:-"Unknown"}
fi

echo "Stopping and removing existing container if it exists..."
docker stop "$CONTAINER_NAME" 2>/dev/null
docker rm "$CONTAINER_NAME" 2>/dev/null

echo "Launching fresh container ($DISPLAY_VERSION)..."
docker run -d \
    --name "$CONTAINER_NAME" \
    -p 8000:8000 \
    -v "$(pwd)/data/test-data.db:$DB_FILE_CONTAINER" \
    -e SECRET_KEY \
    -e AUTO_SEED_DATA \
    "$IMAGE_NAME"

echo "------------------------------------------------"
echo "Container $CONTAINER_NAME is running at http://localhost:8000"
echo "Database is mounted at: $DB_FILE_LOCAL"
echo "View logs with: docker logs -f $CONTAINER_NAME"
echo "------------------------------------------------"
