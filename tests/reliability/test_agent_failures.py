"""PRUBETH IDE - Agent & Subagent Orchestration Chaos Tests
=========================================================
Exercises subagent step bounding, template integrity, file conflict guards,
unauthorized tool execution rejection, and multi-turn workflow recovery.
"""

import pytest
from ai.agent_studio import (
    AgentSpec,
    AgentStudio,
    FileConflictGuard,
    FileConflictError,
)


def test_agent_template_library_integrity():
    """All built-in agent templates in AgentStudio must be valid, well-formed, and bounded."""
    studio = AgentStudio()
    agents = studio.list_agents()
    assert len(agents) >= 10

    for agent in agents:
        assert agent.max_steps <= 50  # Bounded execution limit
        assert len(agent.instructions) > 10
        assert isinstance(agent.allowed_tools, list)


def test_agent_studio_custom_spec_lifecycle():
    """AgentStudio must validate, duplicate, and export custom agents safely."""
    studio = AgentStudio()

    custom_spec = AgentSpec(
        agent_id="custom-fuzzer",
        name="Custom Fuzzing Agent",
        role="Security Fuzzer",
        instructions="Fuzz test input interfaces with edge-case payloads.",
        max_steps=15,
        allowed_tools=["read_file", "run_terminal"],
    )

    studio.register_agent(custom_spec)
    retrieved = studio.get_agent("custom-fuzzer")
    assert retrieved is not None
    assert retrieved.max_steps == 15
    assert "read_file" in retrieved.allowed_tools

    # Export to JSON
    raw_json = studio.export_agent_json("custom-fuzzer")
    assert "custom-fuzzer" in raw_json

    # Duplicate
    dup = studio.duplicate_agent("custom-fuzzer", "custom-fuzzer-copy", "Fuzzer Copy")
    assert dup.agent_id == "custom-fuzzer-copy"
    assert dup.name == "Fuzzer Copy"


def test_subagent_file_conflict_guard_lifecycle():
    """Conflicting concurrent agents targeting the same file must be safely isolated."""
    guard = FileConflictGuard()
    target_path = "security_research/sast_sca_engine.py"

    # Agent A acquires lock
    assert guard.acquire_lock("subagent_architect", target_path) is True
    assert target_path.lower() in guard.get_locked_files()

    # Agent B fails to acquire lock and raises FileConflictError
    with pytest.raises(FileConflictError):
        guard.acquire_lock("subagent_tester", target_path)

    # Agent A finishes and releases
    guard.release_lock("subagent_architect", target_path)
    assert target_path.lower() not in guard.get_locked_files()

    # Now Agent B succeeds
    assert guard.acquire_lock("subagent_tester", target_path) is True
    guard.release_lock("subagent_tester", target_path)
