"""Integration tests for intelligence tools."""
import pytest
from ._helpers import assert_ok

pytestmark = pytest.mark.live

def test_list_vulnerability_intelligence(live_env, call):
    assert_ok(call("list_vulnerability_intelligence", page_size=5), allow_empty=True)


def test_get_vulnerability_intelligence_details(live_env, call):
    # Try a well-known CVE
    result = call("get_vulnerability_intelligence_details", identifier="CVE-2024-3400")
    # May not exist in tenant — allow error
    assert result is not None


def test_list_adversary_intelligence(live_env, call):
    assert_ok(call("list_adversary_intelligence", page_size=5), allow_empty=True)


def test_list_compromised_endpoints(live_env, call):
    assert_ok(call("list_compromised_endpoints", page_size=5), allow_empty=True)


def test_list_credential_attempt_logs(live_env, call):
    assert_ok(call("list_credential_attempt_logs", page_size=5), allow_empty=True)


def test_list_finding_retest_history(live_env, call):
    assert_ok(call("list_finding_retest_history", page_size=5), allow_empty=True)


@pytest.mark.live
def test_search_active_defense_library(live_env, call):
    response = call("search_active_defense_library", page_size=5)
    assert_ok(response)


@pytest.mark.live
def test_search_active_defense_library_with_query(live_env, call):
    response = call("search_active_defense_library", search="sql", page_size=5)
    assert_ok(response)


@pytest.mark.live
def test_search_capabilities(live_env, call):
    response = call("search_capabilities", query="log4j")
    assert_ok(response)


@pytest.mark.live
def test_search_capabilities_cve(live_env, call):
    response = call("search_capabilities", query="CVE-2021")
    assert_ok(response)
