"""
PRUBETH IDE — Executive Autonomous Self-Healing & Project Scaffolding Engine
=============================================================================
Pillar 4 & 5: Autonomous Governance, Self-Processing Agents, and Multi-Scale Project Delivery

Coordinates specialized Executive Agents (Architect, Scaffolder, Critic, Debugger) to:
1. Scaffold Small-, Mid-, and Large-scale powered projects with complete, verified code.
2. Intercept syntax, runtime, import, and test failures autonomously.
3. Dissect tracebacks down to exact failing files, lines, and root cause anomalies.
4. Synthesize and apply surgical atomic patches via WorkspaceGuard and AST analysis.
5. Execute iterative self-healing loops until the project achieves 100% clean verification.
6. Enforce Model Restriction Governance (Low = Zero friction / Full Authority, Mid = Supervised, High = Review).
"""

from __future__ import annotations

import ast
import enum
import os
import re
import sys
import time
import uuid
import subprocess
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Set

from core.workspace import WorkspaceGuard, WorkspaceSecurityError
from ai.agents.critic import AgentCritic, ReviewReport, ReviewStatus
from ai.agents.planner import ExecutionPlan, TaskStep, TaskStatus


class ProjectScale(str, enum.Enum):
    SMALL = "small"          # Micro-utilities, fast single-script tools, CLI scripts (1-3 steps)
    MID = "mid"              # Multi-file service/API, business logic, data models, unit tests (5-15 steps)
    LARGE_POWERED = "large"  # Enterprise-grade multi-tier architecture, repositories, schemas, full test suites (15-50+ steps)


class ErrorCategory(str, enum.Enum):
    SYNTAX = "syntax"
    IMPORT = "import"
    ATTRIBUTE = "attribute"
    TYPE = "type"
    RUNTIME = "runtime"
    ASSERTION = "assertion"
    MISSING_FILE = "missing_file"
    UNKNOWN = "unknown"


@dataclass
class StackFrame:
    file_path: str
    line_number: int
    function_name: str
    code_line: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TracebackDiagnostic:
    error_type: str
    error_message: str
    category: ErrorCategory
    failing_file: Optional[str] = None
    line_number: Optional[int] = None
    frames: List[StackFrame] = field(default_factory=list)
    raw_output: str = ""
    suggested_fix_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        return d


