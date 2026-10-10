"""
Tests for SUKHI IDE Multi-Agent Subsystem:
ExecutionPlan (DAG), AgentCritic (Safety & AST), and MultiAgentOrchestrator.
"""
import pytest
from ai.agents.planner import ExecutionPlan, TaskStep, TaskStatus, CycleDetectedError
from ai.agents.critic import AgentCritic, ReviewStatus
from ai.agents.orchestrator import MultiAgentOrchestrator, AgentRole, Subagent


def test_execution_plan_topological_sort_and_cycle_detection():
    plan = ExecutionPlan(goal="Build Feature")
    s1 = plan.add_step("Design", "Spec interfaces", assigned_role="architect", step_id="s1")
    s2 = plan.add_step("Code", "Implement core logic", assigned_role="coder", dependencies=["s1"], step_id="s2")
    s3 = plan.add_step("Test", "Run test cases", assigned_role="tester", dependencies=["s2"], step_id="s3")

    order = plan.topological_order()
    assert [s.step_id for s in order] == ["s1", "s2", "s3"]

    # Verify ready steps initially
    ready = plan.get_ready_steps()
    assert len(ready) == 1
    assert ready[0].step_id == "s1"

    # Mark s1 complete
    plan.mark_step_status("s1", TaskStatus.COMPLETED)
    ready = plan.get_ready_steps()
    assert len(ready) == 1
    assert ready[0].step_id == "s2"

    # Test cycle detection
    with pytest.raises(CycleDetectedError):
        plan.add_step("Cycle Step", "Depends on s3", dependencies=["s3"], step_id="s1")


def test_agent_critic_security_and_syntax_analysis():
    critic = AgentCritic()

    # 1. Clean valid Python code
    clean_code = '''
def add(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b
'''
    report = critic.analyze_code(clean_code, file_path="math_utils.py")
    assert report.status == ReviewStatus.APPROVED
    assert report.score >= 9.0

    # 2. Dangerous eval() call
    eval_code = "result = eval(user_input)"
    report = critic.analyze_code(eval_code, file_path="insecure.py")
    assert report.status == ReviewStatus.REJECTED
    assert any("eval()" in issue.message for issue in report.issues)

    # 3. Hardcoded OpenAI secret
    secret_code = 'API_KEY = "sk-1234567890abcdef1234567890abcdef"'
    report = critic.analyze_code(secret_code, file_path="config.py")
    assert report.status == ReviewStatus.REJECTED
    assert any("secret" in issue.message.lower() for issue in report.issues)

    # 4. Syntax error
    broken_code = "def bad_syntax(:\n    pass"
    report = critic.analyze_code(broken_code, file_path="syntax_err.py")
    assert report.status == ReviewStatus.REJECTED
    assert any("SyntaxError" in issue.message for issue in report.issues)


def test_multi_agent_orchestrator_pipeline(tmp_path):
    orchestrator = MultiAgentOrchestrator(str(tmp_path))

    # Check default registered agents
    assert orchestrator.get_subagent(AgentRole.ARCHITECT) is not None
    assert orchestrator.get_subagent(AgentRole.CODER) is not None
    assert orchestrator.get_subagent(AgentRole.CRITIC) is not None
    assert orchestrator.get_subagent(AgentRole.TESTER) is not None

    # Custom coder handler generating clean code
    coder = orchestrator.get_subagent(AgentRole.CODER)
    coder.set_handler(lambda task, ctx: {
        "status": "success",
        "output": "def compute():\n    return 42\n",
        "artifacts": ["compute.py"]
    })

    plan = orchestrator.build_plan("Implement compute feature")
    assert len(plan.steps) == 4

    result = orchestrator.run_plan(plan)
    assert result["success"] is True
    assert result["progress"] == 100.0
    assert len(result["execution_log"]) == 4

    # Verify messages were posted
    assert len(orchestrator.messages) > 0


def test_multi_agent_orchestrator_critic_rejection(tmp_path):
    orchestrator = MultiAgentOrchestrator(str(tmp_path))

    # Coder outputs dangerous eval code
    coder = orchestrator.get_subagent(AgentRole.CODER)
    coder.set_handler(lambda task, ctx: {
        "status": "success",
        "output": "def run_raw(cmd):\n    return eval(cmd)\n",
        "artifacts": []
    })

    plan = orchestrator.build_plan("Insecure task")
    result = orchestrator.run_plan(plan)

    # Since Coder output was rejected by Critic, coder step failed and plan is not complete
    assert result["success"] is False
    assert any("Rejected by Critic" in step.result_output for step in plan.steps.values() if step.result_output)
