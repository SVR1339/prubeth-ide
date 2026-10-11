"""
PRUBETH IDE — PRUBETH Horizon SWE-Bench Style Evaluation Harness
Evidence-based acceptance testing for autonomous coding agents (PRINCE2 Acceptance Stage).

Research Foundation:
  - SWE-bench (Jimenez et al., 2023): Evaluating autonomous agents by measuring whether
    their edits make hidden tests pass is the gold-standard for coding agent evaluation.
  - PRINCE2 Acceptance Stage: "Did the deliverable meet the acceptance criteria?" must be
    answered with hard evidence (test pass/fail counts, coverage deltas), not agent self-report.

Architecture:
  1. TestRunnerConfig:   Configures test collection (pytest, unittest, pattern, timeout)
  2. TestCaseResult:     Per-test structured result (id, status, stdout, traceback)
  3. CoverageReport:     Per-file coverage metrics (lines_covered, lines_total, pct)
  4. EvalReport:         Full evaluation report: summary, per-test results, coverage delta
  5. TestHarnessRunner:  Orchestrates test execution in a sandboxed subprocess
"""
import subprocess
import sys
import json
import time
import tempfile
import shutil
import re
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"
    XFAILED = "xfailed"    # Expected failure — acceptable


@dataclass
class TestCaseResult:
    """Per-test case structured result from the harness."""
    test_id: str
    status: TestStatus
    duration_ms: float = 0.0
    stdout: str = ""
    stderr: str = ""
    traceback: Optional[str] = None
    file_path: Optional[str] = None
    line_number: Optional[int] = None

    @property
    def passed(self) -> bool:
        return self.status in (TestStatus.PASSED, TestStatus.XFAILED)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["passed"] = self.passed
        return d


@dataclass
class CoverageReport:
    """Per-file coverage metrics from a coverage.py run."""
    file_path: str
    lines_covered: int
    lines_total: int
    missing_lines: List[int] = field(default_factory=list)
    coverage_pct: float = 0.0

    def __post_init__(self):
        if self.lines_total > 0:
            self.coverage_pct = round(self.lines_covered / self.lines_total * 100, 1)


@dataclass
class EvalReport:
    """
    Full evaluation report for the PRINCE2 Acceptance Stage.
    Contains hard evidence: pass/fail counts, coverage delta, and per-test details.
    """
    run_id: str
    timestamp: float = field(default_factory=time.time)
    test_suite: str = "pytest"
    total_tests: int = 0
    passed_count: int = 0
    failed_count: int = 0
    error_count: int = 0
    skipped_count: int = 0
    duration_seconds: float = 0.0
    test_results: List[TestCaseResult] = field(default_factory=list)
    coverage: Dict[str, CoverageReport] = field(default_factory=dict)
    coverage_total_pct: float = 0.0
    overall_passed: bool = False
    exit_code: int = -1
    raw_output: str = ""

    @property
    def pass_rate(self) -> float:
        if self.total_tests == 0:
            return 0.0
        return round(self.passed_count / self.total_tests * 100, 1)

    def to_summary(self) -> str:
        """One-line summary for artifact/stage gate reporting."""
        icon = "✅" if self.overall_passed else "❌"
        return (
            f"{icon} EvalReport[{self.run_id}] "
            f"{self.passed_count}/{self.total_tests} passed ({self.pass_rate}%) "
            f"in {self.duration_seconds:.1f}s"
        )

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "test_suite": self.test_suite,
            "total_tests": self.total_tests,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "error_count": self.error_count,
            "skipped_count": self.skipped_count,
            "duration_seconds": self.duration_seconds,
            "overall_passed": self.overall_passed,
            "pass_rate": self.pass_rate,
            "exit_code": self.exit_code,
            "test_results": [r.to_dict() for r in self.test_results],
            "coverage_total_pct": self.coverage_total_pct,
        }
        return d


# ---------------------------------------------------------------------------
# Pytest JSON Output Parser
# ---------------------------------------------------------------------------

