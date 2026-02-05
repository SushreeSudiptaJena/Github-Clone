#!/usr/bin/env bash
# Simple deploy helper (example):
# - Builds images with tags and optionally pushes to a registry
# - SSH into remote host and runs docker-compose pull && docker-compose up -d

set -euo pipefail

# Usage: ./scripts/deploy.sh <registry> <repo> <tag> <remote_host>
if [ "$#" -lt 4 ]; then
  echo "Usage: $0 <registry> <repo> <tag> <remote_host>"
  exit 1
fi

REGISTRY=$1
REPO=$2
TAG=$3
REMOTE_HOST=$4

BACKEND_IMAGE="$REGISTRY/$REPO-backend:$TAG"
FRONTEND_IMAGE="$REGISTRY/$REPO-frontend:$TAG"

echo "Building backend image $BACKEND_IMAGE"
docker build -t $BACKEND_IMAGE ./backend

echo "Building frontend image $FRONTEND_IMAGE"
docker build -t $FRONTEND_IMAGE --file frontend/Dockerfile.prod ./frontend

# Push images
echo "Pushing images"
docker push $BACKEND_IMAGE
docker push $FRONTEND_IMAGE

# SSH to server and pull images + restart
echo "Deploying to $REMOTE_HOST"
ssh $REMOTE_HOST "docker pull $BACKEND_IMAGE && docker pull $FRONTEND_IMAGE && docker-compose -f /path/to/your/docker-compose.prod.yml pull && docker-compose -f /path/to/your/docker-compose.prod.yml up -d"

echo "Deploy complete."
