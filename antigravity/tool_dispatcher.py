"""
PRUBETH IDE — Antigravity Structured Tool Dispatcher
Bridges the ReAct `Action` step to real tool execution with schema validation and audit.

Research Foundation:
  - ReAct (Yao et al., 2022): The "Action" step requires a structured dispatch mechanism
    that validates arguments BEFORE execution to prevent hallucinated tool calls.
  - Tool-calling in LLMs: JSON schema validation on tool inputs prevents a class of
    bugs where models hallucinate non-existent arguments or incorrect types.

Architecture:
  1. ToolParameter:    JSON-schema-style parameter definition (name, type, required)
  2. ToolSchema:       Complete tool specification with parameters and docstring
  3. ToolRegistry:     Maps tool names → schemas and handlers
  4. ToolCallResult:   Structured result containing observation text and raw output
  5. ToolDispatcher:   Routes Action strings → validated execution → Observation
"""
import re
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple


# ---------------------------------------------------------------------------
# Tool Schema & Parameter Definitions
# ---------------------------------------------------------------------------

class ToolParameterType(str):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    LIST = "list"
    DICT = "dict"
    ANY = "any"


@dataclass
class ToolParameter:
    """JSON-schema-style parameter definition for a tool input."""
    name: str
    param_type: str          # ToolParameterType constant
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[Any]] = None    # Allowed values for string enums

    def validate(self, value: Any) -> Tuple[bool, Optional[str]]:
        """Validates a value against this parameter's schema. Returns (valid, error_msg)."""
        if value is None:
            if self.required and self.default is None:
                return False, f"Required parameter '{self.name}' is missing"
            return True, None

        if self.param_type == ToolParameterType.STRING and not isinstance(value, str):
            return False, f"Parameter '{self.name}' must be a string, got {type(value).__name__}"
        elif self.param_type == ToolParameterType.INTEGER and not isinstance(value, int):
            return False, f"Parameter '{self.name}' must be an integer, got {type(value).__name__}"
        elif self.param_type == ToolParameterType.FLOAT and not isinstance(value, (int, float)):
            return False, f"Parameter '{self.name}' must be a number, got {type(value).__name__}"
        elif self.param_type == ToolParameterType.BOOLEAN and not isinstance(value, bool):
            return False, f"Parameter '{self.name}' must be a boolean, got {type(value).__name__}"
        elif self.param_type == ToolParameterType.LIST and not isinstance(value, list):
            return False, f"Parameter '{self.name}' must be a list, got {type(value).__name__}"
        elif self.param_type == ToolParameterType.DICT and not isinstance(value, dict):
            return False, f"Parameter '{self.name}' must be a dict, got {type(value).__name__}"

        if self.enum is not None and value not in self.enum:
            return False, f"Parameter '{self.name}' must be one of {self.enum}, got '{value}'"

        return True, None


@dataclass
class ToolSchema:
    """Complete specification for an agent-callable tool."""
    name: str
    description: str
    parameters: List[ToolParameter] = field(default_factory=list)
    returns: str = "string"             # Expected return type description
    examples: List[str] = field(default_factory=list)
    category: str = "general"          # "file_io", "shell", "web", "git", "analysis", "general"
    requires_approval: bool = False    # Whether high-risk actions need user sign-off

    def to_prompt_description(self) -> str:
        """Renders a compact tool signature for injection into agent prompts."""
        param_parts = []
        for p in self.parameters:
            req_str = "" if p.required else "?"
            param_parts.append(f"{p.name}{req_str}: {p.param_type}")
        params_str = ", ".join(param_parts)
        return f"{self.name}({params_str}) → {self.returns}: {self.description}"

    def to_json_schema(self) -> Dict[str, Any]:
        """Returns a JSON-schema-compatible dict for LLM function-calling APIs."""
        properties = {}
        required_fields = []
        for p in self.parameters:
            prop: Dict[str, Any] = {"type": p.param_type, "description": p.description}
            if p.enum:
                prop["enum"] = p.enum
            if p.default is not None:
                prop["default"] = p.default
            properties[p.name] = prop
            if p.required:
                required_fields.append(p.name)
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_fields
            }
        }


# ---------------------------------------------------------------------------
# Tool Call Result
# ---------------------------------------------------------------------------

