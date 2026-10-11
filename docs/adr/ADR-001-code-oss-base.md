# ADR-001: Adoption of Code-OSS Architecture and Monaco Host

## Status
Accepted

## Date
2026-10-11

## Context
PRUBETH IDE requires an enterprise-grade editor surface with support for language servers (LSP), debugging protocols (DAP), rich extensions, and syntactical intelligence. Building an editor from scratch would take excessive development bandwidth and lack community extension ecosystem compatibility. We needed an open, verifiable foundation that can be extended with autonomous developer tooling without commercial vendor lock-in or telemetry leaks.

## Decision
We adopted the open-source **Code-OSS** architecture as the core foundation for PRUBETH IDE:
1. **Manifest Configuration (`code_oss/product.json`)**: Configured a vendor-neutral product manifest pointing to the community Open VSX marketplace gallery (`https://open-vsx.org/vscode/gallery`) with telemetry completely disabled (`enableTelemetry: false`).
2. **Monaco Host Bridge (`code_oss/monaco/bridge.py`)**: Embedded a self-contained Monaco editor environment with two-way communication between Qt/Chromium WebEngine and Monaco JavaScript APIs.
3. **Multi-File Composer Engine (`code_oss/composer/engine.py`)**: Implemented transactional diff application and atomic multi-file edits with instant rollback and unified diff representations.
4. **AST Codebase Indexer (`code_oss/context/codebase_indexer.py`)**: Built an AST-based Python symbol indexer generating dense `@Codebase` context summaries.

## Consequences
- **Positive**: Full compatibility with standard Monaco editing semantics; access to open extensions via Open VSX; zero proprietary telemetry or vendor tracking.
- **Negative**: Requires maintaining the lightweight bridge layer between the Qt surface and the Monaco host environment.
