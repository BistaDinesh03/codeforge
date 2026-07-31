# Contributing

## Quick Setup

```bash
# Backend
cd server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests/ -v

# Extension
cd extension
npm install
npm run compile
npm test
Rules
Write tests with new features

Run all tests before committing

Use feat:, fix:, docs: for commit messages

Keep it simple

Questions?
Open an issue.

text

Save. Type "NEXT."