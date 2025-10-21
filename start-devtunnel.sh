#!/bin/bash
# Start DevTunnel and FastAPI Bot for local development
# Usage: ./start-devtunnel.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
TUNNEL_NAME="fastapi-bot"
PORT=3978

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  FastAPI Bot - DevTunnel Startup${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if DevTunnel is installed
echo -e "${YELLOW}Checking DevTunnel installation...${NC}"
if ! command -v devtunnel &> /dev/null; then
    echo -e "${RED}❌ DevTunnel not found!${NC}"
    echo -e "${YELLOW}Install with:${NC}"
    echo -e "  macOS: brew install devtunnel"
    echo -e "  Linux: Download from https://aka.ms/devtunnels/download"
    exit 1
fi

echo -e "${GREEN}✅ DevTunnel found${NC}"
echo ""

# Check if user is logged in
echo -e "${YELLOW}Checking DevTunnel authentication...${NC}"
if ! devtunnel user show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to DevTunnel${NC}"
    echo -e "${YELLOW}Logging in...${NC}"
    devtunnel user login
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Login failed!${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Authenticated${NC}"
echo ""

# Check if tunnel exists
echo -e "${YELLOW}Checking for existing tunnel '$TUNNEL_NAME'...${NC}"
if ! devtunnel show "$TUNNEL_NAME" &> /dev/null; then
    echo -e "${YELLOW}⚠️  Tunnel '$TUNNEL_NAME' not found. Creating...${NC}"
    devtunnel create "$TUNNEL_NAME" --allow-anonymous
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to create tunnel!${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Tunnel created${NC}"
else
    echo -e "${GREEN}✅ Tunnel exists${NC}"
fi

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Starting DevTunnel${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Start DevTunnel in background
echo -e "${YELLOW}Starting tunnel on port $PORT...${NC}"
devtunnel host "$TUNNEL_NAME" &
TUNNEL_PID=$!

# Wait for tunnel to initialize
sleep 3

# Get tunnel URL
TUNNEL_URL=$(devtunnel show "$TUNNEL_NAME" --output json | grep -o '"uri":"[^"]*' | cut -d'"' -f4)

if [ -n "$TUNNEL_URL" ]; then
    echo -e "${GREEN}✅ DevTunnel is running!${NC}"
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  Tunnel Information${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo -e "${GREEN}Public URL: $TUNNEL_URL${NC}"
    echo -e "${GREEN}Bot Endpoint: ${TUNNEL_URL}/api/messages${NC}"
    echo ""
    echo -e "${YELLOW}Update your Azure Bot messaging endpoint to:${NC}"
    echo -e "  ${TUNNEL_URL}/api/messages"
    echo ""
else
    echo -e "${YELLOW}⚠️  Could not retrieve tunnel URL${NC}"
fi

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  Starting FastAPI Application${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if virtual environment exists
if [ -f "venv/bin/activate" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment not found at ./venv${NC}"
    echo -e "${YELLOW}Continuing without venv...${NC}"
fi

echo ""
echo -e "${YELLOW}Starting FastAPI application...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop both DevTunnel and FastAPI${NC}"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  Shutting down...${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo -e "${YELLOW}Stopping DevTunnel...${NC}"
    kill $TUNNEL_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

# Register cleanup on exit
trap cleanup INT TERM EXIT

# Run FastAPI
python main.py
