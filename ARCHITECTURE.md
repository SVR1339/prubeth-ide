# Architecture & System Design: PRUBETH IDE

**PRUBETH IDE** (Horizon Edition v3.0.0) is built to deliver unmatched responsiveness, source code privacy, autonomous agent velocity, and sovereign local code compilation.
Official Showcase: [**https://www.bsvr.work/**](https://www.bsvr.work/)

---

## 🏛️ System Architecture Diagram

```
+-------------------------------------------------------------------------+
|                               PRUBETH IDE                               |
|        (Obsidian Hologram Theme · QScintilla Polyglot Lexers)          |
+-------------------------------------------------------------------------+
                                     |
               +---------------------+---------------------+
               |                                           |
               v                                           v
+-------------------------------+           +-----------------------------+
|    Intelligent Model Router   |           |    Self-Healing Compiler    |
|   (Dynamic Priority Cascade)  |           |     (1-Click AST Auto-Fix)  |
+-------------------------------+           +-----------------------------+
   |             |             |                           |
   | (Tier 1)    | (Tier 2)    | (Tier 3)                  v
   v             v             v            +-----------------------------+
[Gemini 3.8]  [Gemini 3.5]  [Local GPU]     | Visual Diff Reviewer        |
 (1M Context)  (Fast Cloud)  (CUDA Ollama)  | (+ Additions / - Deletions) |
   |                           |            +-----------------------------+
   +-------------+-------------+
                 |
                 v
+-------------------------------------------------------------------------+
|                 Autonomous Multi-Agent DAG Orchestrator                 |
|   Planner  ->  Code Architect  ->  Test Fixer  ->  AST Critic Engine   |
|   - <tool:read_file>        - <tool:patch_file>    - <tool:run_command> |
|   - <tool:write_file>       - <tool:search_code>   - <tool:run_tests>   |
|   - <tool:checkpoint>       - <tool:call_mcp>      - <tool:verify_deliv>|
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                    Security & Boundary Guard Engine                     |
|  - Windows DPAPI / Fernet Secret Vault with real-time log redaction     |
|  - Workspace Jail: traversal blocking (../) & reserved device guards   |
|  - Two-Phase Transactional Rollback Engine with shadow state backups    |
+-------------------------------------------------------------------------+
```

---

## 1. Intelligent Model Router & Zero-Downtime Cascade

The router eliminates developer downtime by dynamically probing network latency and fallback tiers:

```python
# Cascade Hierarchy
Tier 1: Google Gemini 3.8 Flash (SSE streaming, 1,000,000 token context window)
Tier 2: Google Gemini 3.5 Flash (Ultra-low latency cloud reasoning)
Tier 3: Local GPU Ollama (CUDA 12.6 GTX 1050 Ti, zero network latency, 100% offline)
Tier 4: OpenAI-compatible endpoints (Custom gateways, Azure, vLLM)
```

If an active cloud request experiences socket timeout, HTTP 429 rate limit, or network disconnection, the active prompt payload and memory are rerouted to Tier 3 Local GPU instantly.

---

## 2. Hologram Cybernetic Design Theme

PRUBETH features an obsidian glassmorphic theme engineered for high contrast and sustained developer focus:
- **Obsidian Dark (`#050811`):** Deep black backdrop maximizing contrast and reducing eye strain.
- **Electric Cyan (`#00F0FF`) & Neon Magenta (`#D946EF`):** Distinctive neon gradients for tabs, selection states, progress bars, and glowing borders.
- **Pure White (`#FFFFFF`):** High-contrast typography for maximum readability.
- **Positive White Theme:** High-key alternative theme with dark silhouette blades and bright contrast.

---

## 3. Self-Healing Traceback Auto-Fix Compiler

When executing scripts (**`F5`**) or test suites (**`pytest`**):
1. **Traceback Extraction:** The IDE intercepts `stderr` via `QProcess` and parses exception frames (`Traceback (most recent call last)`).
2. **Context Compilation:** The affected file content and the exact traceback snippet are packaged into a high-priority surgical prompt.
3. **AST Patching:** The AI returns the repaired file inside one markdown fenced block.
4. **Visual Diff Dialog:** Generates side-by-side colorized diffs (`difflib.ndiff` + HTML styling) highlighting additions in emerald green and deletions in ruby red.
5. **Re-Test Verification:** The user applies the changes, which triggers an automated test pass to confirm resolution.

---

## 4. Cybernetic Blinking AI Status Beacon

The blinking AI beacon (`BlinkingAIIndicator`) provides continuous peripheral awareness to the developer without cluttering the screen:

- **Mathematical Sine Breathing:**
  $$\text{glow} = 0.65 + 0.35 \cdot \sin(\theta)$$
  Where $\theta$ updates every $40\text{ ms}$ at $25\text{ FPS}$.
- **States:**
  - `ONLINE`: Gentle breathing cycle in cyan (`#00F0FF`).
  - `STREAMING`: Chromatic alternating pulses between electric violet (`#A855F7`) and cyan (`#00F0FF`) at $300\text{ ms}$ frequency.
  - `AUTOFIX`: Emerald (`#10B981`) and amber (`#F59E0B`) strobe.
  - `ALERT`: Ruby red (`#EF4444`) alert.

---

## 5. Autonomous Agent Tool Protocol

The agent loop executes XML-tagged actions:

| Action | Tag Syntax | Capability |
| :--- | :--- | :--- |
| `read_file` | `<tool:read_file path="file.py" />` | Loads entire file into model memory |
| `write_file` | `<tool:write_file path="file.py">code</tool:write_file>` | Creates/overwrites file with `.bak` safety backup |
| `patch_file` | `<tool:patch_file path="file.py"><search>old</search><replace>new</replace></tool:patch_file>` | Surgical search-and-replace |
| `list_files` | `<tool:list_files dir="." />` | Discovers project structure |
| `search_code` | `<tool:search_code query="symbol" />` | Grep across project directory |
| `run_command` | `<tool:run_command cmd="git status" />` | Shell execution with security guard check |
| `run_tests` | `<tool:run_tests />` | Executes `pytest` and feeds results back to agent |
| `call_mcp` | `<tool:call_mcp server="srv" tool="act" />` | Calls MCP tools with Content-Length stdio framing |
| `create_checkpoint` | `<tool:create_checkpoint description="..." />` | Creates two-phase transactional restore point |
| `rollback_checkpoint` | `<tool:rollback_checkpoint id="..." />` | Atomic rollback with shadow stage recovery |

---

## 6. Packaging & Runtime Bootstrap Architecture

To eliminate installation breakdowns and silent failures:

```
+-----------------------------------------------------------------------+
|                       Packaging Pipeline                              |
+-----------------------------------------------------------------------+
                                   |
         +-------------------------+-------------------------+
         |                                                   |
         v                                                   v
[build_setup_exe.py]                                [build_installer.py]
         |                                                   |
         v                                                   v
+-----------------------------+                     +-------------------+
| Creates app_payload.zip     |                     | Universal Source  |
| - local_ai_studio_pro.py    |                     | Portable ZIP      |
| - assets/ & tests/          |                     +-------------------+
| - requirements.txt          |
+-----------------------------+
         |
         v (PyInstaller --add-data app_payload.zip;.)
+-----------------------------------------------------------------------+
|      PrubethIDE-v3.0.0-Setup.exe / setup.exe (Embedded Payload)       |
+-----------------------------------------------------------------------+
                                   | (User Installs)
                                   v
+-----------------------------------------------------------------------+
|  InstallWorker (%LOCALAPPDATA%\Programs\PrubethIDE)                   |
|  - Extracts app_payload.zip into target directory                     |
|  - Validates existence of local_ai_studio_pro.py / PrubethIDE.exe     |
|  - Writes self-diagnosing PrubethIDE.bat with error alerts (mshta)    |
|  - Configures Desktop & Start Menu shortcuts                          |
+-----------------------------------------------------------------------+
```

### Self-Bootstrapping Launchers:
- **`run_ide.bat` / `run_local_ai_studio_pro.bat`:** Developers launching from source are automatically verified. Missing `.venv` or dependencies trigger automatic virtualenv creation and `requirements.txt` installation before launch.
- **`PrubethIDE.bat`:** Installed runtime verifies Python presence and GUI libraries. If an environment is broken, it raises an explicit Windows GUI dialog rather than failing silently in the background.
