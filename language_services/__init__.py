"""
SUKHI IDE — Language Intelligence & Language Server Protocol (LSP) Subsystem
Provides JSON-RPC 2.0 stdio transport, document sync, cross-file definitions,
and real-time diagnostics from language servers.
"""
from language_services.lsp_client import LspClient, LspDiagnostic, LspLocation

__all__ = [
    "LspClient",
    "LspDiagnostic",
    "LspLocation"
]
