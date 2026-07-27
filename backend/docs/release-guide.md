# Release Guide

Checklist for publishing a new CodeForge release.

## Before Release

- [ ] All tests pass: `cd backend && python -m pytest tests/ -v`
- [ ] Extension compiles: `cd vscode-extension && npm run compile`
- [ ] CHANGELOG.md updated with new version
- [ ] Version bumped in:
  - [ ] `backend/pyproject.toml`
  - [ ] `backend/app/core/config.py`
  - [ ] `vscode-extension/package.json`
- [ ] Documentation reviewed for accuracy
- [ ] Breaking changes documented

## Create GitHub Release

1. Go to [Releases](https://github.com/codeforge/codeforge/releases)
2. Click "Draft a new release"
3. Tag version: `v0.1.0` (use semver)
4. Release title: `CodeForge v0.1.0`
5. Copy relevant section from CHANGELOG.md
6. Attach files:
   - [ ] Backend source (zip)
   - [ ] Extension VSIX (if built)
7. Click "Publish release"

## After Release

- [ ] Verify release page looks correct
- [ ] Announce in relevant communities
- [ ] Update any external documentation links

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

| Type | When | Example |
|------|------|---------|
| MAJOR | Breaking changes | 1.0.0, 2.0.0 |
| MINOR | New features | 0.1.0, 0.2.0 |
| PATCH | Bug fixes | 0.1.1, 0.1.2 |

## VS Code Marketplace (Future)

When ready for Marketplace:
- [ ] Create publisher account at [marketplace.visualstudio.com](https://marketplace.visualstudio.com/)
- [ ] Generate Personal Access Token
- [ ] Run `vsce publish`
- [ ] Verify listing page