from datetime import datetime, timedelta

from watchtowr_api.api.findings_api import FindingsApi
from watchtowr_api.api.hunts_api import HuntsApi
from watchtowr_api.api.business_unit_api import BusinessUnitApi
from watchtowr_api.api.certificates_api import CertificatesApi
from watchtowr_api.api.service_listing_api import ServiceListingApi
from watchtowr_api.api.asset_ip_addresses_api import AssetIPAddressesApi
from watchtowr_api.api.asset_domains_api import AssetDomainsApi
from watchtowr_api.api.asset_subdomains_api import AssetSubdomainsApi
from watchtowr_api.api.asset_ports_api import AssetPortsApi
from watchtowr_api.api.asset_ip_ranges_api import AssetIPRangesApi
from watchtowr_api.api.asset_cloud_storage_assets_api import AssetCloudStorageAssetsApi
from watchtowr_api.api.asset_source_code_repositories_api import AssetSourceCodeRepositoriesApi
from watchtowr_api.api.asset_containers_api import AssetContainersApi
from watchtowr_api.api.asset_saa_s_platforms_api import AssetSaaSPlatformsApi
from watchtowr_api.api.asset_mobile_applications_api import AssetMobileApplicationsApi
from watchtowr_api.api.points_of_interest_api import PointsOfInterestApi

from ..client import get_api_client, get_total, parse_date, format_bus


_ASSET_API_MAP = [
    ("IP Addresses", AssetIPAddressesApi, "get_list_asset_ips"),
    ("Domains", AssetDomainsApi, "get_list_asset_domains"),
    ("Subdomains", AssetSubdomainsApi, "get_list_asset_subdomains"),
    ("Ports", AssetPortsApi, "get_list_asset_ports"),
    ("IP Ranges", AssetIPRangesApi, "get_list_asset_ipranges"),
    ("Cloud Storage", AssetCloudStorageAssetsApi, "get_list_asset_cloud_storages"),
    ("Repositories", AssetSourceCodeRepositoriesApi, "get_list_asset_repositories"),
    ("Containers", AssetContainersApi, "get_list_asset_container"),
    ("SaaS Platforms", AssetSaaSPlatformsApi, "get_list_asset_saas_platforms"),
    ("Mobile Apps", AssetMobileApplicationsApi, "get_list_asset_mobile_apps"),
]


def _count(api_instance, method_name, **kwargs):
    """Call a list method with page_size=1 and extract the total count."""
    method = getattr(api_instance, method_name)
    response = method(page_size=1, **kwargs)
    return get_total(response) or (len(response.data) if hasattr(response, 'data') and response.data else 0)


