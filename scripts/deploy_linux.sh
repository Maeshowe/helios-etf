#!/bin/bash
# HELIOS ETF FLOW - Linux Server Deployment Script
#
# Usage: ./scripts/deploy_linux.sh
#
# Prerequisites:
#   - Python 3.11+
#   - uv (https://docs.astral.sh/uv/)
#   - Git

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== HELIOS ETF FLOW Linux Deployment ===${NC}"

# Configuration - uses current directory
INSTALL_DIR="$(pwd)"

echo "Install directory: ${INSTALL_DIR}"

# Step 1: Check Python version
echo -e "\n${GREEN}[1/5] Checking Python version...${NC}"
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.11"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python 3.11+ required. Found: ${PYTHON_VERSION}${NC}"
    exit 1
fi
echo "Python ${PYTHON_VERSION} OK"

# Step 2: Check uv
echo -e "\n${GREEN}[2/5] Checking uv...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}uv not found. Installing...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi
UV_VERSION=$(uv --version 2>&1)
echo "uv: ${UV_VERSION} OK"

# Step 3: Install dependencies
echo -e "\n${GREEN}[3/5] Installing dependencies...${NC}"
uv sync
echo "Dependencies installed"

# Step 4: Create required directories
echo -e "\n${GREEN}[4/5] Creating data directories...${NC}"
mkdir -p "${INSTALL_DIR}/data/raw/polygon"
mkdir -p "${INSTALL_DIR}/data/raw/unusual_whales"
mkdir -p "${INSTALL_DIR}/data/processed/helios"

# Step 5: Check for .env file
echo -e "\n${GREEN}[5/5] Checking configuration...${NC}"
if [ ! -f "${INSTALL_DIR}/.env" ]; then
    echo -e "${YELLOW}Warning: .env file not found. Creating from template...${NC}"
    cp "${INSTALL_DIR}/.env.example" "${INSTALL_DIR}/.env"
    echo -e "${YELLOW}Please edit ${INSTALL_DIR}/.env with your API keys${NC}"
else
    echo ".env file found"
fi

# Verify installation
echo -e "\n${GREEN}Verifying installation...${NC}"
uv run python -c "from helios.pipeline.daily import DailyPipeline; print('Import OK')" && echo "Installation successful!"

echo -e "\n${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Next steps:"
echo "  1. Edit .env file with your API keys (POLYGON_KEY required, UW_API_KEY recommended)"
echo "  2. Copy systemd files:"
echo "     sudo cp scripts/helios-daily.service /etc/systemd/system/"
echo "     sudo cp scripts/helios-daily.timer /etc/systemd/system/"
echo "     sudo cp scripts/helios-dashboard.service /etc/systemd/system/"
echo "  3. Enable services:"
echo "     sudo systemctl daemon-reload"
echo "     sudo systemctl enable --now helios-daily.timer"
echo "     sudo systemctl enable --now helios-dashboard"
echo "  4. Configure nginx for https://helios.ssh.services"
echo ""
echo "Manual run: uv run python scripts/run_daily.py --verbose"
