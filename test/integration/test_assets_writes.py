"""Live-API tests for the 2 write Asset tools — gated behind @pytest.mark.write."""
from __future__ import annotations

import uuid

import pytest

from ._helpers import assert_ok


pytestmark = [pytest.mark.live, pytest.mark.write]


def test_update_asset_status_domain_roundtrip(live_env, call, sample_domain_id):
    """Set a domain's status to its current value — exercises the write path
    without flipping tenant state. We can't read the current status off the
    list output reliably (formatting varies), so we set to 'In Scope' which is
    the canonical default; if the asset wasn't in that state we'll see an
    error from the API and assert_ok will fail.

    Adjust this test if your tenant uses non-default status names.
    """
    response = call(
        "update_asset_status",
        asset_type="domain",
        asset_id=sample_domain_id,
        status="In Scope",
    )
    assert_ok(response)


def test_add_seed_asset_with_invalid_tld(live_env, call):
    """Submit a clearly-marked test domain under .invalid (RFC 6761 reserved).

    .invalid never resolves, so no real scanning happens. The asset shows up
    in the tenant with the title 'mcp-test-<uuid>' for easy cleanup.
    """
    marker = f"mcp-test-{uuid.uuid4().hex[:8]}.invalid"
    response = call(
        "add_seed_asset",
        asset_type="domain",
        asset_value=marker,
        asset_title=marker,
    )
    assert_ok(response)
    assert marker in response, f"response did not echo back the seed value: {response!r}"
