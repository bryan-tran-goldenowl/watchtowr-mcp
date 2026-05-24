"""Live-API tests for the 2 Services tools."""
from __future__ import annotations

import pytest

from ._helpers import assert_ok


pytestmark = pytest.mark.live


def test_list_services(live_env, call):
    assert_ok(call("list_services", page_size=5), allow_empty=True)


def test_search_services_by_technology(live_env, call):
    assert_ok(call("search_services_by_technology", port_services="http", page_size=5), allow_empty=True)
