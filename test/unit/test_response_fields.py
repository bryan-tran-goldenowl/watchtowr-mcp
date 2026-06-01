"""Static check: load-bearing response attributes the MCP tools read exist on
the SDK Pydantic models. Catches field renames after an SDK regeneration that
would otherwise degrade output to N/A silently (getattr default).

Field sets below were confirmed by reading the SDK model __properties during the
2026-05 module audit. When the SDK changes a field name, update both the SDK and
the tool, then this list.
"""
from __future__ import annotations

import importlib

import pytest

# (module_path, class_name, [attribute names a tool reads])
MODEL_FIELD_CHECKS = [
    # threat_intel.list_certificates / get_certificate_details / composite expiring certs
    ("watchtowr_api_sdk.models.service_information_response", "ServiceInformationResponse",
     ["id", "certificate", "asset"]),
    ("watchtowr_api_sdk.models.service_information_certificate", "ServiceInformationCertificate",
     ["subject_common_name", "subject_organisation", "issuer_organisation",
      "issuer_common_name", "subject_alt_names", "status"]),
    # incident / composite service listing
    ("watchtowr_api_sdk.models.service_listing", "ServiceListing",
     ["id", "ip", "hostname", "port", "service", "country", "banner", "technologies"]),
    ("watchtowr_api_sdk.models.technology", "Technology",
     ["name", "version", "display_name"]),
    # organization activity logs
    ("watchtowr_api_sdk.models.client_activity_log", "ClientActivityLog",
     ["id", "description", "type", "created_at", "caused_by"]),
    ("watchtowr_api_sdk.models.causer", "Causer",
     ["name"]),
    # organization source IPs (get_watchtowr_source_ips reads whitelist)
    ("watchtowr_api_sdk.models.client_testing_infrastructure", "ClientTestingInfrastructure",
     ["name", "description", "region", "whitelist"]),
    # organization business unit details
    ("watchtowr_api_sdk.models.client_business_unit_detail_with_rules", "ClientBusinessUnitDetailWithRules",
     ["id", "name", "description", "type", "parent_id", "user_ids", "created_at", "updated_at", "rules"]),
]


def _model_fields(module: str, cls: str) -> set[str]:
    mod = importlib.import_module(module)
    model = getattr(mod, cls)
    # pydantic v2: field names are the python attribute names (not aliases)
    return set(model.model_fields.keys())


@pytest.mark.parametrize("module,cls,attrs", MODEL_FIELD_CHECKS)
def test_response_attrs_exist_on_model(module, cls, attrs):
    available = _model_fields(module, cls)
    missing = [a for a in attrs if a not in available]
    assert not missing, (
        f"{cls} is missing {missing} (tool reads them). Available: {sorted(available)}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Round-2: response-schema mismatch guards (app-server ↔ SDK).
# Các field dưới đây đã được sửa ở schema app-server cho khớp dữ liệu thật rồi
# regenerate SDK. Test giữ cho lần regenerate sau không lặng lẽ quay về kiểu sai
# (gây ValidationError → crash tool khi parse dữ liệu thật).
# ─────────────────────────────────────────────────────────────────────────────

import typing


def _is_optional(annotation) -> bool:
    return type(None) in typing.get_args(annotation)


def _accepts_number(annotation) -> bool:
    s = str(annotation)
    return ("int" in s) or ("float" in s)


# (module, class, [field]) — field đã sửa thành nullable ở schema app-server.
NULLABLE_FIELDS = [
    ("watchtowr_api_sdk.models.client_cloud_asset", "ClientCloudAsset",
     ["super_type", "sub_type", "hostname"]),
]

# (module, class, field) — field phải nhận kiểu number (API trả int, schema đã
# sửa từ string → number). Round-2 BUG-R2-1: ClientFinding.id.
NUMBER_FIELDS = [
    ("watchtowr_api_sdk.models.client_finding", "ClientFinding", "id"),
]


@pytest.mark.parametrize("module,cls,fields", NULLABLE_FIELDS)
def test_fields_are_optional_in_sdk(module, cls, fields):
    mod = importlib.import_module(module)
    model = getattr(mod, cls)
    not_optional = [f for f in fields if not _is_optional(model.model_fields[f].annotation)]
    assert not not_optional, (
        f"{cls}: field {not_optional} đáng lẽ Optional nhưng SDK đang required — "
        f"kiểm tra @ApiPropertyOptional({{nullable:true}}) ở schema app-server "
        f"và chạy lại sync_sdk.sh."
    )


@pytest.mark.parametrize("module,cls,field", NUMBER_FIELDS)
def test_fields_accept_number_in_sdk(module, cls, field):
    mod = importlib.import_module(module)
    model = getattr(mod, cls)
    ann = model.model_fields[field].annotation
    assert _accepts_number(ann), (
        f"{cls}.{field} phải nhận number (API trả int) nhưng SDK đang {ann}. "
        f"Kiểm tra @ApiProperty({{type:'number'}}) ở schema app-server và chạy lại "
        f"sync_sdk.sh. (Round-2 BUG-R2-1: id string vs int)."
    )
