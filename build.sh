#!/bin/bash

# Build script for job-Tracker Docker image
set -e

# Get the version from VERSION file
VERSION=$(cat VERSION)
IMAGE_NAME="job-tracker"

echo "🚀 Building job-Tracker Docker image..."
echo "📦 Version: $VERSION"

# Clean up older versions of the image
echo "🧹 Cleaning up older images..."

# Parse current version
IFS='.' read -r MAJOR MINOR PATCH <<< "$VERSION"

# Find and remove older images (keeping current version and latest)
for img in $(docker images --format "{{.Repository}}:{{.Tag}}" | grep "^$IMAGE_NAME:" | grep -v "latest" | grep -v "$VERSION"); do
  if [[ $img =~ $IMAGE_NAME:([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
    IMG_MAJOR="${BASH_REMATCH[1]}"
    IMG_MINOR="${BASH_REMATCH[2]}"
    IMG_PATCH="${BASH_REMATCH[3]}"

    # Only remove if it's an older version
    if [[ "$IMG_MAJOR" -lt "$MAJOR" ]] ||
       [[ "$IMG_MAJOR" -eq "$MAJOR" && "$IMG_MINOR" -lt "$MINOR" ]] ||
       [[ "$IMG_MAJOR" -eq "$MAJOR" && "$IMG_MINOR" -eq "$MINOR" && "$IMG_PATCH" -lt "$PATCH" ]]; then
      echo "Removing older image: $img"
      docker rmi "$img" 2>/dev/null || echo "Failed to remove $img"
    fi
  fi
done

# Remove existing 'latest' tag (will be recreated)
docker rmi "$IMAGE_NAME:latest" 2>/dev/null || echo "No existing 'latest' image to remove"

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t "$IMAGE_NAME:$VERSION" -t "$IMAGE_NAME:latest" .

echo "✅ Build completed successfully!"
echo "📋 Created images:"
echo "   - $IMAGE_NAME:$VERSION"
echo "   - $IMAGE_NAME:latest"

# Show the built images
echo ""
echo "📦 Docker images:"
docker images | grep "$IMAGE_NAME" || echo "No images found with name $IMAGE_NAME"
