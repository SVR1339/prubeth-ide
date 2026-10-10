"""
SUKHI IDE — Debugging & Debug Adapter Protocol (DAP) Subsystem
Provides DAP client execution, breakpoint management, stack inspection,
and variable evaluation for interactive debugging sessions.
"""
from debugging.dap_client import DapClient, SourceBreakpoint, StackFrame, Variable

__all__ = [
    "DapClient",
    "SourceBreakpoint",
    "StackFrame",
    "Variable"
]
