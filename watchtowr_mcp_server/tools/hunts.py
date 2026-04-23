from watchtowr_api.api.hunts_api import HuntsApi

from ..client import get_api_client, get_total, parse_date, severity_display


def register_hunt_tools(mcp):

    @mcp.tool()
    def list_recent_hunts(page_size: int = 10) -> str:
        """List recent hunts with their findings and asset counts.

        Args:
            page_size: Number of results per page (max 30).
        """
        try:
            api = HuntsApi(get_api_client())
            response = api.get_client_hunts(page_size=min(page_size, 30))

            if not hasattr(response, 'data') or not response.data:
                return "No recent hunts found."

            total = get_total(response)
            lines = []
            for h in response.data:
                hid = getattr(h, 'id', '')
                title = getattr(h, 'title', 'Unnamed hunt')
                status = getattr(h, 'status', 'Unknown')
                priority = getattr(h, 'priority', '')
                hunt_type = getattr(h, 'type', '')
                findings = getattr(h, 'total_findings', 0)
                assets = getattr(h, 'total_assets', 0)
                created = getattr(h, 'created_at', '')
                extras = []
                if priority:
                    extras.append(priority)
                if hunt_type:
                    extras.append(hunt_type)
                extra_str = f" ({', '.join(extras)})" if extras else ""
                lines.append(
                    f"• [ID:{hid}] {title} - {status}{extra_str} "
                    f"[{findings} findings, {assets} assets] (created: {created})"
                )

            header = f"Recent Hunts ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error retrieving recent hunts: {e}"

    @mcp.tool()
    def get_hunt_details(hunt_id: int) -> str:
        """Get full details for a specific hunt including description, hypothesis, and references.

        Args:
            hunt_id: The hunt ID to retrieve.
        """
        try:
            api = HuntsApi(get_api_client())
            response = api.show_the_detail_hunt(id=hunt_id)

            h = response.data if hasattr(response, 'data') else response
            if not h:
                return f"Hunt {hunt_id} not found."

            lines = [
                f"Hunt #{getattr(h, 'id', hunt_id)}",
                f"Title: {getattr(h, 'title', 'N/A')}",
                f"Status: {getattr(h, 'status', 'N/A')}",
                f"Priority: {getattr(h, 'priority', 'N/A')}",
                f"Type: {getattr(h, 'type', 'N/A')}",
                f"Total Findings: {getattr(h, 'total_findings', 0)}",
                f"Total Assets: {getattr(h, 'total_assets', 0)}",
                f"Created: {getattr(h, 'created_at', 'N/A')}",
            ]

            completed_at = getattr(h, 'completed_at', None)
            if completed_at:
                lines.append(f"Completed: {completed_at}")
                completed_by = getattr(h, 'completed_by', None)
                if completed_by:
                    lines.append(f"Completed by: {completed_by}")

            requested_by = getattr(h, 'requested_by', None)
            if requested_by:
                lines.append(f"Requested by: {requested_by}")

            desc = getattr(h, 'description', None)
            if desc:
                lines.append(f"\nDescription:\n{desc}")

            hypothesis = getattr(h, 'hypothesis', None)
            if hypothesis:
                lines.append(f"\nHypothesis:\n{hypothesis}")

            refs = getattr(h, 'references', [])
            if refs:
                lines.append("\nReferences:")
                for ref in refs:
                    lines.append(f"  • {ref}")

            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving hunt details: {e}"

    @mcp.tool()
    def list_findings_by_hunt(hunt_id: int, page: int = 1, page_size: int = 30) -> str:
        """List all findings discovered by a specific hunt.

        Args:
            hunt_id: The hunt ID.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = HuntsApi(get_api_client())
            response = api.get_list_finding_by_hunt(
                id=hunt_id, page=page, page_size=min(page_size, 30)
            )

            if not hasattr(response, 'data') or not response.data:
                return f"No findings for hunt {hunt_id}."

            total = get_total(response)
            lines = []
            for f in response.data:
                fid = getattr(f, 'id', '')
                severity = severity_display(getattr(f, 'severity', None))
                title = getattr(f, 'title', 'No title')
                status = getattr(f, 'status', 'Unknown')
                lines.append(f"• [ID:{fid}] [{severity}] {title} ({status})")

            header = f"Findings for Hunt {hunt_id} ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error retrieving findings for hunt: {e}"

    @mcp.tool()
    def list_assets_by_hunt(hunt_id: int, page: int = 1, page_size: int = 30) -> str:
        """List all assets tested by a specific hunt.

        Args:
            hunt_id: The hunt ID.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = HuntsApi(get_api_client())
            response = api.get_list_asset_by_hunt(
                id=hunt_id, page=page, page_size=min(page_size, 30)
            )

            if not hasattr(response, 'data') or not response.data:
                return f"No assets for hunt {hunt_id}."

            total = get_total(response)
            lines = []
            for a in response.data:
                aid = getattr(a, 'id', '')
                name = getattr(a, 'name', 'Unknown')
                asset_type = getattr(a, 'type', '')
                status = getattr(a, 'status', 'Unknown')
                type_str = f" [{asset_type}]" if asset_type else ""
                lines.append(f"• [ID:{aid}] {name}{type_str} - {status}")

            header = f"Assets for Hunt {hunt_id} ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error retrieving assets for hunt: {e}"

    @mcp.tool()
    def search_hunts(
        hunt_search: str = None,
        statuses: str = None,
        types: str = None,
        priorities: str = None,
        created_from: str = None,
        created_to: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """Search hunts with rich filters.

        Args:
            hunt_search: Search by hunt name keyword.
            statuses: Comma-separated hunt statuses.
            types: Comma-separated hunt types.
            priorities: Comma-separated priorities.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = HuntsApi(get_api_client())
            kwargs = {"page": page, "page_size": min(page_size, 30)}
            if hunt_search:
                kwargs["hunt_search"] = hunt_search
            if statuses:
                kwargs["statuses"] = statuses
            if types:
                kwargs["types"] = types
            if priorities:
                kwargs["priorities"] = priorities
            if created_from:
                kwargs["created_from"] = parse_date(created_from)
            if created_to:
                kwargs["created_to"] = parse_date(created_to)

            response = api.get_client_hunts(**kwargs)

            if not hasattr(response, 'data') or not response.data:
                return "No hunts match the search criteria."

            total = get_total(response)
            lines = []
            for h in response.data:
                hid = getattr(h, 'id', '')
                title = getattr(h, 'title', 'Unnamed')
                status = getattr(h, 'status', 'Unknown')
                priority = getattr(h, 'priority', '')
                findings = getattr(h, 'total_findings', 0)
                assets = getattr(h, 'total_assets', 0)
                pri_str = f" [{priority}]" if priority else ""
                lines.append(
                    f"• [ID:{hid}] {title} - {status}{pri_str} "
                    f"[{findings} findings, {assets} assets]"
                )

            header = f"Hunts ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error searching hunts: {e}"

    @mcp.tool()
    def get_hunt_impact_summary(hunt_id: int) -> str:
        """Get a combined impact summary for a hunt: detail, findings by severity, and assets tested.

        Note: severity breakdown covers the first page of findings (up to 30). Use list_findings_by_hunt for full pagination.

        Args:
            hunt_id: The hunt ID.
        """
        try:
            api = HuntsApi(get_api_client())

            detail_resp = api.show_the_detail_hunt(id=hunt_id)
            h = detail_resp.data if hasattr(detail_resp, 'data') else detail_resp
            if not h:
                return f"Hunt {hunt_id} not found."

            lines = [
                f"Hunt Impact Summary: {getattr(h, 'title', 'N/A')}",
                f"Status: {getattr(h, 'status', 'N/A')}",
                f"Priority: {getattr(h, 'priority', 'N/A')}",
                f"Total Findings: {getattr(h, 'total_findings', 0)}",
                f"Total Assets: {getattr(h, 'total_assets', 0)}",
            ]

            hypothesis = getattr(h, 'hypothesis', None)
            if hypothesis:
                lines.append(f"Hypothesis: {hypothesis}")

            findings_resp = api.get_list_finding_by_hunt(id=hunt_id, page_size=30)
            if hasattr(findings_resp, 'data') and findings_resp.data:
                severity_counts = {}
                for f in findings_resp.data:
                    sev = severity_display(getattr(f, 'severity', None))
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1
                lines.append("\nFindings by Severity:")
                ordered_sevs = ["Critical", "High", "Medium", "Low", "Info"]
                for sev in ordered_sevs:
                    if sev in severity_counts:
                        lines.append(f"  • {sev}: {severity_counts[sev]}")
                unknown_sevs = {k: v for k, v in severity_counts.items()
                                if k not in ordered_sevs}
                for sev, count in unknown_sevs.items():
                    lines.append(f"  • {sev}: {count}")

            assets_resp = api.get_list_asset_by_hunt(id=hunt_id, page_size=30)
            if hasattr(assets_resp, 'data') and assets_resp.data:
                lines.append("\nAssets Tested:")
                for a in assets_resp.data[:10]:
                    name = getattr(a, 'name', 'Unknown')
                    asset_type = getattr(a, 'type', '')
                    type_str = f" [{asset_type}]" if asset_type else ""
                    lines.append(f"  • {name}{type_str}")
                if len(assets_resp.data) > 10:
                    lines.append(f"  ... and {len(assets_resp.data) - 10} more")

            return "\n".join(lines)
        except Exception as e:
            return f"Error generating hunt impact summary: {e}"
