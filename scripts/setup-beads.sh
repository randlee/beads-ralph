#!/bin/bash
# Setup script for beads-ralph dependencies
# Installs: beads CLI (bd), Dolt, and configures database

set -e

BEADS_REPO="${BEADS_REPO:-$HOME/Documents/github/beads}"
BEADS_VERSION="${BEADS_VERSION:-v0.49.6}"

echo "🔧 beads-ralph Setup"
echo "===================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command_exists go; then
    echo -e "${RED}✗ Go is not installed${NC}"
    echo "  Install from: https://go.dev/dl/"
    exit 1
fi
echo -e "${GREEN}✓ Go $(go version | awk '{print $3}')${NC}"

if ! command_exists brew && [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${YELLOW}⚠ Homebrew not found (optional but recommended)${NC}"
    echo "  Install from: https://brew.sh"
fi

# Install Dolt
echo ""
echo "Installing Dolt..."
if command_exists dolt; then
    DOLT_VERSION=$(dolt version | head -1)
    echo -e "${GREEN}✓ Dolt already installed: ${DOLT_VERSION}${NC}"
else
    if command_exists brew; then
        echo "  Using Homebrew..."
        brew install dolt
    else
        echo "  Using install script..."
        curl -L https://github.com/dolthub/dolt/releases/latest/download/install.sh | bash
    fi
    echo -e "${GREEN}✓ Dolt installed: $(dolt version)${NC}"
fi

# Install bd CLI (beads)
echo ""
echo "Installing bd CLI (beads)..."

if command_exists bd; then
    BD_VERSION=$(bd version 2>&1 | head -1)
    echo -e "${YELLOW}⚠ bd already installed: ${BD_VERSION}${NC}"
    read -p "  Reinstall? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "  Skipping bd installation"
        BD_INSTALLED=true
    fi
fi

if [[ "$BD_INSTALLED" != "true" ]]; then
    # Check for local beads repo (for development builds)
    if [[ -d "$BEADS_REPO/.git" ]]; then
        echo "  Building from source: $BEADS_REPO"
        cd "$BEADS_REPO"

        # Build with CGO for Dolt support
        echo "  Building with CGO_ENABLED=1 for Dolt backend..."
        CGO_ENABLED=1 go build -o "$HOME/bin/bd" ./cmd/bd

        if [[ ! -d "$HOME/bin" ]]; then
            mkdir -p "$HOME/bin"
        fi

        # Add ~/bin to PATH if not already there
        if [[ ":$PATH:" != *":$HOME/bin:"* ]]; then
            echo "  Adding ~/bin to PATH..."
            if [[ -f "$HOME/.zshrc" ]]; then
                echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
                echo "  Added to ~/.zshrc (reload with: source ~/.zshrc)"
            elif [[ -f "$HOME/.bashrc" ]]; then
                echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
                echo "  Added to ~/.bashrc (reload with: source ~/.bashrc)"
            fi
        fi

        cd - > /dev/null
        echo -e "${GREEN}✓ bd built from source: $(bd version)${NC}"
    else
        echo "  Downloading release binary..."

        # Detect architecture
        ARCH=$(uname -m)
        if [[ "$ARCH" == "arm64" ]]; then
            BINARY_URL="https://github.com/steveyegge/beads/releases/download/${BEADS_VERSION}/beads_${BEADS_VERSION#v}_darwin_arm64.tar.gz"
        elif [[ "$ARCH" == "x86_64" ]]; then
            BINARY_URL="https://github.com/steveyegge/beads/releases/download/${BEADS_VERSION}/beads_${BEADS_VERSION#v}_darwin_amd64.tar.gz"
        else
            echo -e "${RED}✗ Unsupported architecture: $ARCH${NC}"
            exit 1
        fi

        echo "  Downloading: $BINARY_URL"
        cd /tmp
        curl -LO "$BINARY_URL"
        tar -xzf "beads_${BEADS_VERSION#v}_darwin_${ARCH}.tar.gz"

        mkdir -p "$HOME/bin"
        mv bd "$HOME/bin/"
        chmod +x "$HOME/bin/bd"
        rm "beads_${BEADS_VERSION#v}_darwin_${ARCH}.tar.gz"

        echo -e "${YELLOW}⚠ Pre-built binaries don't include CGO/Dolt support${NC}"
        echo "  For Dolt backend, build from source with CGO_ENABLED=1"
        echo -e "${GREEN}✓ bd installed: $(bd version)${NC}"
    fi
fi

# Initialize beads database
echo ""
echo "Initializing beads database..."
cd "$(git rev-parse --show-toplevel)"

if [[ -d ".beads" ]]; then
    echo -e "${GREEN}✓ .beads/ directory exists${NC}"
else
    echo "  Running: bd init"
    bd init
    echo -e "${GREEN}✓ beads database initialized${NC}"
fi

# Check database backend
echo ""
echo "Database Configuration:"
if [[ -f ".beads/metadata.json" ]]; then
    BACKEND=$(jq -r '.backend // "sqlite"' .beads/metadata.json)
    echo "  Backend: $BACKEND"

    if [[ "$BACKEND" == "dolt" ]]; then
        echo -e "${YELLOW}⚠ Dolt backend configured${NC}"
        echo "  For DoltHub remote access, set environment variable:"
        echo "    export DOLT_REMOTE_PASSWORD='your-dolthub-token'"
        echo "  Create token at: https://www.dolthub.com/settings/tokens"
    fi
fi

# Verify setup
echo ""
echo "Verifying setup..."
bd info --json > /dev/null 2>&1 && echo -e "${GREEN}✓ bd database accessible${NC}" || echo -e "${RED}✗ bd database not accessible${NC}"

# Python dependencies
echo ""
echo "Installing Python dependencies..."
cd scripts
if [[ -f "requirements.txt" ]]; then
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Python dependencies installed${NC}"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "Quick test:"
echo "  bd version"
echo "  bd info --json"
echo "  python3 scripts/validate-bead-schema.py examples/example-work-bead.json"
echo ""
echo "For DoltHub access:"
echo "  1. Create account at https://www.dolthub.com"
echo "  2. Create API token at https://www.dolthub.com/settings/tokens"
echo "  3. export DOLT_REMOTE_PASSWORD='your-token'"
echo ""
