"""Tests for PRUBETH IDE Cybersecurity Research Subsystem (security_research/)
"""

import json
import os
import tempfile
import pytest
from pathlib import Path
from security_research import (
    SecurityFinding,
    SecuritySeverity,
    SASTEngine,
    SCAEngine,
    BinaryArchitecture,
    BinaryFormat,
    ReverseEngineeringBridge,
    NetworkIsolationMode,
    ResourceQuota,
    IsolatedLabManager,
)


def test_sast_engine_vulnerability_detection():
    sast = SASTEngine()

    sample_vulnerable_code = """
import os
import pickle
import hashlib

def run_cmd(user_arg):
    os.system("echo " + user_arg)  # Command injection
    data = pickle.loads(b"cos\\nsystem\\n(S'ls'\\ntR.")  # Insecure deserialization
    h = hashlib.md5(user_arg.encode()).hexdigest()  # Insecure hash
    api_key = "AKIA1234567890ABCDEF"  # AWS secret
    eval(user_arg)  # AST eval
"""

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
        tf.write(sample_vulnerable_code)
        temp_path = tf.name

    try:
        findings = sast.scan_file(temp_path)
        rule_ids = {f.rule_id for f in findings}

        assert "PRUBETH-SEC-001" in rule_ids  # Command injection
        assert "PRUBETH-SEC-002" in rule_ids  # Insecure deserialization
        assert "PRUBETH-SEC-003" in rule_ids  # Hardcoded AWS secret
        assert "PRUBETH-SEC-005" in rule_ids  # Insecure MD5 hash
        assert "PRUBETH-SEC-008" in rule_ids  # AST eval detection

        summary = sast.get_summary(findings)
        assert summary["total_findings"] >= 5
        assert summary["risk_status"] == "HIGH_RISK"
    finally:
        os.unlink(temp_path)


def test_sca_engine_and_sbom_generation():
    sca = SCAEngine()

    sample_requirements = """
# Test dependencies
requests==2.25.1
urllib3==1.25.10
pytest>=8.0.0
"""

    with tempfile.NamedTemporaryFile("w", suffix="requirements.txt", delete=False) as tf:
        tf.write(sample_requirements)
        req_path = tf.name

    try:
        # Audit dependencies
        findings = sca.audit_dependencies(req_path)
        cve_ids = {f.cve_id for f in findings if f.cve_id}
        assert "CVE-2023-32681" in cve_ids  # requests < 2.31.0
        assert "CVE-2023-43804" in cve_ids  # urllib3 < 1.26.18

        # Generate CycloneDX SBOM
        cyclonedx_sbom = sca.generate_cyclonedx_sbom(req_path, project_name="test-suite")
        assert cyclonedx_sbom["bomFormat"] == "CycloneDX"
        assert cyclonedx_sbom["specVersion"] == "1.5"
        assert len(cyclonedx_sbom["components"]) == 3

        # Generate SPDX SBOM
        spdx_sbom = sca.generate_spdx_sbom(req_path, project_name="test-suite")
        assert spdx_sbom["spdxVersion"] == "SPDX-2.3"
        assert len(spdx_sbom["packages"]) == 3
    finally:
        os.unlink(req_path)


def test_reverse_engineering_bridge():
    re_bridge = ReverseEngineeringBridge()

    # Shannon Entropy tests
    all_zeros = bytes(100)
    assert re_bridge.calculate_entropy(all_zeros) == 0.0

    random_like = bytes(range(256))
    assert re_bridge.calculate_entropy(random_like) == 8.0

    # String & IoC extraction
    sample_binary_payload = (
        b"MZ\x00\x00SomeHeaderData"
        b"\x00VirtualAlloc\x00IsDebuggerPresent\x00"
        b"http://malicious-c2.test/payload.exe\x00"
        b"198.51.100.42\x00"
    )

    strings = re_bridge.extract_strings(sample_binary_payload, min_length=4)
    assert "VirtualAlloc" in strings
    assert "IsDebuggerPresent" in strings

    iocs = re_bridge._detect_iocs(strings)
    ioc_indicators = {i["indicator"] for i in iocs}
    assert "VirtualAlloc" in ioc_indicators
    assert "IsDebuggerPresent" in ioc_indicators
    assert "198.51.100.42" in ioc_indicators

    # Fallback opcode disassembly
    test_opcodes = b"\x90\x55\x48\x89\xe5\x31\xc0\xc3"  # nop, push rbp, mov rbp, rsp, xor eax, eax, ret
    instructions = re_bridge.disassemble_bytes(test_opcodes, base_address=0x1000)
    mnemonics = [i.mnemonic for i in instructions]

    assert "nop" in mnemonics
    assert "push" in mnemonics
    assert "mov" in mnemonics
    assert "xor" in mnemonics
    assert "ret" in mnemonics


def test_isolated_lab_manager_lifecycle():
    with tempfile.TemporaryDirectory() as temp_dir:
        lab_mgr = IsolatedLabManager(base_lab_dir=temp_dir)
        session_id = "test_lab_session_01"

        # Initialize session
        session_path = lab_mgr.create_session(
            session_id=session_id,
            isolation_mode=NetworkIsolationMode.AIR_GAPPED,
            quota=ResourceQuota(timeout_seconds=10),
        )
        assert session_path.is_dir()

        # Execute harmless Python script inside sandbox that creates a file
        script_code = 'import os; open("detonated_artifact.txt", "w").write("hello sandbox")'
        cmd = [
            ".venv/Scripts/python.exe" if os.path.exists(".venv/Scripts/python.exe") else "python",
            "-c",
            script_code,
        ]

        report = lab_mgr.execute_target(session_id, cmd)
        assert report.exit_code == 0
        assert not report.timed_out
        assert "detonated_artifact.txt" in report.created_files

        # Verify rollback purges the newly created file
        assert (session_path / "detonated_artifact.txt").exists()
        assert lab_mgr.rollback_session(session_id)
        assert not (session_path / "detonated_artifact.txt").exists()

        # Destroy session
        assert lab_mgr.destroy_session(session_id)
        assert not session_path.exists()
