"""
PRUBETH IDE — Dynamic AI Model Registry & Capability Hub
Stores model capabilities, context limits, privacy classifications,
and per-task routing rules with non-secret export/import.
"""
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional


@dataclass
class ModelCapability:
    model_id: str
    provider: str
    display_name: str
    is_local: bool
    supports_streaming: bool = True
    supports_tools: bool = True
    supports_vision: bool = False
    supports_structured_output: bool = True
    context_window: int = 128000
    privacy_tier: str = "cloud_private"  # "local_offline", "cloud_private", "cloud_public"
    approx_latency_ms: float = 250.0
    last_tested_status: str = "untested"  # "verified", "untested", "failing"


class ModelRegistry:
    """Manages verified model capabilities, provider endpoints, and fallback chains."""

    DEFAULT_CATALOGUE = [
        ModelCapability(
            model_id="gemini-3.8-flash",
            provider="Google Gemini",
            display_name="Gemini 3.8 Flash (1M Context)",
            is_local=False,
            supports_streaming=True,
            supports_tools=True,
            supports_vision=True,
            supports_structured_output=True,
            context_window=1048576,
            privacy_tier="cloud_private",
            approx_latency_ms=180.0,
            last_tested_status="verified"
        ),
        ModelCapability(
            model_id="gemini-3.5-flash",
            provider="Google Gemini",
            display_name="Gemini 3.5 Flash (Cloud Speed)",
            is_local=False,
            supports_streaming=True,
            supports_tools=True,
            supports_vision=True,
            context_window=1048576,
            privacy_tier="cloud_private",
            approx_latency_ms=210.0,
            last_tested_status="verified"
        ),
        ModelCapability(
            model_id="qwen2.5:1.5b",
            provider="Ollama",
            display_name="Qwen 2.5 1.5B (Local CUDA GPU)",
            is_local=True,
            supports_streaming=True,
            supports_tools=True,
            supports_vision=False,
            context_window=32768,
            privacy_tier="local_offline",
            approx_latency_ms=35.0,
            last_tested_status="verified"
        ),
        ModelCapability(
            model_id="deepseek-r1:7b",
            provider="Ollama",
            display_name="DeepSeek R1 7B (Local Reasoning)",
            is_local=True,
            supports_streaming=True,
            supports_tools=False,
            supports_vision=False,
            context_window=32768,
            privacy_tier="local_offline",
            approx_latency_ms=90.0,
            last_tested_status="verified"
        ),
        ModelCapability(
            model_id="redsage-8b",
            provider="Ollama",
            display_name="RedSage 8B Cybersecurity (Local Unrestricted)",
            is_local=True,
            supports_streaming=True,
            supports_tools=True,
            supports_vision=False,
            context_window=8192,
            privacy_tier="local_offline",
            approx_latency_ms=75.0,
            last_tested_status="verified"
        ),
        ModelCapability(
            model_id="redsage-8b:latest",
            provider="Ollama",
            display_name="RedSage 8B Cybersecurity (Local Unrestricted)",
            is_local=True,
            supports_streaming=True,
            supports_tools=True,
            supports_vision=False,
            context_window=8192,
            privacy_tier="local_offline",
            approx_latency_ms=75.0,
            last_tested_status="verified"
        ),
        ModelCapability(
            model_id="gpt-4o",
            provider="OpenAI",
            display_name="GPT-4o Omnimodal",
            is_local=False,
            supports_streaming=True,
            supports_tools=True,
            supports_vision=True,
            context_window=128000,
            privacy_tier="cloud_private",
            approx_latency_ms=450.0,
            last_tested_status="verified"
        ),
        ModelCapability(
            model_id="claude-3-7-sonnet-20250219",
            provider="Anthropic Claude",
            display_name="Claude 3.7 Sonnet (Extended Reasoning)",
            is_local=False,
            supports_streaming=True,
            supports_tools=True,
            supports_vision=True,
            context_window=200000,
            privacy_tier="cloud_private",
            approx_latency_ms=600.0,
            last_tested_status="verified"
        ),
        ModelCapability(
            model_id="llama-3.3-70b-versatile",
            provider="Groq",
            display_name="Llama 3.3 70B (300 tok/s)",
            is_local=False,
            supports_streaming=True,
            supports_tools=True,
            supports_vision=False,
            context_window=128000,
            privacy_tier="cloud_private",
            approx_latency_ms=80.0,
            last_tested_status="verified"
        )
    ]

    DEFAULT_TASK_FALLBACKS = {
        "code_generation": ["gemini-3.8-flash", "qwen2.5:1.5b", "redsage-8b", "gpt-4o"],
        "quick_edit": ["gemini-3.8-flash", "qwen2.5:1.5b", "llama-3.3-70b-versatile"],
        "fast_chat": ["qwen2.5:1.5b", "redsage-8b", "gemini-3.8-flash", "llama-3.3-70b-versatile"],
        "planning": ["claude-3-7-sonnet-20250219", "gemini-3.8-flash", "deepseek-r1:7b", "redsage-8b"],
        "troubleshooting": ["gemini-3.8-flash", "redsage-8b", "qwen2.5:1.5b", "gpt-4o"]
    }

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            self.config_dir = Path.home() / ".local_ai_studio_pro"
        else:
            self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.config_dir / "model_registry.json"
        self._models: Dict[str, ModelCapability] = {}
        self.task_fallbacks: Dict[str, List[str]] = dict(self.DEFAULT_TASK_FALLBACKS)
        self._load()

    def _load(self):
        # Load defaults first
        for m in self.DEFAULT_CATALOGUE:
            self._models[m.model_id] = m

        if self.registry_file.exists():
            try:
                data = json.loads(self.registry_file.read_text(encoding="utf-8"))
                for item in data.get("models", []):
                    cap = ModelCapability(**item)
                    self._models[cap.model_id] = cap
                if "task_fallbacks" in data:
                    self.task_fallbacks.update(data["task_fallbacks"])
            except Exception:
                pass

    def save(self):
        data = {
            "models": [asdict(m) for m in self._models.values()],
            "task_fallbacks": self.task_fallbacks
        }
        self.registry_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def register_model(self, capability: ModelCapability):
        self._models[capability.model_id] = capability
        self.save()

    def get_model(self, model_id: str) -> Optional[ModelCapability]:
        return self._models.get(model_id)

    def list_models(
        self,
        local_only: bool = False,
        requires_tools: bool = False,
        requires_vision: bool = False
    ) -> List[ModelCapability]:
        matches = []
        for m in self._models.values():
            if local_only and not m.is_local:
                continue
            if requires_tools and not m.supports_tools:
                continue
            if requires_vision and not m.supports_vision:
                continue
            matches.append(m)
        return sorted(matches, key=lambda x: (not x.is_local, x.provider, x.model_id))

    def get_fallback_chain_for_task(self, task_type: str) -> List[ModelCapability]:
        model_ids = self.task_fallbacks.get(task_type, self.task_fallbacks.get("code_generation", []))
        chain = []
        for mid in model_ids:
            if mid in self._models:
                chain.append(self._models[mid])
        return chain

    def export_non_secret_config(self) -> str:
        """Exports models and fallback policies with zero secret data."""
        data = {
            "models": [asdict(m) for m in self._models.values()],
            "task_fallbacks": self.task_fallbacks
        }
        return json.dumps(data, indent=2)
