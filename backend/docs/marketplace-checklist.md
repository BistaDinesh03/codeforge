# VS Code Marketplace Checklist

Steps to publish CodeForge on the VS Code Marketplace.

## Prerequisites

- [ ] Microsoft account
- [ ] Azure DevOps organization (free)
- [ ] Personal Access Token with Marketplace scope

## Extension Requirements

- [ ] Unique publisher ID (e.g., `codeforge-team`)
- [ ] Extension name not taken
- [ ] Icon (128x128 PNG)
- [ ] README updated for Marketplace
- [ ] LICENSE file included
- [ ] Repository URL in `package.json`

## package.json Checklist

```json
{
  "publisher": "codeforge-team",
  "icon": "images/icon.png",
  "repository": {
    "type": "git",
    "url": "https://github.com/codeforge/codeforge"
  },
  "bugs": {
    "url": "https://github.com/codeforge/codeforge/issues"
  },
  "homepage": "https://github.com/codeforge/codeforge#readme"
}