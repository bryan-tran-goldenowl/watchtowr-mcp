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
from watchtowr_api_sdk.api.cloud_integration_assets_api import CloudIntegrationAssetsApi
from watchtowr_api_sdk.api.api_documentation_api import APIDocumentationApi
from watchtowr_api_sdk.api.package_managers_api import PackageManagersApi
from watchtowr_api_sdk.api.add_asset_api import AddAssetApi
from watchtowr_api_sdk.models.update_client_legacy_asset_status_dto import UpdateClientLegacyAssetStatusDto
from watchtowr_api_sdk.models.update_client_next_gen_asset_status_dto import UpdateClientNextGenAssetStatusDto
from watchtowr_api_sdk.models.update_client_cloud_asset_status_dto import UpdateClientCloudAssetStatusDto
from watchtowr_api_sdk.models.update_api_documentation_status_dto import UpdateApiDocumentationStatusDto
from watchtowr_api_sdk.models.create_client_seed_data_request_body import CreateClientSeedDataRequestBody
from watchtowr_api_sdk.models.client_seed_data import ClientSeedData
import inspect

from ..client import get_api_client, get_total, parse_date, format_bus


def _build_asset_kwargs(page, page_size, asset_name=None, statuses=None,
                        business_unit_ids=None, created_from=None, created_to=None,
                        source=None, integration_connections=None,
                        custom_property_key=None, custom_property_value=None):
    kwargs = {"page": page, "page_size": min(page_size, 30)}
    if asset_name:
        kwargs["asset_name"] = asset_name
    if statuses:
        kwargs["statuses"] = [s.strip() for s in statuses.split(",")]
    if business_unit_ids:
        kwargs["business_unit_ids"] = business_unit_ids
    if created_from:
        kwargs["created_from"] = parse_date(created_from)
    if created_to:
        kwargs["created_to"] = parse_date(created_to)
    if source:
        kwargs["source"] = source
    if integration_connections:
        kwargs["integration_connections"] = integration_connections
    if custom_property_key:
        kwargs["custom_property_key"] = custom_property_key
    if custom_property_value:
        kwargs["custom_property_value"] = custom_property_value
    return kwargs


def _filter_kwargs(func, kwargs):
    sig = inspect.signature(func)
    return {k: v for k, v in kwargs.items() if k in sig.parameters}


