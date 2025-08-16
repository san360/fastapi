#!/bin/bash

# Docker Run Script for FastAPI Auto Sign-In Agent
# This script builds and runs the application using Docker

set -e

echo "🐳 FastAPI Auto Sign-In Agent - Docker Deployment"
echo "=================================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📝 Please copy .env.docker to .env and configure your Azure credentials:"
    echo "   cp .env.docker .env"
    echo "   # Then edit .env with your actual values"
    echo "   # Make sure to set HOST=0.0.0.0 for Docker"
    exit 1
fi

# Build the Docker image
echo "🔨 Building Docker image..."
echo "Using docker-compose for better environment handling..."

# Stop existing container if running
echo "🛑 Stopping existing container (if any)..."
docker-compose down 2>/dev/null || true

# Run the container
echo "🚀 Starting new container..."
docker-compose up -d --build

if [ $? -eq 0 ]; then
    echo "✅ Container started successfully!"
    echo "📊 Container status:"
    docker ps --filter name=fastapi-auto-signin-agent --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    echo "❌ Failed to start container!"
    echo "📋 Check logs with: docker-compose logs fastapi-agent"
    exit 1
fi

echo ""
echo "🌐 Application URLs:"
echo "   • Health Check: http://localhost:3978/health"
echo "   • API Docs:     http://localhost:3978/docs"
echo "   • Root:         http://localhost:3978/"

echo ""
echo "📋 Useful commands:"
echo "   • View logs:    docker-compose logs -f fastapi-agent"
echo "   • Stop:         docker-compose down"
echo "   • Restart:      docker-compose restart fastapi-agent"
echo "   • Rebuild:      docker-compose up -d --build"
