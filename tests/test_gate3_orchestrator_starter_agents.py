"""
Tests for Gate 3 — Multi-Agent Orchestrator GUI & Starter Agents:
Planner, Researcher, Coder, Reviewer, Tester, Debugger, Release,
StructuredAgentResult contract, and AgentCritic gating.
"""
import pytest
from ai.agents.orchestrator import MultiAgentOrchestrator, AgentRole, Subagent, StructuredAgentResult
from ai.agents.critic import AgentCritic, ReviewStatus


def test_starter_agents_registration(tmp_path):
    orchestrator = MultiAgentOrchestrator(str(tmp_path))

    # Verify all specification starter agents are registered
    assert orchestrator.get_subagent(AgentRole.PLANNER) is not None
    assert orchestrator.get_subagent(AgentRole.RESEARCHER) is not None
    assert orchestrator.get_subagent(AgentRole.CODER) is not None
    assert orchestrator.get_subagent(AgentRole.REVIEWER) is not None
    assert orchestrator.get_subagent(AgentRole.TESTER) is not None
    assert orchestrator.get_subagent(AgentRole.DEBUGGER) is not None
    assert orchestrator.get_subagent(AgentRole.RELEASE) is not None
    assert orchestrator.get_subagent(AgentRole.ARCHITECT) is not None
    assert orchestrator.get_subagent(AgentRole.CRITIC) is not None


def test_structured_agent_result_contract():
    result = StructuredAgentResult(
        task_id="task-01",
        status="success",
        changed_files=["auth/login.py", "tests/test_login.py"],
        evidence="100% test coverage achieved",
        errors=[],
        test_results={"passed": 5, "failed": 0},
        unresolved_questions=[],
        output="Authentication module implemented.",
        artifacts=["login.py"]
    )

    d = result.to_dict()
    assert d["task_id"] == "task-01"
    assert d["status"] == "success"
    assert len(d["changed_files"]) == 2
    assert d["test_results"]["passed"] == 5


def test_orchestrator_critic_blocks_vulnerable_code_in_pipeline(tmp_path):
    orchestrator = MultiAgentOrchestrator(str(tmp_path))

    # Coder generates code with dangerous eval()
    coder = orchestrator.get_subagent(AgentRole.CODER)
    coder.set_handler(lambda task, ctx: {
        "status": "success",
        "output": "def execute_user_script(payload):\n    return eval(payload)\n",
        "artifacts": ["script.py"]
    })

    plan = orchestrator.build_plan("Execute user scripts dynamically")
    res = orchestrator.run_plan(plan)

    # Must fail because Critic rejected the eval() injection
    assert res["success"] is False
    assert any("Rejected by Critic" in str(step.result_output) for step in plan.steps.values())
