"""Tests for PRUBETH IDE Agentic Stack
Verifies LangGraph, HarnessKit, SWE-agent, Superharness integration.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
import pytest

from core.agentic_stack import (
    AgenticMasterDispatcher,
    HarnessKitFuzzyEditor,
    SuperHarnessOrchestrator,
    build_prubeth_agentic_graph,
    HAS_HK,
    HAS_LANGGRAPH,
    HAS_SWEAGENT,
    HAS_SWEBENCH
)


def test_agentic_stack_status():
    """Verify all agentic tools are detected and available."""
    dispatcher = AgenticMasterDispatcher()
    status = dispatcher.handle_status_request()

    assert "langgraph" in status
    assert status["langgraph"]["available"] is True
    assert "harnesskit" in status
    assert status["harnesskit"]["available"] is True
    assert "sweagent" in status
    assert status["sweagent"]["available"] is True
    assert "swebench" in status
    assert status["swebench"]["available"] is True
    assert "superharness" in status
    assert "models_supported" in status
    assert "claude-opus-4-6" in status["models_supported"]
    assert "gemini-3.8-flash" in status["models_supported"]


def test_harnesskit_fuzzy_editor():
    """Verify HarnessKit fuzzy matching replaces code accurately."""
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".py") as f:
        f.write("def calculate_metric(x):\n    # Old logic\n    return x * 2\n")
        temp_path = f.name

    try:
        editor = HarnessKitFuzzyEditor()
        # Test exact match
        res = editor.apply_patch(temp_path, "    return x * 2", "    return x * 4")
        assert res["success"] is True

        content = Path(temp_path).read_text()
        assert "return x * 4" in content

        # Test whitespace tolerant matching
        res = editor.apply_patch(temp_path, "  #   Old  logic  ", "    # Updated neural logic")
        assert res["success"] is True

        content = Path(temp_path).read_text()
        assert "Updated" in content and "logic" in content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_langgraph_workflow_execution():
    """Verify LangGraph StateGraph executes autonomous plan and verification."""
    dispatcher = AgenticMasterDispatcher()
    plan_res = dispatcher.handle_plan_request("Create neural AST transformer")

    assert plan_res["success"] is True
    assert len(plan_res["plan"]) >= 3
    assert "AST" in plan_res["plan"][0]
    assert plan_res["status"] in ["verified", "completed", "planned_fallback"]


def test_superharness_orchestrator():
    """Verify SuperHarness worktree interface handles paths and commands."""
    orchestrator = SuperHarnessOrchestrator()
    assert orchestrator.repo_dir.exists()


def test_probabilistic_convergence_engine():
    """Verify multi-path probability search tree explores alternative solution branches."""
    dispatcher = AgenticMasterDispatcher()
    res = dispatcher.handle_explore_paths("Synthesize robust distributed state cache")

    assert res["success"] is True
    assert res["probability_branches_analyzed"] >= 3
    assert res["highest_confidence_path"]["probability"] > 0.9
    assert "branch_1" in res["highest_confidence_path"]["path_id"]


def test_error_assessment_and_healing():
    """Verify compiler and runtime tracebacks are assessed and deterministic healing derived."""
    dispatcher = AgenticMasterDispatcher()

    # 1. Syntax error assessment
    syntax_err = "  File 'main.py', line 42\n    def foo(\nSyntaxError: unexpected EOF while parsing"
    res1 = dispatcher.handle_assess_heal(syntax_err)
    assert res1["assessed"] is True
    assert res1["error_category"] == "SyntaxError"
    assert "HarnessKit" in res1["healing_strategy"]

    # 2. Dependency missing assessment
    import_err = "Traceback (most recent call last):\n  File 'app.py', line 3\nModuleNotFoundError: No module named 'fastapi'"
    res2 = dispatcher.handle_assess_heal(import_err)
    assert res2["assessed"] is True
    assert res2["error_category"] == "DependencyMissing"
    assert "pip install" in res2["healing_strategy"]
    assert "fastapi" in res2["healing_strategy"]
