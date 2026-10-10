"""
Unit and Integration Tests for Source Control Subsystem (GitService & GitSidebarWidget)
"""
import os
import shutil
import tempfile
import subprocess
from pathlib import Path
import pytest
from PyQt5.QtWidgets import QApplication
from source_control.git_service import GitService, GitStatus
from ui.git_sidebar import GitSidebarWidget


@pytest.fixture(scope="session")
def qapp():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def temp_git_repo():
    tmp_dir = tempfile.mkdtemp(prefix="test_sukhi_git_")
    repo_path = Path(tmp_dir)

    # Initialize git repo with config
    subprocess.run(["git", "init"], cwd=str(repo_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Sukhi Tester"], cwd=str(repo_path), check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "tester@sukhi.ide"], cwd=str(repo_path), check=True, capture_output=True)

    service = GitService(repo_path)
    yield repo_path, service
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_git_repo_detection(temp_git_repo):
    repo_path, service = temp_git_repo
    assert service.is_git_repo() is True

    # Non-repo folder
    non_repo = repo_path / "sub_non_repo"
    non_repo.mkdir()
    non_service = GitService(Path(tempfile.gettempdir()) / "completely_random_folder_12345")
    assert non_service.is_git_repo() is False


def test_git_status_untracked_and_staging(temp_git_repo):
    repo_path, service = temp_git_repo

    # Create initial file
    f1 = repo_path / "hello.py"
    f1.write_text("print('hello')\n", encoding="utf-8")

    st = service.get_status()
    assert st.is_repo is True
    assert "hello.py" in st.untracked
    assert len(st.staged) == 0

    # Stage file
    ok = service.stage_file("hello.py")
    assert ok is True

    st_after = service.get_status()
    assert len(st_after.staged) == 1
    assert st_after.staged[0].file_path == "hello.py"
    assert "hello.py" not in st_after.untracked


def test_git_commit_and_log(temp_git_repo):
    repo_path, service = temp_git_repo
    f = repo_path / "version.txt"
    f.write_text("v1.0.0\n", encoding="utf-8")

    service.stage_all()
    res = service.commit("Initial commit test")
    assert res["success"] is True

    st = service.get_status()
    assert st.is_clean is True

    logs = service.get_log(max_count=5)
    assert len(logs) == 1
    assert logs[0]["message"] == "Initial commit test"
    assert logs[0]["author"] == "Sukhi Tester"


def test_git_sidebar_ui_widget(qapp, temp_git_repo):
    repo_path, service = temp_git_repo

    f = repo_path / "test_ui.txt"
    f.write_text("sample content\n", encoding="utf-8")

    widget = GitSidebarWidget(repo_path)
    assert widget is not None
    assert widget.tree.topLevelItemCount() > 0

    # Test commit message handling
    widget.commit_msg_input.setPlainText("Test via sidebar")
    assert widget.commit_msg_input.toPlainText() == "Test via sidebar"
    widget.close()
