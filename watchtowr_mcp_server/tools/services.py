from watchtowr_api_sdk.api.service_discovery_api import ServiceDiscoveryApi

from ..client import get_api_client, get_total, parse_date, format_bus


def register_service_tools(mcp):

    @mcp.tool()
    def list_services(
        search: str = None,
        countries: str = None,
        port_numbers: str = None,
        port_services: str = None,
        business_unit_ids: str = None,
        include_closed_port: bool = False,
        created_from: str = None,
        created_to: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """List exposed services across the attack surface with technology, port, and country info.

        Args:
            search: Search keyword.
            countries: Comma-separated country codes.
            port_numbers: Comma-separated port numbers.
            port_services: Comma-separated service names.
            business_unit_ids: Comma-separated business unit IDs.
            include_closed_port: Whether to include closed ports (default false).
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = ServiceDiscoveryApi(get_api_client())
            kwargs = {"page": page, "page_size": min(page_size, 30)}
            if search:
                kwargs["search"] = search
            if countries:
                kwargs["countries"] = countries
            if port_numbers:
                kwargs["port_numbers"] = port_numbers
            if port_services:
                kwargs["port_services"] = port_services
            if business_unit_ids:
                kwargs["business_unit_ids"] = business_unit_ids
            if include_closed_port:
                kwargs["include_closed_port"] = include_closed_port
            if created_from:
                kwargs["created_from"] = parse_date(created_from)
            if created_to:
                kwargs["created_to"] = parse_date(created_to)

            response = api.get_list_service_listing(**kwargs)

            if not hasattr(response, 'data') or not response.data:
                return "No services found."

            total = get_total(response)
            lines = []
            for s in response.data:
                sid = getattr(s, 'id', '')
                ip = getattr(s, 'ip', 'Unknown')
                port = getattr(s, 'port', '?')
                service = getattr(s, 'service', '')
                country = getattr(s, 'country', '')
                techs = getattr(s, 'technologies', [])
                tech_names = [getattr(t, 'display_name', getattr(t, 'name', ''))
                              for t in techs] if techs else []
                tech_str = f" [{', '.join(tech_names)}]" if tech_names else ""
                svc_str = f" ({service})" if service else ""
                country_str = f" [{country}]" if country else ""
                lines.append(f"• [ID:{sid}] {ip}:{port}{svc_str}{tech_str}{country_str}")

            header = f"Services ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error listing services: {e}"

    @mcp.tool()
    def search_services_by_technology(
        technology_ids: str = None,
        port_numbers: str = None,
        port_services: str = None,
        service_type_ids: str = None,
        countries: str = None,
        business_unit_ids: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """Search services filtered by technology, port, or service type.

        Args:
            technology_ids: Comma-separated technology IDs.
            port_numbers: Comma-separated port numbers.
            port_services: Comma-separated service names (e.g. "http,ssh").
            service_type_ids: Comma-separated service type IDs.
            countries: Comma-separated country codes.
            business_unit_ids: Comma-separated business unit IDs.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = ServiceDiscoveryApi(get_api_client())
            kwargs = {"page": page, "page_size": min(page_size, 30)}
            if technology_ids:
                kwargs["technology_ids"] = technology_ids
            if port_numbers:
                kwargs["port_numbers"] = port_numbers
            if port_services:
                kwargs["port_services"] = port_services
            if service_type_ids:
                kwargs["service_type_ids"] = service_type_ids
            if countries:
                kwargs["countries"] = countries
            if business_unit_ids:
                kwargs["business_unit_ids"] = business_unit_ids

            response = api.get_list_service_listing(**kwargs)

            if not hasattr(response, 'data') or not response.data:
                return "No services match the criteria."

            total = get_total(response)
            lines = []
            for s in response.data:
                sid = getattr(s, 'id', '')
                ip = getattr(s, 'ip', 'Unknown')
                port = getattr(s, 'port', '?')
                service = getattr(s, 'service', '')
                banner = getattr(s, 'banner', '')
                techs = getattr(s, 'technologies', [])
                tech_names = [getattr(t, 'display_name', getattr(t, 'name', ''))
                              for t in techs] if techs else []
                tech_str = f" [{', '.join(tech_names)}]" if tech_names else ""
                svc_str = f" ({service})" if service else ""
                banner_str = f" - {banner}" if banner else ""
                lines.append(f"• [ID:{sid}] {ip}:{port}{svc_str}{tech_str}{banner_str}")

            header = f"Services ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error searching services: {e}"
