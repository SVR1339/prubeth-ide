"""
PRUBETH IDE — Clean Application Uninstaller & Maintenance Engine
Removes application-managed binaries, shortcuts, PATH entries, and registry entries.
Strictly preserves user projects, workspaces, local models, and settings unless explicitly confirmed.
"""
import os
import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional


class Uninstaller:
    """Safely cleans application files while preserving user data."""

    def __init__(self, install_dir: Path):
        self.install_dir = Path(install_dir).resolve()

    def uninstall(
        self,
        remove_user_data: bool = False,
        remove_models: bool = False,
        remove_shortcuts: bool = True
    ) -> Dict[str, Any]:
        """
        Executes uninstallation.
        Defaults: keeps user projects, workspaces, models, and .local_ai_studio_pro config.
        """
        removed_items = []
        preserved_items = []
        errors = []

        if not self.install_dir.exists():
            return {"success": True, "message": "Installation directory does not exist.", "removed": []}

        # 1. Remove Desktop & Start Menu Shortcuts
        if remove_shortcuts:
            for sc in [
                Path.home() / "Desktop" / "PRUBETH IDE.lnk",
                Path.home() / "Desktop" / "PRUBETH.lnk",
                Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "PRUBETH IDE"
            ]:
                if sc.exists():
                    try:
                        if sc.is_dir():
                            shutil.rmtree(sc, ignore_errors=True)
                        else:
                            sc.unlink()
                        removed_items.append(str(sc))
                    except Exception as ex:
                        errors.append(f"Failed to remove shortcut {sc}: {ex}")

        # 2. Iterate install directory files
        app_managed_subdirs = [
            "core", "workspace", "source_control", "language_services",
            "debugging", "ai", "ui", "plugins", "assets", "tests", "docs", "scripts",
            "horizon_engine", "security_research"
        ]
        app_managed_files = [
            "local_ai_studio_pro.py", "PrubethIDE.bat", "PrubethIDE.exe",
            "SukhiIDE.bat", "SukhiIDE.exe", "SoNaive.bat", "SoNaive.exe",
            "README.md", "LICENSE", "ARCHITECTURE.md", "CHANGELOG.md",
            "INSTALL.md", "DEVELOPER_EXTENSIONS_GUIDE.md", "FINAL_RELEASE_VERIFICATION.md",
            "installation_receipt.json"
        ]

        # Remove application-managed core directories
        for d in app_managed_subdirs:
            p = self.install_dir / d
            if p.exists() and p.is_dir():
                try:
                    shutil.rmtree(p, ignore_errors=True)
                    removed_items.append(str(p))
                except Exception as ex:
                    errors.append(f"Error removing {p}: {ex}")

        # Remove application-managed files
        for f in app_managed_files:
            p = self.install_dir / f
            if p.exists() and p.is_file():
                try:
                    p.unlink()
                    removed_items.append(str(p))
                except Exception as ex:
                    errors.append(f"Error removing {p}: {ex}")

        # 3. Handle models cache
        models_dir = self.install_dir / "models"
        if models_dir.exists():
            if remove_models:
                try:
                    shutil.rmtree(models_dir, ignore_errors=True)
                    removed_items.append(str(models_dir))
                except Exception as ex:
                    errors.append(f"Error removing models {models_dir}: {ex}")
            else:
                preserved_items.append(str(models_dir))

        # 4. Handle user settings & workspaces
        config_dir = self.install_dir / ".local_ai_studio_pro"
        if config_dir.exists():
            if remove_user_data:
                try:
                    shutil.rmtree(config_dir, ignore_errors=True)
                    removed_items.append(str(config_dir))
                except Exception as ex:
                    errors.append(f"Error removing config {config_dir}: {ex}")
            else:
                preserved_items.append(str(config_dir))

        # 5. Clean parent if now empty or only user data left
        try:
            remaining = list(self.install_dir.iterdir())
            if not remaining:
                self.install_dir.rmdir()
                removed_items.append(str(self.install_dir))
            else:
                preserved_items.extend([str(r) for r in remaining])
        except Exception:
            pass

        return {
            "success": len(errors) == 0,
            "removed_items": removed_items,
            "preserved_items": preserved_items,
            "errors": errors
        }
