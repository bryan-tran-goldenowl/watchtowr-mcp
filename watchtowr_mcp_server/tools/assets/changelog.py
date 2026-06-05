from watchtowr_api_sdk.api.activity_log_api import ActivityLogApi

from ...client import get_api_client, get_total, supported_kwargs


def register_asset_changelog_tools(mcp):

    @mcp.tool()
    def get_asset_changelog(
        asset_type: str,
        asset_id: int,
        page: int = 1,
        page_size: int = 10,
    ) -> str:
        """Get change history (changelog) for a specific asset.

        Args:
            asset_type: Asset type (domain, subdomain, ip, ip_range, cloud_storage, repository, container, mobile_app, saas_platform, api_documentation, package_manager).
            asset_id: The asset ID.
            page: Page number.
            page_size: Results per page (max 30).
        """
        try:
            api = ActivityLogApi(get_api_client())
            kwargs = {
                "page": page,
                "page_size": min(page_size, 30),
                "search": f"{asset_type}:{asset_id}",
            }
            response = api.get_list_activity_logs(
                **supported_kwargs(api.get_list_activity_logs, kwargs)
            )

            if not hasattr(response, "data") or not response.data:
                return f"No changelog entries found for {asset_type} #{asset_id}."

            total = get_total(response) or 0
            lines = [f"Asset Changelog for {asset_type} #{asset_id} ({len(response.data)} of {total}):"]
            lines.append("")

            for entry in response.data:
                ts = getattr(entry, "created_at", "")
                action = getattr(entry, "type", "") or getattr(entry, "action", "unknown")
                description = getattr(entry, "description", "") or getattr(entry, "message", "")
                user = getattr(entry, "user_name", "") or getattr(entry, "user", {})
                if hasattr(user, "name"):
                    user = user.name

                line = f"[{ts}] {action}"
                if description:
                    line += f" — {description}"
                if user:
                    line += f" (by {user})"
                lines.append(line)

            return "\n".join(lines)
        except Exception as e:
            return f"Error: {str(e)}"
