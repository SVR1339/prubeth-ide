# SUKHI IDE — Horizon Edition
## LINE COUNT & SOURCE METRICS POLICY

**Standard Document:** ENG-POL-001  
**Status:** Approved & Active  
**Effective Date:** October 10, 2026  
**Audience:** Core Architects, Subsystem Leads, Security & QA Engineers

---

### 1. Purpose & Scope

This policy establishes the formal methodology, classification taxonomy, and reproducible metrics standards for measuring source code volume and complexity across the **SUKHI IDE — Horizon Edition** repository.

The long-term program planning target for the codebase is **292,770 verified source lines**. This document defines what constitutes a verified source line, how counting is automated, and the anti-bloat principles that govern real, high-quality software engineering.

---

### 2. Metrics Taxonomy

Every file within the repository is classified into one of the following distinct categories:

1. **Production Source Code (`Production Source`):**
   - Active runtime implementation files that compile or interpret during application execution.
   - Formats: `.py`, `.pyw`, `.js`, `.ts`, `.jsx`, `.tsx`, `.c`, `.cpp`, `.h`, `.rs`, `.go`, `.qss`, `.html`, `.css`, `.bat`, `.sh`, `.ps1`, `.sql`.
   - Locations: `core/`, `ui/`, `editor/`, `language_services/`, `debugging/`, `terminal/`, `source_control/`, `ai/`, `providers/`, `tools/`, `workspace/`, `extensions/`, `integrations/`, and primary launchers.

2. **Automated Test Code (`Tests`):**
   - Unit tests, integration test harnesses, behavioral verification suites, and test fixtures.
   - Locations: `tests/`, `testing/`.

3. **Tooling & Engineering Scripts (`Tooling & Scripts`):**
   - Build automation, line counting scripts, asset generators, packaging engines.
   - Locations: `scripts/`, `build_setup_exe.py`, `build_installer.py`, `generate_assets.py`.

4. **Technical Documentation (`Documentation`):**
   - Architecture blueprints, security threat models, roadmaps, engineering policies, API specifications, and README guides.
   - Formats: `.md`, `.txt`, `.rst`.

5. **Configuration & Manifests (`Config & Metadata`):**
   - Environment templates, packaging specifications, dependencies, project manifests.
   - Formats: `.toml`, `.json`, `.yaml`, `.yml`, `.iss`, `.ini`, `.cfg`.

---

### 3. Source Line Counting Methodology

Lines are measured across four explicit dimensions:

- **Raw Lines:** Total newline-separated records in the file.
- **Blank Lines:** Lines containing exclusively whitespace or zero characters.
- **Comment Lines:**
  - Python: Lines starting with `#`, docstrings enclosed in `"""` or `'''`.
  - C/C++/JS/Rust/Go/CSS: Single-line `//` or multi-line `/* ... */` blocks.
  - Windows Batch: Lines starting with `rem ` or `::`.
  - Shell / PowerShell: Lines starting with `#`.
- **SLOC (Source Lines of Code):** Executable, non-blank, non-comment lines.

#### Reproducibility
Line counts must be generated using the official repository script:
```bash
python scripts/count_lines.py --json
```

---

### 4. Non-Negotiable Exclusions

The following artifacts are strictly excluded from all source metrics:
1. **Third-Party Virtual Environments:** `.venv/`, `venv/`, `env/`.
2. **Intermediate Build Artifacts & Caches:** `__pycache__/`, `*.pyc`, `.pytest_cache/`, `build/`, `dist/`.
3. **Compiled & Compressed Binaries:** `*.exe`, `*.zip`, `*.tar.gz`, `*.deb`, `*.dmg`, `*.dll`, `*.pyd`.
4. **Media & Icon Assets:** `*.ico`, `*.png`, `*.jpg`, `*.svg`.
5. **Experimental Scratch Directories:** `scratch/`.
6. **Version Control Internals:** `.git/`.

---

### 5. Anti-Inflation & Software Quality Mandates

The 292,770 line target is a structural roadmap capacity estimate for an industrial-scale, multi-language IDE containing complete language servers, debugger adapters, terminal emulators, version control, AI orchestration, and multi-cloud providers.

To prevent artificial inflation:
- **No Boilerplate Inflation:** Do not duplicate code, generate repetitive classes, or create artificial intermediate wrappers simply to add lines.
- **No Synthetic Comments:** Do not pad files with decorative ASCII banners, trivial docstrings, or repeated comments.
- **No Mock Test Proliferation:** Tests must validate real behavioral logic, security boundaries, or state transitions; tests that merely assert hardcoded constants are prohibited.
- **Honesty Over Numbers:** If a subsystem is cleanly, concisely, and securely implemented in fewer lines than estimated, that fact must be documented transparently in the ledger. Architectural elegance and runtime safety take precedence over raw volume.
