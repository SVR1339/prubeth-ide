"""
Comprehensive unit and integration test suite for PRUBETH Code-OSS Fork Subsystem.
Validates product.json configuration, Composer engine, Codebase indexer,
Open VSX marketplace client, and Monaco editor bridge.
"""
import os
import json
import pytest
from pathlib import Path

from code_oss.composer.engine import ComposerEngine, FileDiffPlan
from code_oss.context.codebase_indexer import CodebaseIndexer, CodeSymbol
from code_oss.extension_host.open_vsx_client import OpenVsxClient
from code_oss.monaco.bridge import MonacoEditorBridge
from workspace.checkpoints import CheckpointManager
from core.workspace import WorkspaceGuard


def test_code_oss_product_manifest_validity():
    """Validates product.json matches the Code-OSS fork specifications."""
    product_path = Path("code_oss/product.json")
    assert product_path.exists(), "code_oss/product.json must exist"

    data = json.loads(product_path.read_text(encoding="utf-8"))
    assert data["nameShort"] == "PRUBETH"
    assert "Code-OSS" in data["forkOrigin"]
    assert data["forkType"] == "Proprietary Autonomous AI IDE Fork (PORK)"
    assert data["telemetry"]["enableTelemetry"] is False
    assert data["extensionsGallery"]["serviceUrl"] == "https://open-vsx.org/vscode/gallery"
    assert data["aiCapabilities"]["composerEnabled"] is True
    assert data["aiCapabilities"]["defaultLocalModel"] == "redsage-8b:latest"


def test_composer_engine_planning_and_diff(tmp_path):
    """Tests file change planning and unified diff generation in Composer."""
    target_file = tmp_path / "app.py"
    target_file.write_text("def run():\n    return 42\n", encoding="utf-8")

    engine = ComposerEngine(workspace_root=tmp_path)
    plan = engine.plan_file_change("app.py", "def run():\n    return 100\n")

    assert plan.file_path == "app.py"
    assert plan.is_new is False
    assert plan.additions_count >= 1
    assert plan.deletions_count >= 1
    assert "return 100" in plan.diff_unified


def test_composer_parse_xml_and_markdown(tmp_path):
    """Tests parsing multi-file agent response in Composer format."""
    engine = ComposerEngine(workspace_root=tmp_path)
    response_text = """
Here is the multi-file architecture plan:

<composer:file path="src/utils.py">
def helper():
    return True
</composer:file>

<composer:file path="src/main.py">
from src.utils import helper
def main():
    return helper()
</composer:file>
"""
    plans = engine.parse_composer_response(response_text)
    assert len(plans) == 2
    assert plans[0].file_path == "src/utils.py"
    assert plans[1].file_path == "src/main.py"
    assert "def helper" in plans[0].proposed_content


def test_composer_atomic_apply_and_rollback(tmp_path):
    """Tests transactional apply and rollback with CheckpointManager."""
    guard = WorkspaceGuard(tmp_path)
    mgr = CheckpointManager(workspace_guard=guard, storage_dir=tmp_path / ".checkpoints")
    engine = ComposerEngine(workspace_root=tmp_path, checkpoint_manager=mgr)

    engine.plan_file_change("module_a.py", "# version 1\n")
    engine.plan_file_change("module_b.py", "# version 2\n")

    res = engine.apply_all("Composer multi-file apply test")
    assert res["success"] is True
    assert res["file_count"] == 2
    assert (tmp_path / "module_a.py").exists()
    assert (tmp_path / "module_b.py").exists()
    assert "# version 1" in (tmp_path / "module_a.py").read_text(encoding="utf-8")

    # Test rollback
    roll_res = engine.rollback()
    assert roll_res["success"] is True
    assert not (tmp_path / "module_a.py").exists()
    assert not (tmp_path / "module_b.py").exists()


def test_composer_path_traversal_blocking(tmp_path):
    """Verifies Composer prevents path traversal outside the workspace."""
    engine = ComposerEngine(workspace_root=tmp_path)
    with pytest.raises(PermissionError):
        engine.plan_file_change("../../outside.txt", "malicious payload")


def test_codebase_indexer_symbol_extraction(tmp_path):
    """Tests AST symbol extraction from Python files."""
    code = '''
class ModelRouter:
    """Intelligent dynamic model router."""
    def route(self, prompt: str):
        return "gemini-3.8-flash"

def standalone_helper():
    """Helper documentation."""
    pass
'''
    (tmp_path / "router.py").write_text(code, encoding="utf-8")

    indexer = CodebaseIndexer(workspace_root=tmp_path)
    symbol_count = indexer.index_workspace()
    assert symbol_count >= 2

    symbols = indexer.search_symbols("ModelRouter")
    assert len(symbols) == 1
    assert symbols[0].name == "ModelRouter"
    assert symbols[0].symbol_type == "class"
    assert "router.py" in symbols[0].file_path

    # Test building @Codebase context
    context = indexer.build_codebase_context("route model")
    assert "@CODEBASE SYMBOL INDEX" in context
    assert "ModelRouter" in context


def test_open_vsx_client_catalog():
    """Tests Open VSX marketplace search client."""
    client = OpenVsxClient()
    results = client.search_extensions("python", size=5)
    assert len(results) >= 1
    assert any("python" in r["id"].lower() for r in results)


def test_monaco_editor_bridge():
    """Tests Monaco editor HTML host generation."""
    html = MonacoEditorBridge.generate_html(
        initial_code="print('Hello PRUBETH')",
        language="python",
        file_name="script.py"
    )
    assert "monaco-editor" in html
    assert "obsidian-slate" in html
    assert "Hello PRUBETH" in html
    assert "script.py" in html
