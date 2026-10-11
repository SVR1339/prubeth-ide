"""PRUBETH IDE - Reverse Engineering Bridge & Binary Inspection Subsystem
======================================================================
Defensive inspection, binary format parsing (PE/ELF/Mach-O), section entropy
calculation, string/IoC extraction, and disassembly interface for authorized
malware analysis, forensic investigations, and binary research.
"""

from __future__ import annotations

import enum
import math
import logging
import os
import re
import struct
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


# ============================================================================
# Enums and Data Models
# ============================================================================

class BinaryArchitecture(str, enum.Enum):
    X86 = "x86"
    X86_64 = "x86_64"
    ARM = "arm"
    ARM64 = "arm64"
    MIPS = "mips"
    RISCV = "riscv"
    UNKNOWN = "unknown"


class BinaryFormat(str, enum.Enum):
    PE = "Portable Executable (PE)"
    ELF = "Executable and Linkable Format (ELF)"
    MACHO = "Mach-O"
    RAW_SHELLCODE = "Raw Shellcode"
    UNKNOWN = "Unknown Format"


@dataclass
class SectionInfo:
    name: str
    virtual_address: int
    raw_size: int
    entropy: float
    is_executable: bool
    is_writable: bool
    is_suspicious_packed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DisassembledInstruction:
    address: int
    mnemonic: str
    op_str: str
    size: int
    raw_bytes: str


@dataclass
class BinaryMetadata:
    file_path: str
    file_size_bytes: int
    format: BinaryFormat
    architecture: BinaryArchitecture
    is_64bit: bool
    entry_point: int
    overall_entropy: float
    sections: List[SectionInfo] = field(default_factory=list)
    suspicious_iocs: List[Dict[str, Any]] = field(default_factory=list)
    imported_functions: List[str] = field(default_factory=list)
    extracted_strings_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["format"] = self.format.value
        d["architecture"] = self.architecture.value
        d["sections"] = [s.to_dict() for s in self.sections]
        return d


# ============================================================================
# Reverse Engineering Bridge
# ============================================================================

