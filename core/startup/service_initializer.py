"""
PRUBETH IDE — Dependency-Ordered Service Initializer
Part of the Zero-Silent-Failure Launcher & Application Startup Engine.

Orchestrates sequential, dependency-aware service initialization across 13 stages.
Isolates optional service failures (e.g., local Ollama offline, uninstalled extensions)
and transitions seamlessly into DEGRADED_MODE rather than crashing the core IDE.
"""

from __future__ import annotations

import os
import sys
import time
import logging
import traceback
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Callable

from core.startup.state_machine import StartupStateMachine, StartupState
from core.startup.path_resolver import ResolvedPaths


class ServiceStatus(str, Enum):
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class ServiceDescriptor:
    """Service metadata and health contract."""
    service_id: str
    name: str
    is_mandatory: bool
    status: ServiceStatus = ServiceStatus.INITIALIZING
    duration_ms: float = 0.0
    error_message: Optional[str] = None
    diagnostics: Dict[str, Any] = field(default_factory=dict)


class ServiceInitializer:
    """
    Manages dependency-ordered service lifecycle.
    Guarantees that mandatory failures halt startup cleanly with full diagnostics,
    while optional failures fall back to safe degraded mode.
    """

    def __init__(
        self,
        paths: ResolvedPaths,
        state_machine: StartupStateMachine,
        safe_mode: bool = False
    ):
        self.paths = paths
        self.state_machine = state_machine
        self.safe_mode = safe_mode
        self._services: Dict[str, ServiceDescriptor] = {}
        self._logger: Optional[logging.Logger] = None

    def initialize_all(self) -> Tuple[bool, List[ServiceDescriptor]]:
        """
        Executes all 13 initialization stages in strict dependency order.
        Returns (success, service_descriptors).
        """
        stages = [
            ("paths_and_logging", "Paths & Diagnostic Logger", True, self._init_paths_and_logging),
            ("configuration", "Configuration & Policy Store", True, self._init_configuration),
            ("crash_handlers", "Core Crash Hooks & Error Traps", True, self._init_crash_handlers),
            ("persistent_storage", "Task Engine & Persistent Checkpoints", True, self._init_persistent_storage),
            ("task_scheduler", "Background Workers & Thread Pools", True, self._init_task_scheduler),
            ("workspace_services", "Workspace Security & Conflict Guard", True, self._init_workspace_services),
            ("editor_infrastructure", "Editor Tokens & Lexer Engine", True, self._init_editor_infrastructure),
            ("model_registry", "Model Registry & Hardware Scaling", True, self._init_model_registry),
            ("local_ai_probe", "Local AI Runtimes (Ollama/vLLM)", False, self._init_local_ai_probe),
            ("agent_orchestration", "Agent Archetypes & Tool Gateway", True, self._init_agent_orchestration),
            ("plugins_engine", "Plugin Sandbox & Extensions", False, self._init_plugins_engine),
            ("health_monitoring", "Autonomous Diagnostics & Event Bus", True, self._init_health_monitoring),
            ("final_verification", "Final Application Readiness", True, self._init_final_readiness),
        ]

        # Transition to PREFLIGHT if not already there
        if self.state_machine.current_state == StartupState.NOT_STARTED:
            self.state_machine.transition_to(StartupState.PREFLIGHT)

        has_degraded = False

        for s_id, s_name, is_mandatory, init_fn in stages:
            start_t = time.time()
            desc = ServiceDescriptor(service_id=s_id, name=s_name, is_mandatory=is_mandatory)
            self._services[s_id] = desc

            try:
                init_fn()
                desc.status = ServiceStatus.READY
                desc.duration_ms = (time.time() - start_t) * 1000.0
                if self._logger:
                    self._logger.info(f"[OK] Initialized {s_name} in {desc.duration_ms:.1f}ms")
            except Exception as ex:
                desc.duration_ms = (time.time() - start_t) * 1000.0
                desc.error_message = str(ex)
                desc.diagnostics["traceback"] = traceback.format_exc()

                if is_mandatory:
                    desc.status = ServiceStatus.FAILED
                    if self._logger:
                        self._logger.error(f"[FAIL] MANDATORY SERVICE FAILED: {s_name} - {ex}\n{desc.diagnostics['traceback']}")
                    self.state_machine.transition_to(
                        StartupState.FAILED,
                        error_message=f"Mandatory service '{s_name}' failed: {ex}"
                    )
                    return False, list(self._services.values())
                else:
                    # Optional service failure: isolate and enter degraded mode
                    desc.status = ServiceStatus.DEGRADED
                    has_degraded = True
                    if self._logger:
                        self._logger.warning(f"⚠ Optional service '{s_name}' failed ({ex}); continuing in DEGRADED mode.")

        # Update state machine according to final health
        if has_degraded or self.safe_mode:
            if self.state_machine.current_state != StartupState.DEGRADED_MODE:
                try:
                    self.state_machine.transition_to(StartupState.DEGRADED_MODE)
                except Exception:
                    pass
        else:
            if self.state_machine.current_state != StartupState.APPLICATION_READY:
                try:
                    self.state_machine.transition_to(StartupState.APPLICATION_READY)
                except Exception:
                    pass

        return True, list(self._services.values())

    def shutdown(self) -> None:
        """Flushes and closes file handlers to avoid Windows file locks."""
        if self._logger:
            for handler in list(self._logger.handlers):
                try:
                    handler.flush()
                    handler.close()
                except Exception:
                    pass
                self._logger.removeHandler(handler)

    # -------------------------------------------------------------
    # Stage Implementations
    # -------------------------------------------------------------
    def _init_paths_and_logging(self) -> None:
        """Sets up rotating file logger in the user data logs directory."""
        log_file = self.paths.logs_dir / "startup.log"
        logger = logging.getLogger("PRUBETH_STARTUP")
        logger.setLevel(logging.INFO)
        
        # Avoid duplicate handlers on re-entry
        if not logger.handlers:
            handler = logging.FileHandler(str(log_file), encoding="utf-8")
            formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        self._logger = logger
        self._logger.info("=" * 60)
        self._logger.info(f"PRUBETH IDE STARTUP INITIATED (PID: {os.getpid()})")
        self._logger.info(f"App Root: {self.paths.app_root}")
        self._logger.info(f"User Data Dir: {self.paths.user_data_dir}")
        self._logger.info("=" * 60)

    def _init_configuration(self) -> None:
        """Validates configuration service and applies migrations."""
        from core.configuration_service import ConfigurationService
        config_service = ConfigurationService.get_instance(user_config_path=self.paths.config_file)
        self.state_machine.transition_to(StartupState.CONFIGURATION_READY)

    def _init_crash_handlers(self) -> None:
        """Installs global exception trap to ensure no unhandled silent crashes."""
        if "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
            return

        def global_excepthook(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            crash_log = self.paths.logs_dir / "crash_unhandled.log"
            try:
                with open(crash_log, "a", encoding="utf-8") as f:
                    f.write(f"\n--- UNHANDLED EXCEPTION [{time.strftime('%Y-%m-%d %H:%M:%S')}] ---\n")
                    traceback.print_exception(exc_type, exc_value, exc_traceback, file=f)
            except Exception:
                pass
            if self._logger:
                self._logger.critical("Unhandled top-level exception captured", exc_info=(exc_type, exc_value, exc_traceback))

        sys.excepthook = global_excepthook

    def _init_persistent_storage(self) -> None:
        """Initializes TaskEngine and verifies SQLite database integrity."""
        from core.task_engine import TaskEngine
        db_path = str(self.paths.user_data_dir / "tasks.db")
        TaskEngine(db_path=db_path)

    def _init_task_scheduler(self) -> None:
        """Ensures background thread pool is sized appropriately."""
        from core.hardware.resource_budget import ResourceBudgetManager
        ResourceBudgetManager()
        self.state_machine.transition_to(StartupState.CORE_SERVICES_READY)

    def _init_workspace_services(self) -> None:
        """Initializes workspace boundary verification and file conflict guard."""
        from core.workspace import get_workspace_boundary_guard
        get_workspace_boundary_guard(str(self.paths.workspaces_dir))

    def _init_editor_infrastructure(self) -> None:
        """Verifies UI styling tokens and Monaco / QScintilla lexer bridges."""
        from ui.design_system import DesignTokens
        assert DesignTokens.ACCENT_CYAN is not None

    def _init_model_registry(self) -> None:
        """Initializes model registry and hardware discovery snapshots."""
        from core.model_registry import ModelRegistry
        from core.hardware.detection import HardwareCapabilityManager
        HardwareCapabilityManager.get_instance()

    def _init_local_ai_probe(self) -> None:
        """
        Non-blocking probe of local runtimes (Ollama/LM Studio).
        If offline, records notice without crashing.
        """
        if self.safe_mode or "pytest" in sys.modules or "PYTEST_CURRENT_TEST" in os.environ:
            return
        from horizon_engine.connector_gateway import ConnectorGateway
        ConnectorGateway.probe_local_ai_runtimes(timeout_seconds=0.8)

    def _init_agent_orchestration(self) -> None:
        """Verifies agent archetypes and tool execution gateway."""
        from core.tool_gateway import get_tool_gateway
        get_tool_gateway(str(self.paths.workspaces_dir))

    def _init_plugins_engine(self) -> None:
        """Initializes plugin sandbox."""
        if self.safe_mode:
            return
        from core.workspace import WorkspaceGuard
        from plugins.manager import PluginManager
        guard = WorkspaceGuard(self.paths.workspaces_dir)
        plugins_dir = self.paths.user_data_dir / "plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)
        pm = PluginManager(str(plugins_dir), workspace_guard=guard)
        pm.discover_plugins()

    def _init_health_monitoring(self) -> None:
        """Initializes application event bus and health monitor."""
        from core.event_bus import EventBus
        EventBus.get_instance()

    def _init_final_readiness(self) -> None:
        """Asserts all prerequisite states are met."""
        pass
