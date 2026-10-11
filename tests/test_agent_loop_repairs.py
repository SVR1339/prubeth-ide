"""
Regression and Integration Tests for Phase One Agent Execution Loop Repairs:
1. Context and Goal Survival Across Multi-Step Agent Loops
2. ToolGateway Approval Hook Execution and Rejection
3. Reachability and Execution of Checkpoint and Semantic Tools via Regex Extractor
4. TaskEngine State Tracking and Step Recording
5. Idempotent Handling and Graceful Error Reporting
"""
import pytest
from pathlib import Path
from local_ai_studio_pro import AgentToolEngine
from core.workspace import WorkspaceGuard
from core.tool_gateway import ToolGateway, CommandRiskLevel, ToolSecurityError
from core.task_engine import TaskState


def test_agent_tool_extractor_comprehensive_coverage():
    """Verify all 13 supported tools are extractable via model XML tags."""
    sample_xml = """
    I will inspect the workspace, create a checkpoint, and search the code.
    <tool:read_file path="core/router.py" />
    <tool:write_file path="output.txt">Sample text content</tool:write_file>
    <tool:patch_file path="file.py">
      <search>old_val = 1</search>
      <replace>old_val = 2</replace>
    </tool:patch_file>
    <tool:list_files dir="core" />
    <tool:search_code query="WorkspaceGuard" />
    <tool:semantic_search query="model router cascade" top_k="3" />
    <tool:create_checkpoint description="Before critical refactor" />
    <tool:rollback_checkpoint id="chk_12345" />
    <tool:run_command cmd="git status" />
    <tool:run_tests />
    <tool:web_search query="PyQt5 QScintilla documentation" />
    <tool:verify_deliverable name="Auth Module" criteria="All tests pass" />
    <tool:call_mcp server="local" tool="ping" args='{"count": 1}' />
    """
    tools = AgentToolEngine.extract_tools(sample_xml)
    tool_names = [t[0] for t in tools]

    assert "read_file" in tool_names
    assert "write_file" in tool_names
    assert "patch_file" in tool_names
    assert "list_files" in tool_names
    assert "search_code" in tool_names
    assert "semantic_search" in tool_names
    assert "create_checkpoint" in tool_names
    assert "rollback_checkpoint" in tool_names
    assert "run_command" in tool_names
    assert "run_tests" in tool_names
    assert "web_search" in tool_names
    assert "verify_deliverable" in tool_names
    assert "call_mcp" in tool_names

    # Check extracted parameters
    sem = next(t for t in tools if t[0] == "semantic_search")[1]
    assert sem["query"] == "model router cascade"
    assert sem["top_k"] == 3

    chk = next(t for t in tools if t[0] == "create_checkpoint")[1]
    assert chk["description"] == "Before critical refactor"

    rb = next(t for t in tools if t[0] == "rollback_checkpoint")[1]
    assert rb["id"] == "chk_12345"


def test_tool_gateway_approval_hook_approved(tmp_path):
    """Verify that a registered approval hook allows high-risk commands when approved."""
    ws = WorkspaceGuard(tmp_path)
    approved_calls = []

    def mock_approval(cmd, reason):
        approved_calls.append((cmd, reason))
        return True

    engine = AgentToolEngine(tmp_path, settings={"unrestricted_mode": False}, approval_hook=mock_approval)
    cmd = 'python -c "print(\'approved_safe\')" # powershell -enc'
    res = engine.execute_tool("run_command", {"cmd": cmd})

    # Tool execution proceeded without throwing unhandled ToolSecurityError
    assert len(approved_calls) == 1
    assert "powershell -enc" in approved_calls[0][0]
    assert "approved_safe" in res


def test_tool_gateway_approval_hook_rejected(tmp_path):
    """Verify that a rejected approval safely blocks command execution without crashing."""
    ws = WorkspaceGuard(tmp_path)
    rejected_calls = []

    def mock_rejection(cmd, reason):
        rejected_calls.append((cmd, reason))
        return False

    engine = AgentToolEngine(tmp_path, settings={"unrestricted_mode": False}, approval_hook=mock_rejection)
    cmd = 'python -c "print(\'blocked\')" # rmdir /s'
    res = engine.execute_tool("run_command", {"cmd": cmd})

    assert len(rejected_calls) == 1
    assert "Security Error" in res
    assert "Execution rejected by user" in res


def test_task_engine_records_steps_during_execution(tmp_path):
    """Verify that TaskEngine automatically logs task steps and status transitions."""
    engine = AgentToolEngine(tmp_path)
    task_id = engine.start_agent_task("Refactor authentication logic")
    assert task_id is not None
    assert engine.active_task == task_id

    # 1. Successful file write
    res1 = engine.execute_tool("write_file", {"path": "auth.py", "content": "def authenticate(): return True\n"})
    assert "Successfully wrote" in res1

    # 2. Reading created file
    res2 = engine.execute_tool("read_file", {"path": "auth.py"})
    assert "def authenticate" in res2

    # 3. Failing read on non-existent file
    res3 = engine.execute_tool("read_file", {"path": "missing.py"})
    assert "Error:" in res3

    # Check TaskEngine recorded steps
    task = engine.task_engine.get_task(task_id)
    assert task is not None
    assert task.goal == "Refactor authentication logic"
    assert len(task.steps) == 3

    assert task.steps[0].tool_name == "write_file"
    assert task.steps[0].state == TaskState.COMPLETED

    assert task.steps[1].tool_name == "read_file"
    assert task.steps[1].state == TaskState.COMPLETED

    assert task.steps[2].tool_name == "read_file"
    assert task.steps[2].state == TaskState.FAILED


def test_checkpoint_and_rollback_tool_execution(tmp_path):
    """Verify autonomous checkpoint creation and rollback via AgentToolEngine."""
    engine = AgentToolEngine(tmp_path)
    test_file = tmp_path / "app.py"
    test_file.write_text("initial_state = 1", encoding="utf-8")

    # 1. Create checkpoint
    res_chk = engine.execute_tool("create_checkpoint", {"description": "Baseline state"})
    assert "Created transactional checkpoint" in res_chk
    chk_id = engine.current_checkpoint_id
    assert chk_id is not None

    # 2. Mutate file
    engine.execute_tool("write_file", {"path": "app.py", "content": "mutated_state = 99"})
    assert test_file.read_text(encoding="utf-8") == "mutated_state = 99"

    # 3. Rollback checkpoint
    res_rb = engine.execute_tool("rollback_checkpoint", {"id": chk_id})
    assert "Rollback successful" in res_rb
    assert test_file.read_text(encoding="utf-8") == "initial_state = 1"


def test_unknown_tool_rejection_and_schema_validation(tmp_path):
    """Verify unknown tools or invalid arguments produce clear actionable error strings."""
    engine = AgentToolEngine(tmp_path)
    res = engine.execute_tool("fake_destructive_tool", {"foo": "bar"})
    assert "Unknown tool: fake_destructive_tool" in res
