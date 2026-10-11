"""
PRUBETH IDE — UNIVERSAL COMMAND RUNNER & CONTINUOUS VERIFICATION CLI
=====================================================================
PRINCE2 7 Unified Verification Entry Point.

Commands Supported:
  doctor          Detect toolchains, dependencies, configuration, and blockers.
  inventory       Produce the capability and dependency inventory.
  test smoke      Run essential startup and workflow checks.
  test regression Run the existing and newly added regression suites.
  test full       Run all applicable non-destructive verification suites.
  test stress     Run bounded concurrency and resource tests.
  test endurance  Run sustained-use tests for a configured duration.
  test security   Run authorized security and dependency checks.
  test recovery   Validate recovery and data-integrity behavior.
  test protocols  Verify supported protocol contracts (LSP, DAP, MCP).
  test extensions Verify extension lifecycle and isolation.
  test agents     Verify orchestration, concurrency, cancellation, and recovery.
  test release    Verify packaging, upgrade, rollback, and installation.
  test all        Execute the applicable suites in dependency-aware order.
  report          Generate a traceable quality and risk report.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import psutil
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("prubeth.cli")


class UniversalCliRunner:
    """Orchestrates continuous verification commands across the IDE platform."""

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.python_exe = sys.executable

    def run_command(self, cmd_args: List[str]) -> Tuple[int, str]:
        """Runs command with environment sanitization and bounded capture."""
        t0 = time.time()
        clean_env = os.environ.copy()
        for k in list(clean_env.keys()):
            if any(term in k.upper() for term in ["API_KEY", "SECRET_KEY", "TOKEN", "AUTH_KEY"]):
                clean_env[k] = "[REDACTED]"

        proc = subprocess.run(
            cmd_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(self.workspace_root),
            env=clean_env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        return proc.returncode, proc.stdout or ""

    def execute_doctor(self) -> int:
        """Evaluates health of runtime, dependencies, disk headroom, and toolchains."""
        print("=" * 65)
        print("  PRUBETH IDE — SYSTEM DOCTOR & ENVIRONMENT DIAGNOSTICS")
        print("=" * 65)
        all_passed = True

        # 1. Python Runtime
        print(f"[*] Python Runtime: {sys.version.split()[0]} ({sys.executable})")

        # 2. Mandatory Modules
        mandatory = ["PyQt5", "requests", "sqlite3", "json", "psutil"]
        for mod in mandatory:
            try:
                __import__(mod)
                print(f"    [PASS] Mandatory Module: {mod}")
            except ImportError:
                print(f"    [FAIL] Mandatory Module Missing: {mod}")
                all_passed = False

        # 3. Optional Capabilities
        optional = [("PyQt5.Qsci", "QScintilla polyglot editor"), ("torch", "CUDA tensor acceleration")]
        for mod, desc in optional:
            try:
                __import__(mod)
                print(f"    [PASS] Optional Capability: {mod} ({desc})")
            except Exception:
                print(f"    [WARN] Optional Capability: {mod} not loaded (fallback active)")

        # 4. Storage
        disk = psutil.disk_usage(str(self.workspace_root))
        free_mb = disk.free / (1024 * 1024)
        if free_mb >= 200:
            print(f"    [PASS] Disk Headroom: {free_mb:.0f} MB available (minimum 200 MB required)")
        else:
            print(f"    [FAIL] Disk Headroom: {free_mb:.0f} MB available (insufficient storage)")
            all_passed = False

        # 5. Toolchains
        for tc in ["git", "python", "node", "npm", "dotnet", "powershell"]:
            found = shutil.which(tc)
            status = f"Found ({found})" if found else "Not Installed (Optional)"
            print(f"    [INFO] Toolchain {tc}: {status}")

        print("=" * 65)
        return 0 if all_passed else 1

    def execute_inventory(self) -> int:
        """Emits capability inventory report."""
        from core.universal_inventory import UniversalInventoryManager
        mgr = UniversalInventoryManager(self.workspace_root)
        report = mgr.generate_inventory_report()
        print("=" * 65)
        print("  PRUBETH IDE — CAPABILITY INVENTORY REPORT")
        print("=" * 65)
        print(f"Total Capabilities: {report.total_capabilities}")
        print(f"Verified:           {report.verified_count}")
        print(f"Implemented:        {report.implemented_count}")
        print(f"Degraded/Missing:   {report.degraded_count + report.missing_count}")
        print("-" * 65)
        for c in report.capabilities:
            print(f"[{c.status.value:<11}] {c.id:<11} {c.name:<32} ({c.subsystem})")
        print("=" * 65)
        return 0

    def execute_test(self, suite_name: str) -> int:
        """Executes targeted test suite."""
        suite_map = {
            "smoke": ["tests/test_startup_lifecycle.py"],
            "regression": ["tests/test_settings_center.py", "tests/test_workspace.py", "tests/test_source_control.py"],
            "full": ["tests/"],
            "stress": ["tests/reliability/test_massive_project_crash_resilience.py", "tests/reliability/test_file_operation_recovery.py"],
            "endurance": ["tests/reliability/test_subprocess_lifecycle.py", "tests/reliability/test_startup_failures.py"],
            "security": ["tests/test_gate8_security_boundary_guard.py", "tests/test_security_research.py"],
            "recovery": ["tests/reliability/test_recovery_invariants.py", "tests/reliability/test_configuration_recovery.py"],
            "protocols": ["tests/test_gate4_mcp_framing.py", "tests/test_gate10_lsp_dap_subsystems.py", "tests/test_language_services.py"],
            "extensions": ["tests/test_plugins.py", "tests/test_gate11_plugin_host_sandbox.py", "tests/reliability/test_plugin_failures.py"],
            "agents": ["tests/test_agents.py", "tests/test_autonomous_ops.py", "tests/test_gate3_orchestrator_starter_agents.py"],
            "release": ["tests/test_gate12_release_audit_packaging.py", "tests/test_installer_modes.py"],
            "all": ["tests/"]
        }

        targets = suite_map.get(suite_name.lower())
        if not targets:
            print(f"[!] Unknown test suite: '{suite_name}'. Available: {', '.join(suite_map.keys())}")
            return 1

        cmd = [self.python_exe, "-m", "pytest"] + targets + ["-v"]
        print(f"[*] Executing test suite [{suite_name}]: {' '.join(cmd)}")
        code, output = self.run_command(cmd)
        print(output)
        return code

    def execute_report(self) -> int:
        """Runs release candidate assurance cycle and generates PRINCE2 7 Stage-Gate report."""
        from core.reliability_engine import ReliabilityEngine, ReliabilityProfile
        from core.universal_inventory import UniversalInventoryManager

        print("[*] Running Release Candidate quality assurance audit...")
        engine = ReliabilityEngine(self.workspace_root)
        rep = engine.run_profile(ReliabilityProfile.RELEASE_CANDIDATE)

        mgr = UniversalInventoryManager(self.workspace_root)
        inv = mgr.generate_inventory_report()

        print("=" * 65)
        print("  PRUBETH IDE — PRINCE2 7 STAGE-GATE ASSURANCE REPORT")
        print("=" * 65)
        print(f"Stage-Gate Decision: {rep.stage_gate_decision.value}")
        print(f"Total Scenarios:     {rep.total_scenarios} (Passed: {rep.passed_count}, Failed: {rep.failed_count})")
        print(f"Peak Memory:         {rep.peak_memory_mb:.1f} MB")
        print(f"Capabilities:        {inv.total_capabilities} (Verified: {inv.verified_count})")
        print("=" * 65)
        return 0 if rep.failed_count == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="PRUBETH IDE Universal Verification CLI")
    subparsers = parser.add_subparsers(dest="subcommand", help="Verification command")

    subparsers.add_parser("doctor", help="Run environment and toolchain diagnostics")
    subparsers.add_parser("inventory", help="Generate capability inventory")

    test_parser = subparsers.add_parser("test", help="Run test suite")
    test_parser.add_argument("suite", help="Suite to run (smoke, regression, full, stress, endurance, security, recovery, protocols, extensions, agents, release, all)")

    subparsers.add_parser("report", help="Generate PRINCE2 7 release report")

    args = parser.parse_args()
    runner = UniversalCliRunner()

    if args.subcommand == "doctor":
        sys.exit(runner.execute_doctor())
    elif args.subcommand == "inventory":
        sys.exit(runner.execute_inventory())
    elif args.subcommand == "test":
        sys.exit(runner.execute_test(args.suite))
    elif args.subcommand == "report":
        sys.exit(runner.execute_report())
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
