#!/bin/bash

# Build script for job-Tracker Docker image
set -e

# Get the version from VERSION file
VERSION=$(cat VERSION)
IMAGE_NAME="job-tracker"

echo "🚀 Building job-Tracker Docker image..."
echo "📦 Version: $VERSION"

# Remove existing images with the same tags
echo "🧹 Cleaning up existing images..."
docker rmi "$IMAGE_NAME:latest" 2>/dev/null || echo "No existing 'latest' image to remove"
docker rmi "$IMAGE_NAME:$VERSION" 2>/dev/null || echo "No existing '$VERSION' image to remove"

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
