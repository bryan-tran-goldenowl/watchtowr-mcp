import os

from .findings import register_findings_tools
from .assets import register_asset_tools
from .hunts import register_hunt_tools
from .threat_intel import register_threat_intel_tools
from .services import register_service_tools
from .organization import register_organization_tools
from .composite import register_composite_tools
from .reporting import register_reporting_tools
from .incident import register_incident_tools
from .workflow import register_workflow_tools


def register_all_tools(mcp):
    disabled_groups = [g.strip().lower() for g in os.environ.get("WATCHTOWR_DISABLED_TOOL_GROUPS", "").split(",")]

    if "findings" not in disabled_groups:
        register_findings_tools(mcp)
    if "assets" not in disabled_groups:
        register_asset_tools(mcp)
    if "hunts" not in disabled_groups:
        register_hunt_tools(mcp)
    if "threat_intel" not in disabled_groups:
        register_threat_intel_tools(mcp)
    if "services" not in disabled_groups:
        register_service_tools(mcp)
    if "organization" not in disabled_groups:
        register_organization_tools(mcp)
    if "composite" not in disabled_groups:
        register_composite_tools(mcp)
    if "reporting" not in disabled_groups:
        register_reporting_tools(mcp)
    if "incident" not in disabled_groups:
        register_incident_tools(mcp)
    if "workflow" not in disabled_groups:
        register_workflow_tools(mcp)