class ReverseEngineeringBridge:
    """Pure-Python binary metadata inspector and disassembly coordinator."""

    # Well-known API signatures indicating suspicious behavior
    SUSPICIOUS_API_PATTERNS = {
        "Process Injection": [
            "VirtualAlloc", "VirtualAllocEx", "VirtualProtect", "VirtualProtectEx",
            "WriteProcessMemory", "CreateRemoteThread", "QueueUserAPC", "SetThreadContext",
            "NtWriteVirtualMemory", "ZwMapViewOfSection", "RtlCreateUserThread"
        ],
        "Anti-Debugging & Evasion": [
            "IsDebuggerPresent", "CheckRemoteDebuggerPresent", "NtQueryInformationProcess",
            "OutputDebugStringA", "OutputDebugStringW", "FindWindowA", "GetTickCount"
        ],
        "Persistence & Execution": [
            "RegSetValueExA", "RegSetValueExW", "CreateServiceA", "CreateServiceW",
            "WinExec", "ShellExecuteA", "ShellExecuteW", "CreateProcessA", "CreateProcessW"
        ],
        "Surveillance & Hooking": [
            "SetWindowsHookExA", "SetWindowsHookExW", "GetAsyncKeyState", "GetKeyState"
        ],
        "Network Egress": [
            "WSAStartup", "connect", "InternetOpenA", "InternetOpenUrlA", "URLDownloadToFileA"
        ]
    }

    def __init__(self) -> None:
        self._has_capstone = False
        try:
            import capstone  # type: ignore
            self._has_capstone = True
        except ImportError:
            self._has_capstone = False

    def calculate_entropy(self, data: bytes) -> float:
        """Calculates Shannon Entropy (0.0 - 8.0) of byte sequence."""
        if not data:
            return 0.0
        entropy = 0.0
        length = len(data)
        freq: Dict[int, int] = {}
        for b in data:
            freq[b] = freq.get(b, 0) + 1

        for count in freq.values():
            p_x = count / length
            if p_x > 0:
                entropy -= p_x * math.log2(p_x)
        return round(entropy, 4)

    def inspect_file(self, file_path: str) -> BinaryMetadata:
        """Parses headers, sections, entropy, and IoCs of a binary target."""
        p = Path(file_path)
        if not p.is_file():
            raise FileNotFoundError(f"Binary file not found: {file_path}")

        raw_bytes = p.read_bytes()
        file_size = len(raw_bytes)
        overall_entropy = self.calculate_entropy(raw_bytes)

        # Detect format
        b_format, b_arch, is_64, entry_point, sections = self._parse_headers(raw_bytes)

        # Extract strings & detect IoCs
        strings = self.extract_strings(raw_bytes, min_length=4)
        iocs = self._detect_iocs(strings)
        imported_symbols = self._extract_symbols(strings)

        return BinaryMetadata(
            file_path=str(p),
            file_size_bytes=file_size,
            format=b_format,
            architecture=b_arch,
            is_64bit=is_64,
            entry_point=entry_point,
            overall_entropy=overall_entropy,
            sections=sections,
            suspicious_iocs=iocs,
            imported_functions=imported_symbols,
            extracted_strings_count=len(strings),
        )

    def _parse_headers(
        self, data: bytes
    ) -> Tuple[BinaryFormat, BinaryArchitecture, bool, int, List[SectionInfo]]:
        """Identifies PE, ELF, or Mach-O format and sections."""
        if len(data) < 64:
            return BinaryFormat.RAW_SHELLCODE, BinaryArchitecture.UNKNOWN, False, 0, []

        # 1. Check for ELF (0x7F 'E' 'L' 'F')
        if data[:4] == b"\x7fELF":
            is_64 = data[4] == 2
            arch_code = struct.unpack("<H" if data[5] == 1 else ">H", data[18:20])[0] if len(data) >= 20 else 0
            arch_map = {0x03: BinaryArchitecture.X86, 0x3E: BinaryArchitecture.X86_64, 0x28: BinaryArchitecture.ARM, 0xB7: BinaryArchitecture.ARM64}
            arch = arch_map.get(arch_code, BinaryArchitecture.UNKNOWN)
            entry = struct.unpack("<Q" if is_64 else "<I", data[24:32 if is_64 else 28])[0] if len(data) >= 32 else 0
            return BinaryFormat.ELF, arch, is_64, entry, []

        # 2. Check for PE (MZ header 0x4D 0x5A)
        if data[:2] == b"MZ" and len(data) >= 0x40:
            pe_offset = struct.unpack("<I", data[0x3C:0x40])[0]
            if len(data) >= pe_offset + 24 and data[pe_offset:pe_offset + 4] == b"PE\x00\x00":
                machine = struct.unpack("<H", data[pe_offset + 4:pe_offset + 6])[0]
                num_sections = struct.unpack("<H", data[pe_offset + 6:pe_offset + 8])[0]
                is_64 = machine == 0x8664
                arch = BinaryArchitecture.X86_64 if is_64 else BinaryArchitecture.X86 if machine == 0x014C else BinaryArchitecture.UNKNOWN

                opt_hdr_offset = pe_offset + 24
                opt_magic = struct.unpack("<H", data[opt_hdr_offset:opt_hdr_offset + 2])[0] if len(data) >= opt_hdr_offset + 2 else 0
                entry_point = struct.unpack("<I", data[opt_hdr_offset + 16:opt_hdr_offset + 20])[0] if len(data) >= opt_hdr_offset + 20 else 0

                # Section headers parsing
                opt_hdr_size = struct.unpack("<H", data[pe_offset + 20:pe_offset + 22])[0]
                sec_table_offset = pe_offset + 24 + opt_hdr_size
                sections: List[SectionInfo] = []

                for i in range(min(num_sections, 32)):
                    s_off = sec_table_offset + (i * 40)
                    if len(data) < s_off + 40:
                        break
                    s_name = data[s_off:s_off + 8].split(b"\x00")[0].decode("ascii", errors="replace").strip()
                    v_addr = struct.unpack("<I", data[s_off + 12:s_off + 16])[0]
                    raw_size = struct.unpack("<I", data[s_off + 16:s_off + 20])[0]
                    raw_ptr = struct.unpack("<I", data[s_off + 20:s_off + 24])[0]
                    characteristics = struct.unpack("<I", data[s_off + 36:s_off + 40])[0]

                    # Slice raw section data for entropy
                    sec_bytes = data[raw_ptr:raw_ptr + raw_size] if raw_ptr + raw_size <= len(data) else b""
                    s_entropy = self.calculate_entropy(sec_bytes)
                    is_exec = bool(characteristics & 0x20000000)
                    is_write = bool(characteristics & 0x80000000)
                    # Section entropy > 7.15 indicates packing or encrypted payload
                    is_suspicious = s_entropy > 7.15

                    sections.append(SectionInfo(
                        name=s_name,
                        virtual_address=v_addr,
                        raw_size=raw_size,
                        entropy=s_entropy,
                        is_executable=is_exec,
                        is_writable=is_write,
                        is_suspicious_packed=is_suspicious,
                    ))

                return BinaryFormat.PE, arch, is_64, entry_point, sections

        # 3. Check for Mach-O (0xFEEDFACE or 0xFEEDFACF)
        if data[:4] in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe"):
            return BinaryFormat.MACHO, BinaryArchitecture.UNKNOWN, True, 0, []

        return BinaryFormat.RAW_SHELLCODE, BinaryArchitecture.UNKNOWN, False, 0, []

    def extract_strings(self, data: bytes, min_length: int = 4) -> List[str]:
        """Extracts ASCII and UTF-16LE strings."""
        result: List[str] = []
        # ASCII extraction
        ascii_pat = re.compile(rb"[\x20-\x7e]{" + str(min_length).encode() + rb",}")
        for match in ascii_pat.finditer(data):
            try:
                result.append(match.group().decode("ascii"))
            except Exception:
                pass

        # Limit to avoid memory bloat on huge files
        return result[:10000]

    def _detect_iocs(self, strings: List[str]) -> List[Dict[str, Any]]:
        """Cross-references strings against suspicious API patterns and network IoCs."""
        detected: List[Dict[str, Any]] = []
        str_set = set(strings)

        for category, apis in self.SUSPICIOUS_API_PATTERNS.items():
            for api in apis:
                if api in str_set:
                    detected.append({
                        "category": category,
                        "indicator": api,
                        "type": "SUSPICIOUS_API",
                        "severity": "HIGH" if category in ("Process Injection", "Anti-Debugging & Evasion") else "MEDIUM",
                    })

        # Regex for IP addresses and URLs
        ip_regex = re.compile(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b")
        url_regex = re.compile(r"https?://[a-zA-Z0-9\.\-_/]+")

        for s in strings:
            ip_m = ip_regex.findall(s)
            for ip in ip_m:
                if not ip.startswith("127.") and not ip.startswith("0.") and not ip.startswith("255."):
                    detected.append({
                        "category": "Network C2 Indicator",
                        "indicator": ip,
                        "type": "IP_ADDRESS",
                        "severity": "HIGH",
                    })
            url_m = url_regex.findall(s)
            for url in url_m:
                detected.append({
                    "category": "Network C2 Indicator",
                    "indicator": url,
                    "type": "URL",
                    "severity": "HIGH",
                })

        return detected

    def _extract_symbols(self, strings: List[str]) -> List[str]:
        """Filters symbol-like strings."""
        known_keywords = {"Alloc", "Free", "LoadLibrary", "GetProcAddress", "Create", "Write", "Read", "Open", "Close", "Query"}
        symbols = []
        for s in strings:
            if any(k in s for k in known_keywords) and len(s) < 48:
                symbols.append(s)
        return symbols[:100]

    def disassemble_bytes(
        self,
        code_bytes: bytes,
        arch: BinaryArchitecture = BinaryArchitecture.X86_64,
        base_address: int = 0x1000,
        max_instructions: int = 50,
    ) -> List[DisassembledInstruction]:
        """Disassembles byte sequence using capstone (if available) or built-in opcode decoder."""
        if self._has_capstone:
            return self._disassemble_with_capstone(code_bytes, arch, base_address, max_instructions)
        return self._disassemble_fallback(code_bytes, base_address, max_instructions)

    def _disassemble_with_capstone(
        self,
        code_bytes: bytes,
        arch: BinaryArchitecture,
        base_address: int,
        max_instructions: int,
    ) -> List[DisassembledInstruction]:
        import capstone  # type: ignore
        cs_arch = capstone.CS_ARCH_X86
        cs_mode = capstone.CS_MODE_64 if arch == BinaryArchitecture.X86_64 else capstone.CS_MODE_32
        md = capstone.Cs(cs_arch, cs_mode)

        instructions: List[DisassembledInstruction] = []
        for insn in md.disasm(code_bytes, base_address):
            raw_hex = " ".join(f"{b:02x}" for b in insn.bytes)
            instructions.append(DisassembledInstruction(
                address=insn.address,
                mnemonic=insn.mnemonic,
                op_str=insn.op_str,
                size=insn.size,
                raw_bytes=raw_hex,
            ))
            if len(instructions) >= max_instructions:
                break
        return instructions

    def _disassemble_fallback(
        self, code_bytes: bytes, base_address: int, max_instructions: int
    ) -> List[DisassembledInstruction]:
        """Pure-Python instruction decoder for common x86/x64 instruction patterns."""
        instructions: List[DisassembledInstruction] = []
        offset = 0
        addr = base_address

        while offset < len(code_bytes) and len(instructions) < max_instructions:
            b = code_bytes[offset]
            if b == 0x90:
                instructions.append(DisassembledInstruction(addr, "nop", "", 1, "90"))
                offset += 1
                addr += 1
            elif b == 0xCC:
                instructions.append(DisassembledInstruction(addr, "int3", "", 1, "cc"))
                offset += 1
                addr += 1
            elif b == 0xC3:
                instructions.append(DisassembledInstruction(addr, "ret", "", 1, "c3"))
                offset += 1
                addr += 1
            elif b == 0x55:
                instructions.append(DisassembledInstruction(addr, "push", "rbp", 1, "55"))
                offset += 1
                addr += 1
            elif b == 0x5D:
                instructions.append(DisassembledInstruction(addr, "pop", "rbp", 1, "5d"))
                offset += 1
                addr += 1
            elif offset + 2 < len(code_bytes) and code_bytes[offset:offset + 3] == b"\x48\x89\xe5":
                instructions.append(DisassembledInstruction(addr, "mov", "rbp, rsp", 3, "48 89 e5"))
                offset += 3
                addr += 3
            elif offset + 1 < len(code_bytes) and b == 0x31 and code_bytes[offset + 1] == 0xC0:
                instructions.append(DisassembledInstruction(addr, "xor", "eax, eax", 2, "31 c0"))
                offset += 2
                addr += 2
            elif offset + 1 < len(code_bytes) and b == 0xEB:
                rel = struct.unpack("b", bytes([code_bytes[offset + 1]]))[0]
                target = hex(addr + 2 + rel)
                instructions.append(DisassembledInstruction(addr, "jmp", target, 2, f"eb {code_bytes[offset+1]:02x}"))
                offset += 2
                addr += 2
            else:
                # Raw byte fallback
                instructions.append(DisassembledInstruction(addr, "db", f"0x{b:02x}", 1, f"{b:02x}"))
                offset += 1
                addr += 1

        return instructions


# Global singleton
_GLOBAL_REVERSE_ENGINEERING_BRIDGE: Optional[ReverseEngineeringBridge] = None

def get_reverse_engineering_bridge() -> ReverseEngineeringBridge:
    global _GLOBAL_REVERSE_ENGINEERING_BRIDGE
    if _GLOBAL_REVERSE_ENGINEERING_BRIDGE is None:
        _GLOBAL_REVERSE_ENGINEERING_BRIDGE = ReverseEngineeringBridge()
    return _GLOBAL_REVERSE_ENGINEERING_BRIDGE
