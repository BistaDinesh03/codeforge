# CodeForge Roadmap

## Phase 1: Foundation (Current)
**Goal:** Working skeleton - server runs, extension loads

- [x] Project structure & repository setup
- [x] FastAPI backend with health endpoint
- [ ] VS Code extension compilation & loading
- [ ] ADB communication proof-of-concept

## Phase 2: Core Communication
**Goal:** VS Code talks to Android backend

- [ ] Extension sends HTTP requests to backend
- [ ] Backend responds with generated text
- [ ] Status bar shows connection state
- [ ] Error handling for connection failures

## Phase 3: AI Integration
**Goal:** Real AI responses from phone

- [ ] llama.cpp setup in Termux
- [ ] Model loading & management
- [ ] Code completion endpoint
- [ ] Code explanation endpoint

## Phase 4: Developer Experience
**Goal:** Feels native to VS Code

- [ ] Context-aware suggestions
- [ ] Inline completions
- [ ] Sidebar chat panel
- [ ] Multiple model support

## Phase 5: Production Ready
**Goal:** Stable, secure, documented

- [ ] End-to-end tests
- [ ] Security audit
- [ ] Full API documentation
- [ ] VS Code marketplace publication
- [ ] v1.0 release