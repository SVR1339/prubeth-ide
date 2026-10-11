"""PRUBETH IDE - Plugin & Extension Failure Chaos Tests
=====================================================
Exercises manifest validation failures, unrecognized permission escalations,
malformed plugin structures, and MCP transport error recovery.
"""

import pytest
from core.plugin_engine import PluginManifestValidator, PluginManifestValidationError


def test_plugin_manifest_missing_required_fields():
    """Manifest missing required fields must be rejected safely."""
    incomplete_manifest = {
        "id": "unvetted-plugin",
        "name": "Unvetted Plugin",
        # Missing version, publisher, permissions
    }

    with pytest.raises(PluginManifestValidationError) as exc:
        PluginManifestValidator.validate(incomplete_manifest)

    assert "Missing required manifest field" in str(exc.value)


def test_plugin_manifest_privilege_escalation_rejected():
    """Manifest requesting unrecognized or excessive permissions must be rejected."""
    escalated_manifest = {
        "id": "malicious-ext",
        "name": "Malicious Extension",
        "version": "1.0.0",
        "publisher": "bad-actor",
        "description": "Attempts privilege escalation",
        "permissions": ["workspace:read", "system:kernel_driver_load"],  # Illegal permission
    }

    with pytest.raises(PluginManifestValidationError) as exc:
        PluginManifestValidator.validate(escalated_manifest)

    assert "Unrecognized or excessively privileged permission" in str(exc.value)


def test_valid_plugin_manifest_acceptance():
    """Well-formed plugin manifest with allowed permissions must validate cleanly."""
    valid_manifest = {
        "id": "safe-linter",
        "name": "Safe Code Linter",
        "version": "1.2.0",
        "publisher": "trusted-org",
        "description": "Lints Python and TS code within workspace",
        "permissions": ["workspace:read", "settings:read"],
    }

    assert PluginManifestValidator.validate(valid_manifest) is True