class TracebackParser:
    """Robust multi-pattern diagnostic parser for Python, JS, and test runners."""

    PYTHON_FRAME_RE = re.compile(
        r'File\s+["\'](?P<file>[^"\']+)["\'],\s+line\s+(?P<line>\d+)(?:,\s+in\s+(?P<func>[^\n]+))?(?:\n\s+(?P<code>[^\n]+))?'
    )
    PYTHON_EXC_RE = re.compile(
        r'(?:(?P<exc>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Warning|Interrupt))|AssertionError):\s*(?P<msg>[^\n]*)'
    )
    SYNTAX_ERROR_RE = re.compile(
        r'SyntaxError:\s*(?P<msg>[^\n]+)'
    )
    PYTEST_FAIL_RE = re.compile(
        r'FAILED\s+(?P<file>[^:]+)::(?P<test>\w+)\s+-\s+(?P<exc>\w+)?(?::\s*(?P<msg>[^\n]+))?'
    )

    @classmethod
    def parse(cls, output: str, workspace_root: Optional[str] = None) -> Optional[TracebackDiagnostic]:
        if not output or not output.strip():
            return None

        frames: List[StackFrame] = []
        for m in cls.PYTHON_FRAME_RE.finditer(output):
            fpath = m.group("file")
            lno = int(m.group("line"))
            func = m.group("func") or "<module>"
            code = (m.group("code") or "").strip()
            frames.append(StackFrame(file_path=fpath, line_number=lno, function_name=func, code_line=code))

        # Determine failing file and line (typically the last frame within workspace or last frame overall)
        failing_file: Optional[str] = None
        line_number: Optional[int] = None
        if frames:
            # Prefer frame located inside workspace root if available
            chosen_frame = frames[-1]
            if workspace_root:
                ws_norm = str(Path(workspace_root).resolve()).lower()
                for frame in reversed(frames):
                    try:
                        resolved = str(Path(frame.file_path).resolve()).lower()
                        if ws_norm in resolved:
                            chosen_frame = frame
                            break
                    except Exception:
                        pass
            failing_file = chosen_frame.file_path
            line_number = chosen_frame.line_number

        # Parse Exception Type & Message
        error_type = "RuntimeError"
        error_msg = ""
        category = ErrorCategory.RUNTIME

        exc_match = None
        for m in cls.PYTHON_EXC_RE.finditer(output):
            exc_match = m

        if exc_match:
            error_type = exc_match.group("exc") or "AssertionError"
            error_msg = (exc_match.group("msg") or "").strip()
        elif "SyntaxError" in output:
            syn_m = cls.SYNTAX_ERROR_RE.search(output)
            error_type = "SyntaxError"
            error_msg = syn_m.group("msg").strip() if syn_m else "Invalid syntax"

        if "FAILED" in output and "::" in output:
            pt_m = cls.PYTEST_FAIL_RE.search(output)
            if pt_m:
                if not exc_match:
                    error_type = pt_m.group("exc") or "AssertionError"
                    error_msg = pt_m.group("msg") or f"Test failed in {pt_m.group('file')}::{pt_m.group('test')}"
                if not failing_file:
                    failing_file = pt_m.group("file")

        # Classify Category
        err_lower = error_type.lower()
        if "syntax" in err_lower or "indentation" in err_lower or "taberror" in err_lower:
            category = ErrorCategory.SYNTAX
        elif "import" in err_lower or "modulenotfound" in err_lower:
            category = ErrorCategory.IMPORT
        elif "attribute" in err_lower:
            category = ErrorCategory.ATTRIBUTE
        elif "type" in err_lower:
            category = ErrorCategory.TYPE
        elif "assertion" in err_lower:
            category = ErrorCategory.ASSERTION
        elif "filenotfound" in err_lower:
            category = ErrorCategory.MISSING_FILE
        else:
            category = ErrorCategory.RUNTIME

        # Generate summary
        summary = f"{error_type}: {error_msg}"
        if failing_file and line_number:
            summary += f" at {Path(failing_file).name}:{line_number}"

        return TracebackDiagnostic(
            error_type=error_type,
            error_message=error_msg,
            category=category,
            failing_file=failing_file,
            line_number=line_number,
            frames=frames,
            raw_output=output,
            suggested_fix_summary=summary
        )


@dataclass
class HealingResult:
    success: bool
    iterations_used: int
    diagnostics_resolved: List[TracebackDiagnostic] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    final_output: str = ""
    exit_code: int = 0
    audit_notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "iterations_used": self.iterations_used,
            "modified_files": self.modified_files,
            "exit_code": self.exit_code,
            "audit_notes": self.audit_notes,
            "diagnostics_resolved_count": len(self.diagnostics_resolved)
        }


