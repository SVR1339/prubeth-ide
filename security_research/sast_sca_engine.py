"""PRUBETH IDE - SAST (Static Application Security Testing) & SCA Engine
======================================================================
Defensive security analysis system providing multi-rule AST/regex code
scanning, Software Composition Analysis, dependency vulnerability checks,
and CycloneDX/SPDX SBOM generation for personal sovereignty and research.
"""

from __future__ import annotations

import ast
import enum
import json
import logging
import math
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Models
# ============================================================================

class SecuritySeverity(str, enum.Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def rank(self) -> int:
        return {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}[self.value]


@dataclass
class SecurityFinding:
    finding_id: str
    rule_id: str
    severity: SecuritySeverity
    title: str
    description: str
    file_path: str
    line_number: int
    code_snippet: str
    remediation: str
    cwe_id: str
    cve_id: Optional[str] = None
    cvss_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


# ============================================================================
# SAST Engine (Static Code Analysis)
# ============================================================================

class SASTEngine:
    """Multi-rule AST and pattern static security analyzer for defensive code review."""

    def __init__(self) -> None:
        self._compiled_regexes = self._init_patterns()

    def _init_patterns(self) -> List[Tuple[str, str, SecuritySeverity, str, str, str, re.Pattern]]:
        """Returns list of regex rule tuples:
        (rule_id, title, severity, cwe, description, remediation, pattern)
        """
        raw_rules = [
            (
                "PRUBETH-SEC-001",
                "Command Injection via Shell Execution",
                SecuritySeverity.CRITICAL,
                "CWE-78",
                "Execution of shell commands with untrusted inputs or shell=True permits arbitrary execution.",
                "Use subprocess.run() with shell=False and pass arguments as an explicit list.",
                r"(subprocess\.(Popen|run|call|check_output|check_call)\([^)]*shell\s*=\s*True|os\.system\(|os\.popen\()",
            ),
            (
                "PRUBETH-SEC-002",
                "Insecure Deserialization",
                SecuritySeverity.CRITICAL,
                "CWE-502",
                "Unsafe deserialization can execute arbitrary code during object reconstruction.",
                "Use safe serialization formats such as JSON or safetensors; avoid pickle or yaml.Loader.",
                r"(pickle\.loads?\(|_pickle\.loads?\(|yaml\.load\([^)]*Loader\s*=\s*(yaml\.)?Loader)",
            ),
            (
                "PRUBETH-SEC-003",
                "Hardcoded High-Entropy Secret or Private Key",
                SecuritySeverity.HIGH,
                "CWE-798",
                "Hardcoded credentials, API keys, or private keys exposed in source files.",
                "Move secrets to environment variables, .env or PRUBETH Secure Credentials Vault.",
                r"(-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|sk-[a-zA-Z0-9]{32,}|ghp_[a-zA-Z0-9]{36})",
            ),
            (
                "PRUBETH-SEC-004",
                "Path Traversal Pattern",
                SecuritySeverity.HIGH,
                "CWE-22",
                "Unchecked directory traversal sequences in path resolution.",
                "Validate input with os.path.abspath and ensure it remains within the target base directory.",
                r"(open\([^)]*\.\./|os\.path\.join\([^)]*(\.\./|\.\.\\))",
            ),
            (
                "PRUBETH-SEC-005",
                "Broken or Insecure Cryptographic Hash",
                SecuritySeverity.MEDIUM,
                "CWE-327",
                "Usage of broken cryptographic algorithms (MD5/SHA1) for security-sensitive purposes.",
                "Upgrade to SHA-256, SHA-512, or argon2/bcrypt for credential verification.",
                r"(hashlib\.(md5|sha1)\(|AES\.MODE_ECB|DES\.new\()",
            ),
            (
                "PRUBETH-SEC-006",
                "SQL Injection via Unparameterized Query Formatting",
                SecuritySeverity.CRITICAL,
                "CWE-89",
                "Dynamic string formatting within database SQL execution strings.",
                "Use parameterized query execution (e.g. cursor.execute(query, (params,)))",
                r"(cursor\.execute\(\s*f[\"'].*SELECT|cursor\.execute\(\s*[\"'].*SELECT.*%|\.raw\(\s*f[\"'])",
            ),
            (
                "PRUBETH-SEC-007",
                "Cryptographically Insecure Pseudorandom Number Generator",
                SecuritySeverity.LOW,
                "CWE-338",
                "Standard pseudo-random generators are predictable and unsafe for security tokens.",
                "Use the 'secrets' module (secrets.token_hex, secrets.randbelow) for security tokens.",
                r"(random\.(random|randint|choice|sample|randrange)\()",
            ),
        ]
        compiled = []
        for rule_id, title, sev, cwe, desc, rem, pat in raw_rules:
            compiled.append((rule_id, title, sev, cwe, desc, rem, re.compile(pat, re.IGNORECASE)))
        return compiled

    def scan_file(self, file_path: str, content: Optional[str] = None) -> List[SecurityFinding]:
        """Scans a single file with AST (if Python) and regex security rules."""
        findings: List[SecurityFinding] = []
        p = Path(file_path)

        if content is None:
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                logger.error(f"Failed to read file for SAST scan {file_path}: {e}")
                return findings

        lines = content.splitlines()

        # 1. Regex rule scan across lines
        for line_idx, line in enumerate(lines, start=1):
            # Check secrets & dangerous functions
            for rule_id, title, sev, cwe, desc, rem, regex in self._compiled_regexes:
                match = regex.search(line)
                if match:
                    # Filter out benign comments or docs
                    trimmed = line.strip()
                    if trimmed.startswith("#") or trimmed.startswith("//"):
                        continue
                    
                    finding_id = f"{rule_id}:{p.name}:{line_idx}"
                    snippet = line.strip()[:160]
                    findings.append(SecurityFinding(
                        finding_id=finding_id,
                        rule_id=rule_id,
                        severity=sev,
                        title=title,
                        description=desc,
                        file_path=str(p),
                        line_number=line_idx,
                        code_snippet=snippet,
                        remediation=rem,
                        cwe_id=cwe,
                    ))

        # 2. Python-specific AST Visitor scan
        if p.suffix.lower() == ".py":
            try:
                tree = ast.parse(content, filename=str(p))
                ast_findings = self._scan_ast_nodes(tree, str(p), lines)
                findings.extend(ast_findings)
            except SyntaxError:
                pass  # Handled gracefully if file has active parse errors

        return findings

    def _scan_ast_nodes(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[SecurityFinding]:
        """Performs deep structural AST analysis for eval, exec, and dangerous calls."""
        findings: List[SecurityFinding] = []

        class SecurityVisitor(ast.NodeVisitor):
            def __init__(self, owner: SASTEngine):
                self.owner = owner

            def visit_Call(self, node: ast.Call) -> None:
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                line_no = getattr(node, "lineno", 1)
                snippet = lines[line_no - 1].strip() if 0 < line_no <= len(lines) else ""

                if func_name in ("eval", "exec"):
                    findings.append(SecurityFinding(
                        finding_id=f"PRUBETH-SEC-008:{Path(file_path).name}:{line_no}",
                        rule_id="PRUBETH-SEC-008",
                        severity=SecuritySeverity.CRITICAL,
                        title=f"Dynamic Code Execution via {func_name}()",
                        description=f"Direct invocation of {func_name}() can allow arbitrary code injection.",
                        file_path=file_path,
                        line_number=line_no,
                        code_snippet=snippet,
                        remediation="Use structured parsing (ast.literal_eval, json.loads) instead of dynamic execution.",
                        cwe_id="CWE-95",
                    ))

                self.generic_visit(node)

        visitor = SecurityVisitor(self)
        visitor.visit(tree)
        return findings

    def scan_directory(
        self,
        dir_path: str,
        extensions: Optional[List[str]] = None,
        max_files: int = 500,
    ) -> List[SecurityFinding]:
        """Recursively scans files in directory up to max_files."""
        findings: List[SecurityFinding] = []
        target_exts = set(extensions or [".py", ".js", ".ts", ".sh", ".json", ".yaml", ".yml"])
        count = 0

        for root, dirs, files in os.walk(dir_path):
            # Ignore VCS and venv directories
            dirs[:] = [d for d in dirs if d not in {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}]
            for fname in files:
                p = Path(root) / fname
                if p.suffix.lower() in target_exts:
                    file_findings = self.scan_file(str(p))
                    findings.extend(file_findings)
                    count += 1
                    if count >= max_files:
                        logger.warning(f"SAST scan hit maximum file limit of {max_files}")
                        return findings

        return findings

    def get_summary(self, findings: List[SecurityFinding]) -> Dict[str, Any]:
        """Aggregates findings into executive summary."""
        by_sev = {s.value: 0 for s in SecuritySeverity}
        by_cwe: Dict[str, int] = {}

        for f in findings:
            by_sev[f.severity.value] += 1
            by_cwe[f.cwe_id] = by_cwe.get(f.cwe_id, 0) + 1

        return {
            "total_findings": len(findings),
            "by_severity": by_sev,
            "by_cwe": by_cwe,
            "risk_status": "HIGH_RISK" if by_sev["CRITICAL"] > 0 or by_sev["HIGH"] > 2 else "MODERATE" if by_sev["MEDIUM"] > 0 else "CLEAN",
        }


# ============================================================================
# SCA Engine (Software Composition Analysis & SBOM)
# ============================================================================

class SCAEngine:
    """Software Composition Analysis, Vulnerability Auditing & CycloneDX/SPDX SBOM generation."""

    def __init__(self) -> None:
        self._known_advisories = self._load_advisory_database()

    def _load_advisory_database(self) -> Dict[str, List[Dict[str, Any]]]:
        """Built-in authoritative vulnerability signatures for common dependencies."""
        return {
            "urllib3": [
                {
                    "cve_id": "CVE-2023-43804",
                    "affected_lt": "1.26.18",
                    "severity": SecuritySeverity.HIGH,
                    "cvss_score": 7.5,
                    "title": "Cookie Leak on Cross-Origin Redirect",
                    "remediation": "Upgrade urllib3 >= 1.26.18 or >= 2.0.7",
                }
            ],
            "requests": [
                {
                    "cve_id": "CVE-2023-32681",
                    "affected_lt": "2.31.0",
                    "severity": SecuritySeverity.MEDIUM,
                    "cvss_score": 6.1,
                    "title": "Proxy-Authorization Header Leak",
                    "remediation": "Upgrade requests >= 2.31.0",
                }
            ],
            "cryptography": [
                {
                    "cve_id": "CVE-2023-49083",
                    "affected_lt": "41.0.6",
                    "severity": SecuritySeverity.HIGH,
                    "cvss_score": 7.5,
                    "title": "NULL Pointer Dereference in PKCS7 Loading",
                    "remediation": "Upgrade cryptography >= 41.0.6",
                }
            ],
            "werkzeug": [
                {
                    "cve_id": "CVE-2023-46136",
                    "affected_lt": "3.0.1",
                    "severity": SecuritySeverity.HIGH,
                    "cvss_score": 7.5,
                    "title": "High Resource Consumption via Large Multipart Form Data",
                    "remediation": "Upgrade werkzeug >= 3.0.1",
                }
            ],
            "lodash": [
                {
                    "cve_id": "CVE-2021-23337",
                    "affected_lt": "4.17.21",
                    "severity": SecuritySeverity.CRITICAL,
                    "cvss_score": 9.8,
                    "title": "Command Injection in template method",
                    "remediation": "Upgrade lodash >= 4.17.21",
                }
            ],
        }

    def parse_manifest(self, manifest_path: str) -> List[Dict[str, str]]:
        """Parses dependency manifests (requirements.txt, package.json, Cargo.toml)."""
        p = Path(manifest_path)
        if not p.is_file():
            return []

        text = p.read_text(encoding="utf-8", errors="replace")
        fname = p.name.lower()

        if fname == "requirements.txt" or fname.endswith("requirements.txt") or fname.endswith(".txt"):
            return self._parse_requirements_txt(text)
        elif fname == "package.json" or fname.endswith("package.json"):
            return self._parse_package_json(text)
        elif fname == "cargo.toml" or fname.endswith("cargo.toml"):
            return self._parse_cargo_toml(text)
        return []

    def _parse_requirements_txt(self, content: str) -> List[Dict[str, str]]:
        deps: List[Dict[str, str]] = []
        for line in content.splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#") or clean.startswith("-"):
                continue
            # Match package==1.2.3 or package>=1.2.3
            m = re.match(r"^([a-zA-Z0-9_\-\.]+)(?:[=><~]=?([0-9a-zA-Z\.\-]+))?", clean)
            if m:
                name = m.group(1).lower()
                ver = m.group(2) or "0.0.0"
                deps.append({"name": name, "version": ver, "ecosystem": "PyPI"})
        return deps

    def _parse_package_json(self, content: str) -> List[Dict[str, str]]:
        deps: List[Dict[str, str]] = []
        try:
            data = json.loads(content)
            merged = {}
            merged.update(data.get("dependencies", {}))
            merged.update(data.get("devDependencies", {}))
            for name, ver in merged.items():
                clean_ver = re.sub(r"[^0-9\.]", "", ver) or "0.0.0"
                deps.append({"name": name.lower(), "version": clean_ver, "ecosystem": "npm"})
        except Exception:
            pass
        return deps

    def _parse_cargo_toml(self, content: str) -> List[Dict[str, str]]:
        deps: List[Dict[str, str]] = []
        in_deps = False
        for line in content.splitlines():
            clean = line.strip()
            if clean.startswith("[dependencies]") or clean.startswith("[dev-dependencies]"):
                in_deps = True
                continue
            elif clean.startswith("[") and in_deps:
                in_deps = False
                continue
            if in_deps and "=" in clean:
                parts = clean.split("=", 1)
                name = parts[0].strip()
                val = parts[1].strip().strip('"').strip("'")
                clean_ver = re.sub(r"[^0-9\.]", "", val) or "0.0.0"
                deps.append({"name": name.lower(), "version": clean_ver, "ecosystem": "crates.io"})
        return deps

    def _version_lt(self, v1: str, v2: str) -> bool:
        """Determines if numeric version string v1 is less than v2."""
        try:
            p1 = [int(x) for x in re.findall(r"\d+", v1)]
            p2 = [int(x) for x in re.findall(r"\d+", v2)]
            while len(p1) < len(p2):
                p1.append(0)
            while len(p2) < len(p1):
                p2.append(0)
            return p1 < p2
        except Exception:
            return False

    def audit_dependencies(self, manifest_path: str) -> List[SecurityFinding]:
        """Audits manifest dependencies against the advisory database."""
        findings: List[SecurityFinding] = []
        deps = self.parse_manifest(manifest_path)

        for d in deps:
            name = d["name"]
            ver = d["version"]
            if name in self._known_advisories:
                for adv in self._known_advisories[name]:
                    if self._version_lt(ver, adv["affected_lt"]):
                        findings.append(SecurityFinding(
                            finding_id=f"SCA-{adv['cve_id']}-{name}",
                            rule_id="PRUBETH-SCA-001",
                            severity=adv["severity"],
                            title=f"{name} Vulnerability ({adv['cve_id']})",
                            description=f"{adv['title']}. Installed version {ver} is below {adv['affected_lt']}.",
                            file_path=manifest_path,
                            line_number=1,
                            code_snippet=f"{name}=={ver}",
                            remediation=adv["remediation"],
                            cwe_id="CWE-1395",
                            cve_id=adv["cve_id"],
                            cvss_score=adv["cvss_score"],
                        ))
        return findings

    def generate_cyclonedx_sbom(self, manifest_path: str, project_name: str = "prubeth-project") -> Dict[str, Any]:
        """Generates standard CycloneDX 1.5 JSON Software Bill of Materials."""
        deps = self.parse_manifest(manifest_path)
        components = []
        for d in deps:
            purl = f"pkg:{d['ecosystem'].lower()}/{d['name']}@{d['version']}"
            components.append({
                "type": "library",
                "name": d["name"],
                "version": d["version"],
                "purl": purl,
                "properties": [{"name": "ecosystem", "value": d["ecosystem"]}],
            })

        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:prubeth-sbom-{Path(manifest_path).stem}",
            "version": 1,
            "metadata": {
                "component": {
                    "type": "application",
                    "name": project_name,
                    "version": "1.0.0",
                }
            },
            "components": components,
        }

    def generate_spdx_sbom(self, manifest_path: str, project_name: str = "prubeth-project") -> Dict[str, Any]:
        """Generates standard SPDX 2.3 JSON Software Bill of Materials."""
        deps = self.parse_manifest(manifest_path)
        packages = []
        for idx, d in enumerate(deps, start=1):
            packages.append({
                "SPDXID": f"SPDXRef-Package-{d['name']}-{idx}",
                "name": d["name"],
                "versionInfo": d["version"],
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
            })

        return {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": "SPDXRef-DOCUMENT",
            "name": f"{project_name}-SPDX-SBOM",
            "packages": packages,
        }


# ============================================================================
# Singletons
# ============================================================================

_GLOBAL_SAST_ENGINE: Optional[SASTEngine] = None
_GLOBAL_SCA_ENGINE: Optional[SCAEngine] = None

def get_sast_engine() -> SASTEngine:
    global _GLOBAL_SAST_ENGINE
    if _GLOBAL_SAST_ENGINE is None:
        _GLOBAL_SAST_ENGINE = SASTEngine()
    return _GLOBAL_SAST_ENGINE

def get_sca_engine() -> SCAEngine:
    global _GLOBAL_SCA_ENGINE
    if _GLOBAL_SCA_ENGINE is None:
        _GLOBAL_SCA_ENGINE = SCAEngine()
    return _GLOBAL_SCA_ENGINE
