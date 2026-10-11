"""
PRUBETH IDE — Zero-Silent-Failure Launcher & Application Startup Subsystem
Public package interface.
"""

from core.startup.state_machine import (
    StartupState,
    TransitionRecord,
    InvalidStateTransitionError,
    StartupStateMachine,
)
from core.startup.path_resolver import (
    PathResolver,
    ResolvedPaths,
)
from core.startup.preflight import (
    CheckStatus,
    PreflightItem,
    PreflightReport,
    PreflightChecker,
)
from core.startup.service_initializer import (
    ServiceStatus,
    ServiceDescriptor,
    ServiceInitializer,
)
from core.startup.recovery_dialog import (
    StartupRecoveryHandler,
)
from core.startup.launcher import (
    AuthoritativeLauncher,
)

__all__ = [
    "StartupState",
    "TransitionRecord",
    "InvalidStateTransitionError",
    "StartupStateMachine",
    "PathResolver",
    "ResolvedPaths",
    "CheckStatus",
    "PreflightItem",
    "PreflightReport",
    "PreflightChecker",
    "ServiceStatus",
    "ServiceDescriptor",
    "ServiceInitializer",
    "StartupRecoveryHandler",
    "AuthoritativeLauncher",
]
