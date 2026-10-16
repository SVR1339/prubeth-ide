"""
PRUBETH IDE — Authoritative Path Resolution Engine
Part of the Zero-Silent-Failure Launcher & Application Startup Engine.

Resolves application root, bundled assets, user configuration, log journals,
workspaces, and temporary directories safely across source and frozen PyInstaller environments.
Handles spaces, Unicode characters, and invocations from arbitrary working directories.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class ResolvedPaths:
    """Resolved, validated directory paths for application runtime."""
    app_root: Path
    assets_dir: Path
    user_data_dir: Path
    logs_dir: Path
    config_file: Path
    workspaces_dir: Path
    temp_dir: Path
    is_frozen: bool


class PathResolver:
    """
    Authoritative path resolver ensuring absolute independence from the process CWD.
    Works reliably when launched from Start Menu, Desktop Shortcut, or CLI.
    """

    DEFAULT_USER_DIR_NAME = ".local_ai_studio_pro"
    SETTINGS_FILE_NAME = "settings.json"

    @classmethod
    def resolve(
        cls,
        custom_user_dir: Optional[Path] = None,
        custom_workspace_dir: Optional[Path] = None
    ) -> ResolvedPaths:
        """
        Determines and verifies all required runtime paths.
        Creates writable directories if they do not exist.
        """
        is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

        if is_frozen:
            # Running inside PyInstaller standalone bundle
            app_root = Path(sys._MEIPASS).resolve()
        else:
            # Running from source tree
            # This file is in core/startup/path_resolver.py -> parent.parent.parent is app_root
            app_root = Path(__file__).resolve().parent.parent.parent

        # Assets directory
        assets_dir = app_root / "assets"
        if not assets_dir.exists():
            # Check fallback in app_root
            assets_dir = app_root

        # User data directory (Settings, history, logs)
        if custom_user_dir:
            user_data_dir = Path(custom_user_dir).resolve()
        else:
            user_data_dir = (Path.home() / cls.DEFAULT_USER_DIR_NAME).resolve()

        # Ensure user data directory exists and is writable
        user_data_dir.mkdir(parents=True, exist_ok=True)

        # Logs directory
        logs_dir = user_data_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Config file path
        config_file = user_data_dir / cls.SETTINGS_FILE_NAME

        # Workspaces directory
        if custom_workspace_dir:
            workspaces_dir = Path(custom_workspace_dir).resolve()
        else:
            workspaces_dir = Path.home() / "Projects"
            try:
                workspaces_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                workspaces_dir = user_data_dir / "workspaces"
                workspaces_dir.mkdir(parents=True, exist_ok=True)

        # Dedicated isolated temp directory
        temp_dir = user_data_dir / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        return ResolvedPaths(
            app_root=app_root,
            assets_dir=assets_dir,
            user_data_dir=user_data_dir,
            logs_dir=logs_dir,
            config_file=config_file,
            workspaces_dir=workspaces_dir,
            temp_dir=temp_dir,
            is_frozen=is_frozen
        )

    @classmethod
    def resolve_dynamic_path(cls, target_path: str) -> Path:
        """
        Dynamically resolves paths that may reference missing or relettered drives (e.g. E:\\).
        Auto-relocates to verified local paths on C:\\ or workspace.
        """
        p = Path(target_path)
        if p.exists():
            return p.resolve()
        try:
            from core.probabilistic_resilience_engine import ProbabilisticResilienceEngine
            healed = ProbabilisticResilienceEngine.get_instance().heal_missing_drive_path(target_path)
            if healed and healed.exists():
                return healed
        except Exception:
            pass
        return p
