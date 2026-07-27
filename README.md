# CodeForge

> Turn your Android phone into a private AI coding server for VS Code.

[![CI/CD](https://github.com/codeforge/codeforge/actions/workflows/ci.yml/badge.svg)](https://github.com/codeforge/codeforge/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/codeforge/codeforge/releases)

## What is CodeForge?

CodeForge runs AI coding models on your Android phone and connects to VS Code via USB. No cloud, no subscriptions, no data leaving your device. Your phone becomes your private AI pair programmer.

## Why CodeForge?

- **Private**: All code stays on your devices. Nothing sent to the cloud.
- **Free**: No API keys, no subscriptions. Use models you download.
- **Offline**: Works without internet. Your phone + USB cable is all you need.
- **Open Source**: MIT licensed. Audit, modify, contribute.

## Architecture
VS Code (Windows/Mac/Linux)
│
│ USB / ADB
▼
Android Phone (Termux)
├── FastAPI Server (Python)
├── llama.cpp (C++ inference engine)
└── AI Model (GGUF format)

text

## Quick Start

### Prerequisites
- Android phone with Termux installed
- USB cable
- VS Code
- ADB installed on your computer

### Setup (2 commands)

**On your computer:**
```powershell
git clone https://github.com/codeforge/codeforge.git
cd codeforge
.\scripts\codeforge.ps1 setup
On your phone (Termux):

bash
curl -sL https://raw.githubusercontent.com/codeforge/codeforge/main/scripts/setup-android.sh | bash
Usage
Start the server on your phone:

bash
cd ~/codeforge/backend && uvicorn app.main:app --host 0.0.0.0 --port 8000
Connect from VS Code:

Press Ctrl+Shift+P

Run CodeForge: Connect to Android

Run CodeForge: Open Chat

Use code actions:

Select code → Right-click → Explain / Rewrite / Generate

Features
Chat: Ask questions about your code

Explain Code: Select code → Get plain-English explanation

Generate Code: Describe what you want → AI generates it

Rewrite Code: Select messy code → AI cleans it up

Diff Preview: See changes side-by-side before accepting

Offline: Fully local, no internet needed after setup

Documentation
Setup Guide

API Documentation

Architecture

Contributing

Roadmap
See ROADMAP.md for planned features.

License
MIT — see LICENSE for details.

Acknowledgments
llama.cpp — Efficient LLM inference

FastAPI — Python web framework

Termux — Android terminal emulator

text

Save and close.

---

**Type "Next" when done.**
