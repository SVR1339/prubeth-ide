"""
SUKHI IDE — Three-Tier Product Architecture & Capability Gating
Defines capability envelopes, quota limits, model permissions, and tool restrictions
for Free Community, Pro Horizon, and Frontier Pro Max tiers.
"""
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Set, Optional

from core.model_registry import ModelCapability


class ProductTier(str, Enum):
    FREE_COMMUNITY = "free_community"   # Local models, offline privacy, core editing & tests
    PRO_HORIZON = "pro_horizon"         # Fast cloud models (Gemini Flash, Groq), multi-agent, MCP
    FRONTIER_PRO_MAX = "frontier_pro_max" # Frontier reasoning (Claude Sonnet, GPT-4o), full DAG teams


class TierRestrictionError(PermissionError):
    """Raised when an operation, model, or tool exceeds the active tier entitlement."""
    pass


@dataclass
class TierSpecification:
    tier: ProductTier
    display_name: str
    max_context_window: int
    allow_cloud_models: bool
    allow_frontier_models: bool
    allowed_privacy_tiers: Set[str]
    allowed_agent_archetypes: Set[str]
    allowed_tools: Set[str]
    max_workspace_bytes: int = 500 * 1024 * 1024  # Default 500MB
    max_file_size_bytes: int = 10 * 1024 * 1024   # Default 10MB


TIER_SPECS: Dict[ProductTier, TierSpecification] = {
    ProductTier.FREE_COMMUNITY: TierSpecification(
        tier=ProductTier.FREE_COMMUNITY,
        display_name="Free Community Edition",
        max_context_window=32768,
        allow_cloud_models=False,
        allow_frontier_models=False,
        allowed_privacy_tiers={"local_offline"},
        allowed_agent_archetypes={"PLANNER", "CODER", "TESTER"},
        allowed_tools={
            "read_file", "write_file", "patch_file", "list_files",
            "search_code", "run_tests", "create_checkpoint", "rollback_checkpoint"
        },
        max_workspace_bytes=100 * 1024 * 1024,
        max_file_size_bytes=5 * 1024 * 1024
    ),
    ProductTier.PRO_HORIZON: TierSpecification(
        tier=ProductTier.PRO_HORIZON,
        display_name="Pro Horizon Edition",
        max_context_window=1048576,
        allow_cloud_models=True,
        allow_frontier_models=False,
        allowed_privacy_tiers={"local_offline", "cloud_private"},
        allowed_agent_archetypes={
            "PLANNER", "RESEARCHER", "CODER", "TESTER", "REVIEWER", "DEBUGGER"
        },
        allowed_tools={
            "read_file", "write_file", "patch_file", "list_files",
            "search_code", "semantic_search", "run_tests", "run_command",
            "call_mcp", "web_search", "create_checkpoint", "rollback_checkpoint"
        },
        max_workspace_bytes=1024 * 1024 * 1024,
        max_file_size_bytes=50 * 1024 * 1024
    ),
    ProductTier.FRONTIER_PRO_MAX: TierSpecification(
        tier=ProductTier.FRONTIER_PRO_MAX,
        display_name="Frontier Pro Max Edition",
        max_context_window=2000000,
        allow_cloud_models=True,
        allow_frontier_models=True,
        allowed_privacy_tiers={"local_offline", "cloud_private", "cloud_public"},
        allowed_agent_archetypes={
            "PLANNER", "RESEARCHER", "CODER", "TESTER", "REVIEWER",
            "DEBUGGER", "RELEASE", "ARCHITECT", "CRITIC", "WORK", "CODEX", "DOTS"
        },
        allowed_tools={
            "read_file", "write_file", "patch_file", "list_files",
            "search_code", "semantic_search", "run_tests", "run_command",
            "call_mcp", "web_search", "create_checkpoint", "rollback_checkpoint"
        },
        max_workspace_bytes=10 * 1024 * 1024 * 1024,
        max_file_size_bytes=200 * 1024 * 1024
    )
}

# Frontier-grade models requiring FRONTIER_PRO_MAX
FRONTIER_MODEL_IDS: Set[str] = {
    "claude-3-7-sonnet-20250219",
    "gpt-4o",
    "o1",
    "o3-mini"
}


def get_tier_spec(tier: ProductTier) -> TierSpecification:
    """Returns the TierSpecification for the given product tier."""
    if tier not in TIER_SPECS:
        return TIER_SPECS[ProductTier.PRO_HORIZON]
    return TIER_SPECS[tier]


def is_model_allowed_for_tier(tier: ProductTier, model: ModelCapability) -> bool:
    """Evaluates whether a model is permitted under the specified tier."""
    spec = get_tier_spec(tier)

    # Free Community restricts all non-local models
    if not spec.allow_cloud_models and not model.is_local:
        return False

    # Privacy tier check
    if model.privacy_tier not in spec.allowed_privacy_tiers:
        return False

    # Frontier models require FRONTIER_PRO_MAX
    if model.model_id in FRONTIER_MODEL_IDS and not spec.allow_frontier_models:
        return False

    return True


def filter_models_for_tier(tier: ProductTier, models: List[ModelCapability]) -> List[ModelCapability]:
    """Filters a list of models according to active tier rules."""
    return [m for m in models if is_model_allowed_for_tier(tier, m)]


def is_tool_allowed_for_tier(tier: ProductTier, tool_name: str) -> bool:
    """Checks whether a tool is authorized for the given tier."""
    spec = get_tier_spec(tier)
    return tool_name in spec.allowed_tools


def is_agent_allowed_for_tier(tier: ProductTier, agent_name: str) -> bool:
    """Checks whether an agent archetype is authorized for the given tier."""
    spec = get_tier_spec(tier)
    return agent_name.upper() in spec.allowed_agent_archetypes
