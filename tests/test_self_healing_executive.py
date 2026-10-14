"""
Unit and Integration Tests for Executive Autonomous Self-Healing & Scaffolding Engine
(ai/agents/self_healing_executive.py)
"""
import os
import sys
import subprocess
from pathlib import Path
import pytest

from ai.agents.self_healing_executive import (
    SelfHealingExecutiveAgent,
    TracebackParser,
    ProjectScale,
    ErrorCategory,
    TracebackDiagnostic,
)
from ai.agents.orchestrator import MultiAgentOrchestrator, AgentRole
from ai.agents.critic import AgentCritic


def test_traceback_parser_syntax_error():
    raw_error = """
  File "C:\\work\\calc.py", line 14
    def add(a, b)
                 ^
SyntaxError: expected ':'
"""
    diag = TracebackParser.parse(raw_error, workspace_root="C:\\work")
    assert diag is not None
    assert diag.error_type == "SyntaxError"
    assert diag.category == ErrorCategory.SYNTAX
    assert diag.line_number == 14
    assert "calc.py" in str(diag.failing_file)


def test_traceback_parser_runtime_and_attribute_errors():
    raw_error = """
Traceback (most recent call last):
  File "services/worker.py", line 42, in process_record
    item = payload["user_id"]
KeyError: 'user_id'
"""
    diag = TracebackParser.parse(raw_error)
    assert diag is not None
    assert diag.error_type == "KeyError"
    assert diag.category == ErrorCategory.RUNTIME
    assert diag.line_number == 42
    assert "worker.py" in str(diag.failing_file)


def test_traceback_parser_pytest_failure():
    raw_error = """
=================================== FAILURES ===================================
FAILED tests/test_service.py::test_calculation - AssertionError: assert 42 == 100
"""
    diag = TracebackParser.parse(raw_error)
    assert diag is not None
    assert diag.category == ErrorCategory.ASSERTION
    assert "test_service.py" in str(diag.failing_file)


def test_scaffold_small_scale_project(tmp_path):
    agent = SelfHealingExecutiveAgent(workspace_root=tmp_path)
    result = agent.scaffold_project(
        scale=ProjectScale.SMALL,
        goal="Fast CLI Data Hasher",
        target_subfolder="cli_tool"
    )
    assert result["scale"] == "small"
    assert len(result["files_created"]) == 1
    assert result["verified"] is True

    # Verify script execution
    entry = result["entrypoint"]
    proc = subprocess.run([sys.executable, entry, "--test"], capture_output=True, text=True)
    assert proc.returncode == 0
    assert "PASSED cleanly" in proc.stdout


def test_scaffold_mid_scale_project(tmp_path):
    agent = SelfHealingExecutiveAgent(workspace_root=tmp_path)
    result = agent.scaffold_project(
        scale=ProjectScale.MID,
        goal="Inventory Management Service",
        target_subfolder="inventory_pkg"
    )
    assert result["scale"] == "mid"
    assert len(result["files_created"]) >= 4
    assert result["verified"] is True

    # Verify entrypoint runs cleanly
    entry = result["entrypoint"]
    proc = subprocess.run([sys.executable, entry], cwd=str(tmp_path / "inventory_pkg"), capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Verified item: Alpha Item" in proc.stdout


def test_scaffold_large_scale_project(tmp_path):
    agent = SelfHealingExecutiveAgent(workspace_root=tmp_path)
    result = agent.scaffold_project(
        scale=ProjectScale.LARGE_POWERED,
        goal="High-Throughput Financial Ledger",
        target_subfolder="ledger_system"
    )
    assert result["scale"] == "large"
    assert len(result["files_created"]) >= 6
    assert result["verified"] is True

    # Verify enterprise bootstrap entrypoint
    entry = result["entrypoint"]
    proc = subprocess.run([sys.executable, entry], cwd=str(tmp_path / "ledger_system"), capture_output=True, text=True)
    assert proc.returncode == 0
    assert "Total verified transaction audit records: 1" in proc.stdout


def test_autonomous_self_healing_loop_on_broken_code(tmp_path):
    # Create a deliberately broken script with a syntax missing colon
    broken_file = tmp_path / "flawed_script.py"
    broken_code = """
def compute_value(x)
    return x * 10

if __name__ == "__main__":
    val = compute_value(5)
    print(f"Calculated: {val}")
"""
    broken_file.write_text(broken_code, encoding="utf-8")

    agent = SelfHealingExecutiveAgent(workspace_root=tmp_path)

    progress_events = []
    def on_prog(msg, cur, tot):
        progress_events.append(msg)

    # Launch autonomous self-healing loop
    heal_res = agent.autonomous_self_healing_loop(
        command_or_script=str(broken_file),
        max_iterations=4,
        on_progress=on_prog
    )

    assert heal_res.success is True
    assert heal_res.exit_code == 0
    assert "Calculated: 50" in heal_res.final_output
    assert len(heal_res.audit_notes) >= 2


def test_orchestrator_auto_heal_execution(tmp_path):
    orchestrator = MultiAgentOrchestrator(str(tmp_path))

    # Coder outputs code with eval() which Critic rejects, but auto_heal sanitizes it
    coder = orchestrator.get_subagent(AgentRole.CODER)
    coder.set_handler(lambda task, ctx: {
        "status": "success",
        "output": "def safe_parse(data):\n    return eval(data)\n",
        "artifacts": []
    })

    plan = orchestrator.build_plan("Parse data")
    # Run with auto_heal=True
    result = orchestrator.run_plan(plan, auto_heal=True)
    assert result["success"] is True
    assert any("self-healed successfully" in m.content for m in orchestrator.messages)
