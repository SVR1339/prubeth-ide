"""
PRUBETH IDE — PRUBETH Horizon Reusable Skill Protocol (SKILL.md) & Progressive Disclosure
Solves LLM Token Dilution & Budget Exhaustion:
1. On-Demand Discovery: Skills packaged in directories containing a SKILL.md manifest.
2. Progressive Disclosure: The orchestrator keeps ONLY compact skill signatures in memory
   (~50 tokens each). When an agent identifies that a task requires a specific capability,
   it dynamically pulls the full detailed instructions into its active context.
"""
import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set


@dataclass
class SkillSignature:
    """Lightweight skill signature for low-token progressive disclosure."""
    name: str
    description: str
    triggers: List[str] = field(default_factory=list)
    skill_path: str = ""
    estimated_tokens: int = 40

    def to_summary_line(self) -> str:
        triggers_str = f" [triggers: {', '.join(self.triggers)}]" if self.triggers else ""
        return f"- **{self.name}**: {self.description}{triggers_str}"


@dataclass
class SkillManifest:
    """Full parsed SKILL.md manifest including frontmatter and complete instructions."""
    name: str
    description: str
    triggers: List[str] = field(default_factory=list)
    tools_required: List[str] = field(default_factory=list)
    full_instructions: str = ""
    file_path: str = ""
    version: str = "1.0.0"


class SkillsEngine:
    """
    Manages discovery, signature indexing, and on-demand progressive disclosure of skills.
    """

    def __init__(self, workspace_root: Path, extra_search_paths: Optional[List[Path]] = None):
        self.workspace_root = Path(workspace_root).resolve()
        self.search_paths: List[Path] = [
            self.workspace_root / ".skills",
            self.workspace_root / "skills",
            self.workspace_root / "horizon_engine" / "skills",
        ]
        if extra_search_paths:
            self.search_paths.extend([Path(p).resolve() for p in extra_search_paths])

        self.signatures: Dict[str, SkillSignature] = {}
        self._manifest_cache: Dict[str, SkillManifest] = {}
        self.discover_skills()

    def discover_skills(self) -> int:
        """Discovers all SKILL.md files and extracts lightweight signatures."""
        self.signatures.clear()
        self._manifest_cache.clear()

        for base in self.search_paths:
            if not base.exists():
                continue
            for root, _, files in os.walk(base):
                for f in files:
                    if f.lower() == "skill.md":
                        skill_file = Path(root) / f
                        try:
                            manifest = self._parse_skill_file(skill_file)
                            if manifest:
                                sig = SkillSignature(
                                    name=manifest.name,
                                    description=manifest.description,
                                    triggers=manifest.triggers,
                                    skill_path=str(skill_file),
                                    estimated_tokens=len(manifest.description.split()) * 2 + 10
                                )
                                self.signatures[manifest.name] = sig
                                self._manifest_cache[manifest.name] = manifest
                        except Exception:
                            pass

        # Register default builtin skills if none discovered
        if not self.signatures:
            self._register_default_builtin_skills()

        return len(self.signatures)

    def _parse_skill_file(self, file_path: Path) -> Optional[SkillManifest]:
        """Parses YAML frontmatter and Markdown body of a SKILL.md file."""
        text = file_path.read_text(encoding="utf-8", errors="replace")
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)

        name = file_path.parent.name
        description = "Specialized agent capability."
        triggers: List[str] = []
        tools: List[str] = []

        if frontmatter_match:
            fm_text, body = frontmatter_match.group(1), frontmatter_match.group(2)
            for line in fm_text.splitlines():
                line = line.strip()
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip().strip("\"'")
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip().strip("\"'")
                elif line.startswith("triggers:"):
                    raw = line.split(":", 1)[1].strip()
                    triggers = [t.strip().strip("\"'[]") for t in raw.split(",") if t.strip()]
                elif line.startswith("tools:"):
                    raw = line.split(":", 1)[1].strip()
                    tools = [t.strip().strip("\"'[]") for t in raw.split(",") if t.strip()]
        else:
            body = text

        return SkillManifest(
            name=name,
            description=description,
            triggers=triggers,
            tools_required=tools,
            full_instructions=body.strip(),
            file_path=str(file_path)
        )

    def _register_default_builtin_skills(self):
        """Registers built-in PRUBETH Horizon core skills."""
        builtins = [
            SkillManifest(
                name="browser-verification",
                description="Runs headless Chromium to navigate routes, test UI buttons, and verify console errors.",
                triggers=["browser", "frontend", "ui test", "visual", "click", "web page"],
                tools_required=["headless_chrome", "screenshot"],
                full_instructions="Use the browser verifier to start local dev servers, verify routes, click components, and capture screenshots."
            ),
            SkillManifest(
                name="git-worktree-sandbox",
                description="Manages isolated shadow Git worktree branches for non-destructive multi-file execution.",
                triggers=["git", "worktree", "branch", "sandbox", "isolation", "merge"],
                tools_required=["git"],
                full_instructions="Create a shadow worktree, run tasks without modifying working tree, then produce unified diffs."
            ),
            SkillManifest(
                name="database-migration",
                description="Handles safe schema migrations, foreign keys, and rollbacks with verification checks.",
                triggers=["db", "sql", "migration", "schema", "table", "postgres", "sqlite"],
                tools_required=["sql_runner"],
                full_instructions="Draft forward and backward migration scripts, verify against test database, and generate checkpoints."
            ),
            SkillManifest(
                name="swe-bench-issue-resolver",
                description="Solves real-world GitHub issues using iterative repository exploration, diff planning, and regression tests.",
                triggers=["bug", "issue", "patch", "regression", "fix", "swe-bench"],
                tools_required=["ast_indexer", "composer", "pytest"],
                full_instructions="Locate offending functions via AST indexing, plan multi-file diff in Composer, and verify with pytest."
            ),
        ]
        for m in builtins:
            sig = SkillSignature(
                name=m.name,
                description=m.description,
                triggers=m.triggers,
                skill_path="builtin",
                estimated_tokens=30
            )
            self.signatures[m.name] = sig
            self._manifest_cache[m.name] = m

    def get_progressive_disclosure_prompt(self) -> str:
        """
        Returns a low-token summary table of all available skills.
        The agent can see what skills exist without loading thousands of words into context.
        """
        lines = [
            "### AVAILABLE SPECIALIZED SKILLS (Call activate_skill(name) to disclose instructions):"
        ]
        for sig in self.signatures.values():
            lines.append(sig.to_summary_line())
        return "\n".join(lines)

    def match_skills(self, task_prompt: str) -> List[str]:
        """Detects relevant skills based on trigger keywords in the prompt."""
        p_lower = task_prompt.lower()
        matched = []
        for name, sig in self.signatures.items():
            if name.lower() in p_lower:
                matched.append(name)
            elif any(t.lower() in p_lower for t in sig.triggers):
                matched.append(name)
        return matched

    def disclose_skill(self, skill_name: str) -> Optional[str]:
        """
        Dynamically discloses and returns the full instructions for a requested skill.
        Used by the agent when it decides to activate a skill.
        """
        manifest = self._manifest_cache.get(skill_name)
        if not manifest:
            return None
        return (
            f"=== ACTIVATED SKILL: {manifest.name} ===\n"
            f"Description: {manifest.description}\n"
            f"Tools Required: {', '.join(manifest.tools_required)}\n\n"
            f"--- INSTRUCTIONS ---\n"
            f"{manifest.full_instructions}\n"
            f"=== END SKILL: {manifest.name} ==="
        )
