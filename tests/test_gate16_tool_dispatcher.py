"""
Gate 16: Structured Tool Dispatcher — Integration Tests
Tests: ToolSchema, ToolRegistry, ActionParser, ToolDispatcher, and approval gate.
"""
import pytest
from antigravity.tool_dispatcher import (
    ToolSchema, ToolParameter, ToolRegistry, ToolDispatcher,
    ActionParser, ToolCallResult, DuplicateToolError, UnknownToolError
)


# ─── Helpers ─── #

def make_registry() -> ToolRegistry:
    """Builds a ToolRegistry with two test tools."""
    registry = ToolRegistry()

    # Tool 1: read_file — safe, no approval needed
    read_schema = ToolSchema(
        name="read_file",
        description="Reads a file and returns its contents.",
        parameters=[
            ToolParameter("path", "string", "Absolute file path", required=True),
            ToolParameter("max_lines", "integer", "Maximum lines to return", required=False, default=100),
        ],
        returns="string",
        category="file_io"
    )
    registry.register(read_schema, lambda path, max_lines=100: f"Contents of {path} ({max_lines} lines)")

    # Tool 2: run_shell — high-risk, requires approval
    shell_schema = ToolSchema(
        name="run_shell",
        description="Executes a shell command.",
        parameters=[
            ToolParameter("command", "string", "Shell command to execute", required=True),
        ],
        returns="string",
        category="shell",
        requires_approval=True
    )
    registry.register(shell_schema, lambda command: f"$ {command}\nok")

    return registry


# ─── Test 1: ToolRegistry registration and duplicate handling ─── #
def test_tool_registry_register_and_list():
    """ToolRegistry registers tools, blocks duplicates, and supports listing."""
    registry = make_registry()

    assert "read_file" in registry.list_tools()
    assert "run_shell" in registry.list_tools()
    assert len(registry) == 2

    # Duplicate registration should raise
    dup_schema = ToolSchema("read_file", "Duplicate", parameters=[], returns="string")
    with pytest.raises(DuplicateToolError):
        registry.register(dup_schema, lambda: None)

    # Allow overwrite
    registry.register(dup_schema, lambda: "overwritten", overwrite=True)
    assert registry.get_schema("read_file").description == "Duplicate"

    # Verify prompt table contains all tools
    prompt_table = registry.build_tool_prompt_table()
    assert "read_file" in prompt_table
    assert "run_shell" in prompt_table


# ─── Test 2: ActionParser — multiple input formats ─── #
def test_action_parser_multiple_formats():
    """ActionParser handles function-call, JSON, and simple space-separated formats."""
    # Function-call format
    name, args = ActionParser.parse('read_file(path="/workspace/main.py", max_lines=50)')
    assert name == "read_file"
    assert args["path"] == "/workspace/main.py"
    assert args["max_lines"] == 50

    # JSON format
    name, args = ActionParser.parse('{"tool": "run_shell", "args": {"command": "ls -la"}}')
    assert name == "run_shell"
    assert args["command"] == "ls -la"

    # Simple format
    name, args = ActionParser.parse('read_file path=/workspace/config.json')
    assert name == "read_file"

    # Boolean auto-cast
    name, args = ActionParser.parse('some_tool flag=true count=42 ratio=3.14')
    assert args.get("flag") is True
    assert args.get("count") == 42


# ─── Test 3: ToolDispatcher — successful dispatch and observation ─── #
def test_tool_dispatcher_successful_dispatch():
    """ToolDispatcher routes an action string to the correct handler and returns Observation."""
    registry = make_registry()
    dispatcher = ToolDispatcher(registry=registry)

    result = dispatcher.dispatch_action('read_file(path="/workspace/utils.py", max_lines=30)')

    assert result.success is True
    assert result.tool_name == "read_file"
    assert "/workspace/utils.py" in result.observation
    assert result.error is None
    assert result.duration_ms >= 0

    # Verify observation format for ReAct injection
    react_obs = result.to_react_observation()
    assert react_obs.startswith("Observation:")

    # Audit log entry
    log = dispatcher.get_audit_log()
    assert len(log) == 1
    assert log[0]["tool_name"] == "read_file"


# ─── Test 4: ToolDispatcher — schema validation rejects bad args ─── #
def test_tool_dispatcher_schema_validation_failure():
    """ToolDispatcher rejects calls that fail schema validation without executing."""
    registry = make_registry()
    dispatcher = ToolDispatcher(registry=registry)

    # Missing required "path" argument
    result = dispatcher.dispatch_action("read_file(max_lines=50)")
    assert result.success is False
    assert "path" in (result.error or "").lower() or "required" in (result.error or "").lower()
    assert result.observation.startswith("Schema validation failed") or "missing" in result.observation.lower()


# ─── Test 5: ToolDispatcher — unknown tool returns error observation ─── #
def test_tool_dispatcher_unknown_tool():
    """ToolDispatcher returns a structured error when an unknown tool is called."""
    registry = make_registry()
    dispatcher = ToolDispatcher(registry=registry)

    result = dispatcher.dispatch_action("nonexistent_tool(x=1)")
    assert result.success is False
    assert "nonexistent_tool" in (result.error or "")
    assert "not registered" in result.observation.lower() or "nonexistent_tool" in result.observation


# ─── Test 6: ToolDispatcher — approval gate blocks high-risk tools ─── #
def test_tool_dispatcher_approval_gate_rejection():
    """High-risk tools are blocked by the approval gate when it returns False."""
    registry = make_registry()

    # Approval gate always rejects
    dispatcher = ToolDispatcher(registry=registry, approval_hook=lambda tool, args: False)

    result = dispatcher.dispatch_action('run_shell(command="rm -rf /critical_dir")')
    assert result.success is False
    assert "rejected" in result.observation.lower() or "approval" in result.observation.lower()

    # Now with an approving hook
    approving_dispatcher = ToolDispatcher(registry=registry, approval_hook=lambda tool, args: True)
    result = approving_dispatcher.dispatch_action('run_shell(command="echo hello")')
    assert result.success is True
    assert "echo hello" in result.observation
