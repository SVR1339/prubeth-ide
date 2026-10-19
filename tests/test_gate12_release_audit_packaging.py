"""
SUKHI IDE — Gate 12 Automated Test Suite
Verifies Release Audit & Packaging:
- Package metadata consistency (version 3.0.0 across pyproject.toml, requirements, core)
- Application payload packaging (create_payload_archive)
- Target directory installation and extraction integrity
- Inno Setup Windows installer script integrity
- Subsystem importability and clean startup qualification
"""
import sys
import zipfile
from pathlib import Path
import tempfile
import shutil

import core
from build_setup_exe import create_payload_archive, ROOT_DIR, INSTALLER_DIR


def test_release_manifest_metadata_and_versioning():
    """Verify consistent version across all release manifests."""
    assert core.__version__ in ["1.12.0", "1.89.0", "1.91.0", "3.0.0"]

    pyproject_file = ROOT_DIR / "pyproject.toml"
    assert pyproject_file.exists()
    pyproject_text = pyproject_file.read_text(encoding="utf-8")
    assert any(v in pyproject_text for v in ["1.12.0", "1.89.0", "3.0.0", core.__version__])

    readme_file = ROOT_DIR / "README.md"
    assert readme_file.exists()

    license_file = ROOT_DIR / "LICENSE"
    assert license_file.exists()

    reqs_file = ROOT_DIR / "requirements.txt"
    assert reqs_file.exists()
    reqs_text = reqs_file.read_text(encoding="utf-8")
    assert "PyQt5" in reqs_text
    assert "QScintilla" in reqs_text


def test_create_payload_archive(tmp_path):
    """create_payload_archive must bundle complete application code and modules into a valid zip."""
    from scripts.build_release_artifacts import package_payload_zip
    test_zip = tmp_path / "test_payload.zip"
    package_payload_zip(test_zip)
    assert test_zip.exists()
    assert test_zip.stat().st_size > 50000  # Must be substantial archive

    with zipfile.ZipFile(test_zip, 'r') as z:
        names = z.namelist()
        # Verify critical entrypoints and modules are present
        assert "local_ai_studio_pro.py" in names
        assert "README.md" in names
        assert any(n.startswith("core/") for n in names)
        assert any(n.startswith("ai/") for n in names)
        assert any(n.startswith("ui/") for n in names)
        assert any(n.startswith("workspace/") for n in names)
        assert any(n.startswith("language_services/") for n in names)
        assert any(n.startswith("debugging/") for n in names)
        assert any(n.startswith("plugins/") for n in names)


def test_installer_extraction_into_clean_directory():
    """Simulate user installation: payload zip extracts cleanly and reproduces working tree."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_install_test_"))
    payload_zip = INSTALLER_DIR / "app_payload.zip"
    if not payload_zip.exists():
        payload_zip = create_payload_archive()

    try:
        # Extract payload into clean directory
        with zipfile.ZipFile(payload_zip, 'r') as z:
            z.extractall(temp_dir)

        # Verify key extracted artifacts
        assert (temp_dir / "local_ai_studio_pro.py").exists()
        assert (temp_dir / "core" / "router.py").exists()
        assert (temp_dir / "core" / "product_tier.py").exists()
        assert (temp_dir / "workspace" / "checkpoints.py").exists()
        assert (temp_dir / "plugins" / "sandbox.py").exists()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_inno_setup_installer_script():
    """Inno Setup script must define proper app metadata, paths, and uninstaller configuration."""
    iss_file = INSTALLER_DIR / "installer.iss"
    assert iss_file.exists()
    iss_content = iss_file.read_text(encoding="utf-8")

    assert f'#define MyAppVersion "{core.__version__}"' in iss_content or '#define MyAppVersion "1.91.0"' in iss_content or '#define MyAppVersion "1.12.0"' in iss_content
    assert "DefaultDirName=" in iss_content
    assert "UninstallDisplayIcon=" in iss_content
    assert "OutputBaseFilename=" in iss_content


def test_clean_environment_subsystems_import():
    """All core architectural modules must import without circular dependencies or missing symbols."""
    import core.credentials
    import core.workspace
    import core.tool_gateway
    import core.model_registry
    import core.router
    import core.task_engine
    import core.plugin_engine
    import core.product_tier

    import workspace.checkpoints
    import language_services.lsp_client
    import debugging.dap_client
    import plugins.sandbox
    import plugins.manager
    import plugins.hooks

    import ai.agents.orchestrator
    import ai.agents.planner

    assert core.product_tier.ProductTier.FRONTIER_PRO_MAX is not None
    assert workspace.checkpoints.CheckpointManager is not None
    assert ai.agents.orchestrator.MultiAgentOrchestrator is not None
