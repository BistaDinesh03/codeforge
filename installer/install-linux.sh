#!/bin/bash
# CodeForge Server Installer for Linux
# Run: curl -sL https://codeforge.dev/install.sh | bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

INSTALL_PATH="${HOME}/codeforge-server"
MODEL="qwen-1.5b"

echo -e "${CYAN}"
echo "============================================"
echo "   CodeForge Server Installer"
echo "   Private AI Coding Assistant"
echo "============================================"
echo -e "${NC}"

# Step 1: Check Python
echo -e "${YELLOW}[1/5] Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}  Found: $PYTHON_VERSION${NC}"
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}  Found: $PYTHON_VERSION${NC}"
    PYTHON="python"
else
    echo -e "${RED}  Python not found. Installing...${NC}"
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-pip python3-venv
    PYTHON="python3"
    echo -e "${GREEN}  Python installed${NC}"
fi

# Step 2: Create directory
echo -e "${YELLOW}[2/5] Creating install directory...${NC}"
mkdir -p "$INSTALL_PATH"
echo -e "${GREEN}  Created: $INSTALL_PATH${NC}"

# Step 3: Download server
echo -e "${YELLOW}[3/5] Downloading server...${NC}"
if [ -d "../server" ]; then
    cp -r ../server/* "$INSTALL_PATH/"
else
    curl -sL https://github.com/codeforge/codeforge/archive/main.tar.gz | tar xz -C /tmp/
    cp -r /tmp/codeforge-main/server/* "$INSTALL_PATH/"
    rm -rf /tmp/codeforge-main
fi
echo -e "${GREEN}  Server downloaded${NC}"

# Step 4: Install dependencies
echo -e "${YELLOW}[4/5] Installing dependencies...${NC}"
cd "$INSTALL_PATH"
$PYTHON -m venv venv
source venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet llama-cpp-python
deactivate
echo -e "${GREEN}  Dependencies installed${NC}"

# Step 5: Download model
echo -e "${YELLOW}[5/5] Setting up AI model...${NC}"
MODEL_DIR="$INSTALL_PATH/models"
mkdir -p "$MODEL_DIR"

MODEL_URL="https://huggingface.co/bartowski/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-Coder-1.5B-Instruct-Q4_K_M.gguf"
MODEL_NAME=$(basename "$MODEL_URL")
MODEL_PATH="$MODEL_DIR/$MODEL_NAME"

if [ -f "$MODEL_PATH" ]; then
    echo -e "${GREEN}  Model already exists${NC}"
else
    echo -e "${YELLOW}  Downloading model...${NC}"
    wget -q --show-progress "$MODEL_URL" -O "$MODEL_PATH" || {
        echo -e "${YELLOW}  Download failed. Download manually to: $MODEL_DIR${NC}"
    }
fi

# Create start script
cat > "$INSTALL_PATH/start.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "Starting CodeForge Server..."
echo "Server: http://localhost:8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF
chmod +x "$INSTALL_PATH/start.sh"

# Create desktop entry
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/codeforge.desktop << EOF
[Desktop Entry]
Name=CodeForge Server
Comment=Private AI Coding Assistant
Exec=$INSTALL_PATH/start.sh
Path=$INSTALL_PATH
Terminal=true
Type=Application
Categories=Development;
EOF

echo -e "${GREEN}  Desktop shortcut created${NC}"

# Done
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Installation Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "  Start server: $INSTALL_PATH/start.sh"
echo "  Or find 'CodeForge Server' in your applications menu"
echo ""
echo "  Next: Install VS Code extension from Marketplace"
echo ""