"""
PRUBETH IDE — Secure Credentials & Secret Redaction Engine
Provides Windows DPAPI-backed encryption (with AES-GCM fallback),
idempotent legacy settings migration, secret masking, and log/traceback redaction.
"""
import os
import sys
import json
import re
import base64
import ctypes
import ctypes.wintypes
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# DPAPI Structures for Windows
class _DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ('cbData', ctypes.wintypes.DWORD),
        ('pbData', ctypes.POINTER(ctypes.c_byte))
    ]


class DPAPIEncryptionProvider:
    """Uses Windows Data Protection API (CryptProtectData / CryptUnprotectData)."""

    @classmethod
    def is_available(cls) -> bool:
        return sys.platform == "win32" and hasattr(ctypes, 'windll') and hasattr(ctypes.windll, 'crypt32')

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        if not plaintext:
            return ""
        data_bytes = plaintext.encode('utf-8')
        in_blob = _DATA_BLOB(len(data_bytes), ctypes.cast(ctypes.c_char_p(data_bytes), ctypes.POINTER(ctypes.c_byte)))
        out_blob = _DATA_BLOB()

        # CryptProtectData(pDataIn, szDataDescr, pOptionalEntropy, pvReserved, pPromptStruct, dwFlags, pDataOut)
        # dwFlags = 1 (CRYPTPROTECT_UI_FORBIDDEN)
        res = ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(in_blob),
            "SoNaiveCredential",
            None,
            None,
            None,
            1,
            ctypes.byref(out_blob)
        )
        if not res:
            raise RuntimeError(f"DPAPI CryptProtectData failed with error code: {ctypes.GetLastError()}")

        try:
            encrypted_bytes = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            return "dpapi:" + base64.b64encode(encrypted_bytes).decode('ascii')
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        if not ciphertext.startswith("dpapi:"):
            raise ValueError("Ciphertext does not have DPAPI prefix")

        raw_b64 = ciphertext[len("dpapi:"):]
        encrypted_bytes = base64.b64decode(raw_b64)
        in_blob = _DATA_BLOB(len(encrypted_bytes), ctypes.cast(ctypes.c_char_p(encrypted_bytes), ctypes.POINTER(ctypes.c_byte)))
        out_blob = _DATA_BLOB()

        res = ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(in_blob),
            None,
            None,
            None,
            None,
            1,
            ctypes.byref(out_blob)
        )
        if not res:
            raise RuntimeError(f"DPAPI CryptUnprotectData failed with error code: {ctypes.GetLastError()}")

        try:
            decrypted_bytes = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            return decrypted_bytes.decode('utf-8')
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)


class CryptographyFallbackProvider:
    """Fallback AES encryption when DPAPI is not available."""

    @classmethod
    def _get_key(cls) -> bytes:
        # Derive machine/user bound key
        seed = f"{os.environ.get('USERNAME', 'user')}-{os.environ.get('COMPUTERNAME', 'machine')}-SoNaiveIDE"
        return base64.urlsafe_b64encode(hashlib.sha256(seed.encode('utf-8')).digest())

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        if not plaintext:
            return ""
        try:
            from cryptography.fernet import Fernet
            f = Fernet(cls._get_key())
            token = f.encrypt(plaintext.encode('utf-8'))
            return "fernet:" + token.decode('ascii')
        except Exception:
            # Simple reversible obfuscation only if cryptography not importable
            encoded = base64.b64encode(plaintext.encode('utf-8')).decode('ascii')
            return "b64:" + encoded

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        if ciphertext.startswith("fernet:"):
            from cryptography.fernet import Fernet
            f = Fernet(cls._get_key())
            return f.decrypt(ciphertext[len("fernet:"):].encode('ascii')).decode('utf-8')
        elif ciphertext.startswith("b64:"):
            return base64.b64decode(ciphertext[len("b64:"):].encode('ascii')).decode('utf-8')
        return ciphertext


class SecretRedactor:
    """Sanitizes sensitive tokens, API keys, and passwords from logs, tracebacks, and dialogs."""

    SECRET_PATTERNS = [
        re.compile(r'(sk-[A-Za-z0-9_-]{20,})'),
        re.compile(r'(AQ[A-Za-z0-9_-]{20,})'),
        re.compile(r'(ghp_[A-Za-z0-9]{30,})'),
        re.compile(r'(github_pat_[A-Za-z0-9_]{30,})'),
        re.compile(r'(Bearer\s+[A-Za-z0-9._\-]{20,})', re.IGNORECASE),
        re.compile(r'("?(?:api[_-]?key|secret|password|access[_-]?token)"?\s*[:=]\s*"?[A-Za-z0-9_\-\.]{12,}"?)', re.IGNORECASE),
    ]

    def __init__(self):
        self._exact_secrets = set()

    def register_secret(self, secret: str):
        if secret and len(secret) >= 8:
            self._exact_secrets.add(secret)

    def redact(self, text: str) -> str:
        if not text:
            return ""
        result = str(text)
        # Redact registered exact values
        for sec in self._exact_secrets:
            if sec in result:
                masked = sec[:3] + "..." + sec[-3:] if len(sec) > 8 else "***REDACTED***"
                result = result.replace(sec, masked)

        # Apply regex pattern masks
        for pattern in self.SECRET_PATTERNS:
            result = pattern.sub("[***REDACTED_SECRET***]", result)

        return result

    def redact_exception(self, exc: Exception) -> str:
        msg = f"{type(exc).__name__}: {str(exc)}"
        return self.redact(msg)


