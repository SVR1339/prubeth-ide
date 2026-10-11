"""
PRUBETH IDE — Code-OSS Fork Subsystem
Proprietary Code-OSS fork architecture with Composer, Monaco bridge, and Open VSX.
"""
from code_oss.composer.engine import ComposerEngine, FileDiffPlan
from code_oss.context.codebase_indexer import CodebaseIndexer, CodeSymbol
from code_oss.extension_host.open_vsx_client import OpenVsxClient
from code_oss.monaco.bridge import MonacoEditorBridge

__all__ = [
    "ComposerEngine",
    "FileDiffPlan",
    "CodebaseIndexer",
    "CodeSymbol",
    "OpenVsxClient",
    "MonacoEditorBridge"
]
