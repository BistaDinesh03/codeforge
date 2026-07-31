# API Reference

**Base URL:** `http://localhost:8000`

## Health
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Quick health check |
| GET | `/health/diagnostics` | Full system info |
| GET | `/version` | Server version |

## Models
| Method | Path | Description |
|--------|------|-------------|
| GET | `/models` | List available models |
| GET | `/models/status` | Current model state |
| POST | `/models/load` | Load a model |
| POST | `/models/auto-load` | Auto-detect best model |

## Chat
| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Send message |
| POST | `/chat/stream` | Stream response |
| POST | `/chat/explain` | Explain code |
| POST | `/chat/generate` | Generate code |
| POST | `/chat/rewrite` | Improve code |

## Completion
| Method | Path | Description |
|--------|------|-------------|
| POST | `/complete` | Inline code completion |

## Updates
| Method | Path | Description |
|--------|------|-------------|
| GET | `/update/check` | Check for updates |
| POST | `/update/apply` | Apply update |
| POST | `/update/rollback` | Restore previous version |