@dataclass
class ToolCallResult:
    """Structured result from a tool dispatch, forming the ReAct Observation."""
    call_id: str = field(default_factory=lambda: f"call-{uuid.uuid4().hex[:6]}")
    tool_name: str = ""
    args_used: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    observation: str = ""           # Human-readable summary for ReAct prompt injection
    raw_output: Any = None          # Raw return value from handler
    error: Optional[str] = None
    duration_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_react_observation(self) -> str:
        """Formats as a ReAct Observation: string for prompt injection."""
        if self.success:
            return f"Observation: {self.observation}"
        return f"Observation: ERROR calling '{self.tool_name}': {self.error}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "success": self.success,
            "observation": self.observation,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp
        }


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

class DuplicateToolError(ValueError):
    """Raised when registering a tool that already exists."""
    pass


class UnknownToolError(KeyError):
    """Raised when dispatching a call to an unregistered tool."""
    pass


class ToolValidationError(ValueError):
    """Raised when tool arguments fail schema validation."""
    pass


class ToolRegistry:
    """
    Central registry mapping tool names → schemas and callable handlers.
    Provides a compact prompt table of all available tools for agent context.
    """

    def __init__(self):
        self._schemas: Dict[str, ToolSchema] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}

    def register(self, schema: ToolSchema, handler: Callable[..., Any],
                 overwrite: bool = False) -> None:
        """Registers a tool schema and its implementation handler."""
        if schema.name in self._schemas and not overwrite:
            raise DuplicateToolError(f"Tool '{schema.name}' is already registered. Use overwrite=True to replace.")
        self._schemas[schema.name] = schema
        self._handlers[schema.name] = handler

    def unregister(self, tool_name: str) -> bool:
        """Removes a tool from the registry."""
        if tool_name in self._schemas:
            del self._schemas[tool_name]
            del self._handlers[tool_name]
            return True
        return False

    def get_schema(self, tool_name: str) -> Optional[ToolSchema]:
        return self._schemas.get(tool_name)

    def list_tools(self) -> List[str]:
        return list(self._schemas.keys())

    def get_all_schemas(self) -> List[ToolSchema]:
        return list(self._schemas.values())

    def build_tool_prompt_table(self, category: Optional[str] = None) -> str:
        """Builds a compact tool directory for injection into agent system prompts."""
        schemas = [s for s in self._schemas.values()
                   if category is None or s.category == category]
        if not schemas:
            return "No tools available."
        lines = ["### AVAILABLE TOOLS:"]
        for schema in sorted(schemas, key=lambda s: s.category + s.name):
            lines.append(f"  {schema.to_prompt_description()}")
        return "\n".join(lines)

    def to_json_schemas(self) -> List[Dict[str, Any]]:
        """Returns all tool schemas in JSON-schema format for LLM function-calling APIs."""
        return [s.to_json_schema() for s in self._schemas.values()]

    def __len__(self) -> int:
        return len(self._schemas)


# ---------------------------------------------------------------------------
# Action Parser — parses "tool_name(arg1=val1, arg2=val2)" from ReAct output
# ---------------------------------------------------------------------------

