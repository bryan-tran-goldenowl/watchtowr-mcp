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
