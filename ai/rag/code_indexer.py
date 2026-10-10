"""
SUKHI IDE — AST-Aware Code Chunking & Local Search Retrieval Engine
Extracts classes, functions, methods, and docstrings from source code,
and ranks semantic query matches using offline lexical term scoring.
"""
import os
import ast
import re
import math
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from core.workspace import WorkspaceGuard, IGNORE_DIRS, TEXT_EXTENSIONS


@dataclass
class CodeChunk:
    file_path: str
    symbol_name: str
    symbol_type: str  # 'class', 'function', 'method', 'module', 'block'
    start_line: int
    end_line: int
    content: str
    docstring: Optional[str] = None
    tokens: Set[str] = field(default_factory=set)


def tokenize_code(text: str) -> Set[str]:
    """Extracts alphanumeric words, camelCase and snake_case sub-tokens."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    words = re.findall(r"[A-Za-z0-9_]+", spaced.lower())
    tokens = set()
    for w in words:
        tokens.add(w)
        sub = w.split("_")
        for s in sub:
            if len(s) > 1:
                tokens.add(s)
    for orig in re.findall(r"[A-Za-z0-9_]+", text.lower()):
        tokens.add(orig)
    return tokens


class AstSymbolChunker:
    """Parses source files into symbol-aware semantic code chunks."""

    @classmethod
    def chunk_python(cls, rel_path: str, code_text: str) -> List[CodeChunk]:
        chunks = []
        lines = code_text.splitlines()
        try:
            tree = ast.parse(code_text)
        except Exception:
            # Fallback if syntax invalid
            return cls.chunk_generic(rel_path, code_text)

        module_doc = ast.get_docstring(tree)
        if module_doc:
            chunks.append(CodeChunk(
                file_path=rel_path,
                symbol_name="<module>",
                symbol_type="module",
                start_line=1,
                end_line=min(20, len(lines)),
                content="\n".join(lines[:20]),
                docstring=module_doc,
                tokens=tokenize_code(module_doc)
            ))

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = node.lineno
                end = getattr(node, "end_lineno", start + 10)
                chunk_lines = lines[start - 1:end]
                content = "\n".join(chunk_lines)
                doc = ast.get_docstring(node)
                chunks.append(CodeChunk(
                    file_path=rel_path,
                    symbol_name=node.name,
                    symbol_type="function",
                    start_line=start,
                    end_line=end,
                    content=content,
                    docstring=doc,
                    tokens=tokenize_code(content + " " + (doc or ""))
                ))

            elif isinstance(node, ast.ClassDef):
                start = node.lineno
                end = getattr(node, "end_lineno", start + 20)
                chunk_lines = lines[start - 1:end]
                content = "\n".join(chunk_lines)
                doc = ast.get_docstring(node)
                chunks.append(CodeChunk(
                    file_path=rel_path,
                    symbol_name=node.name,
                    symbol_type="class",
                    start_line=start,
                    end_line=end,
                    content=content,
                    docstring=doc,
                    tokens=tokenize_code(content + " " + (doc or ""))
                ))

                # Also chunk individual methods inside the class
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        m_start = item.lineno
                        m_end = getattr(item, "end_lineno", m_start + 10)
                        m_content = "\n".join(lines[m_start - 1:m_end])
                        m_doc = ast.get_docstring(item)
                        chunks.append(CodeChunk(
                            file_path=rel_path,
                            symbol_name=f"{node.name}.{item.name}",
                            symbol_type="method",
                            start_line=m_start,
                            end_line=m_end,
                            content=m_content,
                            docstring=m_doc,
                            tokens=tokenize_code(m_content + " " + (m_doc or ""))
                        ))

        if not chunks:
            return cls.chunk_generic(rel_path, code_text)
        return chunks

    @classmethod
    def chunk_generic(cls, rel_path: str, text: str, window_size: int = 50, overlap: int = 10) -> List[CodeChunk]:
        chunks = []
        lines = text.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return []

        step = max(1, window_size - overlap)
        for i in range(0, total_lines, step):
            sub = lines[i:i + window_size]
            start = i + 1
            end = min(total_lines, i + len(sub))
            content = "\n".join(sub)
            chunks.append(CodeChunk(
                file_path=rel_path,
                symbol_name=f"lines_{start}_{end}",
                symbol_type="block",
                start_line=start,
                end_line=end,
                content=content,
                docstring=None,
                tokens=tokenize_code(content)
            ))
        return chunks


class CodebaseIndexer:
    """Scans and indexes workspace code for fast semantic and keyword search."""

    def __init__(self, workspace_root: Path):
        self.root = Path(workspace_root).resolve()
        self.chunks: List[CodeChunk] = []

    def build_index(self, max_files: int = 500) -> int:
        """Indexes all text files in workspace, returning total chunks extracted."""
        self.chunks = []
        file_count = 0

        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

            for fname in sorted(filenames):
                p = Path(dirpath) / fname
                if p.suffix.lower() not in TEXT_EXTENSIONS:
                    continue

                rel_path = str(p.relative_to(self.root)).replace("\\", "/")
                try:
                    content = p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue

                if p.suffix.lower() in (".py", ".pyw"):
                    file_chunks = AstSymbolChunker.chunk_python(rel_path, content)
                else:
                    file_chunks = AstSymbolChunker.chunk_generic(rel_path, content)

                self.chunks.extend(file_chunks)
                file_count += 1
                if file_count >= max_files:
                    break

        return len(self.chunks)

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Ranks chunks by token match frequency and keyword overlap."""
        q_tokens = tokenize_code(query)
        if not q_tokens or not self.chunks:
            return []

        scored = []
        for chunk in self.chunks:
            overlap = q_tokens.intersection(chunk.tokens)
            partial = {q for q in q_tokens if any(q in t or t in q for t in chunk.tokens if len(t) > 2 and len(q) > 2)}
            effective_matches = overlap.union(partial)
            if not effective_matches:
                continue

            # Score by overlap size and symbol name relevance
            score = len(effective_matches) * 2.0
            if any(q in chunk.symbol_name.lower() for q in q_tokens):
                score += 5.0  # Symbol name exact match boost
            if chunk.docstring and any(q in chunk.docstring.lower() for q in q_tokens):
                score += 3.0

            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scored[:top_k]:
            results.append({
                "score": round(score, 2),
                "file_path": chunk.file_path,
                "symbol_name": chunk.symbol_name,
                "symbol_type": chunk.symbol_type,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "snippet": chunk.content[:300] + ("..." if len(chunk.content) > 300 else "")
            })

        return results
