"""
PRUBETH IDE — Code-OSS Codebase Context Indexer
Extracts AST symbols, function signatures, and relevance-ranked code chunks for @Codebase queries.
"""
import os
import ast
from pathlib import Path
from typing import List, Dict, Any, Optional

IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build", ".pytest_cache"}
CODE_EXTS = {".py", ".js", ".ts", ".jsx", ".tsx", ".cpp", ".c", ".rs", ".go", ".sql", ".json", ".md"}


class CodeSymbol:
    """Represents an extracted code symbol (class, function, method)."""
    def __init__(self, name: str, symbol_type: str, file_path: str, line_no: int, docstring: str = ""):
        self.name = name
        self.symbol_type = symbol_type
        self.file_path = file_path
        self.line_no = line_no
        self.docstring = docstring

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.symbol_type,
            "file": self.file_path,
            "line": self.line_no,
            "docstring": self.docstring
        }


class CodebaseIndexer:
    """Scans and indexes workspace codebases for Cursor-grade @Codebase retrieval."""
    def __init__(self, workspace_root: Path):
        self.workspace_root = Path(workspace_root).resolve()
        self.symbols: List[CodeSymbol] = []
        self.file_index: List[str] = []

    def index_workspace(self, max_files: int = 500) -> int:
        """Indexes workspace files and extracts AST symbols."""
        self.symbols.clear()
        self.file_index.clear()
        scanned = 0

        for root, dirs, files in os.walk(self.workspace_root):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            for f in files:
                p = Path(root) / f
                if p.suffix.lower() not in CODE_EXTS:
                    continue

                rel_path = str(p.relative_to(self.workspace_root))
                self.file_index.append(rel_path)
                scanned += 1

                if p.suffix.lower() == ".py":
                    self._index_python_file(p, rel_path)

                if scanned >= max_files:
                    break
            if scanned >= max_files:
                break

        return len(self.symbols)

    def _index_python_file(self, full_path: Path, rel_path: str):
        try:
            content = full_path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(content, filename=str(full_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    doc = ast.get_docstring(node) or ""
                    self.symbols.append(CodeSymbol(node.name, "class", rel_path, node.lineno, doc))
                elif isinstance(node, ast.FunctionDef) or isinstance(node, getattr(ast, "AsyncFunctionDef", ast.FunctionDef)):
                    doc = ast.get_docstring(node) or ""
                    self.symbols.append(CodeSymbol(node.name, "function", rel_path, node.lineno, doc))
        except Exception:
            pass

    def search_symbols(self, query: str, limit: int = 10) -> List[CodeSymbol]:
        """Searches symbols matching the query string or its terms."""
        q = query.lower().strip()
        terms = [t for t in q.split() if len(t) > 1]
        matches = []
        for s in self.symbols:
            name_low = s.name.lower()
            doc_low = s.docstring.lower()
            if q in name_low or q in doc_low:
                matches.append(s)
            elif terms and any(t in name_low or t in doc_low for t in terms):
                matches.append(s)
        return matches[:limit]

    def build_codebase_context(self, query: str, max_chars: int = 8000) -> str:
        """Constructs a high-density @Codebase context prompt for the AI model."""
        matching_symbols = self.search_symbols(query, limit=15)
        lines = [f"=== @CODEBASE SYMBOL INDEX FOR '{query}' ==="]
        for s in matching_symbols:
            lines.append(f"• [{s.symbol_type.upper()}] {s.name} in {s.file_path}:{s.line_no} — {s.docstring[:100]}")

        lines.append("\n=== RELEVANT WORKSPACE FILES ===")
        # Find files matching query terms
        terms = query.lower().split()
        relevant_files = [f for f in self.file_index if any(t in f.lower() for t in terms)][:8]
        for rf in relevant_files:
            lines.append(f"• {rf}")

        result = "\n".join(lines)
        return result[:max_chars]
