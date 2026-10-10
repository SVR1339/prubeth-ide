"""
SUKHI IDE — Automated Code & Plan Verification Critic Engine
Inspects synthesized code and execution plans against security guardrails,
AST syntax validity, error handling robustness, and test coverage requirements.
"""
import ast
import re
from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from ai.agents.planner import ExecutionPlan, TaskStatus


class ReviewStatus(str, Enum):
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"


@dataclass
class ReviewIssue:
    severity: str  # 'critical', 'warning', 'info'
    category: str  # 'security', 'syntax', 'quality', 'testing'
    message: str
    file_path: Optional[str] = None
    line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "file_path": self.file_path,
            "line": self.line
        }


@dataclass
class ReviewReport:
    status: ReviewStatus
    score: float  # 0.0 to 10.0
    issues: List[ReviewIssue] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "score": round(self.score, 1),
            "summary": self.summary,
            "issues": [i.to_dict() for i in self.issues]
        }


# Regex detectors for critical security and credential leakage
SECRET_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
    (r"ghp_[a-zA-Z0-9]{20,}", "GitHub Personal Access Token"),
    (r"AIza[0-9A-Za-z-_]{35}", "Google API Key"),
    (r"hf_[a-zA-Z0-9]{20,}", "Hugging Face Access Token"),
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{25,}", "Hardcoded Bearer Token"),
]

DANGEROUS_CALLS = {
    "eval": "Dynamic code evaluation via eval() poses severe code injection risks.",
    "exec": "Dynamic code execution via exec() poses severe arbitrary code execution risks.",
    "__import__": "Direct reflection call via __import__() violates sandbox boundaries."
}


class AgentCritic:
    """Automated reviewer providing security and quality gating for subagent outputs."""

    def __init__(self, strict_security: bool = True):
        self.strict_security = strict_security

    def analyze_code(self, code: str, file_path: str = "") -> ReviewReport:
        """Inspects source code for syntax errors, security flaws, and code smells."""
        issues: List[ReviewIssue] = []
        score = 10.0

        # 1. Secret leakage detection
        for pattern, label in SECRET_PATTERNS:
            match = re.search(pattern, code)
            if match:
                issues.append(ReviewIssue(
                    severity="critical",
                    category="security",
                    message=f"Detected hardcoded secret: {label}. Secrets must be sourced from environment or CredentialStore.",
                    file_path=file_path
                ))
                score -= 4.0

        # 2. Path traversal detection
        if "../" in code or "..\\" in code:
            issues.append(ReviewIssue(
                severity="warning",
                category="security",
                message="Relative path traversal ('../') detected. Ensure paths are resolved via WorkspaceGuard.",
                file_path=file_path
            ))
            score -= 1.5

        # 3. Python AST analysis (if Python file or syntax recognizable)
        is_python = file_path.endswith(".py") or ("def " in code or "class " in code or "import " in code)
        if is_python:
            try:
                tree = ast.parse(code)
                # AST inspection visitor
                for node in ast.walk(tree):
                    # Check for dangerous calls
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_CALLS:
                            issues.append(ReviewIssue(
                                severity="critical",
                                category="security",
                                message=DANGEROUS_CALLS[node.func.id],
                                file_path=file_path,
                                line=node.lineno
                            ))
                            score -= 3.5

                    # Check for subprocess shell=True
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Attribute) and node.func.attr in ("run", "Popen", "call"):
                            for kw in node.keywords:
                                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                    issues.append(ReviewIssue(
                                        severity="critical",
                                        category="security",
                                        message="subprocess called with shell=True creates command injection risk.",
                                        file_path=file_path,
                                        line=node.lineno
                                    ))
                                    score -= 3.0

                    # Check for bare except:
                    if isinstance(node, ast.ExceptHandler) and node.type is None:
                        issues.append(ReviewIssue(
                            severity="warning",
                            category="quality",
                            message="Bare 'except:' handler silences unexpected system exceptions.",
                            file_path=file_path,
                            line=node.lineno
                        ))
                        score -= 1.0

            except SyntaxError as syn_err:
                issues.append(ReviewIssue(
                    severity="critical",
                    category="syntax",
                    message=f"SyntaxError: {syn_err.msg} at line {syn_err.lineno}:{syn_err.offset}",
                    file_path=file_path,
                    line=syn_err.lineno
                ))
                score -= 5.0

        score = max(0.0, min(10.0, score))

        # Determine approval status
        has_critical = any(i.severity == "critical" for i in issues)
        if has_critical or score < 5.0:
            status = ReviewStatus.REJECTED
            summary = f"Rejected with {len(issues)} issue(s). Critical security or syntax defects found."
        elif len(issues) > 0 or score < 8.0:
            status = ReviewStatus.CHANGES_REQUESTED
            summary = f"Changes requested with {len(issues)} issue(s). Review warnings and suggestions."
        else:
            status = ReviewStatus.APPROVED
            summary = "Approved cleanly. Zero critical defects detected."

        return ReviewReport(
            status=status,
            score=score,
            issues=issues,
            summary=summary
        )

    def analyze_plan(self, plan: ExecutionPlan) -> ReviewReport:
        """Inspects an execution plan for completeness, testability, and role coverage."""
        issues: List[ReviewIssue] = []
        score = 10.0

        if len(plan.steps) == 0:
            return ReviewReport(
                status=ReviewStatus.REJECTED,
                score=0.0,
                issues=[ReviewIssue(severity="critical", category="planning", message="Plan contains no steps.")],
                summary="Plan rejected: empty step list."
            )

        has_testing = any(s.assigned_role == "tester" or "test" in s.title.lower() for s in plan.steps.values())
        if not has_testing:
            issues.append(ReviewIssue(
                severity="warning",
                category="testing",
                message="Plan lacks automated testing or deliverable verification step."
            ))
            score -= 2.0

        roles_used = {s.assigned_role for s in plan.steps.values()}
        if len(roles_used) < 2 and len(plan.steps) > 3:
            issues.append(ReviewIssue(
                severity="info",
                category="quality",
                message="Consider distributing tasks across specialized roles (architect, coder, critic, tester)."
            ))
            score -= 0.5

        score = max(0.0, min(10.0, score))
        status = ReviewStatus.APPROVED if score >= 8.0 else ReviewStatus.CHANGES_REQUESTED

        return ReviewReport(
            status=status,
            score=score,
            issues=issues,
            summary=f"Plan evaluated: {len(plan.steps)} step(s). Status: {status.value}"
        )
