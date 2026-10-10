# SO NAIVE IDE — Architecture Assessment & Target Modularization Design
**Document ID:** DOC-ASSESS-002  
**Version:** 3.0.0-RC1  
**Date:** October 10, 2026  

---

## 1. Existing Architectural Topology
The application has historically grown as a single-file implementation (`local_ai_studio_pro.py`, ~5,700 lines). While maintaining the entire IDE in one file provided rapid early prototyping, it created tight coupling:
- GUI widgets in PyQt5 directly instantiate `requests.post()` and `subprocess.run()`.
- Unprotected configuration dictionaries are shared across threads without synchronized state or access control.
- Hardcoded cascades cannot dynamically evaluate model capabilities or enforce granular security policies.

---

## 2. Target Clean Modular Architecture (`core/`)

To preserve stability and guarantee zero regressions, the application is refactored into a decoupled core architecture:

```
c:\Users\asus\heretic-work\
├── core/
│   ├── __init__.py           # Package exports and version metadata
│   ├── credentials.py        # Windows DPAPI + AES-256-GCM secure store, secret redactor
│   ├── workspace.py          # Canonical path resolution, traversal rejection, boundary guard
│   ├── tool_gateway.py       # Safe subprocess dispatcher, command allowlist, dry-run
│   ├── model_registry.py     # Extensible model hub, capability registry, latency tracker
│   ├── router.py             # Small/Medium/Large agent profiles, deterministic policy engine
│   ├── task_engine.py        # Persistent state machine, checkpoints, cancellation tokens
│   └── plugin_engine.py      # Real MCP stdio transport, manifest schema validator
├── local_ai_studio_pro.py   # Preserved IDE shell with seamless adapters to core.*
└── tests/                    # Comprehensive unit and integration test suite
```

---

## 3. Backward Compatibility & Adapter Strategy
1. `local_ai_studio_pro.py` imports and delegates to `core.*` modules when present.
2. If any optional subsystem is missing or runs in a constrained environment, graceful fallbacks maintain uninterrupted IDE functionality.
3. User settings in `%USERPROFILE%\.local_ai_studio_pro\settings.json` are transparently migrated so that secrets are encrypted while all user preferences (themes, fonts, editor settings) remain intact.
