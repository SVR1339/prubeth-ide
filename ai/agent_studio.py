"""
PRUBETH IDE — Agent Studio & Subagent Orchestration Architecture
Pillar 4 & 5: Agent Governance & Incremental Delivery

Provides a comprehensive Agent Studio with reusable agent definitions, 10 industry-standard
role templates, per-agent resource budgets, permission profiles, and an active
FileConflictGuard preventing concurrent subagents from corrupting shared workspace files.
"""

from __future__ import annotations

import copy
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Set


class FileConflictError(PermissionError):
    """Raised when concurrent agents attempt conflicting mutations on identical file paths."""
    pass


class FileConflictGuard:
    """Guards against simultaneous concurrent agent writes to identical file paths."""

    def __init__(self):
        self._file_locks: Dict[str, str] = {}  # normalized_path -> agent_id

    def acquire_lock(self, agent_id: str, file_path: str) -> bool:
        norm = file_path.replace("\\", "/").lower().strip()
        current_owner = self._file_locks.get(norm)
        if current_owner and current_owner != agent_id:
            raise FileConflictError(
                f"File conflict detected: '{file_path}' is currently locked by agent '{current_owner}'. "
                f"Agent '{agent_id}' cannot overwrite concurrently."
            )
        self._file_locks[norm] = agent_id
        return True

    def release_lock(self, agent_id: str, file_path: str) -> None:
        norm = file_path.replace("\\", "/").lower().strip()
        if self._file_locks.get(norm) == agent_id:
            del self._file_locks[norm]

    def release_all_locks(self, agent_id: str) -> None:
        to_del = [p for p, aid in self._file_locks.items() if aid == agent_id]
        for p in to_del:
            del self._file_locks[p]

    def get_locked_files(self) -> Dict[str, str]:
        return dict(self._file_locks)


@dataclass
class AgentSpec:
    """Complete specification defining an autonomous or task-specialized agent."""
    agent_id: str
    name: str
    role: str
    instructions: str
    model_id: str = "qwen2.5:1.5b"
    allowed_tools: List[str] = field(default_factory=lambda: ["read_file", "search_code"])
    context_policy: str = "workspace_ast"  # open_files, selection_only, workspace_ast, full
    permission_profile: str = "standard"  # read_only, standard, full_sandbox
    max_steps: int = 30
    timeout_seconds: int = 180
    retry_policy: str = "exponential_backoff"
    output_format: str = "markdown"
    enabled: bool = True
    version: str = "1.0.0"


class AgentStudio:
    """Central catalog and lifecycle manager for all custom and templated agents."""

    _instance: Optional[AgentStudio] = None

    def __init__(self):
        self._agents: Dict[str, AgentSpec] = {}
        self.conflict_guard = FileConflictGuard()
        self._load_templates()

    @classmethod
    def get_instance(cls) -> AgentStudio:
        if cls._instance is None:
            cls._instance = AgentStudio()
        return cls._instance

    def register_agent(self, spec: AgentSpec) -> None:
        self._agents[spec.agent_id] = spec

    def get_agent(self, agent_id: str) -> Optional[AgentSpec]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[AgentSpec]:
        return list(self._agents.values())

    def duplicate_agent(self, source_id: str, new_id: str, new_name: str) -> AgentSpec:
        src = self.get_agent(source_id)
        if not src:
            raise KeyError(f"Source agent '{source_id}' does not exist.")
        dup = copy.deepcopy(src)
        dup.agent_id = new_id
        dup.name = new_name
        self.register_agent(dup)
        return dup

    def export_agent_json(self, agent_id: str) -> str:
        agent = self.get_agent(agent_id)
        if not agent:
            raise KeyError(f"Agent '{agent_id}' not found.")
        return json.dumps(asdict(agent), indent=2)

    def import_agent_json(self, raw_json: str) -> AgentSpec:
        data = json.loads(raw_json)
        spec = AgentSpec(**data)
        self.register_agent(spec)
        return spec

    def _load_templates(self) -> None:
        """Pre-populates the 10 industry-standard reusable agent role templates."""
        templates = [
            AgentSpec(
                agent_id="template.planner",
                name="System Architect & Planner",
                role="Planner",
                instructions="Decompose requirements into verifiable implementation milestones with PRINCE2 stage boundaries.",
                allowed_tools=["read_file", "list_files", "search_code"],
                permission_profile="read_only",
                max_steps=15
            ),
            AgentSpec(
                agent_id="template.researcher",
                name="Codebase & Documentation Researcher",
                role="Researcher",
                instructions="Inspect symbol hierarchies, AST references, and dependencies to answer implementation queries.",
                allowed_tools=["read_file", "search_code", "web_search"],
                permission_profile="read_only",
                max_steps=20
            ),
            AgentSpec(
                agent_id="template.implementer",
                name="Code Implementer",
                role="Code Implementer",
                instructions="Author high-efficiency, clean, and bug-free code matching design tokens and architectural contracts.",
                allowed_tools=["read_file", "write_file", "patch_file", "list_files"],
                permission_profile="standard",
                max_steps=40
            ),
            AgentSpec(
                agent_id="template.reviewer",
                name="Peer Code Reviewer",
                role="Code Reviewer",
                instructions="Review unified diffs for algorithmic soundness, edge cases, type safety, and framework adherence.",
                allowed_tools=["read_file", "search_code"],
                permission_profile="read_only",
                max_steps=15
            ),
            AgentSpec(
                agent_id="template.tester",
                name="Test Engineer",
                role="Test Engineer",
                instructions="Generate and execute comprehensive unit, integration, and crash test suites with 100% assertions.",
                allowed_tools=["read_file", "write_file", "run_tests", "run_command"],
                permission_profile="standard",
                max_steps=30
            ),
            AgentSpec(
                agent_id="template.debugger",
                name="Runtime Debugger & RCA Specialist",
                role="Debugger",
                instructions="Analyze tracebacks, inspect variable bounds, and formulate surgical minimal-diff fixes.",
                allowed_tools=["read_file", "patch_file", "run_tests"],
                permission_profile="standard",
                max_steps=25
            ),
            AgentSpec(
                agent_id="template.doc_writer",
                name="Technical Documentation Writer",
                role="Documentation Writer",
                instructions="Produce clear, accurate Architecture Decision Records, READMEs, and API specifications.",
                allowed_tools=["read_file", "write_file", "list_files"],
                permission_profile="standard",
                max_steps=15
            ),
            AgentSpec(
                agent_id="template.security_reviewer",
                name="Application Security Auditor",
                role="Security Reviewer",
                instructions="Audit source code for command injection, path traversal, hardcoded secrets, and unsafe deserialization.",
                allowed_tools=["read_file", "search_code"],
                permission_profile="read_only",
                max_steps=20
            ),
            AgentSpec(
                agent_id="template.refactorer",
                name="Refactoring Specialist",
                role="Refactoring Specialist",
                instructions="Refactor redundant patterns into clean abstractions while preserving 100% test pass rates.",
                allowed_tools=["read_file", "patch_file", "run_tests"],
                permission_profile="standard",
                max_steps=35
            ),
            AgentSpec(
                agent_id="template.release_engineer",
                name="Release & Packaging Specialist",
                role="Release Specialist",
                instructions="Verify build manifests, executable packaging, dependency licenses, and clean runtime payloads.",
                allowed_tools=["read_file", "list_files", "run_command"],
                permission_profile="standard",
                max_steps=25
            )
        ]
        for t in templates:
            self.register_agent(t)
