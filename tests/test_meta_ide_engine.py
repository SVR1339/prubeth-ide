"""
PRUBETH IDE — Meta-IDE Engine Verification Test Suite
=====================================================
Automated tests for MetaIdeEngine ensuring 100% intellectual property
safe harbor compliance, trademark de-escalation, Open VSX verification,
and clean-room scaffolding across all child IDE archetypes.
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
import pytest

from core.meta_ide_engine import (
    MetaIdeEngine,
    ChildIdeArchetype,
    LicenseTier,
    ChildIdeManifest,
    ScaffoldingResult,
)


@pytest.fixture
def temp_workspace():
    tmp_dir = tempfile.mkdtemp(prefix="prubeth_meta_ide_test_")
    yield Path(tmp_dir)
    shutil.rmtree(tmp_dir, ignore_errors=True)


def test_sanitize_trademark_strings():
    engine = MetaIdeEngine()
    dirty_text = "This is a custom build of Visual Studio Code and VSCode with GitHub Copilot integration."
    clean_text, mod_count = engine.sanitize_trademark_strings(dirty_text, "PRUBETH Studio")

    assert mod_count >= 3
    assert "Visual Studio Code" not in clean_text
    assert "VSCode" not in clean_text
    assert "GitHub Copilot" not in clean_text
    assert "PRUBETH Studio" in clean_text


def test_verify_clean_room_compliance_valid():
    engine = MetaIdeEngine()
    manifest = ChildIdeManifest(
        name="AegisIDE",
        display_title="Aegis IDE Autonomous Studio",
        version="1.0.0",
        archetype=ChildIdeArchetype.ELECTRON_WEB,
        license=LicenseTier.DUAL_MIT_APACHE,
        author="Dev Team",
        repository_url="https://github.com/aegis/ide",
        extensions_gallery_url="https://open-vsx.org/vscode/gallery",
        telemetry_opt_out=True,
    )
    compliance = engine.verify_clean_room_compliance(manifest)
    assert all(compliance.values())
    assert compliance["marketplace_is_neutral_open_vsx"] is True
    assert compliance["telemetry_opt_out_enforced"] is True
    assert compliance["license_is_permissive_or_lgpl"] is True
    assert compliance["trademark_clean"] is True
    assert compliance["open_protocols_enabled"] is True


def test_verify_clean_room_compliance_rejections():
    engine = MetaIdeEngine()

    # 1. Rejection on Microsoft Proprietary Marketplace
    bad_manifest_market = ChildIdeManifest(
        name="BadMarketIDE",
        display_title="Bad Market Studio",
        version="0.1.0",
        archetype=ChildIdeArchetype.ELECTRON_WEB,
        license=LicenseTier.MIT,
        author="Dev",
        repository_url="https://example.com",
        extensions_gallery_url="https://marketplace.visualstudio.com/_apis/public/gallery",
    )
    res1 = engine.verify_clean_room_compliance(bad_manifest_market)
    assert res1["marketplace_is_neutral_open_vsx"] is False

    # 2. Rejection on Trademark Contamination
    bad_manifest_tm = ChildIdeManifest(
        name="My-VSCode-Clone",
        display_title="My VSCode Fork",
        version="0.1.0",
        archetype=ChildIdeArchetype.ELECTRON_WEB,
        license=LicenseTier.MIT,
        author="Dev",
        repository_url="https://example.com",
    )
    res2 = engine.verify_clean_room_compliance(bad_manifest_tm)
    assert res2["trademark_clean"] is False

    # 3. Rejection on Telemetry Tracking Enabled
    bad_manifest_telem = ChildIdeManifest(
        name="TrackingIDE",
        display_title="Tracking Studio",
        version="0.1.0",
        archetype=ChildIdeArchetype.ELECTRON_WEB,
        license=LicenseTier.MIT,
        author="Dev",
        repository_url="https://example.com",
        telemetry_opt_out=False,
    )
    res3 = engine.verify_clean_room_compliance(bad_manifest_telem)
    assert res3["telemetry_opt_out_enforced"] is False


def test_scaffold_electron_web_archetype(temp_workspace):
    engine = MetaIdeEngine(workspace_root=temp_workspace)
    manifest = ChildIdeManifest(
        name="QuantumCode",
        display_title="Quantum Code Studio",
        version="2.0.0",
        archetype=ChildIdeArchetype.ELECTRON_WEB,
        license=LicenseTier.MIT,
        author="Quantum Team",
        repository_url="https://github.com/quantum/studio",
    )

    result = engine.scaffold_child_ide("quantum_ide", manifest)
    assert result.success is True
    assert result.error is None
    assert (temp_workspace / "quantum_ide" / "product.json").exists()
    assert (temp_workspace / "quantum_ide" / "package.json").exists()
    assert (temp_workspace / "quantum_ide" / "main.js").exists()
    assert (temp_workspace / "quantum_ide" / "index.html").exists()
    assert (temp_workspace / "quantum_ide" / "LICENSE").exists()
    assert (temp_workspace / "quantum_ide" / "README.md").exists()

    # Verify Open VSX enforcement in product.json
    prod_data = json.loads((temp_workspace / "quantum_ide" / "product.json").read_text(encoding="utf-8"))
    assert "open-vsx.org" in prod_data["extensionsGallery"]["serviceUrl"]
    assert prod_data["telemetry"]["enableTelemetry"] is False
    assert prod_data["telemetry"]["optOutByDefault"] is True


def test_scaffold_rust_tauri_archetype(temp_workspace):
    engine = MetaIdeEngine(workspace_root=temp_workspace)
    manifest = ChildIdeManifest(
        name="TauriCode",
        display_title="Tauri Native IDE",
        version="0.5.0",
        archetype=ChildIdeArchetype.RUST_TAURI,
        license=LicenseTier.DUAL_MIT_APACHE,
        author="Rustacean",
        repository_url="https://github.com/tauri/native-ide",
    )

    result = engine.scaffold_child_ide("tauri_ide", manifest)
    assert result.success is True
    assert (temp_workspace / "tauri_ide" / "Cargo.toml").exists()
    assert (temp_workspace / "tauri_ide" / "src" / "main.rs").exists()
    cargo_content = (temp_workspace / "tauri_ide" / "Cargo.toml").read_text(encoding="utf-8")
    assert 'tauri = { version = "2.0"' in cargo_content


def test_scaffold_qt_pyside_archetype(temp_workspace):
    engine = MetaIdeEngine(workspace_root=temp_workspace)
    manifest = ChildIdeManifest(
        name="PyStudio",
        display_title="PyStudio IDE",
        version="1.1.0",
        archetype=ChildIdeArchetype.QT_PYSIDE,
        license=LicenseTier.LGPL_V3,
        author="Pythonistas",
        repository_url="https://github.com/pythonistas/pystudio",
    )

    result = engine.scaffold_child_ide("pystudio", manifest)
    assert result.success is True
    assert (temp_workspace / "pystudio" / "app.py").exists()
    app_code = (temp_workspace / "pystudio" / "app.py").read_text(encoding="utf-8")
    assert "PySide6" in app_code or "PyQt5" in app_code
    assert "PyStudioStudio(QMainWindow)" in app_code


def test_scaffold_headless_agent_archetype(temp_workspace):
    engine = MetaIdeEngine(workspace_root=temp_workspace)
    manifest = ChildIdeManifest(
        name="AgentX",
        display_title="AgentX Autonomous Loop",
        version="3.0.0",
        archetype=ChildIdeArchetype.HEADLESS_AGENT,
        license=LicenseTier.APACHE_2_0,
        author="Agentic Labs",
        repository_url="https://github.com/agentx/loop",
    )

    result = engine.scaffold_child_ide("agentx", manifest)
    assert result.success is True
    assert (temp_workspace / "agentx" / "agent_studio.py").exists()


def test_scaffold_dry_run(temp_workspace):
    engine = MetaIdeEngine(workspace_root=temp_workspace)
    manifest = ChildIdeManifest(
        name="DryRunIDE",
        display_title="Dry Run Studio",
        version="1.0.0",
        archetype=ChildIdeArchetype.ELECTRON_WEB,
        license=LicenseTier.MIT,
        author="Tester",
        repository_url="https://example.com",
    )

    result = engine.scaffold_child_ide("dry_run_target", manifest, dry_run=True)
    assert result.success is True
    assert not (temp_workspace / "dry_run_target").exists()


def test_scaffold_clean_room_failure_blocks_generation(temp_workspace):
    engine = MetaIdeEngine(workspace_root=temp_workspace)
    bad_manifest = ChildIdeManifest(
        name="VSCode-Contaminated",
        display_title="VSCode Pirated",
        version="1.0.0",
        archetype=ChildIdeArchetype.ELECTRON_WEB,
        license=LicenseTier.MIT,
        author="Bad Actor",
        repository_url="https://example.com",
        extensions_gallery_url="https://marketplace.visualstudio.com/_apis/public/gallery",
    )

    result = engine.scaffold_child_ide("bad_ide", bad_manifest)
    assert result.success is False
    assert result.error is not None
    assert "Clean-Room Compliance Verification Failed" in result.error
    assert not (temp_workspace / "bad_ide").exists()
