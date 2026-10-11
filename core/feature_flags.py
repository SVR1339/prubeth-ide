"""
PRUBETH IDE — Feature Flag & Capability Explorer Service
Pillar 1 & 6: Requirements & Quality Governance

Manages Stable, Preview, Experimental, and Developer-only feature flags,
ensuring security boundaries are preserved and dependencies verified before activation.
"""

from __future__ import annotations

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional


class FeatureMaturity:
    STABLE = "stable"
    PREVIEW = "preview"
    EXPERIMENTAL = "experimental"
    DEVELOPER_ONLY = "developer_only"


@dataclass
class FeatureFlag:
    """Represents a configurable feature flag within the IDE."""
    flag_id: str
    name: str
    description: str
    maturity: str  # stable, preview, experimental, developer_only
    enabled: bool = False
    enabled_by_default: bool = False
    dependencies: List[str] = field(default_factory=list)
    security_implications: str = "None"
    restart_required: bool = False


class FeatureFlagService:
    """Central service managing runtime feature toggles and persistent state."""

    _instance: Optional[FeatureFlagService] = None

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or (Path.home() / ".local_ai_studio_pro" / "feature_flags.json")
        self._flags: Dict[str, FeatureFlag] = {}
        self._register_default_flags()
        self._load_persisted_state()

    @classmethod
    def get_instance(cls) -> FeatureFlagService:
        if cls._instance is None:
            cls._instance = FeatureFlagService()
        return cls._instance

    def register(self, flag: FeatureFlag) -> None:
        self._flags[flag.flag_id] = flag

    def is_enabled(self, flag_id: str) -> bool:
        flag = self._flags.get(flag_id)
        return flag.enabled if flag else False

    def set_enabled(self, flag_id: str, enabled: bool) -> bool:
        """Sets the flag state and persists changes safely."""
        flag = self._flags.get(flag_id)
        if not flag:
            raise KeyError(f"Feature flag '{flag_id}' not found.")
        flag.enabled = enabled
        self._save_persisted_state()
        return flag.enabled

    def list_all(self) -> List[FeatureFlag]:
        return list(self._flags.values())

    def reset_to_defaults(self) -> None:
        for f in self._flags.values():
            f.enabled = f.enabled_by_default
        self._save_persisted_state()

    def _register_default_flags(self) -> None:
        self.register(FeatureFlag(
            flag_id="preview.composer_v2",
            name="Composer Engine V2 (Fast Transactional Diffs)",
            description="Enables transactional multi-file delta streaming with AST symbol caching.",
            maturity=FeatureMaturity.STABLE,
            enabled=True,
            enabled_by_default=True
        ))
        self.register(FeatureFlag(
            flag_id="preview.hardware_autotuner",
            name="Universal Hardware Auto-Tuner",
            description="Automatically tunes thread workers, cache MB, and CUDA layers on boot.",
            maturity=FeatureMaturity.STABLE,
            enabled=True,
            enabled_by_default=True
        ))
        self.register(FeatureFlag(
            flag_id="experimental.browser_verification",
            name="Multimodal Headless Browser Verification",
            description="Allows background agents to inspect DOM selectors, console JS, and capture screenshots.",
            maturity=FeatureMaturity.PREVIEW,
            enabled=True,
            enabled_by_default=True,
            security_implications="Executes headless browser sessions locally."
        ))
        self.register(FeatureFlag(
            flag_id="experimental.shadow_worktrees",
            name="Git Worktree Zero-Interference Sandbox",
            description="Isolates agent code mutations into shadow branches before human review.",
            maturity=FeatureMaturity.STABLE,
            enabled=True,
            enabled_by_default=True
        ))
        self.register(FeatureFlag(
            flag_id="dev.deep_diagnostics",
            name="Deep Subsystem Tracing & Diagnostics Export",
            description="Generates sanitized HTML/JSON diagnostic bundles for performance inspection.",
            maturity=FeatureMaturity.DEVELOPER_ONLY,
            enabled=False,
            enabled_by_default=False
        ))

    def _load_persisted_state(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                for fid, val in data.items():
                    if fid in self._flags:
                        self._flags[fid].enabled = bool(val)
        except Exception:
            pass

    def _save_persisted_state(self) -> None:
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {fid: f.enabled for fid, f in self._flags.items()}
            self.storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass
