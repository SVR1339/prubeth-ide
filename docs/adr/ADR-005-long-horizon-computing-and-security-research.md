# ADR-005: Long-Horizon Personal Computing Platform & Cybersecurity Research Architecture

## Status
Accepted

## Date
2026-10-11

## Context
PRUBETH IDE is engineered as a personal super-IDE and long-horizon sovereign computing platform for professional software engineering, defensive cybersecurity research, binary analysis, model experimentation, and offline-first autonomous development. 

To withstand technology shifts spanning multiple decades, the platform cannot depend on ephemeral vendor APIs, proprietary cloud services, or hardcoded assumptions about current hardware. Furthermore, personal research into binaries and unvetted code requires strict execution containment, network sandboxing, static vulnerability auditing, and self-healing resilience.

## Decision
We implemented four sovereign architectural pillars:

1. **Future Compatibility Layer (`core/future_compat.py`)**:
   - Century-scale interface contracts (`IComputeProvider`, `IStorageEngine`, `ISchedulerEngine`, `IIndexerEngine`) with explicit semantic versioning (`V1_0`, `V2_0`, `V3_0`).
   - Dynamic `CompatibilityBroker` providing runtime capability negotiation and automatic adapter synthesis (e.g. elevating V1 synchronous text generation to V2 token streaming and vector embeddings).
   - Zero coupling between UI components and vendor-specific runtimes.

2. **Cybersecurity Research Subsystem (`security_research/`)**:
   - **SAST & SCA Engine (`security_research/sast_sca_engine.py`)**: AST and regex multi-rule static security scanner (detecting command injection, insecure deserialization, hardcoded credentials, weak hashing, and SQL injection) plus Software Composition Analysis generating standard CycloneDX 1.5 and SPDX 2.3 Software Bill of Materials (SBOM).
   - **Reverse Engineering Bridge (`security_research/reverse_engineering_bridge.py`)**: Pure-Python PE/ELF header parser, Shannon entropy calculator for packed/obfuscated malware payload detection, string/IoC extractor (suspicious APIs, C2 network indicators), and opcode disassembler.
   - **Isolated Lab Manager (`security_research/isolated_lab_manager.py`)**: Orchestrates sandboxed target execution under configurable network containment (`AIR_GAPPED`, `HOST_ONLY`, `TOR_PROXY`, `BRIDGED_RESTRICTED`), enforces resource quotas (CPU, RAM, timeout), tracks file state manifests (SHA-256), and provides atomic rollback.

3. **Personal Model Laboratory & Air-Gap Policy Guard (`core/model_lab.py`)**:
   - `ModelBenchmarkHarness`: Profiles first-token latency (FTL), throughput (tokens/second), memory footprint, and context length degradation.
   - `OfflineEnforcementPolicy`: Socket-level interception enforcing zero outbound remote network egress in `STRICT_AIRGAP` mode, guaranteeing that sensitive source code and local research never leave the host.

4. **Autonomous Operations & Self-Diagnostic Engine (`core/autonomous_ops.py`)**:
   - Formal loop: **Observe ➔ Diagnose ➔ Plan ➔ Check Policy ➔ Approve ➔ Execute ➔ Verify ➔ Record**.
   - Auto-executes `READ_ONLY` and `SAFE_EXECUTION` healing plans (e.g. scratch disk cleanup, cache compaction), while generating explicit `ApprovalTicket`s for `MUTATING` or `HIGH_RISK` actions.
   - Maintains an append-only immutable audit trail.

## Consequences
- **Positive**: Complete technical sovereignty, future-proof extensible contracts, high-assurance security containment for binary and malware research, hardware-tuned local AI inference, and automated self-maintenance without risk of unmonitored system modifications.
- **Negative**: Sandboxed executions incur slight filesystem snapshot overhead during pre/post-run diff analysis.