class ActionParser:
    """
    Parses structured action strings from ReAct agent output into tool calls.
    Supports multiple action formats:
      - Function-style: `read_file(path="main.py", max_lines=100)`
      - JSON-style: `{"tool": "read_file", "args": {"path": "main.py"}}`
      - Simple key=value: `read_file path=main.py`
    """

    @staticmethod
    def parse(action_str: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parses an action string into (tool_name, args_dict).
        Raises ValueError if the action string cannot be parsed.
        """
        action_str = action_str.strip()

        # 1. Try JSON format first
        if action_str.startswith("{"):
            try:
                data = json.loads(action_str)
                tool_name = data.get("tool") or data.get("name") or data.get("action")
                args = data.get("args") or data.get("arguments") or data.get("parameters") or {}
                if tool_name:
                    return tool_name, args
            except (json.JSONDecodeError, AttributeError):
                pass

        # 2. Try function-call format: tool_name(arg1=val1, arg2="val2", ...)
        fn_match = re.match(r'^(\w[\w_]*)[\s]*\((.*)?\)$', action_str, re.DOTALL)
        if fn_match:
            tool_name = fn_match.group(1)
            args_str = (fn_match.group(2) or "").strip()
            args = ActionParser._parse_kwargs(args_str)
            return tool_name, args

        # 3. Try simple space-separated format: tool_name key=val key2=val2
        parts = action_str.split(None, 1)
        if parts:
            tool_name = parts[0]
            args = ActionParser._parse_kwargs(parts[1]) if len(parts) > 1 else {}
            return tool_name, args

        raise ValueError(f"Cannot parse action string: '{action_str}'")

    @staticmethod
    def _parse_kwargs(kwargs_str: str) -> Dict[str, Any]:
        """Parses key=value pairs from a string, supporting quoted values."""
        args: Dict[str, Any] = {}
        if not kwargs_str.strip():
            return args

        # Try JSON-object parsing first (handles nested structures)
        try:
            maybe_json = "{" + kwargs_str + "}"
            parsed = json.loads(maybe_json)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, Exception):
            pass

        # Regex-based key=value parsing
        pattern = re.compile(r'(\w+)\s*=\s*(?:"([^"]*?)"|\'([^\']*?)\'|(\S+))')
        for match in pattern.finditer(kwargs_str):
            key = match.group(1)
            value = match.group(2) or match.group(3) or match.group(4)
            # Auto-cast booleans, integers, floats
            if value is not None:
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                else:
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                            value = float(value)
                        except ValueError:
                            pass
            args[key] = value
        return args


# ---------------------------------------------------------------------------
# Tool Dispatcher — routes Action → validated execution → Observation
# ---------------------------------------------------------------------------

class ToolDispatcher:
    """
    Central dispatcher routing ReAct Action strings to registered tools.
    Validates arguments against schema, executes the handler,
    and returns a structured ToolCallResult for observation injection.
    """

    def __init__(self, registry: ToolRegistry,
                 approval_hook: Optional[Callable[[str, Dict[str, Any]], bool]] = None):
        self.registry = registry
        self.approval_hook = approval_hook
        self.audit_log: List[ToolCallResult] = []

    def dispatch_action(self, action_str: str) -> ToolCallResult:
        """
        Parses and dispatches a ReAct action string.
        Returns a ToolCallResult representing the Observation.
        """
        start = time.time()

        # 1. Parse the action string
        try:
            tool_name, args = ActionParser.parse(action_str)
        except ValueError as e:
            result = ToolCallResult(
                tool_name="<unknown>",
                success=False,
                error=f"Action parse error: {e}",
                observation=f"Could not parse action string: '{action_str}'"
            )
            self.audit_log.append(result)
            return result

        # 2. Look up schema
        schema = self.registry.get_schema(tool_name)
        if schema is None:
            result = ToolCallResult(
                tool_name=tool_name,
                args_used=args,
                success=False,
                error=f"Unknown tool: '{tool_name}'",
                observation=f"Tool '{tool_name}' is not registered. Available: {self.registry.list_tools()}"
            )
            self.audit_log.append(result)
            return result

        # 3. Validate arguments against schema
        final_args: Dict[str, Any] = {}
        for param in schema.parameters:
            value = args.get(param.name, param.default)
            valid, error_msg = param.validate(value)
            if not valid:
                result = ToolCallResult(
                    tool_name=tool_name,
                    args_used=args,
                    success=False,
                    error=error_msg,
                    observation=f"Schema validation failed: {error_msg}"
                )
                self.audit_log.append(result)
                return result
            if value is not None:
                final_args[param.name] = value
            elif param.default is not None:
                final_args[param.name] = param.default

        # 4. Approval gate for high-risk tools
        if schema.requires_approval and self.approval_hook:
            approved = self.approval_hook(tool_name, final_args)
            if not approved:
                result = ToolCallResult(
                    tool_name=tool_name,
                    args_used=final_args,
                    success=False,
                    error="Execution rejected by user approval gate",
                    observation=f"Tool '{tool_name}' requires user approval and was rejected."
                )
                self.audit_log.append(result)
                return result

        # 5. Execute the handler
        handler = self.registry._handlers.get(tool_name)
        try:
            raw_output = handler(**final_args)
            observation = str(raw_output) if raw_output is not None else "(no output)"
            result = ToolCallResult(
                tool_name=tool_name,
                args_used=final_args,
                success=True,
                raw_output=raw_output,
                observation=observation[:2000],   # Truncate large outputs for context injection
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as ex:
            result = ToolCallResult(
                tool_name=tool_name,
                args_used=final_args,
                success=False,
                error=str(ex),
                observation=f"Tool '{tool_name}' raised an exception: {ex}",
                duration_ms=(time.time() - start) * 1000
            )

        self.audit_log.append(result)
        return result

    def dispatch_dict(self, tool_name: str, args: Dict[str, Any]) -> ToolCallResult:
        """Convenience method: dispatches a pre-parsed tool call dict."""
        args_str = json.dumps({"tool": tool_name, "args": args})
        return self.dispatch_action(args_str)

    def get_audit_log(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.audit_log]
