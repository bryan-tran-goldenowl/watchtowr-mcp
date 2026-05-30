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
