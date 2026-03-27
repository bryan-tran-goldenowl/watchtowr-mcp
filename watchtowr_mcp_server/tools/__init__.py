from .findings import register_findings_tools
from .assets import register_asset_tools
from .hunts import register_hunt_tools
from .threat_intel import register_threat_intel_tools
from .services import register_service_tools
from .organization import register_organization_tools
from .composite import register_composite_tools


def register_all_tools(mcp):
    register_findings_tools(mcp)
    register_asset_tools(mcp)
    register_hunt_tools(mcp)
    register_threat_intel_tools(mcp)
    register_service_tools(mcp)
    register_organization_tools(mcp)
    register_composite_tools(mcp)
