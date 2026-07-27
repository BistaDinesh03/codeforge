# Contributing to CodeForge

Thank you for your interest in contributing! This guide will help you get started.

## Code of Conduct

Be respectful, be helpful, be kind. We're building something together.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git
- VS Code
- ADB (for testing phone connection)

### Development Setup

1. **Fork and clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/codeforge.git
   cd codeforge
Backend setup

bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e .
pip install pytest pytest-asyncio httpx
Extension setup

bash
cd vscode-extension
npm install
npm run compile
Run tests

bash
# Backend tests
cd backend && python -m pytest tests/ -v

# Extension compile check
cd vscode-extension && npm run compile
Project Structure
text
codeforge/
├── backend/           # Python FastAPI server
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── core/      # Config, logging
│   │   └── services/  # Business logic
│   └── tests/         # Backend tests
├── vscode-extension/  # VS Code extension (TypeScript)
│   └── src/           # Extension source
├── scripts/           # Setup and CLI scripts
└── docs/              # Documentation
Commit Convention
We follow Conventional Commits:

feat: — New feature

fix: — Bug fix

docs: — Documentation changes

test: — Adding or updating tests

refactor: — Code restructuring (no feature change)

chore: — Maintenance tasks

Examples:

text
feat: add code generation with diff preview
fix: handle empty message in chat endpoint
docs: update setup guide for Termux
test: add diagnostics endpoint tests
Pull Request Process
Create a feature branch: git checkout -b feat/my-feature

Make your changes

Write or update tests

Run all tests to ensure nothing breaks

Update documentation if needed

Commit with conventional commit message

Push and create a pull request

Wait for review

Code Style
Python
Follow PEP 8

Use type hints

Document functions with docstrings

4 spaces for indentation

TypeScript
Use strict mode (already configured)

Prefer const over let

Document public methods

2 spaces for indentation

Testing
Every new endpoint needs a test

Every new service needs a test

Run python -m pytest tests/ -v before committing

Tests must pass in CI to merge

Questions?
Open an issue for bugs or feature requests

Start a discussion for questions

Tag maintainers for review

License
By contributing, you agree that your contributions will be licensed under the MIT License.

text

Save and close.

---

**Type "Next" when done.**