class PytestOutputParser:
    """Parses pytest JSON report output into structured TestCaseResult objects."""

    @staticmethod
    def parse_json_report(json_data: Dict[str, Any]) -> Tuple[List[TestCaseResult], Dict[str, Any]]:
        """Parses a pytest --json-report output dict into results."""
        results: List[TestCaseResult] = []
        summary = json_data.get("summary", {})

        for test in json_data.get("tests", []):
            node_id = test.get("nodeid", "unknown")
            outcome = test.get("outcome", "error")
            duration_ms = test.get("duration", 0) * 1000

            # Map pytest outcomes
            status_map = {
                "passed": TestStatus.PASSED,
                "failed": TestStatus.FAILED,
                "error": TestStatus.ERROR,
                "skipped": TestStatus.SKIPPED,
                "xfailed": TestStatus.XFAILED
            }
            status = status_map.get(outcome, TestStatus.ERROR)

            # Extract stdout and traceback
            call_phase = test.get("call", {})
            stdout = (call_phase.get("stdout") or "").strip()
            stderr = (call_phase.get("stderr") or "").strip()
            crash = call_phase.get("crash", {})
            traceback = None
            if crash:
                traceback = crash.get("message", "")

            result = TestCaseResult(
                test_id=node_id,
                status=status,
                duration_ms=duration_ms,
                stdout=stdout[:1000],    # Truncate large outputs
                stderr=stderr[:500],
                traceback=traceback
            )
            results.append(result)

        return results, summary

    @staticmethod
    def parse_stdout_fallback(stdout: str) -> List[TestCaseResult]:
        """
        Fallback parser for pytest stdout output when JSON report is not available.
        Extracts PASSED/FAILED/ERROR lines from the pytest verbose output.
        """
        results: List[TestCaseResult] = []
        pattern = re.compile(r'^(.*?)\s+(PASSED|FAILED|ERROR|SKIPPED)\s*(?:\[.*\])?$')
        for line in stdout.splitlines():
            match = pattern.match(line.strip())
            if match:
                test_id = match.group(1).strip()
                outcome = match.group(2).lower()
                status_map = {
                    "passed": TestStatus.PASSED,
                    "failed": TestStatus.FAILED,
                    "error": TestStatus.ERROR,
                    "skipped": TestStatus.SKIPPED
                }
                results.append(TestCaseResult(
                    test_id=test_id,
                    status=status_map.get(outcome, TestStatus.ERROR)
                ))
        return results


# ---------------------------------------------------------------------------
# Test Harness Runner
# ---------------------------------------------------------------------------

@dataclass
class TestRunnerConfig:
    """Configuration for a test harness run."""
    test_paths: List[str] = field(default_factory=lambda: ["tests/"])
    python_executable: str = sys.executable
    timeout_seconds: float = 120.0
    collect_coverage: bool = False
    coverage_source_dirs: List[str] = field(default_factory=lambda: ["horizon_engine/", "core/", "ai/"])
    extra_pytest_args: List[str] = field(default_factory=list)
    working_dir: Optional[str] = None
    environment_vars: Dict[str, str] = field(default_factory=dict)


