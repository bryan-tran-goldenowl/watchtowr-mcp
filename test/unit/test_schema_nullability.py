"""Cảnh báo schema drift: các model SDK trọng yếu mà MCP deserialize không được
phép có field 'required + non-nullable' nằm ngoài danh sách đã duyệt.

Nếu app-server thêm một field required mới (hoặc đổi một field optional thành
required) và regenerate SDK, test này fail để buộc rà soát: field đó có thể bị
API trả null → crash pydantic khi MCP parse dữ liệu thật.
"""
from __future__ import annotations

import importlib
import typing

import pytest


def _is_optional(annotation) -> bool:
    return type(None) in typing.get_args(annotation)


def _required_non_nullable(model_path: str, cls_name: str) -> set[str]:
    mod = importlib.import_module(model_path)
    cls = getattr(mod, cls_name)
    out = set()
    for fname, finfo in cls.model_fields.items():
        try:
            req = finfo.is_required()
        except Exception:
            req = False
        if req and not _is_optional(finfo.annotation):
            out.add(fname)
    return out


# Tập field required non-nullable ĐÃ DUYỆT cho từng model. Các field này được
# coi là "API luôn trả giá trị, không bao giờ null". Khi cần thêm/bớt, cập nhật
# ở đây SAU KHI đã xác nhận hành vi API thật.
APPROVED = {
    ("watchtowr_api_sdk.models.technology", "Technology"): {"id", "name", "display_name"},
    ("watchtowr_api_sdk.models.causer", "Causer"): {"id", "name"},
    ("watchtowr_api_sdk.models.client_business_unit", "ClientBusinessUnit"): {"id", "name"},
    ("watchtowr_api_sdk.models.service_information_asset", "ServiceInformationAsset"):
        {"id", "name", "type", "business_units"},
    ("watchtowr_api_sdk.models.client_activity_log", "ClientActivityLog"):
        {"id", "description", "type", "caused_by"},
}


@pytest.mark.parametrize("key,approved", list(APPROVED.items()))
def test_required_non_nullable_is_frozen(key, approved):
    module_path, cls_name = key
    actual = _required_non_nullable(module_path, cls_name)
    new_required = actual - approved
    removed = approved - actual
    assert not new_required, (
        f"{cls_name}: field required non-nullable MỚI {sorted(new_required)} — "
        f"hãy xác nhận API không bao giờ trả null cho chúng; nếu có thể null thì "
        f"sửa @ApiPropertyOptional({{nullable:true}}) ở schema app-server rồi regenerate."
    )
    assert not removed, (
        f"{cls_name}: field {sorted(removed)} không còn required — cập nhật APPROVED."
    )
