#!/data/data/com.termux/files/usr/bin/bash
# ─────────────────────────────────────────────
# CodeForge Android/Termux Setup Script
# Run in Termux: bash setup-android.sh
# ─────────────────────────────────────────────

set -e  # Exit on any error

clear
echo "========================================"
echo "   CodeForge Android Setup"
echo "========================================"
echo ""

# ──────────────────────────────────────
# Step 1: Update Termux packages
# ──────────────────────────────────────
echo "[1/6] Updating Termux packages..."
pkg update -y -o Dpkg::Options::="--force-confnew" > /dev/null 2>&1
pkg upgrade -y > /dev/null 2>&1
echo "  ✓ Packages updated"
echo ""

# ──────────────────────────────────────
# Step 2: Install required packages
# ──────────────────────────────────────
echo "[2/6] Installing required packages..."
pkg install -y python git wget cmake ninja build-essential > /dev/null 2>&1
echo "  ✓ Python, Git, CMake installed"
echo ""

# ──────────────────────────────────────
# Step 3: Setup storage access
# ──────────────────────────────────────
echo "[3/6] Setting up storage access..."
if [ ! -d "$HOME/storage" ]; then
    termux-setup-storage
    echo "  ℹ Please allow storage permission when prompted"
    sleep 3
fi
echo "  ✓ Storage configured"
echo ""

# ──────────────────────────────────────
# Step 4: Create project structure
# ──────────────────────────────────────
echo "[4/6] Creating project structure..."
mkdir -p ~/codeforge/backend/app/core
mkdir -p ~/codeforge/backend/app/services
mkdir -p ~/codeforge/models
echo "  ✓ Project folders created"
echo ""

# ──────────────────────────────────────
# Step 5: Install Python packages
# ──────────────────────────────────────
echo "[5/6] Installing Python packages (this may take a few minutes)..."
pip install fastapi uvicorn pydantic > /dev/null 2>&1
echo "  ✓ FastAPI installed"

pip install llama-cpp-python > /dev/null 2>&1
echo "  ✓ llama-cpp-python installed"
echo ""

# ──────────────────────────────────────
# Step 6: Create backend files
# ──────────────────────────────────────
echo "[6/6] Creating backend files..."

# main.py
cat > ~/codeforge/backend/app/main.py << 'PYEOF'
"""Main FastAPI application for CodeForge backend."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CodeForge Backend",
    description="AI coding server running on Android via Termux",
    version="0.0.1",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.0.1", "device": "android"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"Received: {request.message}")
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    return ChatResponse(response=f"[CodeForge] You said: {request.message}")

@app.get("/")
async def root():
    return {"name": "CodeForge Backend", "message": "Running on Android via Termux"}
PYEOF

# __init__.py files
touch ~/codeforge/backend/app/__init__.py
touch ~/codeforge/backend/app/core/__init__.py
touch ~/codeforge/backend/app/services/__init__.py

echo "  ✓ Backend files created"
echo ""

# ──────────────────────────────────────
# Summary
# ──────────────────────────────────────
cat << "EOF"
========================================
   Android Setup Complete!
========================================

To start the server:
  cd ~/codeforge/backend
  uvicorn app.main:app --host 0.0.0.0 --port 8000

Then on your computer:
  adb forward tcp:8000 tcp:8000

========================================
EOF

# ──────────────────────────────────────
# Ask to start server now
# ──────────────────────────────────────
read -p "Start the server now? (y/n): " start_now
if [ "$start_now" = "y" ] || [ "$start_now" = "Y" ]; then
    echo ""
    echo "Starting server..."
    echo "Press Ctrl+C to stop"
    cd ~/codeforge/backend
    uvicorn app.main:app --host 0.0.0.0 --port 8000
fi