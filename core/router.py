"""
SO NAIVE IDE — Intelligent Agent Router & Policy Engine
Implements Small, Medium, Large agent profiles, deterministic routing constraints,
and task complexity classification.
"""
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

from core.model_registry import ModelRegistry, ModelCapability
from core.product_tier import (
    ProductTier,
    TierRestrictionError,
    is_model_allowed_for_tier,
    filter_models_for_tier,
    is_tool_allowed_for_tier,
    get_tier_spec
)


class AgentProfile(str, Enum):
    SMALL = "small"    # Fast, read-only inspection, symbols, explanations
    MEDIUM = "medium"  # Bounded multi-file editing, test execution, diff review
    LARGE = "large"    # Architecture, complex refactor, human approval gates


@dataclass
class PolicyConstraint:
    tier: ProductTier = ProductTier.PRO_HORIZON
    local_only: bool = False
    privacy_first: bool = False
    low_latency: bool = False
    quality_first: bool = True
    max_retries: int = 3
    timeout_seconds: int = 120


class IntelligentRouter:
    """Deterministic routing and policy engine selecting models and tool scopes."""

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry()

    def classify_task_profile(self, prompt: str, task_hint: Optional[str] = None) -> AgentProfile:
        p_lower = prompt.lower()
        if task_hint:
            if task_hint.lower() in ("small", "explain", "search", "lint"):
                return AgentProfile.SMALL
            elif task_hint.lower() in ("large", "architecture", "refactor"):
                return AgentProfile.LARGE

        # Pattern classification
        if any(w in p_lower for w in ["explain", "what does", "find symbol", "lint", "how does", "summarize"]):
            return AgentProfile.SMALL

        if any(w in p_lower for w in ["architect", "redesign", "full migration", "multi-module", "security audit"]):
            return AgentProfile.LARGE

        # Default for coding/editing/fixing
        return AgentProfile.MEDIUM

    def get_allowed_tools_for_profile(self, profile: AgentProfile, tier: Optional[ProductTier] = None) -> List[str]:
        if profile == AgentProfile.SMALL:
            base_tools = ["read_file", "list_files", "search_code", "web_search"]
        elif profile == AgentProfile.MEDIUM:
            base_tools = ["read_file", "write_file", "patch_file", "list_files", "search_code", "run_tests", "web_search"]
        else:  # LARGE
            base_tools = ["read_file", "write_file", "patch_file", "list_files", "search_code", "run_command", "run_tests", "call_mcp", "web_search"]

        if tier is not None:
            return [t for t in base_tools if is_tool_allowed_for_tier(tier, t)]
        return base_tools

    def build_execution_plan(
        self,
        prompt: str,
        policy: PolicyConstraint,
        explicit_provider: Optional[str] = None,
        explicit_model: Optional[str] = None
    ) -> Tuple[AgentProfile, List[ModelCapability], List[str]]:
        profile = self.classify_task_profile(prompt)
        allowed_tools = self.get_allowed_tools_for_profile(profile, tier=policy.tier)

        # Filter candidates based on policy constraints and tier capability bounds
        candidates: List[ModelCapability] = []

        if explicit_model and explicit_model != "Auto":
            mod = self.registry.get_model(explicit_model)
            if mod:
                if policy.local_only and not mod.is_local:
                    pass  # Reject remote model if local_only is enforced
                elif not is_model_allowed_for_tier(policy.tier, mod):
                    pass  # Reject model if restricted by tier
                else:
                    candidates.append(mod)

        # Get task-appropriate fallback chain
        task_category = "planning" if profile == AgentProfile.LARGE else "code_generation"
        for mod in self.registry.get_fallback_chain_for_task(task_category):
            if policy.local_only and not mod.is_local:
                continue
            if policy.privacy_first and mod.privacy_tier == "cloud_public":
                continue
            if not is_model_allowed_for_tier(policy.tier, mod):
                continue
            if mod not in candidates:
                candidates.append(mod)

        # Ensure we always have at least local fallback
        if not candidates:
            local_models = [
                m for m in self.registry.list_models(local_only=True)
                if is_model_allowed_for_tier(policy.tier, m)
            ]
            if local_models:
                candidates.extend(local_models)

        return profile, candidates, allowed_tools

    def route(
        self,
        prompt: str,
        profile: Optional[AgentProfile] = None,
        policy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Convenience method returning structured execution plan dictionary."""
        p_obj = PolicyConstraint()
        if policy:
            for k, v in policy.items():
                if k == "tier" and isinstance(v, str):
                    try:
                        p_obj.tier = ProductTier(v)
                    except ValueError:
                        pass
                elif hasattr(p_obj, k):
                    setattr(p_obj, k, v)

        assigned_profile = profile or self.classify_task_profile(prompt)
        allowed_tools = self.get_allowed_tools_for_profile(assigned_profile, tier=p_obj.tier)
        _, candidates, _ = self.build_execution_plan(prompt, p_obj)

        primary = candidates[0] if candidates else None
        return {
            "tier": p_obj.tier.value,
            "profile": assigned_profile,
            "primary_model": {
                "model_id": primary.model_id,
                "provider": primary.provider,
                "is_local": primary.is_local
            } if primary else None,
            "fallback_models": [
                {"model_id": m.model_id, "provider": m.provider, "is_local": m.is_local}
                for m in candidates[1:]
            ],
            "allowed_tools": allowed_tools
        }


AgentRouter = IntelligentRouter

