from watchtowr_api.api.findings_api import FindingsApi
from watchtowr_api.models.update_client_finding_status_request_body import UpdateClientFindingStatusRequestBody

from ..client import get_api_client, get_total, normalize_severities, parse_date, severity_display
from ..constants import SUMMARY_SEVERITIES


def register_findings_tools(mcp):

    @mcp.tool()
    def list_cisa_kev_findings(page_size: int = 30) -> str:
        """List findings tagged as CISA-KEV (Known Exploited Vulnerabilities).

        Args:
            page_size: Number of results per page (max 30).
        """
        try:
            api = FindingsApi(get_api_client())
            response = api.get_list_findings(tags="CISA-KEV", page_size=min(page_size, 30))

            if not hasattr(response, 'data') or not response.data:
                return "No CISA-KEV findings found."

            total = get_total(response)
            lines = []
            for f in response.data:
                fid = getattr(f, 'id', '')
                severity = severity_display(getattr(f, 'severity', None))
                title = getattr(f, 'title', 'No title')
                status = getattr(f, 'status', 'Unknown')
                lines.append(f"• [ID:{fid}] [{severity}] {title} ({status})")

            header = f"CISA-KEV Findings ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error retrieving CISA-KEV findings: {e}"

    @mcp.tool()
    def list_findings_by_severity(severity: str = "Critical", page_size: int = 30) -> str:
        """List findings filtered by severity level.

        Args:
            severity: Severity level - Critical, High, Medium, or Low.
            page_size: Number of results per page (max 30).
        """
        try:
            api = FindingsApi(get_api_client())
            response = api.get_list_findings(
                severities=normalize_severities(severity),
                page_size=min(page_size, 30),
            )

            if not hasattr(response, 'data') or not response.data:
                return f"No {severity} severity findings found."

            total = get_total(response)
            lines = []
            for f in response.data:
                fid = getattr(f, 'id', '')
                title = getattr(f, 'title', 'No title')
                status = getattr(f, 'status', 'Unknown')
                lines.append(f"• [ID:{fid}] {title} ({status})")

            header = f"{severity} Severity Findings ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error retrieving {severity} findings: {e}"

    @mcp.tool()
    def get_finding_details(finding_id: int) -> str:
        """Get full details for a specific finding including description, evidence, CVSS, CVE, EPSS, and retest history.

        Args:
            finding_id: The finding ID to retrieve.
        """
        try:
            api = FindingsApi(get_api_client())
            response = api.get_finding_details(id=finding_id, api_token="")

            finding = response.data if hasattr(response, 'data') else response
            if not finding:
                return f"Finding {finding_id} not found."

            lines = [f"Finding #{getattr(finding, 'id', finding_id)}"]
            lines.append(f"Title: {getattr(finding, 'title', 'N/A')}")
            lines.append(f"Severity: {severity_display(getattr(finding, 'severity', None))}")
            lines.append(f"Status: {getattr(finding, 'status', 'N/A')}")

            cvss = getattr(finding, 'cvssv3_score', None)
            if cvss is not None:
                lines.append(f"CVSS v3: {cvss}")
                metrics = getattr(finding, 'cvssv3_metrics', None)
                if metrics:
                    lines.append(f"CVSS Metrics: {metrics}")

            cve = getattr(finding, 'cve_id', None)
            if cve:
                lines.append(f"CVE: {cve}")

            epss = getattr(finding, 'epss_score', None)
            if epss is not None:
                lines.append(f"EPSS Score: {epss}")

            desc = getattr(finding, 'description', None)
            if desc:
                lines.append(f"\nDescription:\n{desc}")

            impact = getattr(finding, 'impact', None)
            if impact:
                lines.append(f"\nImpact:\n{impact}")

            evidence = getattr(finding, 'evidence', None)
            if evidence:
                lines.append(f"\nEvidence:\n{evidence}")

            recommendation = getattr(finding, 'recommendation', None)
            if recommendation:
                lines.append(f"\nRecommendation:\n{recommendation}")

            tags = getattr(finding, 'tags', [])
            if tags:
                tag_names = [getattr(t, 'name', str(t)) for t in tags]
                lines.append(f"\nTags: {', '.join(tag_names)}")

            assignee = getattr(finding, 'assigned_user', None)
            if assignee:
                lines.append(f"Assigned to: {getattr(assignee, 'name', 'N/A')}")

            lines.append(f"Created: {getattr(finding, 'created_at', 'N/A')}")

            return "\n".join(lines)
        except Exception as e:
            return f"Error retrieving finding details: {e}"

    @mcp.tool()
    def search_findings(
        finding_title: str = None,
        severities: str = None,
        statuses: str = None,
        asset_title: str = None,
        asset_types: str = None,
        assignee: str = None,
        tags: str = None,
        business_unit_ids: str = None,
        finding_impact_threshold: str = None,
        created_from: str = None,
        created_to: str = None,
        page: int = 1,
        page_size: int = 30,
    ) -> str:
        """Search findings with rich filters.

        Args:
            finding_title: Search by finding title keyword.
            severities: Comma-separated severities (Critical,High,Medium,Low).
            statuses: Comma-separated statuses.
            asset_title: Search by asset title.
            asset_types: Comma-separated asset types.
            assignee: Filter by assignee name. Use "No Assignee" for unassigned.
            tags: Comma-separated tags (e.g. "CISA-KEV").
            business_unit_ids: Comma-separated business unit IDs.
            finding_impact_threshold: Impact setting - "High" for prioritised findings or "All" for broader range.
            created_from: Start date (YYYY-MM-DD).
            created_to: End date (YYYY-MM-DD).
            page: Page number (default 1).
            page_size: Results per page (max 30).
        """
        try:
            api = FindingsApi(get_api_client())
            kwargs = {"page": page, "page_size": min(page_size, 30)}
            if finding_title:
                kwargs["finding_title"] = finding_title
            if severities:
                kwargs["severities"] = normalize_severities(severities)
            if statuses:
                kwargs["statuses"] = statuses
            if asset_title:
                kwargs["asset_title"] = asset_title
            if asset_types:
                kwargs["asset_types"] = asset_types
            if assignee:
                kwargs["assignee"] = assignee
            if tags:
                kwargs["tags"] = tags
            if business_unit_ids:
                kwargs["business_unit_ids"] = business_unit_ids
            if finding_impact_threshold:
                kwargs["finding_impact_threshold"] = finding_impact_threshold
            if created_from:
                kwargs["created_from"] = parse_date(created_from)
            if created_to:
                kwargs["created_to"] = parse_date(created_to)

            response = api.get_list_findings(**kwargs)

            if not hasattr(response, 'data') or not response.data:
                return "No findings match the search criteria."

            total = get_total(response)
            lines = []
            for f in response.data:
                fid = getattr(f, 'id', '')
                sev = severity_display(getattr(f, 'severity', None))
                title = getattr(f, 'title', 'No title')
                status = getattr(f, 'status', 'Unknown')
                lines.append(f"• [ID:{fid}] [{sev}] {title} ({status})")

            header = f"Findings ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error searching findings: {e}"

    @mcp.tool()
    def update_finding_status(finding_id: int, status: str) -> str:
        """Update the status of a finding. Use get_finding_statuses to see available values.

        Args:
            finding_id: The finding ID to update.
            status: The new status value.
        """
        try:
            api = FindingsApi(get_api_client())
            body = UpdateClientFindingStatusRequestBody(status=status)
            response = api.update_finding_status(
                id=finding_id,
                api_token="",
                update_client_finding_status_request_body=body,
            )

            finding = response.data if hasattr(response, 'data') else response
            new_status = getattr(finding, 'status', status) if finding else status
            return f"Finding {finding_id} status updated to: {new_status}"
        except Exception as e:
            return f"Error updating finding status: {e}"

    @mcp.tool()
    def retest_finding(finding_id: int) -> str:
        """Trigger a retest for a specific finding to verify remediation.

        Args:
            finding_id: The finding ID to retest.
        """
        try:
            api = FindingsApi(get_api_client())
            response = api.start_specific_finding_retest(finding_id=finding_id)

            finding = response.data if hasattr(response, 'data') else response
            title = getattr(finding, 'title', '') if finding else ''
            return f"Retest initiated for finding {finding_id}" + (f" ({title})" if title else "")
        except Exception as e:
            return f"Error initiating retest: {e}"

    @mcp.tool()
    def get_finding_statuses() -> str:
        """List all available finding status values."""
        try:
            import json
            api = FindingsApi(get_api_client())
            _data, status_code, headers = api.get_available_finding_statuses_with_http_info()

            response_data = headers.get("Content-Type", "")
            if hasattr(_data, 'read'):
                body = _data.read()
            elif isinstance(_data, (str, bytes)):
                body = _data
            else:
                body = str(_data)

            if isinstance(body, bytes):
                body = body.decode("utf-8")

            try:
                parsed = json.loads(body)
                if isinstance(parsed, list):
                    return "Available Finding Statuses:\n" + "\n".join(f"• {s}" for s in parsed)
                if isinstance(parsed, dict) and "data" in parsed:
                    statuses = parsed["data"]
                    if isinstance(statuses, list):
                        return "Available Finding Statuses:\n" + "\n".join(f"• {s}" for s in statuses)
                return f"Available Finding Statuses: {parsed}"
            except (json.JSONDecodeError, TypeError):
                return f"Available Finding Statuses: {body}"
        except Exception as e:
            return f"Error retrieving finding statuses: {e}"

    @mcp.tool()
    def get_findings_summary_by_severity() -> str:
        """Get a count breakdown of findings by severity level."""
        try:
            api = FindingsApi(get_api_client())
            summary = {}
            for severity in SUMMARY_SEVERITIES:
                response = api.get_list_findings(severities=severity, page_size=1)
                count = get_total(response) or (len(response.data) if hasattr(response, 'data') and response.data else 0)
                summary[severity] = count

            total = sum(summary.values())
            lines = [f"Findings Summary (Total: {total}):"]
            for severity, count in summary.items():
                lines.append(f"• {severity_display(severity)}: {count}")
            return "\n".join(lines)
        except Exception as e:
            return f"Error generating findings summary: {e}"

    @mcp.tool()
    def get_unresolved_findings_by_business_unit(
        business_unit_id: str,
        severities: str = None,
        page_size: int = 30,
    ) -> str:
        """List open/unresolved findings for a specific business unit.

        Excludes findings with status Remediated or Accepted Risk.

        Args:
            business_unit_id: The business unit ID.
            severities: Optional comma-separated severities to filter.
            page_size: Results per page (max 30).
        """
        try:
            api = FindingsApi(get_api_client())
            kwargs = {
                "business_unit_ids": business_unit_id,
                "statuses": "Open,Triaged,In Progress",
                "page_size": min(page_size, 30),
            }
            if severities:
                kwargs["severities"] = normalize_severities(severities)

            response = api.get_list_findings(**kwargs)

            if not hasattr(response, 'data') or not response.data:
                return f"No unresolved findings for business unit {business_unit_id}."

            total = get_total(response)
            lines = []
            for f in response.data:
                fid = getattr(f, 'id', '')
                sev = severity_display(getattr(f, 'severity', None))
                title = getattr(f, 'title', 'No title')
                status = getattr(f, 'status', 'Unknown')
                lines.append(f"• [ID:{fid}] [{sev}] {title} ({status})")

            header = f"Findings for BU {business_unit_id} ({len(lines)}"
            if total:
                header += f" of {total}"
            header += "):"
            return header + "\n" + "\n".join(lines)
        except Exception as e:
            return f"Error retrieving findings by business unit: {e}"

    @mcp.tool()
    def export_finding_pdf(finding_id: int) -> str:
        """Export a finding report as PDF.

        Args:
            finding_id: The finding ID to export.
        """
        try:
            api = FindingsApi(get_api_client())
            api.export_pdf_for_finding(id=finding_id, api_token="")
            return f"PDF export initiated for finding {finding_id}. Check the watchTowr Platform for the download."
        except Exception as e:
            return f"Error exporting finding PDF: {e}"
