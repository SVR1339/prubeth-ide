"""
PRUBETH IDE — Code-OSS Open VSX Extension Client
Connects to the Open VSX Registry (Eclipse Foundation) for discovering and downloading .vsix extensions.
"""
import json
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional


OPEN_VSX_API_URL = "https://open-vsx.org/api/-/search"


class OpenVsxClient:
    """Client for querying the vendor-neutral Open VSX extension marketplace."""
    def __init__(self, extensions_dir: Optional[Path] = None):
        self.extensions_dir = Path(extensions_dir or (Path.home() / ".local_ai_studio_pro" / "extensions"))
        self.extensions_dir.mkdir(parents=True, exist_ok=True)

    def search_extensions(self, query: str, size: int = 10) -> List[Dict[str, Any]]:
        """Queries Open VSX for matching extensions."""
        params = urllib.parse.urlencode({"query": query, "size": size})
        url = f"{OPEN_VSX_API_URL}?{params}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PRUBETH-IDE/3.0.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                extensions = []
                for item in data.get("extensions", []):
                    extensions.append({
                        "id": f"{item.get('namespace')}.{item.get('name')}",
                        "name": item.get("displayName") or item.get("name"),
                        "publisher": item.get("namespace"),
                        "version": item.get("version"),
                        "description": item.get("description", ""),
                        "downloadUrl": item.get("files", {}).get("download"),
                        "iconUrl": item.get("files", {}).get("icon")
                    })
                return extensions
        except Exception:
            # Fallback offline extensions catalog
            return self._get_offline_catalog(query)

    def _get_offline_catalog(self, query: str) -> List[Dict[str, Any]]:
        catalog = [
            {
                "id": "ms-python.python",
                "name": "Python Language Support",
                "publisher": "ms-python",
                "version": "2024.18.0",
                "description": "Rich support for the Python language with linting, debugging, and code navigation."
            },
            {
                "id": "rust-lang.rust-analyzer",
                "name": "rust-analyzer",
                "publisher": "rust-lang",
                "version": "0.3.2100",
                "description": "Rust language support with fast type inlay hints and refactorings."
            },
            {
                "id": "esbenp.prettier-vscode",
                "name": "Prettier - Code formatter",
                "publisher": "esbenp",
                "version": "10.4.0",
                "description": "Opinionated code formatter using Prettier."
            },
            {
                "id": "eamodio.gitlens",
                "name": "GitLens — Git supercharged",
                "publisher": "eamodio",
                "version": "15.0.0",
                "description": "Supercharge Git within the editor with blame annotations and commit graph."
            },
            {
                "id": "ms-azuretools.vscode-docker",
                "name": "Docker",
                "publisher": "ms-azuretools",
                "version": "1.29.0",
                "description": "Easily build, manage, and deploy containerized applications from the editor."
            }
        ]
        q = query.lower()
        return [c for c in catalog if q in c["name"].lower() or q in c["id"].lower()]

    def list_installed_extensions(self) -> List[Dict[str, Any]]:
        """Lists extensions installed in the local extensions directory."""
        installed = []
        if not self.extensions_dir.exists():
            return installed

        for ext_folder in self.extensions_dir.iterdir():
            if ext_folder.is_dir():
                pkg_json = ext_folder / "package.json"
                if pkg_json.exists():
                    try:
                        d = json.loads(pkg_json.read_text(encoding="utf-8"))
                        installed.append({
                            "id": f"{d.get('publisher')}.{d.get('name')}",
                            "name": d.get("displayName") or d.get("name"),
                            "version": d.get("version"),
                            "path": str(ext_folder)
                        })
                    except Exception:
                        pass
        return installed
