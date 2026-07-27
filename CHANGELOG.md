# Changelog

All notable changes to CodeForge will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-07-27

### Added
- Initial project structure and repository setup
- FastAPI backend with health check endpoints
- VS Code extension with chat panel
- ADB communication layer for USB connectivity
- BM25 project search engine
- Code actions: Explain, Generate, Rewrite
- Diff preview with accept/reject workflow
- Production logging with file rotation
- Configuration management via Pydantic Settings
- System diagnostics endpoint
- Automated test suite (10 tests)
- CI/CD pipeline via GitHub Actions
- Windows setup script (PowerShell)
- Android setup script (Termux/bash)
- CodeForge CLI with setup, connect, and status commands
- Documentation: README, CONTRIBUTING, ROADMAP

### Changed
- N/A (initial release)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- API key support in configuration (optional)
- Sensitive values redacted in config endpoint

---

## Version Format

Versions follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (1.0.0): Breaking changes
- **MINOR** (0.1.0): New features, backward compatible
- **PATCH** (0.0.1): Bug fixes, backward compatible

[0.1.0]: https://github.com/codeforge/codeforge/releases/tag/v0.1.0