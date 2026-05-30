"""Static check: kwargs passed at each SDK call site are accepted by the SDK method.

`test_sdk_surface.py` proves the methods exist. This proves we call them with
argument names the SDK actually declares. AST-walks tools/*.py, resolves each
`<ApiClass>(...).method(...)` / `var.method(...)` call to a real SDK signature,
and asserts every keyword argument name is in that signature. Catches the class
of bug where a tool passes e.g. statuses= to an endpoint that doesn't accept it
(silently swallowed by try/except at runtime).
"""
from __future__ import annotations

import ast
import importlib
import inspect
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "watchtowr_mcp_server" / "tools"

# Methods called dynamically via getattr(api, method_name) inside _count/_ASSET_API_MAP
# loops cannot be resolved by static kwargs inspection; assert those separately in
# test_asset_map_kwargs below. Here we only check statically-resolvable attribute calls.

# kwargs that are SDK-internal / not real query params — ignore if present.
_IGNORED_KWARGS = {"_request_timeout", "_headers", "_host_index", "_content_type", "_request_auth"}


def _imported_api_classes(tree: ast.Module) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("watchtowr_api_sdk.api."):
            for alias in node.names:
                out[alias.asname or alias.name] = node.module
    return out


def _sig_params(module: str, cls: str, method: str) -> set[str] | None:
    try:
        mod = importlib.import_module(module)
        api_cls = getattr(mod, cls)
        fn = getattr(api_cls, method)
    except (ImportError, AttributeError):
        return None
    return {p for p in inspect.signature(fn).parameters if p != "self"}


class _CallVisitor(ast.NodeVisitor):
    def __init__(self, imported: dict[str, str]):
        self.imported = imported
        self.var_to_class: dict[str, str] = {}
        # (module, cls, method, frozenset(kwarg_names), lineno)
        self.calls: list[tuple] = []

    def visit_Assign(self, node):
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id in self.imported):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    self.var_to_class[t.id] = node.value.func.id
        self.generic_visit(node)

    def visit_Call(self, node):
        func = node.func
        if isinstance(func, ast.Attribute):
            cls = None
            if isinstance(func.value, ast.Name):
                cls = self.var_to_class.get(func.value.id)
            elif (isinstance(func.value, ast.Call)
                  and isinstance(func.value.func, ast.Name)
                  and func.value.func.id in self.imported):
                cls = func.value.func.id
            if cls:
                module = self.imported[cls]
                kwargs = {kw.arg for kw in node.keywords if kw.arg is not None}
                self.calls.append((module, cls, func.attr, frozenset(kwargs), node.lineno))
        self.generic_visit(node)


def _discover_calls():
    found = []
    for path in TOOLS_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        imported = _imported_api_classes(tree)
        if not imported:
            continue
        v = _CallVisitor(imported)
        v.visit(tree)
        for module, cls, method, kwargs, lineno in v.calls:
            found.append((path.name, lineno, module, cls, method, kwargs))
    return found


def test_call_site_kwargs_match_sdk_signatures():
    problems = []
    for filename, lineno, module, cls, method, kwargs in _discover_calls():
        params = _sig_params(module, cls, method)
        if params is None:
            continue  # method existence is covered by test_sdk_surface.py
        for kw in kwargs - _IGNORED_KWARGS:
            if kw not in params:
                problems.append(
                    f"{filename}:{lineno} {cls}.{method}(...) passes '{kw}=' "
                    f"but signature only accepts {sorted(params)}"
                )
    assert not problems, "Kwarg drift between MCP tools and SDK:\n" + "\n".join(problems)


# ── Dynamic dispatch table guard ──────────────────────────────────────────────
# reporting.py / composite.py / workflow.py share an _ASSET_API_MAP and call every
# entry with a common set of kwargs. getattr-based dispatch hides this from the AST
# walk above, so assert the contract explicitly here.

from watchtowr_api_sdk.api.ip_addresses_api import IPAddressesApi
from watchtowr_api_sdk.api.domains_api import DomainsApi
from watchtowr_api_sdk.api.subdomains_api import SubdomainsApi
from watchtowr_api_sdk.api.ports_api import PortsApi
from watchtowr_api_sdk.api.ip_ranges_api import IPRangesApi
from watchtowr_api_sdk.api.cloud_storage_api import CloudStorageApi
from watchtowr_api_sdk.api.repositories_api import RepositoriesApi
from watchtowr_api_sdk.api.containers_api import ContainersApi
from watchtowr_api_sdk.api.saa_s_platforms_api import SaaSPlatformsApi
from watchtowr_api_sdk.api.mobile_applications_api import MobileApplicationsApi

_ASSET_API_MAP = [
    ("IP Addresses", IPAddressesApi, "get_list_asset_ips"),
    ("Domains", DomainsApi, "get_list_asset_domains"),
    ("Subdomains", SubdomainsApi, "get_list_asset_subdomains"),
    ("Ports", PortsApi, "get_list_asset_ports"),
    ("IP Ranges", IPRangesApi, "get_list_asset_ipranges"),
    ("Cloud Storage", CloudStorageApi, "get_list_asset_cloud_storages"),
    ("Repositories", RepositoriesApi, "get_list_asset_repositories"),
    ("Containers", ContainersApi, "get_list_asset_container"),
    ("SaaS Platforms", SaaSPlatformsApi, "get_list_asset_saas_platforms"),
    ("Mobile Apps", MobileApplicationsApi, "get_list_asset_mobile_apps"),
]

# kwargs the reporting/composite tools currently pass through the map.
_MAP_KWARGS = ["statuses", "business_unit_ids", "created_from", "created_to", "page_size"]


@pytest.mark.parametrize("label,cls,method_name", _ASSET_API_MAP)
def test_asset_map_methods_accept_common_kwargs(label, cls, method_name):
    fn = getattr(cls, method_name)
    params = {p for p in inspect.signature(fn).parameters if p != "self"}
    # Known per-endpoint exceptions handled by _supported_kwargs in
    # reporting.py / composite.py (the kwarg is filtered out before the call).
    KNOWN_UNSUPPORTED = {("Ports", "statuses")}
    unsupported = [
        kw for kw in _MAP_KWARGS
        if kw not in params and (label, kw) not in KNOWN_UNSUPPORTED
    ]
    assert not unsupported, (
        f"{label} ({cls.__name__}.{method_name}) does not accept {unsupported} "
        f"and it is not in KNOWN_UNSUPPORTED. Add per-endpoint sanitization via "
        f"_supported_kwargs in reporting.py/composite.py and document the "
        f"exception here."
    )