class SelfHealingExecutiveAgent:
    """
    Executive coordinator for project scaffolding and zero-maintenance autonomous self-healing.
    """

    def __init__(
        self,
        workspace_root: str | Path,
        workspace_guard: Optional[WorkspaceGuard] = None,
        critic: Optional[AgentCritic] = None,
        checkpoint_manager: Optional[Any] = None,
        model_restriction_tier: str = "low"
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_guard = workspace_guard or WorkspaceGuard(self.workspace_root)
        self.critic = critic or AgentCritic(strict_security=False)
        self.checkpoint_manager = checkpoint_manager
        self.model_restriction_tier = model_restriction_tier.lower()

    def set_restriction_tier(self, tier: str) -> None:
        self.model_restriction_tier = tier.lower()

    # =========================================================================
    # 1. MULTI-SCALE PROJECT SCAFFOLDING
    # =========================================================================

    def scaffold_project(
        self,
        scale: ProjectScale,
        goal: str,
        target_subfolder: str = "",
        tech_stack: str = "python"
    ) -> Dict[str, Any]:
        """
        Decomposes requirements and produces production-grade multi-scale projects.
        """
        sub_dir = self.workspace_root / target_subfolder if target_subfolder else self.workspace_root
        sub_dir.mkdir(parents=True, exist_ok=True)

        scaffold_results: Dict[str, Any] = {
            "scale": scale.value,
            "goal": goal,
            "files_created": [],
            "entrypoint": "",
            "tests_entrypoint": "",
            "verified": False,
            "audit_log": []
        }

        # Safe project name token
        slug = re.sub(r'[^a-zA-Z0-9_]', '_', goal.lower().strip())[:25].strip('_') or "project_module"

        if scale == ProjectScale.SMALL:
            # Small-Scale: Single script / CLI utility with embedded tests
            entry_name = f"{slug}.py"
            entry_path = sub_dir / entry_name
            code = self._generate_small_scale_template(slug, goal)
            self.workspace_guard.safe_write(str(entry_path), code, backup=False)
            scaffold_results["files_created"].append(str(entry_path.relative_to(self.workspace_root)))
            scaffold_results["entrypoint"] = str(entry_path)

        elif scale == ProjectScale.MID:
            # Mid-Scale: Modular package with core, models, api/cli, and unit tests
            pkg_dir = sub_dir / slug
            test_dir = sub_dir / "tests"
            pkg_dir.mkdir(parents=True, exist_ok=True)
            test_dir.mkdir(parents=True, exist_ok=True)

            files = self._generate_mid_scale_template(slug, goal)
            for rel_path, content in files.items():
                dest = sub_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                self.workspace_guard.safe_write(str(dest), content, backup=False)
                scaffold_results["files_created"].append(str(dest.relative_to(self.workspace_root)))

            scaffold_results["entrypoint"] = str(pkg_dir / "main.py")
            scaffold_results["tests_entrypoint"] = str(test_dir / f"test_{slug}.py")

        else:
            # Large-Scale: Full enterprise multi-tier architecture
            pkg_dir = sub_dir / slug
            pkg_dir.mkdir(parents=True, exist_ok=True)
            files = self._generate_large_scale_template(slug, goal)
            for rel_path, content in files.items():
                dest = sub_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                self.workspace_guard.safe_write(str(dest), content, backup=False)
                scaffold_results["files_created"].append(str(dest.relative_to(self.workspace_root)))

            scaffold_results["entrypoint"] = str(sub_dir / "run.py")
            scaffold_results["tests_entrypoint"] = str(sub_dir / "tests" / "test_suite.py")

        # Pre-flight syntax validation across all created Python files
        syntax_errors = []
        for f in scaffold_results["files_created"]:
            if f.endswith(".py"):
                full_p = self.workspace_root / f
                try:
                    src = full_p.read_text(encoding="utf-8")
                    ast.parse(src)
                except Exception as e:
                    syntax_errors.append((f, str(e)))

        if syntax_errors:
            scaffold_results["audit_log"].append(f"Pre-flight caught {len(syntax_errors)} syntax errors. Launching self-healing...")
            # Auto-heal syntax errors immediately
            for f, err in syntax_errors:
                self.heal_file_syntax(self.workspace_root / f, err)

        scaffold_results["verified"] = len(syntax_errors) == 0
        return scaffold_results

    # =========================================================================
    # 2. AUTONOMOUS SELF-HEALING ENGINE
    # =========================================================================

    def heal_file_syntax(self, file_path: Path, error_message: str) -> bool:
        """Surgically repairs obvious syntax issues (missing colons, mismatched brackets)."""
        try:
            content = file_path.read_text(encoding="utf-8")
            lines = content.splitlines()

            # Check for line number in error
            lno_m = re.search(r'line\s+(\d+)', error_message)
            if lno_m:
                lno = int(lno_m.group(1)) - 1
                if 0 <= lno < len(lines):
                    target_line = lines[lno]
                    # Common fix: missing colon on def/class/if/elif/else/for/while/try/except/with
                    stripped = target_line.rstrip()
                    if any(stripped.startswith(k) for k in ("def ", "class ", "if ", "elif ", "else", "for ", "while ", "try", "except", "with ")) and not stripped.endswith(":"):
                        lines[lno] = stripped + ":"
                        repaired = "\n".join(lines) + "\n"
                        try:
                            ast.parse(repaired)
                            file_path.write_text(repaired, encoding="utf-8")
                            return True
                        except Exception:
                            pass
            return False
        except Exception:
            return False

    def diagnose_and_heal(
        self,
        traceback_output: str,
        target_script: Optional[str] = None,
        custom_fix_generator: Optional[Callable[[TracebackDiagnostic, str], str]] = None
    ) -> Tuple[bool, Optional[TracebackDiagnostic], str]:
        """
        Diagnoses a runtime/test traceback and applies a surgical atomic repair.
        Returns: (healed_success, diagnostic, explanation_summary)
        """
        diag = TracebackParser.parse(traceback_output, workspace_root=str(self.workspace_root))
        if not diag:
            return False, None, "Could not extract structured traceback frames."

        # Locate target file
        target_file_path: Optional[Path] = None
        if diag.failing_file:
            cand = Path(diag.failing_file)
            if cand.is_file():
                target_file_path = cand
            else:
                ws_cand = self.workspace_root / diag.failing_file
                if ws_cand.is_file():
                    target_file_path = ws_cand

        if not target_file_path and target_script:
            cand = Path(target_script)
            if cand.is_file():
                target_file_path = cand

        if not target_file_path or not target_file_path.is_file():
            return False, diag, f"Could not find offending file on disk for diagnostic: {diag.suggested_fix_summary}"

        try:
            source_code = target_file_path.read_text(encoding="utf-8")
        except Exception as e:
            return False, diag, f"Failed to read file {target_file_path}: {e}"

        # 1. Custom model-based or LLM fix generator if provided
        if custom_fix_generator:
            try:
                new_code = custom_fix_generator(diag, source_code)
                if new_code and new_code.strip() != source_code.strip():
                    # Validate syntax before writing
                    if target_file_path.suffix == ".py":
                        try:
                            ast.parse(new_code)
                        except SyntaxError as syn:
                            return False, diag, f"Synthesized patch contained SyntaxError: {syn}"

                    self.workspace_guard.safe_write(str(target_file_path), new_code, backup=True)
                    return True, diag, f"Applied custom AI repair for {diag.error_type} in {target_file_path.name}"
            except Exception as e:
                pass

        # 2. Executive Deterministic Heuristic Repairs
        healed_code, explanation = self._apply_heuristic_repairs(diag, source_code)
        if healed_code and healed_code != source_code:
            # Validate with AST
            if target_file_path.suffix == ".py":
                try:
                    ast.parse(healed_code)
                except SyntaxError as syn:
                    return False, diag, f"Heuristic patch produced invalid AST: {syn}"

            self.workspace_guard.safe_write(str(target_file_path), healed_code, backup=True)
            return True, diag, explanation

        return False, diag, f"Diagnosis identified {diag.suggested_fix_summary}, but no automated patch converged."

    def _apply_heuristic_repairs(self, diag: TracebackDiagnostic, source: str) -> Tuple[Optional[str], str]:
        """Performs intelligent AST and regex surgical transformations for known defect classes."""
        lines = source.splitlines()

        # CASE A: Missing colon / SyntaxError at line
        if diag.category == ErrorCategory.SYNTAX and diag.line_number:
            idx = diag.line_number - 1
            if 0 <= idx < len(lines):
                line = lines[idx].rstrip()
                if any(line.strip().startswith(kw) for kw in ("def ", "class ", "if ", "elif ", "else", "for ", "while ", "try", "except", "with ")) and not line.endswith(":"):
                    lines[idx] = line + ":"
                    return "\n".join(lines) + "\n", f"Appended missing ':' to line {diag.line_number}"

        # CASE B: NameError - missing import or variable name
        if diag.error_type == "NameError":
            m = re.search(r"name\s+['\"](\w+)['\"]\s+is not defined", diag.error_message)
            if m:
                missing_name = m.group(1)
                common_modules = {
                    "os": "import os",
                    "sys": "import sys",
                    "json": "import json",
                    "re": "import re",
                    "time": "import time",
                    "math": "import math",
                    "Path": "from pathlib import Path",
                    "Dict": "from typing import Dict, Any, List, Optional",
                    "List": "from typing import Dict, Any, List, Optional",
                    "Optional": "from typing import Dict, Any, List, Optional",
                    "Any": "from typing import Dict, Any, List, Optional",
                    "datetime": "import datetime",
                    "traceback": "import traceback",
                    "pytest": "import pytest"
                }
                if missing_name in common_modules:
                    imp_stmt = common_modules[missing_name]
                    if imp_stmt not in source:
                        new_source = f"{imp_stmt}\n" + source
                        return new_source, f"Injected missing import '{imp_stmt}' for NameError '{missing_name}'"

        # CASE C: ZeroDivisionError
        if diag.error_type == "ZeroDivisionError" and diag.line_number:
            idx = diag.line_number - 1
            if 0 <= idx < len(lines):
                target_l = lines[idx]
                # Replace division `/ var` with safe division or conditional
                div_m = re.search(r'/\s*([a-zA-Z0-9_.]+)', target_l)
                if div_m:
                    denom = div_m.group(1)
                    safe_expr = f"/ ({denom} if {denom} != 0 else 1e-9)"
                    lines[idx] = target_l.replace(f"/{denom}", safe_expr)
                    return "\n".join(lines) + "\n", f"Guarded denominator '{denom}' against ZeroDivisionError at line {diag.line_number}"

        # CASE D: AttributeError: 'NoneType' object has no attribute 'x'
        if diag.error_type == "AttributeError" and "NoneType" in diag.error_message and diag.line_number:
            idx = diag.line_number - 1
            if 0 <= idx < len(lines):
                target_l = lines[idx]
                attr_m = re.search(r"has no attribute\s+['\"](\w+)['\"]", diag.error_message)
                if attr_m:
                    attr_name = attr_m.group(1)
                    # Safe navigation guard: object.attr -> (obj.attr if obj is not None else None)
                    match_obj = re.search(rf'([a-zA-Z0-9_.]+)\.{attr_name}', target_l)
                    if match_obj:
                        obj_expr = match_obj.group(1)
                        guarded = f"({obj_expr}.{attr_name} if {obj_expr} is not None else None)"
                        lines[idx] = target_l.replace(f"{obj_expr}.{attr_name}", guarded)
                        return "\n".join(lines) + "\n", f"Inserted None-guard for attribute '{attr_name}' at line {diag.line_number}"

        # CASE E: KeyError
        if diag.error_type == "KeyError" and diag.line_number:
            idx = diag.line_number - 1
            if 0 <= idx < len(lines):
                target_l = lines[idx]
                key_m = re.search(r"['\"]?([^'\"]+)['\"]?", diag.error_message)
                if key_m:
                    missing_k = key_m.group(1).strip()
                    # Transform dict[missing_k] to dict.get(missing_k, default)
                    pattern = rf'\[\s*["\']{re.escape(missing_k)}["\']\s*\]'
                    if re.search(pattern, target_l):
                        replacement = f".get('{missing_k}', None)"
                        lines[idx] = re.sub(pattern, replacement, target_l)
                        return "\n".join(lines) + "\n", f"Converted direct dict lookup to safe .get('{missing_k}') at line {diag.line_number}"

        return None, "No heuristic match found."

    # =========================================================================
    # 3. EXECUTIVE AUTONOMOUS HEALING LOOP
    # =========================================================================

    def autonomous_self_healing_loop(
        self,
        command_or_script: str,
        max_iterations: int = 5,
        on_progress: Optional[Callable[[str, int, int], None]] = None,
        custom_fix_generator: Optional[Callable[[TracebackDiagnostic, str], str]] = None
    ) -> HealingResult:
        """
        Executes a script or test suite in a self-healing loop:
        Runs -> Catches failure -> Diagnoses -> Patches -> Re-executes until pass or max iterations.
        """
        python_bin = sys.executable
        venv_py = self.workspace_root / ".venv" / "Scripts" / "python.exe"
        if venv_py.exists():
            python_bin = str(venv_py)

        # Parse command
        if command_or_script.endswith(".py") and not command_or_script.startswith("python"):
            cmd = [python_bin, "-u", command_or_script]
            entry_file = command_or_script
        else:
            cmd = command_or_script.split()
            entry_file = next((arg for arg in cmd if arg.endswith(".py")), "")

        audit_notes: List[str] = []
        diagnostics_resolved: List[TracebackDiagnostic] = []
        modified_files: Set[str] = set()

        for iteration in range(1, max_iterations + 1):
            if on_progress:
                on_progress(f"Execution pass {iteration}/{max_iterations}", iteration, max_iterations)

            # Execute command
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=str(self.workspace_root),
                    capture_output=True,
                    text=True,
                    timeout=45
                )
                output = (proc.stdout or "") + "\n" + (proc.stderr or "")
                exit_code = proc.returncode
            except subprocess.TimeoutExpired:
                audit_notes.append(f"Iteration {iteration}: Subprocess timed out after 45s.")
                return HealingResult(
                    success=False,
                    iterations_used=iteration,
                    diagnostics_resolved=diagnostics_resolved,
                    modified_files=list(modified_files),
                    final_output="Process timed out.",
                    exit_code=-1,
                    audit_notes=audit_notes
                )
            except Exception as e:
                output = f"Execution error: {e}"
                exit_code = 1

            # Check if clean pass
            if exit_code == 0:
                audit_notes.append(f"Iteration {iteration}: Clean exit code 0. Project verified successfully!")
                if on_progress:
                    on_progress(f"Self-Healing Verified: Clean exit code 0!", iteration, max_iterations)
                return HealingResult(
                    success=True,
                    iterations_used=iteration,
                    diagnostics_resolved=diagnostics_resolved,
                    modified_files=list(modified_files),
                    final_output=output,
                    exit_code=0,
                    audit_notes=audit_notes
                )

            # Error occurred -> Intercept and self-heal
            audit_notes.append(f"Iteration {iteration}: Failure detected with exit code {exit_code}.")
            if on_progress:
                on_progress(f"Intercepted error. Diagnosing traceback...", iteration, max_iterations)

            healed, diag, explanation = self.diagnose_and_heal(
                traceback_output=output,
                target_script=entry_file,
                custom_fix_generator=custom_fix_generator
            )

            if diag:
                diagnostics_resolved.append(diag)
                if diag.failing_file:
                    modified_files.add(diag.failing_file)

            if healed:
                audit_notes.append(f"Iteration {iteration} repair applied: {explanation}")
                if on_progress:
                    on_progress(f"Repaired: {explanation}. Re-executing verification...", iteration, max_iterations)
            else:
                audit_notes.append(f"Iteration {iteration}: Could not synthesize converging repair: {explanation}")
                # Break if cannot repair
                break

        # If loop finishes without success
        return HealingResult(
            success=False,
            iterations_used=max_iterations,
            diagnostics_resolved=diagnostics_resolved,
            modified_files=list(modified_files),
            final_output=output,
            exit_code=exit_code,
            audit_notes=audit_notes
        )

    # =========================================================================
    # 4. TEMPLATE GENERATORS FOR SCALED PROJECTS
    # =========================================================================

    def _generate_small_scale_template(self, name: str, goal: str) -> str:
        return f'''"""
{name} — Small-Scale Utility & CLI Tool
Goal: {goal}
Auto-generated by PRUBETH IDE Executive Autonomous Scaffolder.
"""
from __future__ import annotations

import sys
import argparse
import json
from typing import Dict, Any, List


class {name.title().replace("_", "")}Tool:
    """Core executive processor for {name}."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Executes operational flow for: {goal}."""
        if not data:
            return {{"status": "empty", "result": None}}
        
        # Core transform
        transformed = {{k.upper(): v for k, v in data.items() if isinstance(k, str)}}
        return {{
            "status": "success",
            "count": len(data),
            "output": transformed
        }}


def run_self_tests() -> bool:
    """Embedded self-verification test suite."""
    print("[TEST] Running self-verification suite...")
    tool = {name.title().replace("_", "")}Tool()
    
    # Test 1: Empty input
    res1 = tool.process({{}})
    assert res1["status"] == "empty", "Empty input test failed"
    
    # Test 2: Standard payload
    res2 = tool.process({{"key": "value", "id": 101}})
    assert res2["status"] == "success", "Standard payload test failed"
    assert res2["count"] == 2, "Count assertion failed"
    print("[TEST] All self-verification tests PASSED cleanly.")
    return True


def main():
    parser = argparse.ArgumentParser(description="{goal}")
    parser.add_argument("--test", action="store_true", help="Run embedded self-verification tests")
    parser.add_argument("--payload", type=str, default='{{"status": "active"}}', help="Input JSON payload")
    args = parser.parse_args()

    if args.test or len(sys.argv) == 1:
        ok = run_self_tests()
        if not ok:
            sys.exit(1)
        if args.test:
            return

    tool = {name.title().replace("_", "")}Tool()
    try:
        data = json.loads(args.payload)
    except Exception:
        data = {{"raw": args.payload}}

    result = tool.process(data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
'''

    def _generate_mid_scale_template(self, name: str, goal: str) -> Dict[str, str]:
        title = name.title().replace("_", "")
        return {
            f"{name}/__init__.py": f'"""Package {name}"""\n__version__ = "1.0.0"\n',
            f"{name}/models.py": f'''"""Data models for {name}"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

@dataclass
class ItemPayload:
    item_id: str
    name: str
    metadata: Dict[str, Any]
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
''',
            f"{name}/service.py": f'''"""Service layer for {name}"""
from typing import Dict, List, Optional
try:
    from {name}.models import ItemPayload
except ImportError:
    from models import ItemPayload

class {title}Service:
    def __init__(self):
        self._items: Dict[str, ItemPayload] = {{}}

    def add_item(self, item: ItemPayload) -> bool:
        self._items[item.item_id] = item
        return True

    def get_item(self, item_id: str) -> Optional[ItemPayload]:
        return self._items.get(item_id)

    def count(self) -> int:
        return len(self._items)
''',
            f"{name}/main.py": f'''"""CLI / Entrypoint for {name}"""
import sys
from pathlib import Path

# Ensure package and parent directory are on sys.path
_cur = Path(__file__).resolve().parent
if str(_cur) not in sys.path:
    sys.path.insert(0, str(_cur))
if str(_cur.parent) not in sys.path:
    sys.path.insert(0, str(_cur.parent))

try:
    from {name}.models import ItemPayload
    from {name}.service import {title}Service
except ImportError:
    from models import ItemPayload
    from service import {title}Service

def run_application():
    print("Starting {name} service: {goal}")
    srv = {title}Service()
    srv.add_item(ItemPayload(item_id="1", name="Alpha Item", metadata={{"owner": "dev"}}))
    item = srv.get_item("1")
    print(f"Verified item: {{item.name if item else 'None'}}, Total: {{srv.count()}}")
    return srv.count() == 1

if __name__ == "__main__":
    ok = run_application()
    sys.exit(0 if ok else 1)
''',
            f"tests/test_{name}.py": f'''"""Unit test suite for {name}"""
import sys
from pathlib import Path
_cur = Path(__file__).resolve().parent.parent
if str(_cur) not in sys.path:
    sys.path.insert(0, str(_cur))
if str(_cur / "{name}") not in sys.path:
    sys.path.insert(0, str(_cur / "{name}"))

import pytest
try:
    from {name}.models import ItemPayload
    from {name}.service import {title}Service
except ImportError:
    from models import ItemPayload
    from service import {title}Service

def test_{name}_service_operations():
    srv = {title}Service()
    assert srv.count() == 0
    item = ItemPayload(item_id="test-1", name="Test Item", metadata={{"test": True}})
    ok = srv.add_item(item)
    assert ok is True
    assert srv.count() == 1
    retrieved = srv.get_item("test-1")
    assert retrieved is not None
    assert retrieved.name == "Test Item"
    assert retrieved.to_dict()["item_id"] == "test-1"
'''
        }

    def _generate_large_scale_template(self, name: str, goal: str) -> Dict[str, str]:
        title = name.title().replace("_", "")
        return {
            f"config.json": '{\n  "environment": "development",\n  "max_concurrency": 4,\n  "port": 8080\n}',
            f"{name}/__init__.py": f'"""{title} Enterprise Architecture Package"""\n__version__ = "1.0.0"\n',
            f"{name}/config.py": f'''"""Configuration Loader"""
import json
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    @staticmethod
    def load(config_path: str = "config.json") -> Dict[str, Any]:
        p = Path(config_path)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return {{"environment": "default", "max_concurrency": 2}}
''',
            f"{name}/domain.py": f'''"""Domain Entity Definitions"""
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List
import time

@dataclass
class TransactionRecord:
    tx_id: str
    operation: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    status: str = "COMPLETED"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
''',
            f"{name}/repository.py": f'''"""Persistence and Repository Abstraction"""
from typing import Dict, List, Optional
from {name}.domain import TransactionRecord

class TransactionRepository:
    def __init__(self):
        self._storage: Dict[str, TransactionRecord] = {{}}

    def save(self, record: TransactionRecord) -> None:
        self._storage[record.tx_id] = record

    def find_by_id(self, tx_id: str) -> Optional[TransactionRecord]:
        return self._storage.get(tx_id)

    def list_all(self) -> List[TransactionRecord]:
        return list(self._storage.values())
''',
            f"{name}/engine.py": f'''"""Core Enterprise Processing Engine"""
import uuid
from typing import Dict, Any, List
from {name}.domain import TransactionRecord
from {name}.repository import TransactionRepository

class {title}Engine:
    def __init__(self, repo: TransactionRepository):
        self.repo = repo

    def execute_transaction(self, op: str, data: Dict[str, Any]) -> TransactionRecord:
        tx_id = f"tx-{{uuid.uuid4().hex[:8]}}"
        record = TransactionRecord(tx_id=tx_id, operation=op, payload=data)
        self.repo.save(record)
        return record

    def audit_trail(self) -> List[TransactionRecord]:
        return self.repo.list_all()
''',
            f"run.py": f'''"""Enterprise System Entrypoint"""
import sys
from {name}.config import ConfigManager
from {name}.repository import TransactionRepository
from {name}.engine import {title}Engine

def main():
    print("Initializing Enterprise System: {name}")
    config = ConfigManager.load()
    print(f"Loaded config: Environment={{config.get('environment')}}")
    
    repo = TransactionRepository()
    engine = {title}Engine(repo)
    
    tx = engine.execute_transaction("BOOTSTRAP", {{"goal": "{goal}"}})
    print(f"Executed bootstrap transaction: {{tx.tx_id}} status={{tx.status}}")
    records = engine.audit_trail()
    print(f"Total verified transaction audit records: {{len(records)}}")
    return len(records) > 0

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
''',
            f"tests/test_suite.py": f'''"""Enterprise End-to-End Verification Test Suite"""
import pytest
from {name}.config import ConfigManager
from {name}.domain import TransactionRecord
from {name}.repository import TransactionRepository
from {name}.engine import {title}Engine

def test_config_loader():
    cfg = ConfigManager.load()
    assert "environment" in cfg

def test_enterprise_engine_transaction_lifecycle():
    repo = TransactionRepository()
    engine = {title}Engine(repo)
    
    # 1. Execute initial transaction
    tx = engine.execute_transaction("CREATE_RECORD", {{"val": 42}})
    assert tx.tx_id.startswith("tx-")
    assert tx.status == "COMPLETED"
    
    # 2. Verify repository lookup
    retrieved = repo.find_by_id(tx.tx_id)
    assert retrieved is not None
    assert retrieved.operation == "CREATE_RECORD"
    
    # 3. Verify audit trail
    all_records = engine.audit_trail()
    assert len(all_records) == 1
'''
        }