def register_asset_tools(mcp):

    # ── IP Addresses ──────────────────────────────────────────────

    @mcp.tool()
    def list_asset_ips(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        match_type: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered IP addresses.

        Args:
            asset_name: Search by IP address (partial or full match).
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            match_type: Filter by match type ('exact' or 'partial').
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = IPAddressesApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            if match_type:
                kwargs["match_type"] = match_type
            response = api.get_list_asset_ips(**_filter_kwargs(api.get_list_asset_ips, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No IP addresses found."

            total = get_total(response)
            lines = []
            for ip in response.data:
                iid = getattr(ip, 'id', '')
                name = getattr(ip, 'name', 'Unknown')
                status = getattr(ip, 'status', 'Unknown')
                country = getattr(ip, 'country', '')
                live = " (live)" if getattr(ip, 'live', False) else ""
                country_str = f" [{country}]" if country else ""
                bus = format_bus(getattr(ip, 'business_units', []))
                lines.append(f"• [ID:{iid}] {name} - {status}{live}{country_str}{bus}")

            header = f"IP Addresses ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing IP addresses: {e}"

    @mcp.tool()
    def get_asset_ip_details(ip_id: int) -> str:
        """Get full details for a specific IP address asset.

        Args:
            ip_id: The IP address asset ID.
        """
        try:
            api = IPAddressesApi(get_api_client())
            response = api.get_asset_ip_details(id=ip_id)

            ip = response.data if hasattr(response, 'data') else response
            if not ip:
                return f"IP address {ip_id} not found."

            lines = [
                f"IP Address #{getattr(ip, 'id', ip_id)}",
                f"Name: {getattr(ip, 'name', 'N/A')}",
                f"Status: {getattr(ip, 'status', 'N/A')}",
                f"Source: {getattr(ip, 'source', 'N/A')}",
                f"Live: {getattr(ip, 'live', 'N/A')}",
                f"Country: {getattr(ip, 'country', 'N/A')}",
                f"Created: {getattr(ip, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(ip, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving IP address details: {e}"

    @mcp.tool()
    def list_ports_for_ip(
        ip_id: int,
        include_closed_port: bool = None,
        include_no_service: bool = None,
        created_from: str = None,
        created_to: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List all discovered ports belonging to a specific IP address.

        Args:
            ip_id: The IP address asset ID.
            include_closed_port: Include listings with closed ports.
            include_no_service: Include listings without a service.
            created_from: Filter ports created after a given date and time.
            created_to: Filter ports created before a given date and time.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = IPAddressesApi(get_api_client())
            kwargs = {"page": page, "page_size": min(page_size, 30)}
            if include_closed_port is not None:
                kwargs["include_closed_port"] = include_closed_port
            if include_no_service is not None:
                kwargs["include_no_service"] = include_no_service
            if created_from:
                kwargs["created_from"] = parse_date(created_from)
            if created_to:
                kwargs["created_to"] = parse_date(created_to)
            response = api.get_asset_ip_ports(id=ip_id, **_filter_kwargs(api.get_asset_ip_ports, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return f"No ports found for IP {ip_id}."

            total = get_total(response)
            lines = []
            for p in response.data:
                pid = getattr(p, 'id', '')
                port = getattr(p, 'port', '?')
                service = getattr(p, 'service', '')
                banner = getattr(p, 'banner', '')
                status = getattr(p, 'status', '')
                svc_str = f" ({service})" if service else ""
                banner_str = f" - {banner}" if banner else ""
                lines.append(f"• [ID:{pid}] :{port}{svc_str} {status}{banner_str}")

            header = f"Ports for IP {ip_id} ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing ports for IP: {e}"

    @mcp.tool()
    def get_ip_port_details(ip_id: int, port_id: int) -> str:
        """Get full details for a specific port belonging to an IP address.

        Args:
            ip_id: The IP address asset ID (as string).
            port_id: The port asset ID (as string).
        """
        try:
            api = IPAddressesApi(get_api_client())
            response = api.get_asset_ip_port_details(
                ip_id=int(ip_id), port_id=int(port_id)
            )

            p = response.data if hasattr(response, 'data') else response
            if not p:
                return f"Port {port_id} on IP {ip_id} not found."

            lines = [
                f"Port #{getattr(p, 'id', port_id)} on IP {ip_id}",
                f"Port: {getattr(p, 'port', 'N/A')}",
                f"IP: {getattr(p, 'ip', 'N/A')}",
                f"Service: {getattr(p, 'service', 'N/A')}",
                f"Banner: {getattr(p, 'banner', 'N/A')}",
                f"Status: {getattr(p, 'status', 'N/A')}",
                f"Created: {getattr(p, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(p, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving IP port details: {e}"

    # ── Domains ───────────────────────────────────────────────────

    @mcp.tool()
    def list_asset_domains(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered root domains.

        Args:
            asset_name: Search by domain name.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = DomainsApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            response = api.get_list_asset_domains(**_filter_kwargs(api.get_list_asset_domains, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No domains found."

            total = get_total(response)
            lines = []
            for d in response.data:
                did = getattr(d, 'id', '')
                name = getattr(d, 'name', 'Unknown')
                status = getattr(d, 'status', 'Unknown')
                live = " (live)" if getattr(d, 'live', False) else ""
                bus = format_bus(getattr(d, 'business_units', []))
                lines.append(f"• [ID:{did}] {name} - {status}{live}{bus}")

            header = f"Domains ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing domains: {e}"

    @mcp.tool()
    def get_asset_domain_details(domain_id: int) -> str:
        """Get full details for a specific domain.

        Args:
            domain_id: The domain asset ID.
        """
        try:
            api = DomainsApi(get_api_client())
            response = api.get_asset_domain_details(id=int(domain_id))

            d = response.data if hasattr(response, 'data') else response
            if not d:
                return f"Domain {domain_id} not found."

            lines = [
                f"Domain #{getattr(d, 'id', domain_id)}",
                f"Name: {getattr(d, 'name', 'N/A')}",
                f"Status: {getattr(d, 'status', 'N/A')}",
                f"Source: {getattr(d, 'source', 'N/A')}",
                f"Live: {getattr(d, 'live', 'N/A')}",
                f"Created: {getattr(d, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(d, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving domain details: {e}"

    # ── Subdomains ────────────────────────────────────────────────

    @mcp.tool()
    def list_asset_subdomains(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered subdomains.

        Args:
            asset_name: Search by subdomain name.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = SubdomainsApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            response = api.get_list_asset_subdomains(**_filter_kwargs(api.get_list_asset_subdomains, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No subdomains found."

            total = get_total(response)
            lines = []
            for s in response.data:
                sid = getattr(s, 'id', '')
                name = getattr(s, 'name', 'Unknown')
                status = getattr(s, 'status', 'Unknown')
                live = " (live)" if getattr(s, 'live', False) else ""
                bus = format_bus(getattr(s, 'business_units', []))
                lines.append(f"• [ID:{sid}] {name} - {status}{live}{bus}")

            header = f"Subdomains ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing subdomains: {e}"

    @mcp.tool()
    def get_asset_subdomain_details(subdomain_id: int) -> str:
        """Get full details for a specific subdomain.

        Args:
            subdomain_id: The subdomain asset ID.
        """
        try:
            api = SubdomainsApi(get_api_client())
            response = api.get_asset_subdomain_details(id=int(subdomain_id))

            s = response.data if hasattr(response, 'data') else response
            if not s:
                return f"Subdomain {subdomain_id} not found."

            lines = [
                f"Subdomain #{getattr(s, 'id', subdomain_id)}",
                f"Name: {getattr(s, 'name', 'N/A')}",
                f"Status: {getattr(s, 'status', 'N/A')}",
                f"Source: {getattr(s, 'source', 'N/A')}",
                f"Live: {getattr(s, 'live', 'N/A')}",
                f"Created: {getattr(s, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(s, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving subdomain details: {e}"

    # ── Ports ─────────────────────────────────────────────────────

    @mcp.tool()
    def list_asset_ports(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        include_closed_port: bool = None,
        include_no_service: bool = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered open ports across assets.

        Args:
            asset_name: Search by asset name.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            include_closed_port: Include listings with closed ports.
            include_no_service: Include listings without a service.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = PortsApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            if include_closed_port is not None:
                kwargs["include_closed_port"] = include_closed_port
            if include_no_service is not None:
                kwargs["include_no_service"] = include_no_service
            response = api.get_list_asset_ports(**_filter_kwargs(api.get_list_asset_ports, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No ports found."

            total = get_total(response)
            lines = []
            for p in response.data:
                pid = getattr(p, 'id', '')
                ip = getattr(p, 'ip', 'Unknown')
                port = getattr(p, 'port', '?')
                service = getattr(p, 'service', '')
                banner = getattr(p, 'banner', '')
                svc_str = f" ({service})" if service else ""
                banner_str = f" - {banner}" if banner else ""
                lines.append(f"• [ID:{pid}] {ip}:{port}{svc_str}{banner_str}")

            header = f"Ports ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing ports: {e}"

    @mcp.tool()
    def get_asset_port_details(port_id: int) -> str:
        """Get full details for a specific port including banner and service.

        Args:
            port_id: The port asset ID.
        """
        try:
            api = PortsApi(get_api_client())
            response = api.get_asset_port_details(id=int(port_id))

            p = response.data if hasattr(response, 'data') else response
            if not p:
                return f"Port {port_id} not found."

            lines = [
                f"Port #{getattr(p, 'id', port_id)}",
                f"IP: {getattr(p, 'ip', 'N/A')}",
                f"Port: {getattr(p, 'port', 'N/A')}",
                f"Service: {getattr(p, 'service', 'N/A')}",
                f"Banner: {getattr(p, 'banner', 'N/A')}",
                f"Status: {getattr(p, 'status', 'N/A')}",
                f"Created: {getattr(p, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(p, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving port details: {e}"

    # ── IP Ranges ─────────────────────────────────────────────────

    @mcp.tool()
    def list_asset_ip_ranges(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered IP ranges with ASN and country information.

        Args:
            asset_name: Search by IP range.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = IPRangesApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            response = api.get_list_asset_ipranges(**_filter_kwargs(api.get_list_asset_ipranges, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No IP ranges found."

            total = get_total(response)
            lines = []
            for r in response.data:
                rid = getattr(r, 'id', '')
                iprange = getattr(r, 'iprange', 'Unknown')
                asn = getattr(r, 'asn', '')
                desc = getattr(r, 'desc', '')
                country = getattr(r, 'country', '')
                status = getattr(r, 'status', 'Unknown')
                extras = []
                if asn:
                    extras.append(f"ASN:{asn}")
                if country:
                    extras.append(country)
                if desc:
                    extras.append(desc)
                extra_str = f" ({', '.join(extras)})" if extras else ""
                lines.append(f"• [ID:{rid}] {iprange} - {status}{extra_str}")

            header = f"IP Ranges ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing IP ranges: {e}"

    @mcp.tool()
    def get_asset_iprange_details(iprange_id: int) -> str:
        """Get full details for a specific IP range.

        Args:
            iprange_id: The IP range asset ID.
        """
        try:
            api = IPRangesApi(get_api_client())
            response = api.get_asset_iprange_details(id=int(iprange_id))

            r = response.data if hasattr(response, 'data') else response
            if not r:
                return f"IP range {iprange_id} not found."

            lines = [
                f"IP Range #{getattr(r, 'id', iprange_id)}",
                f"Range: {getattr(r, 'iprange', 'N/A')}",
                f"ASN: {getattr(r, 'asn', 'N/A')}",
                f"Description: {getattr(r, 'desc', 'N/A')}",
                f"Country: {getattr(r, 'country', 'N/A')}",
                f"Status: {getattr(r, 'status', 'N/A')}",
                f"Source: {getattr(r, 'source', 'N/A')}",
                f"Created: {getattr(r, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(r, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving IP range details: {e}"

    # ── Cloud Storage ─────────────────────────────────────────────

    @mcp.tool()
    def list_cloud_storage_assets(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered cloud storage assets (S3, GCS, Azure blobs, etc.).

        Args:
            asset_name: Search by storage URL keyword.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = CloudStorageApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            response = api.get_list_asset_cloud_storages(**_filter_kwargs(api.get_list_asset_cloud_storages, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No cloud storage assets found."

            total = get_total(response)
            lines = []
            for cs in response.data:
                csid = getattr(cs, 'id', '')
                name = getattr(cs, 'name', 'Unknown')
                platform = getattr(cs, 'platform', '')
                url = getattr(cs, 'url', '')
                status = getattr(cs, 'status', 'Unknown')
                bus = format_bus(getattr(cs, 'business_units', []))
                plat_str = f" [{platform}]" if platform else ""
                url_str = f" {url}" if url else ""
                lines.append(f"• [ID:{csid}] {name}{plat_str} - {status}{url_str}{bus}")

            header = f"Cloud Storage Assets ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing cloud storage assets: {e}"

    @mcp.tool()
    def get_asset_cloud_storage_details(cloud_storage_id: int) -> str:
        """Get full details for a specific cloud storage asset.

        Args:
            cloud_storage_id: The cloud storage asset ID.
        """
        try:
            api = CloudStorageApi(get_api_client())
            response = api.get_asset_cloud_storage_details(
                id=int(cloud_storage_id)
            )

            cs = response.data if hasattr(response, 'data') else response
            if not cs:
                return f"Cloud storage asset {cloud_storage_id} not found."

            lines = [
                f"Cloud Storage #{getattr(cs, 'id', cloud_storage_id)}",
                f"Name: {getattr(cs, 'name', 'N/A')}",
                f"Platform: {getattr(cs, 'platform', 'N/A')}",
                f"URL: {getattr(cs, 'url', 'N/A')}",
                f"Status: {getattr(cs, 'status', 'N/A')}",
                f"Source: {getattr(cs, 'source', 'N/A')}",
                f"Created: {getattr(cs, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(cs, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving cloud storage details: {e}"

    # ── Source Code Repositories ──────────────────────────────────

    @mcp.tool()
    def list_source_code_repositories(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered source code repositories.

        Args:
            asset_name: Search by repository name.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = RepositoriesApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            response = api.get_list_asset_repositories(**_filter_kwargs(api.get_list_asset_repositories, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No source code repositories found."

            total = get_total(response)
            lines = []
            for r in response.data:
                rid = getattr(r, 'id', '')
                name = getattr(r, 'name', 'Unknown')
                owner = getattr(r, 'owner', '')
                provider = getattr(r, 'provider', '')
                status = getattr(r, 'status', 'Unknown')
                bus = format_bus(getattr(r, 'business_units', []))
                owner_str = f" ({owner})" if owner else ""
                prov_str = f" [{provider}]" if provider else ""
                lines.append(f"• [ID:{rid}] {name}{owner_str}{prov_str} - {status}{bus}")

            header = f"Source Code Repositories ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing repositories: {e}"

    @mcp.tool()
    def get_asset_repository_details(repository_id: int) -> str:
        """Get full details for a specific source code repository.

        Args:
            repository_id: The repository asset ID.
        """
        try:
            api = RepositoriesApi(get_api_client())
            response = api.get_asset_repository_details(
                id=int(repository_id)
            )

            r = response.data if hasattr(response, 'data') else response
            if not r:
                return f"Repository {repository_id} not found."

            lines = [
                f"Repository #{getattr(r, 'id', repository_id)}",
                f"Name: {getattr(r, 'name', 'N/A')}",
                f"Owner: {getattr(r, 'owner', 'N/A')}",
                f"Provider: {getattr(r, 'provider', 'N/A')}",
                f"Status: {getattr(r, 'status', 'N/A')}",
                f"Source: {getattr(r, 'source', 'N/A')}",
                f"Created: {getattr(r, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(r, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving repository details: {e}"

    # ── Containers ────────────────────────────────────────────────

    @mcp.tool()
    def list_container_assets(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered container registry images.

        Args:
            asset_name: Search by container name.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = ContainersApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            response = api.get_list_asset_container(**_filter_kwargs(api.get_list_asset_container, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No container assets found."

            total = get_total(response)
            lines = []
            for c in response.data:
                cid = getattr(c, 'id', '')
                name = getattr(c, 'name', 'Unknown')
                owner = getattr(c, 'owner', '')
                platform = getattr(c, 'platform', '')
                status = getattr(c, 'status', 'Unknown')
                bus = format_bus(getattr(c, 'business_units', []))
                owner_str = f" ({owner})" if owner else ""
                plat_str = f" [{platform}]" if platform else ""
                lines.append(f"• [ID:{cid}] {name}{owner_str}{plat_str} - {status}{bus}")

            header = f"Container Assets ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing container assets: {e}"

    @mcp.tool()
    def get_asset_container_details(container_id: int) -> str:
        """Get full details for a specific container registry image.

        Args:
            container_id: The container asset ID.
        """
        try:
            api = ContainersApi(get_api_client())
            response = api.get_asset_container_details(
                id=int(container_id)
            )

            c = response.data if hasattr(response, 'data') else response
            if not c:
                return f"Container {container_id} not found."

            lines = [
                f"Container #{getattr(c, 'id', container_id)}",
                f"Name: {getattr(c, 'name', 'N/A')}",
                f"Owner: {getattr(c, 'owner', 'N/A')}",
                f"Platform: {getattr(c, 'platform', 'N/A')}",
                f"URL: {getattr(c, 'url', 'N/A')}",
                f"Status: {getattr(c, 'status', 'N/A')}",
                f"Source: {getattr(c, 'source', 'N/A')}",
                f"Created: {getattr(c, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(c, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving container details: {e}"

    # ── SaaS Platforms ────────────────────────────────────────────

    @mcp.tool()
    def list_saas_platforms(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered SaaS platform instances.

        Args:
            asset_name: Search by SaaS URL.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = SaaSPlatformsApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            response = api.get_list_asset_saas_platforms(**_filter_kwargs(api.get_list_asset_saas_platforms, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No SaaS platforms found."

            total = get_total(response)
            lines = []
            for s in response.data:
                sid = getattr(s, 'id', '')
                url = getattr(s, 'url', 'Unknown')
                provider = getattr(s, 'provider', '')
                status = getattr(s, 'status', 'Unknown')
                bus = format_bus(getattr(s, 'business_units', []))
                prov_str = f" [{provider}]" if provider else ""
                lines.append(f"• [ID:{sid}] {url}{prov_str} - {status}{bus}")

            header = f"SaaS Platforms ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing SaaS platforms: {e}"

    @mcp.tool()
    def get_asset_saas_details(saas_id: int) -> str:
        """Get full details for a specific SaaS platform instance.

        Args:
            saas_id: The SaaS platform asset ID.
        """
        try:
            api = SaaSPlatformsApi(get_api_client())
            response = api.get_asset_saas_platform_details(
                id=int(saas_id)
            )

            s = response.data if hasattr(response, 'data') else response
            if not s:
                return f"SaaS platform {saas_id} not found."

            lines = [
                f"SaaS Platform #{getattr(s, 'id', saas_id)}",
                f"URL: {getattr(s, 'url', 'N/A')}",
                f"Provider: {getattr(s, 'provider', 'N/A')}",
                f"Status: {getattr(s, 'status', 'N/A')}",
                f"Source: {getattr(s, 'source', 'N/A')}",
                f"Created: {getattr(s, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(s, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving SaaS platform details: {e}"

    # ── Mobile Applications ───────────────────────────────────────

    @mcp.tool()
    def list_mobile_app_assets(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered mobile applications.

        Args:
            asset_name: Search by app name.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = MobileApplicationsApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            response = api.get_list_asset_mobile_apps(**_filter_kwargs(api.get_list_asset_mobile_apps, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No mobile applications found."

            total = get_total(response)
            lines = []
            for m in response.data:
                mid = getattr(m, 'id', '')
                name = getattr(m, 'name', 'Unknown')
                publisher = getattr(m, 'publisher', '')
                platform = getattr(m, 'platform', '')
                status = getattr(m, 'status', 'Unknown')
                bus = format_bus(getattr(m, 'business_units', []))
                pub_str = f" by {publisher}" if publisher else ""
                plat_str = f" [{platform}]" if platform else ""
                lines.append(f"• [ID:{mid}] {name}{pub_str}{plat_str} - {status}{bus}")

            header = f"Mobile Applications ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing mobile applications: {e}"

    @mcp.tool()
    def get_asset_mobile_app_details(mobile_app_id: int) -> str:
        """Get full details for a specific mobile application.

        Args:
            mobile_app_id: The mobile application asset ID.
        """
        try:
            api = MobileApplicationsApi(get_api_client())
            response = api.get_asset_mobile_app_details(
                id=int(mobile_app_id)
            )

            m = response.data if hasattr(response, 'data') else response
            if not m:
                return f"Mobile application {mobile_app_id} not found."

            lines = [
                f"Mobile App #{getattr(m, 'id', mobile_app_id)}",
                f"Name: {getattr(m, 'name', 'N/A')}",
                f"Publisher: {getattr(m, 'publisher', 'N/A')}",
                f"Platform: {getattr(m, 'platform', 'N/A')}",
                f"App ID: {getattr(m, 'app_id', 'N/A')}",
                f"URL: {getattr(m, 'url', 'N/A')}",
                f"Status: {getattr(m, 'status', 'N/A')}",
                f"Source: {getattr(m, 'source', 'N/A')}",
                f"Created: {getattr(m, 'created_at', 'N/A')}",
            ]
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving mobile app details: {e}"

    # ── Cloud Assets (Integration) ────────────────────────────────

    @mcp.tool()
    def list_cloud_assets(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        provider: str = None,
        super_type: str = None,
        sub_type: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered cloud assets (AWS, GCP, Azure, etc.).

        Args:
            asset_name: Search by cloud asset name.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            provider: Filter assets by cloud provider.
            super_type: Filter assets by cloud asset type.
            sub_type: Filter assets by cloud asset sub-type.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = CloudIntegrationAssetsApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            if provider:
                kwargs["provider"] = provider
            if super_type:
                kwargs["super_type"] = super_type
            if sub_type:
                kwargs["sub_type"] = sub_type
            response = api.get_list_asset_cloud_asset(**_filter_kwargs(api.get_list_asset_cloud_asset, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No cloud assets found."

            total = get_total(response)
            lines = []
            for ca in response.data:
                caid = getattr(ca, 'id', '')
                name = getattr(ca, 'name', 'Unknown')
                prov = getattr(ca, 'provider', '')
                status = getattr(ca, 'status', 'Unknown')
                bus = format_bus(getattr(ca, 'business_units', []))
                prov_str = f" [{prov}]" if prov else ""
                lines.append(f"• [ID:{caid}] {name}{prov_str} - {status}{bus}")

            header = f"Cloud Assets ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing cloud assets: {e}"

    @mcp.tool()
    def get_cloud_asset_details(cloud_asset_id: int) -> str:
        """Get full details for a specific cloud asset.

        Args:
            cloud_asset_id: The cloud asset ID.
        """
        try:
            api = CloudIntegrationAssetsApi(get_api_client())
            response = api.get_asset_cloud_asset_details(
                id=int(cloud_asset_id)
            )

            ca = response.data if hasattr(response, 'data') else response
            if not ca:
                return f"Cloud asset {cloud_asset_id} not found."

            lines = [
                f"Cloud Asset #{getattr(ca, 'id', cloud_asset_id)}",
                f"Name: {getattr(ca, 'name', 'N/A')}",
                f"Provider: {getattr(ca, 'provider', 'N/A')}",
                f"Status: {getattr(ca, 'status', 'N/A')}",
                f"Source: {getattr(ca, 'source', 'N/A')}",
            ]
            hostname = getattr(ca, 'hostname', None)
            if hostname:
                lines.append(f"Hostname: {hostname}")
            cloud_resource_id = getattr(ca, 'cloud_resource_id', None)
            if cloud_resource_id:
                lines.append(f"Cloud Resource ID: {cloud_resource_id}")
            super_type = getattr(ca, 'super_type', None)
            if super_type:
                lines.append(f"Super Type: {super_type}")
            sub_type = getattr(ca, 'sub_type', None)
            if sub_type:
                lines.append(f"Sub Type: {sub_type}")
            criticality = getattr(ca, 'criticality', None)
            if criticality:
                lines.append(f"Criticality: {criticality}")
            lines.append(f"Created: {getattr(ca, 'created_at', 'N/A')}")
            bus = format_bus(getattr(ca, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving cloud asset details: {e}"

    # ── API Documentations ────────────────────────────────────────

    @mcp.tool()
    def list_api_documentations(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered API documentation assets.

        Args:
            asset_name: Search by API URL/path.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = APIDocumentationApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            response = api.get_list_asset_api_documentation(**_filter_kwargs(api.get_list_asset_api_documentation, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No API documentations found."

            total = get_total(response)
            lines = []
            for ad in response.data:
                adid = getattr(ad, 'id', '')
                name = getattr(ad, 'name', None) or getattr(ad, 'url', None) or 'Unknown'
                url = getattr(ad, 'url', '')
                status = getattr(ad, 'status', 'Unknown')
                bus = format_bus(getattr(ad, 'business_units', []))
                url_str = f" - {url}" if url and url != name else ""
                lines.append(f"• [ID:{adid}] {name}{url_str} - {status}{bus}")

            header = f"API Documentations ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing API documentations: {e}"

    @mcp.tool()
    def get_api_documentation_details(api_documentation_id: int) -> str:
        """Get full details for a specific API documentation asset.

        Args:
            api_documentation_id: The API documentation asset ID.
        """
        try:
            api = APIDocumentationApi(get_api_client())
            response = api.get_asset_api_documentation_details(
                id=int(api_documentation_id)
            )

            ad = response.data if hasattr(response, 'data') else response
            if not ad:
                return f"API documentation asset {api_documentation_id} not found."

            lines = [
                f"API Documentation #{getattr(ad, 'id', api_documentation_id)}",
                f"Name: {getattr(ad, 'name', 'N/A')}",
                f"URL: {getattr(ad, 'url', 'N/A')}",
                f"Platform: {getattr(ad, 'platform', 'N/A')}",
                f"Status: {getattr(ad, 'status', 'N/A')}",
                f"Source: {getattr(ad, 'source', 'N/A')}",
                f"Created: {getattr(ad, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(ad, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving API documentation details: {e}"

    # ── Package Managers ──────────────────────────────────────────

    @mcp.tool()
    def list_package_managers(
        asset_name: str = None,
        statuses: str = None,
        business_unit_ids: str = None,
        created_from: str = None,
        created_to: str = None,
        source: str = None,
        integration_connections: str = None,
        custom_property_key: str = None,
        custom_property_value: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List discovered package manager registry assets.

        Args:
            asset_name: Search by package manager name.
            statuses: Comma-separated status filters.
            business_unit_ids: Comma-separated business unit IDs.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            source: Filter assets by the source that discovered the asset.
            integration_connections: Filter assets by integration connections.
            custom_property_key: Filter assets by custom property key.
            custom_property_value: Filter assets by custom property value.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = PackageManagersApi(get_api_client())
            kwargs = _build_asset_kwargs(
                page, page_size, asset_name, statuses, business_unit_ids,
                created_from, created_to, source, integration_connections,
                custom_property_key, custom_property_value
            )
            response = api.get_list_asset_package_managers(**_filter_kwargs(api.get_list_asset_package_managers, kwargs))

            if not hasattr(response, 'data') or not response.data:
                return "No package managers found."

            total = get_total(response)
            lines = []
            for pm in response.data:
                pmid = getattr(pm, 'id', '')
                name = getattr(pm, 'name', 'Unknown')
                platform = getattr(pm, 'platform', '')
                status = getattr(pm, 'status', 'Unknown')
                bus = format_bus(getattr(pm, 'business_units', []))
                plat_str = f" [{platform}]" if platform else ""
                lines.append(f"• [ID:{pmid}] {name}{plat_str} - {status}{bus}")

            header = f"Package Managers ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing package managers: {e}"

    @mcp.tool()
    def get_package_manager_details(package_manager_id: int) -> str:
        """Get full details for a specific package manager asset.

        Args:
            package_manager_id: The package manager asset ID.
        """
        try:
            api = PackageManagersApi(get_api_client())
            response = api.get_asset_package_manager_details(
                id=int(package_manager_id)
            )

            pm = response.data if hasattr(response, 'data') else response
            if not pm:
                return f"Package manager asset {package_manager_id} not found."

            lines = [
                f"Package Manager #{getattr(pm, 'id', package_manager_id)}",
                f"Name: {getattr(pm, 'name', 'N/A')}",
                f"Platform: {getattr(pm, 'platform', 'N/A')}",
                f"Status: {getattr(pm, 'status', 'N/A')}",
                f"Source: {getattr(pm, 'source', 'N/A')}",
                f"Created: {getattr(pm, 'created_at', 'N/A')}",
            ]
            bus = format_bus(getattr(pm, 'business_units', []))
            if bus:
                lines.append(f"Business Units:{bus}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving package manager details: {e}"

    # ── Update Asset Status (unified) ─────────────────────────────

    @mcp.tool()
    def update_asset_status(
        asset_type: str,
        asset_id: int,
        status: str,
        status_reason: str = None,
    ) -> str:
        """Update the status of any asset type.

        Args:
            asset_type: One of: domain, subdomain, ip, ip_range, container, cloud_storage, saas_platform, mobile_app, repository, cloud_asset, api_documentation, package_manager.
            asset_id: The asset ID to update.
            status: The new status value.
            status_reason: Optional reason for the status change.
        """
        try:
            client = get_api_client()

            legacy_types = {
                "domain": (DomainsApi, "update_asset_domain_status"),
                "subdomain": (SubdomainsApi, "update_asset_subdomain_status"),
                "ip": (IPAddressesApi, "update_asset_ip_status"),
                "ip_range": (IPRangesApi, "update_asset_ip_range_status"),
            }
            nextgen_types = {
                "container": (ContainersApi, "update_asset_container_status"),
                "cloud_storage": (CloudStorageApi, "update_asset_cloud_storage_status"),
                "saas_platform": (SaaSPlatformsApi, "update_asset_saas_platform_status"),
                "mobile_app": (MobileApplicationsApi, "update_asset_mobile_app_status"),
                "repository": (RepositoriesApi, "update_asset_repository_status"),
                "cloud_asset": (CloudIntegrationAssetsApi, "update_asset_cloud_asset_status"),
                "api_documentation": (APIDocumentationApi, "update_asset_api_documentation_status"),
                "package_manager": (PackageManagersApi, "update_asset_package_manager_status"),
            }

            if asset_type in legacy_types:
                api_cls, method_name = legacy_types[asset_type]
                dto_kwargs = {"status": status}
                if status_reason:
                    dto_kwargs["status_reason"] = status_reason
                dto = UpdateClientLegacyAssetStatusDto(**dto_kwargs)
                api = api_cls(client)
                method = getattr(api, method_name)
                param_name = f"update_client_legacy_asset_status_dto"
                method(id=asset_id, **{param_name: dto})
            elif asset_type in nextgen_types:
                api_cls, method_name = nextgen_types[asset_type]
                dto_kwargs = {"status": status}
                if status_reason:
                    dto_kwargs["status_reason"] = status_reason

                if asset_type == "cloud_asset":
                    dto = UpdateClientCloudAssetStatusDto(**dto_kwargs)
                    param_name = "update_client_cloud_asset_status_dto"
                elif asset_type == "api_documentation":
                    dto = UpdateApiDocumentationStatusDto(**dto_kwargs)
                    param_name = "update_api_documentation_status_dto"
                else:
                    dto = UpdateClientNextGenAssetStatusDto(**dto_kwargs)
                    param_name = "update_client_next_gen_asset_status_dto"

                api = api_cls(client)
                method = getattr(api, method_name)
                method(id=asset_id, **{param_name: dto})
            else:
                valid = sorted(list(legacy_types.keys()) + list(nextgen_types.keys()))
                return f"Unknown asset type '{asset_type}'. Valid types: {', '.join(valid)}"

            return f"Asset {asset_type} {asset_id} status updated to: {status}"
        except Exception as e:
            return f"Error updating asset status: {e}"

    # ── Add Seed Asset ────────────────────────────────────────────

    @mcp.tool()
    def add_seed_asset(
        asset_type: str,
        asset_value: str,
        asset_title: str = None,
    ) -> str:
        """Submit a new seed asset for discovery and monitoring.

        Args:
            asset_type: Asset type (e.g. domain, ip, ip_range).
            asset_value: The asset value (e.g. "example.com", "1.2.3.4").
            asset_title: Optional display title for the asset.
        """
        try:
            api = AddAssetApi(get_api_client())
            seed = ClientSeedData(
                title=asset_title or asset_value,
                type=asset_type,
                value=asset_value,
            )
            body = CreateClientSeedDataRequestBody(data=[seed])
            response = api.submit_asset(create_client_seed_data_request_body=body)

            data = response.data if hasattr(response, 'data') else response
            return f"Seed asset submitted: {asset_type} = {asset_value}" + (
                f" (title: {asset_title})" if asset_title else ""
            )
        except Exception as e:
            return f"Error submitting seed asset: {e}"