def register_composite_tools(mcp):

    @mcp.tool()
    def get_attack_surface_summary() -> str:
        """Get an overview of the entire attack surface with asset counts by type and finding counts by severity."""
        try:
            client = get_api_client()

            asset_counts = {}
            for label, api_cls, method_name in _ASSET_API_MAP:
                try:
                    asset_counts[label] = _count(api_cls(client), method_name)
                except Exception:
                    asset_counts[label] = "error"

            findings_api = FindingsApi(client)
            finding_counts = {}
            for severity in ["Critical", "High", "Medium", "Low"]:
                try:
                    finding_counts[severity] = _count(
                        findings_api, "get_list_findings", severities=severity
                    )
                except Exception:
                    finding_counts[severity] = "error"

            total_assets = sum(v for v in asset_counts.values() if isinstance(v, int))
            total_findings = sum(v for v in finding_counts.values() if isinstance(v, int))

            lines = [
                f"Attack Surface Summary",
                f"",
                f"Assets (Total: {total_assets}):",
            ]
            for label, count in asset_counts.items():
                lines.append(f"  • {label}: {count}")

            lines.append(f"\nFindings (Total: {total_findings}):")
            for severity, count in finding_counts.items():
                lines.append(f"  • {severity}: {count}")

            return "\n".join(lines)
        except Exception as e:
            return f"Error generating attack surface summary: {e}"

    @mcp.tool()
    def get_new_assets_since(days: int = 7) -> str:
        """List all newly discovered assets across every type within a given number of days.

        Args:
            days: Number of days to look back (default 7).
        """
        try:
            client = get_api_client()
            since = datetime.now() - timedelta(days=days)

            lines = [f"New Assets Discovered (Last {days} Days):", ""]
            total_new = 0

            for label, api_cls, method_name in _ASSET_API_MAP:
                try:
                    api = api_cls(client)
                    method = getattr(api, method_name)
                    response = method(created_from=since, page_size=30)

                    count = get_total(response) or (
                        len(response.data) if hasattr(response, 'data') and response.data else 0
                    )

                    if count > 0:
                        total_new += count
                        lines.append(f"{label} ({count}):")
                        if hasattr(response, 'data') and response.data:
                            for a in response.data[:5]:
                                name = getattr(a, 'name', None) or getattr(a, 'iprange', None) or getattr(a, 'url', 'Unknown')
                                status = getattr(a, 'status', '')
                                lines.append(f"  • {name} ({status})")
                            if count > 5:
                                lines.append(f"  ... and {count - 5} more")
                        lines.append("")
                except Exception:
                    lines.append(f"{label}: error fetching data")
                    lines.append("")

            if total_new == 0:
                return f"No new assets discovered in the last {days} days."

            lines.insert(0, f"Total New Assets: {total_new}\n")
            return "\n".join(lines)
        except Exception as e:
            return f"Error listing new assets: {e}"

    @mcp.tool()
    def get_attack_surface_delta(days: int = 7) -> str:
        """Get a combined view of new assets AND new findings discovered within a time window.

        Answers "what changed this week" in a single call.

        Args:
            days: Number of days to look back (default 7).
        """
        try:
            client = get_api_client()
            since = datetime.now() - timedelta(days=days)

            lines = [f"Attack Surface Delta (Last {days} Days)", ""]

            # New assets
            total_new_assets = 0
            asset_lines = []
            for label, api_cls, method_name in _ASSET_API_MAP:
                try:
                    count = _count(api_cls(client), method_name, created_from=since)
                    if count > 0:
                        total_new_assets += count
                        asset_lines.append(f"  • {label}: +{count}")
                except Exception:
                    asset_lines.append(f"  • {label}: error")

            lines.append(f"New Assets ({total_new_assets}):")
            lines.extend(asset_lines)
            lines.append("")

            # New findings
            findings_api = FindingsApi(client)
            total_new_findings = 0
            findings_lines = []
            for severity in ["Critical", "High", "Medium", "Low"]:
                try:
                    count = _count(
                        findings_api, "get_list_findings",
                        severities=severity, created_from=since,
                    )
                    if count > 0:
                        total_new_findings += count
                    findings_lines.append(f"  • {severity}: +{count}")
                except Exception:
                    findings_lines.append(f"  • {severity}: error")

            lines.append(f"New Findings ({total_new_findings}):")
            lines.extend(findings_lines)

            return "\n".join(lines)
        except Exception as e:
            return f"Error generating attack surface delta: {e}"

    @mcp.tool()
    def get_business_unit_posture(business_unit_id: str) -> str:
        """Get a full security posture overview for a business unit: details, unresolved findings, asset counts, services, certificates, and points of interest.

        Args:
            business_unit_id: The business unit ID.
        """
        try:
            client = get_api_client()
            lines = []

            # BU details
            try:
                bu_api = BusinessUnitApi(client)
                bu_resp = bu_api.get_business_unit_details(id=int(business_unit_id))
                bu = bu_resp.data if hasattr(bu_resp, 'data') else bu_resp
                if bu:
                    lines.append(f"Business Unit: {getattr(bu, 'name', 'N/A')} (ID: {business_unit_id})")
                    desc = getattr(bu, 'description', '')
                    if desc:
                        lines.append(f"Description: {desc}")
            except Exception:
                lines.append(f"Business Unit ID: {business_unit_id}")
            lines.append("")

            # Unresolved findings by severity
            lines.append("Unresolved Findings:")
            findings_api = FindingsApi(client)
            total_findings = 0
            for severity in ["Critical", "High", "Medium", "Low"]:
                try:
                    count = _count(
                        findings_api, "get_list_findings",
                        severities=severity,
                        business_unit_ids=business_unit_id,
                        statuses="Open,Triaged,In Progress",
                    )
                    total_findings += count
                    lines.append(f"  • {severity}: {count}")
                except Exception:
                    lines.append(f"  • {severity}: error")
            lines.append(f"  Total: {total_findings}")
            lines.append("")

            # Asset counts
            lines.append("Assets:")
            total_assets = 0
            for label, api_cls, method_name in _ASSET_API_MAP:
                try:
                    count = _count(
                        api_cls(client), method_name,
                        business_unit_ids=business_unit_id,
                    )
                    total_assets += count
                    if count > 0:
                        lines.append(f"  • {label}: {count}")
                except Exception:
                    pass
            lines.append(f"  Total: {total_assets}")
            lines.append("")

            # Services
            try:
                svc_api = ServiceListingApi(client)
                svc_count = _count(
                    svc_api, "get_list_service_listing",
                    business_unit_ids=business_unit_id,
                )
                lines.append(f"Services: {svc_count}")
            except Exception:
                lines.append("Services: error")

            # Certificates
            try:
                cert_api = CertificatesApi(client)
                cert_count = _count(
                    cert_api, "get_list_certificates",
                    business_unit_ids=business_unit_id,
                )
                lines.append(f"Certificates: {cert_count}")
            except Exception:
                lines.append("Certificates: error")

            # Points of interest
            try:
                poi_api = PointsOfInterestApi(client)
                poi_count = _count(
                    poi_api, "get_list_points_of_interest",
                    business_unit_ids=business_unit_id,
                )
                lines.append(f"Points of Interest: {poi_count}")
            except Exception:
                lines.append("Points of Interest: error")

            return "\n".join(lines)
        except Exception as e:
            return f"Error generating business unit posture: {e}"

    @mcp.tool()
    def get_finding_with_asset_context(finding_id: int) -> str:
        """Get finding details enriched with the related asset's full details.

        Fetches the finding, identifies the associated asset type and ID, then
        fetches that asset's details for a complete triage view.

        Args:
            finding_id: The finding ID.
        """
        try:
            client = get_api_client()
            findings_api = FindingsApi(client)
            response = findings_api.get_finding_details(id=finding_id, api_token="")

            f = response.data if hasattr(response, 'data') else response
            if not f:
                return f"Finding {finding_id} not found."

            lines = [
                f"Finding #{getattr(f, 'id', finding_id)}",
                f"Title: {getattr(f, 'title', 'N/A')}",
                f"Severity: {getattr(f, 'severity', 'N/A')}",
                f"Status: {getattr(f, 'status', 'N/A')}",
                f"Category: {getattr(f, 'category', 'N/A')}",
                f"Created: {getattr(f, 'created_at', 'N/A')}",
                f"Updated: {getattr(f, 'updated_at', 'N/A')}",
            ]
            bus = format_bus(getattr(f, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")

            description = getattr(f, 'description', '')
            if description:
                lines.append(f"\nDescription:\n{description}")

            remediation = getattr(f, 'remediation', '')
            if remediation:
                lines.append(f"\nRemediation:\n{remediation}")

            # Try to extract asset context
            asset = getattr(f, 'asset', None)
            if asset:
                lines.append("\n--- Associated Asset ---")
                if isinstance(asset, dict):
                    asset_id = asset.get('id')
                    asset_type = asset.get('type', '')
                    asset_name = asset.get('name', '') or asset.get('url', '') or asset.get('iprange', '')
                else:
                    asset_id = getattr(asset, 'id', None)
                    asset_type = getattr(asset, 'type', '')
                    asset_name = getattr(asset, 'name', '') or getattr(asset, 'url', '') or getattr(asset, 'iprange', '')

                lines.append(f"Asset Type: {asset_type}")
                lines.append(f"Asset Name: {asset_name}")
                lines.append(f"Asset ID: {asset_id}")

                if asset_id:
                    try:
                        detail_lines = _fetch_asset_detail(client, asset_type, asset_id)
                        if detail_lines:
                            lines.extend(detail_lines)
                    except Exception:
                        pass

            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving finding with context: {e}"

    @mcp.tool()
    def get_expiring_certificates_with_services(days: int = 30) -> str:
        """List certificates expiring within N days, cross-referenced with exposed services on the same hosts.

        Args:
            days: Number of days to look ahead for expiring certificates (default 30).
        """
        try:
            client = get_api_client()
            cert_api = CertificatesApi(client)
            svc_api = ServiceListingApi(client)

            expiry_cutoff = datetime.now() + timedelta(days=days)
            cert_response = cert_api.get_list_certificates(
                valid_to_before=expiry_cutoff,
                page_size=30,
            )

            if not hasattr(cert_response, 'data') or not cert_response.data:
                return f"No certificates expiring within {days} days."

            cert_total = get_total(cert_response)
            lines = [f"Certificates Expiring Within {days} Days ({cert_total or len(cert_response.data)}):", ""]

            # Collect hostnames from certs for service cross-reference
            cert_hosts = set()
            for cert in cert_response.data:
                cn = getattr(cert, 'common_name', '') or ''
                subject = getattr(cert, 'subject', '') or ''
                valid_to = getattr(cert, 'valid_to', 'N/A')
                issuer = getattr(cert, 'issuer', '')
                bus = format_bus(getattr(cert, 'business_units', []))

                lines.append(f"• {cn or subject}")
                lines.append(f"  Expires: {valid_to}")
                if issuer:
                    lines.append(f"  Issuer: {issuer}")
                if bus:
                    lines.append(f"  {bus}")
                lines.append("")

                if cn:
                    cert_hosts.add(cn.lstrip("*."))

            # Cross-reference with services
            if cert_hosts:
                lines.append("--- Related Services ---")
                try:
                    svc_response = svc_api.get_list_service_listing(page_size=30)
                    if hasattr(svc_response, 'data') and svc_response.data:
                        matched = []
                        for svc in svc_response.data:
                            svc_name = getattr(svc, 'name', '') or ''
                            svc_host = getattr(svc, 'host', '') or ''
                            if any(h in svc_name or h in svc_host for h in cert_hosts):
                                tech = getattr(svc, 'technology', '')
                                port = getattr(svc, 'port', '')
                                matched.append(f"• {svc_host}:{port} ({tech}) - {svc_name}")
                        if matched:
                            lines.extend(matched)
                        else:
                            lines.append("No matching services found for expiring cert hosts.")
                    else:
                        lines.append("No services data available.")
                except Exception:
                    lines.append("Error fetching services for cross-reference.")

            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving expiring certificates: {e}"

    @mcp.tool()
    def get_hunt_remediation_list(hunt_id: int, page_size: int = 30) -> str:
        """Get expanded finding details for a hunt, formatted for remediation handoff.

        Includes full finding details, severity breakdown, and remediation guidance per finding.

        Args:
            hunt_id: The hunt ID.
            page_size: Number of findings to include (max 30).
        """
        try:
            client = get_api_client()
            hunts_api = HuntsApi(client)
            findings_api = FindingsApi(client)

            # Hunt detail
            hunt_resp = hunts_api.show_the_detail_hunt(id=hunt_id)
            hunt = hunt_resp.data if hasattr(hunt_resp, 'data') else hunt_resp
            hunt_title = getattr(hunt, 'title', f'Hunt #{hunt_id}') if hunt else f'Hunt #{hunt_id}'
            hunt_status = getattr(hunt, 'status', 'N/A') if hunt else 'N/A'

            lines = [
                f"Remediation List: {hunt_title}",
                f"Status: {hunt_status}",
                "",
            ]

            # Findings for this hunt
            findings_resp = hunts_api.get_list_finding_by_hunt(
                id=hunt_id, page_size=min(page_size, 30)
            )

            if not hasattr(findings_resp, 'data') or not findings_resp.data:
                lines.append("No findings for this hunt.")
                return "\n".join(lines)

            total = get_total(findings_resp) or len(findings_resp.data)
            severity_counts = {}

            for idx, finding in enumerate(findings_resp.data, 1):
                fid = getattr(finding, 'id', '')
                title = getattr(finding, 'title', 'N/A')
                severity = getattr(finding, 'severity', 'N/A')
                status = getattr(finding, 'status', 'N/A')
                severity_counts[severity] = severity_counts.get(severity, 0) + 1

                lines.append(f"{idx}. [{severity}] {title}")
                lines.append(f"   ID: {fid} | Status: {status}")

                # Attempt to get full detail with remediation
                try:
                    detail_resp = findings_api.get_finding_details(id=fid, api_token="")
                    fd = detail_resp.data if hasattr(detail_resp, 'data') else detail_resp
                    if fd:
                        remediation = getattr(fd, 'remediation', '')
                        asset = getattr(fd, 'asset', None)
                        if asset:
                            if isinstance(asset, dict):
                                asset_name = asset.get('name', '') or asset.get('url', '')
                            else:
                                asset_name = getattr(asset, 'name', '') or getattr(asset, 'url', '')
                            if asset_name:
                                lines.append(f"   Asset: {asset_name}")
                        if remediation:
                            rem_preview = remediation[:200].replace('\n', ' ')
                            lines.append(f"   Remediation: {rem_preview}")
                except Exception:
                    pass

                lines.append("")

            # Summary
            lines.append("--- Summary ---")
            lines.append(f"Total Findings: {total}")
            for sev in ["Critical", "High", "Medium", "Low", "Info"]:
                if sev in severity_counts:
                    lines.append(f"  • {sev}: {severity_counts[sev]}")

            if total > len(findings_resp.data):
                lines.append(f"\nShowing {len(findings_resp.data)} of {total}. Use list_findings_by_hunt for pagination.")

            return "\n".join(lines)
        except Exception as e:
            return f"Error generating hunt remediation list: {e}"


def _fetch_asset_detail(client, asset_type: str, asset_id) -> list[str]:
    """Fetch detailed info for an asset given its type, returning formatted lines."""
    type_lower = str(asset_type).lower().replace(" ", "_")
    lines = []

    dispatch = {
        "ip": (AssetIPAddressesApi, "get_asset_ip_details", ["name", "status", "country", "live", "source"]),
        "ip_address": (AssetIPAddressesApi, "get_asset_ip_details", ["name", "status", "country", "live", "source"]),
        "domain": (AssetDomainsApi, "get_asset_domain_details", ["name", "status", "live", "source"]),
        "subdomain": (AssetSubdomainsApi, "get_asset_subdomain_details", ["name", "status", "live", "source"]),
        "port": (AssetPortsApi, "get_asset_port_details", ["ip", "port", "service", "banner", "status"]),
        "ip_range": (AssetIPRangesApi, "get_asset_iprange_details", ["iprange", "asn", "desc", "country", "status"]),
        "cloud_storage": (AssetCloudStorageAssetsApi, "get_asset_cloud_storage_details", ["name", "platform", "url", "status"]),
        "repository": (AssetSourceCodeRepositoriesApi, "get_asset_repository_details", ["name", "owner", "provider", "status"]),
        "container": (AssetContainersApi, "get_asset_container_details", ["name", "owner", "platform", "url", "status"]),
        "saas_platform": (AssetSaaSPlatformsApi, "get_asset_saas_platform_details", ["url", "provider", "status"]),
        "mobile_app": (AssetMobileApplicationsApi, "get_asset_mobile_app_details", ["name", "publisher", "platform", "url", "status"]),
    }

    if type_lower not in dispatch:
        return [f"(Unknown asset type: {asset_type})"]

    api_cls, method_name, fields = dispatch[type_lower]
    api = api_cls(client)
    method = getattr(api, method_name)

    kwargs = {"id": int(asset_id), "api_token": ""}
    response = method(**kwargs)
    data = response.data if hasattr(response, 'data') else response

    if not data:
        return [f"(Asset {asset_id} not found)"]

    for field in fields:
        val = getattr(data, field, None)
        if val is not None and val != '':
            lines.append(f"  {field.replace('_', ' ').title()}: {val}")

    bus = format_bus(getattr(data, 'business_units', []))
    if bus:
        lines.append(f"  {bus}")

    return lines