class TestHarnessRunner:
    """
    Orchestrates test execution in a subprocess with structured output parsing.
    Used by the PRINCE2 Acceptance Stage to validate that agent deliverables pass tests.
    """

    def __init__(self, config: Optional[TestRunnerConfig] = None):
        self.config = config or TestRunnerConfig()
        self._run_counter = 0

    def run(self) -> EvalReport:
        """Executes the test suite and returns a structured EvalReport."""
        self._run_counter += 1
        run_id = f"eval-{self._run_counter:04d}"
        start_time = time.time()

        # Build pytest command with JSON report
        report_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        report_path = report_file.name
        report_file.close()

        cmd = [
            self.config.python_executable, "-m", "pytest",
            "--tb=short",
            "-v",
            f"--json-report={report_path}",
            "--json-report-omit=keywords",
        ]

        if self.config.collect_coverage:
            source_str = ",".join(self.config.coverage_source_dirs)
            cmd += ["--cov=" + source_str, "--cov-report=json"]

        cmd += self.config.extra_pytest_args
        cmd += self.config.test_paths

        env = os.environ.copy()
        env.update(self.config.environment_vars)
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        report = EvalReport(run_id=run_id)
        raw_output = ""
        exit_code = -1

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout_seconds,
                cwd=self.config.working_dir,
                env=env
            )
            raw_output = proc.stdout + proc.stderr
            exit_code = proc.returncode

        except subprocess.TimeoutExpired as e:
            report.raw_output = f"TIMEOUT after {self.config.timeout_seconds}s"
            report.exit_code = -9
            report.overall_passed = False
            report.duration_seconds = self.config.timeout_seconds
            return report
        except FileNotFoundError as e:
            report.raw_output = f"Command not found: {e}"
            report.exit_code = -2
            report.overall_passed = False
            return report

        duration = time.time() - start_time

        # Parse JSON report
        test_results: List[TestCaseResult] = []
        summary_data: Dict[str, Any] = {}
        try:
            with open(report_path, "r", encoding="utf-8", errors="replace") as f:
                json_data = json.load(f)
            test_results, summary_data = PytestOutputParser.parse_json_report(json_data)
        except Exception:
            # Fallback to stdout parsing
            test_results = PytestOutputParser.parse_stdout_fallback(raw_output)
        finally:
            try:
                os.unlink(report_path)
            except Exception:
                pass

        passed = sum(1 for r in test_results if r.passed)
        failed = sum(1 for r in test_results if r.status == TestStatus.FAILED)
        errors = sum(1 for r in test_results if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in test_results if r.status == TestStatus.SKIPPED)

        report.test_results = test_results
        report.total_tests = len(test_results)
        report.passed_count = passed
        report.failed_count = failed
        report.error_count = errors
        report.skipped_count = skipped
        report.duration_seconds = round(duration, 3)
        report.exit_code = exit_code
        report.raw_output = raw_output[:4000]  # Truncate for storage
        report.overall_passed = (exit_code == 0 and failed == 0 and errors == 0)

        return report

    def run_specific_test(self, test_id: str) -> EvalReport:
        """Runs a single named test (by pytest node ID) and returns its EvalReport."""
        old_paths = self.config.test_paths
        self.config.test_paths = [test_id]
        try:
            return self.run()
        finally:
            self.config.test_paths = old_paths

    def collect_tests(self) -> List[str]:
        """Returns a list of all collectible test IDs without running them."""
        cmd = [
            self.config.python_executable, "-m", "pytest",
            "--collect-only", "-q", "--no-header"
        ] + self.config.test_paths

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30.0,
                cwd=self.config.working_dir
            )
            test_ids = []
            for line in proc.stdout.splitlines():
                line = line.strip()
                if "::" in line and not line.startswith("=") and not line.startswith("<"):
                    test_ids.append(line)
            return test_ids
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Coverage Delta Calculator
# ---------------------------------------------------------------------------

class CoverageCollector:
    """
    Collects and compares line coverage between a baseline and post-edit test run.
    Used to measure the coverage impact of agent-generated code changes.
    """

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir

    def collect_coverage(self, source_dirs: List[str],
                         test_paths: List[str],
                         python_executable: str = sys.executable) -> Optional[Dict[str, CoverageReport]]:
        """
        Runs pytest with coverage and returns per-file CoverageReport objects.
        Returns None if coverage collection failed.
        """
        cov_json_path = tempfile.mktemp(suffix=".coverage.json")
        source_str = ",".join(source_dirs)

        cmd = [
            python_executable, "-m", "pytest",
            "--tb=no", "-q",
            f"--cov={source_str}",
            "--cov-report=json",
            f"--cov-report=json:{cov_json_path}",
            "--no-header"
        ] + test_paths

        try:
            subprocess.run(cmd, capture_output=True, timeout=120.0, cwd=self.working_dir)
            if not Path(cov_json_path).exists():
                return None
            with open(cov_json_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None
        finally:
            try:
                os.unlink(cov_json_path)
            except Exception:
                pass

        reports: Dict[str, CoverageReport] = {}
        for file_path, file_data in data.get("files", {}).items():
            executed = file_data.get("executed_lines", [])
            missing = file_data.get("missing_lines", [])
            total = len(executed) + len(missing)
            reports[file_path] = CoverageReport(
                file_path=file_path,
                lines_covered=len(executed),
                lines_total=total,
                missing_lines=missing
            )
        return reports

    def compute_coverage_delta(self,
                               baseline: Dict[str, CoverageReport],
                               after: Dict[str, CoverageReport]) -> Dict[str, float]:
        """
        Computes per-file coverage delta (after_pct - baseline_pct).
        Returns a dict of file_path → delta_pct.
        """
        deltas: Dict[str, float] = {}
        all_files = set(baseline.keys()) | set(after.keys())
        for f in all_files:
            base_pct = baseline.get(f, CoverageReport(f, 0, 0)).coverage_pct
            after_pct = after.get(f, CoverageReport(f, 0, 0)).coverage_pct
            deltas[f] = round(after_pct - base_pct, 1)
        return deltas
