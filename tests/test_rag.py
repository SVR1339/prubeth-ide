"""
Unit and Integration Tests for AI Subsystem (AST Code Chunking, Lexical Search Ranking)
"""
import tempfile
import shutil
from pathlib import Path
import pytest
from ai.rag.code_indexer import AstSymbolChunker, CodebaseIndexer, tokenize_code


def test_ast_python_chunking():
    sample_code = """
\"\"\"Module docstring for auth service.\"\"\"

def authenticate_user(username, password):
    \"\"\"Validates user credentials against database.\"\"\"
    return username == "admin"

class SessionManager:
    \"\"\"Handles user login sessions and tokens.\"\"\"
    def create_session(self, user_id):
        \"\"\"Creates a new session token.\"\"\"
        return f"token-{user_id}"
"""
    chunks = AstSymbolChunker.chunk_python("auth.py", sample_code)
    assert len(chunks) >= 4  # module doc, authenticate_user, SessionManager, create_session

    symbols = [c.symbol_name for c in chunks]
    assert "authenticate_user" in symbols
    assert "SessionManager" in symbols
    assert "SessionManager.create_session" in symbols

    # Check function docstring
    auth_chunk = next(c for c in chunks if c.symbol_name == "authenticate_user")
    assert auth_chunk.symbol_type == "function"
    assert "Validates user credentials" in auth_chunk.docstring


def test_codebase_indexer_search():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "math_utils.py").write_text("""
def calculate_fibonacci(n):
    \"\"\"Computes the nth Fibonacci number.\"\"\"
    if n <= 1: return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
""", encoding="utf-8")

        (root / "db.py").write_text("""
class DatabaseConnection:
    \"\"\"Manages PostgreSQL pool connections.\"\"\"
    def connect(self):
        pass
""", encoding="utf-8")

        indexer = CodebaseIndexer(root)
        total_chunks = indexer.build_index()
        assert total_chunks >= 2

        # Search for fibonacci
        results = indexer.search("fibonacci number")
        assert len(results) > 0
        top = results[0]
        assert "math_utils.py" in top["file_path"]
        assert top["symbol_name"] == "calculate_fibonacci"

        # Search for database pool
        db_results = indexer.search("database postgres connection")
        assert len(db_results) > 0
        assert "DatabaseConnection" in db_results[0]["symbol_name"]