class CredentialStore:
    """Centralized, encrypted credential repository."""

    KNOWN_SECRET_KEYS = {
        "gemini_api_key",
        "navy_api_key",
        "openai_api_key",
        "claude_api_key",
        "deepseek_api_key",
        "groq_api_key",
        "github_token",
        "hf_token",
    }

    def __init__(self, store_dir: Optional[Path] = None):
        if store_dir is None:
            self.store_dir = Path.home() / ".local_ai_studio_pro"
        else:
            self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.store_dir / "credentials.enc"
        self.redactor = SecretRedactor()
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _encrypt(self, plaintext: str) -> str:
        if DPAPIEncryptionProvider.is_available():
            try:
                return DPAPIEncryptionProvider.encrypt(plaintext)
            except Exception:
                pass
        return CryptographyFallbackProvider.encrypt(plaintext)

    def _decrypt(self, ciphertext: str) -> str:
        if ciphertext.startswith("dpapi:"):
            if DPAPIEncryptionProvider.is_available():
                return DPAPIEncryptionProvider.decrypt(ciphertext)
            raise RuntimeError("DPAPI ciphertext encountered on a platform without DPAPI support.")
        return CryptographyFallbackProvider.decrypt(ciphertext)

    def _load(self):
        if not self.store_file.exists():
            self._cache = {}
            return
        try:
            data = json.loads(self.store_file.read_text(encoding="utf-8"))
            self._cache = data
            # Register loaded secrets into redactor
            for k, entry in self._cache.items():
                cipher = entry.get("ciphertext", "")
                try:
                    plain = self._decrypt(cipher)
                    self.redactor.register_secret(plain)
                except Exception:
                    pass
        except Exception:
            self._cache = {}

    def _save(self):
        tmp_file = self.store_file.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(self._cache, indent=2), encoding="utf-8")
        tmp_file.replace(self.store_file)

    def set_secret(self, key_id: str, secret_val: str, provider: str = "general", endpoint: Optional[str] = None):
        if not key_id:
            raise ValueError("key_id cannot be empty")
        if not secret_val:
            self.delete_secret(key_id)
            return

        ciphertext = self._encrypt(secret_val)
        self._cache[key_id] = {
            "ciphertext": ciphertext,
            "provider": provider,
            "endpoint": endpoint or "*",
            "masked_preview": secret_val[:3] + "..." + secret_val[-3:] if len(secret_val) > 6 else "***"
        }
        self.redactor.register_secret(secret_val)
        self._save()

    def get_secret(self, key_id: str, default: str = "") -> str:
        entry = self._cache.get(key_id)
        if not entry:
            return default
        ciphertext = entry.get("ciphertext", "")
        if not ciphertext:
            return default
        try:
            return self._decrypt(ciphertext)
        except Exception as e:
            return default

    def delete_secret(self, key_id: str):
        if key_id in self._cache:
            del self._cache[key_id]
            self._save()

    def list_secrets(self) -> List[Dict[str, Any]]:
        results = []
        for key_id, entry in self._cache.items():
            results.append({
                "key_id": key_id,
                "provider": entry.get("provider", "general"),
                "endpoint": entry.get("endpoint", "*"),
                "masked_preview": entry.get("masked_preview", "***")
            })
        return sorted(results, key=lambda x: x["key_id"])

    def migrate_legacy_settings(self, settings_path: Optional[Path] = None, accounts_path: Optional[Path] = None) -> int:
        """Idempotently discovers plaintext secrets, saves them to encrypted store, and sanitizes configs."""
        migrated_count = 0
        settings_p = Path(settings_path) if settings_path else (self.store_dir / "settings.json")
        accounts_p = Path(accounts_path) if accounts_path else (self.store_dir / "accounts.json")

        # Migrate settings.json
        if settings_p.exists() and settings_p.is_file():
            try:
                settings_data = json.loads(settings_p.read_text(encoding="utf-8"))
                dirty = False
                for k in list(settings_data.keys()):
                    if k in self.KNOWN_SECRET_KEYS:
                        val = settings_data[k]
                        if val and isinstance(val, str) and not val.startswith("dpapi:") and not val.startswith("fernet:"):
                            self.set_secret(k, val, provider=k.replace("_api_key", ""))
                            migrated_count += 1
                            # Replace with secure reference marker
                            settings_data[k] = "__SECURE_STORE__"
                            dirty = True
                if dirty:
                    settings_p.write_text(json.dumps(settings_data, indent=2), encoding="utf-8")
            except Exception:
                pass

        # Migrate accounts.json
        if accounts_p.exists() and accounts_p.is_file():
            try:
                accounts_data = json.loads(accounts_p.read_text(encoding="utf-8"))
                dirty = False
                for k in ["github_token", "hf_token"]:
                    if k in accounts_data:
                        val = accounts_data[k]
                        if val and isinstance(val, str) and not val.startswith("dpapi:") and not val.startswith("fernet:"):
                            self.set_secret(k, val, provider=k.split("_")[0])
                            migrated_count += 1
                            accounts_data[k] = "__SECURE_STORE__"
                            dirty = True
                if dirty:
                    accounts_p.write_text(json.dumps(accounts_data, indent=2), encoding="utf-8")
            except Exception:
                pass

        return migrated_count


# Module Singleton Provider
_GLOBAL_STORE: Optional[CredentialStore] = None

def get_credential_store() -> CredentialStore:
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = CredentialStore()
    return _GLOBAL_STORE

def get_secret_redactor() -> SecretRedactor:
    return get_credential_store().redactor
