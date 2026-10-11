"""PRUBETH IDE - Terminal & Subprocess Lifecycle Chaos Tests
==========================================================
Exercises child process execution, nonzero exit codes, timeout enforcement,
credential stripping from child environments, and leak-free process termination.
"""

import os
import sys
import pytest
from tests.reliability.helpers.crash_harness import DisposableWorkspace, timed_operation
from security_research.isolated_lab_manager import (
    IsolatedLabManager,
    NetworkIsolationMode,
    ResourceQuota,
)


def test_subprocess_nonzero_exit_code_handling():
    """Child processes exiting with nonzero codes must report the code accurately."""
    with DisposableWorkspace() as ws_path:
        lab_mgr = IsolatedLabManager(base_lab_dir=str(ws_path))
        session_id = "test_subproc_nonzero"
        lab_mgr.create_session(session_id, isolation_mode=NetworkIsolationMode.HOST_ONLY)

        # Run script that exits with code 42
        python_exe = sys.executable
        report = lab_mgr.execute_target(
            session_id,
            [python_exe, "-c", "import sys; sys.exit(42)"],
        )

        assert report.exit_code == 42
        assert not report.timed_out
        lab_mgr.destroy_session(session_id)


def test_subprocess_timeout_enforcement():
    """Child processes hanging or looping must be terminated by the quota timeout."""
    with DisposableWorkspace() as ws_path:
        lab_mgr = IsolatedLabManager(base_lab_dir=str(ws_path))
        session_id = "test_subproc_timeout"
        # 1-second timeout quota
        quota = ResourceQuota(timeout_seconds=1)
        lab_mgr.create_session(session_id, quota=quota)

        python_exe = sys.executable
        # Infinite sleep script
        with timed_operation(3.0):
            report = lab_mgr.execute_target(
                session_id,
                [python_exe, "-c", "import time; time.sleep(10)"],
            )

        assert report.timed_out is True
        lab_mgr.destroy_session(session_id)


def test_subprocess_credential_stripping():
    """Sensitive environment variables must be stripped before spawning child processes."""
    with DisposableWorkspace() as ws_path:
        lab_mgr = IsolatedLabManager(base_lab_dir=str(ws_path))
        session_id = "test_subproc_credentials"
        lab_mgr.create_session(session_id)

        # Set fake sensitive keys in parent process
        os.environ["OPENAI_API_KEY"] = "sk-fake-secret-token"
        os.environ["AWS_SECRET_ACCESS_KEY"] = "fake-aws-key"

        python_exe = sys.executable
        # Child script inspects whether sensitive variables are present
        inspect_script = (
            "import os, sys\n"
            "has_key = 'OPENAI_API_KEY' in os.environ or 'AWS_SECRET_ACCESS_KEY' in os.environ\n"
            "sys.exit(1 if has_key else 0)\n"
        )

        try:
            report = lab_mgr.execute_target(
                session_id,
                [python_exe, "-c", inspect_script],
            )
            assert report.exit_code == 0  # 0 indicates variables were stripped
        finally:
            os.environ.pop("OPENAI_API_KEY", None)
            os.environ.pop("AWS_SECRET_ACCESS_KEY", None)
            lab_mgr.destroy_session(session_id)
