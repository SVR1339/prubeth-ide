"""
SUKHI IDE — Gate 7 Automated Test Suite
Verifies Three-Tier Product Architecture (Free Community, Pro Horizon, Frontier Pro Max),
capability envelopes, context ceilings, tool restrictions, and workspace storage quotas.
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from core.product_tier import (
    ProductTier,
    TierSpecification,
    get_tier_spec,
    is_model_allowed_for_tier,
    filter_models_for_tier,
    is_tool_allowed_for_tier,
    is_agent_allowed_for_tier,
    TIER_SPECS,
    FRONTIER_MODEL_IDS
)
from core.model_registry import ModelRegistry, ModelCapability
from core.router import IntelligentRouter, PolicyConstraint, AgentProfile
from core.workspace import WorkspaceGuard, QuotaExceededError, WorkspaceSecurityError


def test_tier_specifications_completeness():
    """All three tiers must be fully specified with deterministic bounds."""
    assert ProductTier.FREE_COMMUNITY in TIER_SPECS
    assert ProductTier.PRO_HORIZON in TIER_SPECS
    assert ProductTier.FRONTIER_PRO_MAX in TIER_SPECS

    free = get_tier_spec(ProductTier.FREE_COMMUNITY)
    assert free.max_context_window == 32768
    assert not free.allow_cloud_models
    assert not free.allow_frontier_models
    assert "local_offline" in free.allowed_privacy_tiers
    assert "cloud_public" not in free.allowed_privacy_tiers

    pro = get_tier_spec(ProductTier.PRO_HORIZON)
    assert pro.max_context_window == 1048576
    assert pro.allow_cloud_models
    assert not pro.allow_frontier_models
    assert "run_command" in pro.allowed_tools
    assert "call_mcp" in pro.allowed_tools

    frontier = get_tier_spec(ProductTier.FRONTIER_PRO_MAX)
    assert frontier.max_context_window >= 2000000
    assert frontier.allow_cloud_models
    assert frontier.allow_frontier_models
    assert "CRITIC" in frontier.allowed_agent_archetypes
    assert "RELEASE" in frontier.allowed_agent_archetypes


def test_free_community_restricts_cloud_and_frontier():
    """Free Community tier must block remote/cloud and frontier models."""
    registry = ModelRegistry()

    local_qwen = registry.get_model("qwen2.5:1.5b")
    assert local_qwen is not None
    assert is_model_allowed_for_tier(ProductTier.FREE_COMMUNITY, local_qwen)

    cloud_gemini = registry.get_model("gemini-3.8-flash")
    assert cloud_gemini is not None
    assert not is_model_allowed_for_tier(ProductTier.FREE_COMMUNITY, cloud_gemini)

    frontier_claude = registry.get_model("claude-3-7-sonnet-20250219")
    assert frontier_claude is not None
    assert not is_model_allowed_for_tier(ProductTier.FREE_COMMUNITY, frontier_claude)


def test_pro_horizon_allows_cloud_restricts_frontier():
    """Pro Horizon tier must allow standard private cloud models but gate frontier models."""
    registry = ModelRegistry()

    cloud_gemini = registry.get_model("gemini-3.8-flash")
    assert is_model_allowed_for_tier(ProductTier.PRO_HORIZON, cloud_gemini)

    cloud_llama = registry.get_model("llama-3.3-70b-versatile")
    assert is_model_allowed_for_tier(ProductTier.PRO_HORIZON, cloud_llama)

    frontier_claude = registry.get_model("claude-3-7-sonnet-20250219")
    assert not is_model_allowed_for_tier(ProductTier.PRO_HORIZON, frontier_claude)

    frontier_gpt4o = registry.get_model("gpt-4o")
    assert not is_model_allowed_for_tier(ProductTier.PRO_HORIZON, frontier_gpt4o)


def test_frontier_pro_max_allows_all():
    """Frontier Pro Max tier must allow all models without gating."""
    registry = ModelRegistry()

    for mod in registry.list_models():
        assert is_model_allowed_for_tier(ProductTier.FRONTIER_PRO_MAX, mod)


def test_tool_and_agent_capability_gating():
    """Verify tool and agent archetype permissions per tier."""
    # Tools
    assert is_tool_allowed_for_tier(ProductTier.FREE_COMMUNITY, "read_file")
    assert is_tool_allowed_for_tier(ProductTier.FREE_COMMUNITY, "write_file")
    assert not is_tool_allowed_for_tier(ProductTier.FREE_COMMUNITY, "run_command")
    assert not is_tool_allowed_for_tier(ProductTier.FREE_COMMUNITY, "call_mcp")

    assert is_tool_allowed_for_tier(ProductTier.PRO_HORIZON, "run_command")
    assert is_tool_allowed_for_tier(ProductTier.PRO_HORIZON, "call_mcp")

    # Agents
    assert is_agent_allowed_for_tier(ProductTier.FREE_COMMUNITY, "PLANNER")
    assert is_agent_allowed_for_tier(ProductTier.FREE_COMMUNITY, "CODER")
    assert not is_agent_allowed_for_tier(ProductTier.FREE_COMMUNITY, "CRITIC")
    assert not is_agent_allowed_for_tier(ProductTier.FREE_COMMUNITY, "RELEASE")

    assert is_agent_allowed_for_tier(ProductTier.FRONTIER_PRO_MAX, "CRITIC")
    assert is_agent_allowed_for_tier(ProductTier.FRONTIER_PRO_MAX, "RELEASE")


def test_intelligent_router_tier_enforcement():
    """Router must deterministically restrict candidate models and tools by active tier."""
    router = IntelligentRouter()

    # Free Community policy
    policy_free = PolicyConstraint(tier=ProductTier.FREE_COMMUNITY)
    profile, candidates, allowed_tools = router.build_execution_plan(
        "Refactor the authentication architecture", policy=policy_free
    )
    assert all(c.is_local for c in candidates)
    assert "run_command" not in allowed_tools
    assert "call_mcp" not in allowed_tools

    # Pro Horizon policy
    policy_pro = PolicyConstraint(tier=ProductTier.PRO_HORIZON)
    profile, candidates, allowed_tools = router.build_execution_plan(
        "Refactor the authentication architecture", policy=policy_pro
    )
    # Gemini Flash should be present, Claude Sonnet should not be present
    candidate_ids = [c.model_id for c in candidates]
    assert "gemini-3.8-flash" in candidate_ids
    assert "claude-3-7-sonnet-20250219" not in candidate_ids
    assert "run_command" in allowed_tools

    # Route dictionary check
    res = router.route("Explain this function", policy={"tier": "free_community"})
    assert res["tier"] == "free_community"
    if res["primary_model"]:
        assert res["primary_model"]["is_local"] is True


def test_workspace_quota_enforcement():
    """WorkspaceGuard must enforce file size and workspace capacity limits."""
    temp_dir = Path(tempfile.mkdtemp(prefix="sukhi_quota_test_"))
    try:
        # Create guard with 1KB max file and 5KB max workspace
        guard = WorkspaceGuard(
            workspace_root=temp_dir,
            max_workspace_bytes=5120,
            max_file_size_bytes=1024
        )

        # Write normal file below quota
        guard.safe_write("small.txt", "hello world")
        assert (temp_dir / "small.txt").exists()

        # Attempt to write a single file exceeding max_file_size_bytes
        large_content = "X" * 2048
        with pytest.raises(QuotaExceededError) as exc_info:
            guard.safe_write("oversized.txt", large_content)
        assert "File size limit exceeded" in str(exc_info.value)

        # Fill up to near limit (11 + 900*5 = 4511 bytes)
        guard.safe_write("file1.txt", "A" * 900)
        guard.safe_write("file2.txt", "B" * 900)
        guard.safe_write("file3.txt", "C" * 900)
        guard.safe_write("file4.txt", "D" * 900)
        guard.safe_write("file5.txt", "E" * 900)

        # Next write (4511 + 900 = 5411) must exceed total workspace quota (5120 bytes)
        with pytest.raises(QuotaExceededError) as exc_info:
            guard.safe_write("overflow.txt", "F" * 900)
        assert "Workspace storage quota exceeded" in str(exc_info.value)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
