# watchTowr Platform MCP Server

A [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) server that connects AI assistants to the [watchTowr Platform](https://watchtowr.com), providing real-time access to your external attack surface data, findings, hunts, and threat intelligence.

## Features

- **88 tools** covering the full watchTowr Platform API — assets, findings, hunts, certificates, suspicious domains, and more
- **Read and write** — query your attack surface and take action (update statuses, trigger retests, submit seed assets)
- **Composite intelligence** — built-in tools for attack surface summaries, change detection, executive scorecards, and compliance reporting
- **Secure** — authenticates via API key with tenant isolation; credentials never leave your environment

## Prerequisites

- **watchTowr Platform account** with API access enabled
- **API Key** — obtained from your watchTowr Platform dashboard under Settings → API Management
- **Platform Host** — your watchTowr instance URL (e.g. `https://your-tenant.your-region.watchtowr.io`)
- **Python 3.10+** and [uv](https://docs.astral.sh/uv/) (for local installation), or **Docker**

## Quick Start

### Local Installation

```bash
git clone https://github.com/watchtowr/watchtowr-mcp.git
cd watchtowr-mcp

# Clone the API SDK
git clone https://github.com/watchtowr/watchtowr-api-sdk.git

# Install dependencies
uv venv
uv pip install -e .
uv pip install -e watchtowr-api-sdk

# Run the server
WATCHTOWR_API_KEY="your-api-key" \
WATCHTOWR_PLATFORM_HOST="https://your-tenant.your-region.watchtowr.io" \
uv run watchtowr-mcp
```

### Docker

Build the image:

```bash
git clone https://github.com/watchtowr/watchtowr-mcp.git
cd watchtowr-mcp
docker build -t watchtowr-mcp .
```

#### stdio — for MCP clients

```bash
docker run -it --rm \
  -e WATCHTOWR_API_KEY="your-api-key" \
  -e WATCHTOWR_PLATFORM_HOST="https://your-tenant.your-region.watchtowr.io" \
  watchtowr-mcp
```

#### HTTP — standalone service

```bash
docker run -d --rm \
  -e WATCHTOWR_API_KEY="your-api-key" \
  -e WATCHTOWR_PLATFORM_HOST="https://your-tenant.your-region.watchtowr.io" \
  -e MCP_TRANSPORT=streamable-http \
  -p 8080:8080 \
  watchtowr-mcp
```

## MCP Client Configuration

### Claude Desktop / Cursor (local)

```json
{
  "mcpServers": {
    "watchtowr": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/watchtowr-mcp",
        "run", "watchtowr-mcp"
      ],
      "env": {
        "WATCHTOWR_API_KEY": "your-api-key",
        "WATCHTOWR_PLATFORM_HOST": "https://your-tenant.your-region.watchtowr.io"
      }
    }
  }
}
```

### Claude Desktop / Cursor (Docker)

> Build the `watchtowr-mcp` image first — see the [Docker](#docker) section above.

```json
{
  "mcpServers": {
    "watchtowr": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--env", "WATCHTOWR_API_KEY=your-api-key",
        "--env", "WATCHTOWR_PLATFORM_HOST=https://your-tenant.your-region.watchtowr.io",
        "watchtowr-mcp"
      ]
    }
  }
}
```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `WATCHTOWR_API_KEY` | Yes | Your watchTowr Platform API key |
| `WATCHTOWR_PLATFORM_HOST` | Yes | Your watchTowr Platform instance URL |
| `MCP_TRANSPORT` | No | Transport mode: `stdio` (default) or `streamable-http` |
| `PORT` | No | HTTP port when using `streamable-http` transport (default: `8080`) |

## Available Tools

### Findings (10 tools)

| Tool | Description |
|------|-------------|
| `list_cisa_kev_findings` | List findings tagged as CISA Known Exploited Vulnerabilities |
| `list_findings_by_severity` | List findings filtered by severity (Critical, High, Medium, Low) |
| `get_finding_details` | Get full finding detail — description, evidence, CVSS, CVE, EPSS |
| `search_findings` | Search with filters: title, severity, status, asset, assignee, tags, date range |
| `update_finding_status` | Change the status of a finding |
| `retest_finding` | Trigger a retest to verify remediation |
| `get_finding_statuses` | List available finding status values |
| `get_findings_summary_by_severity` | Count breakdown of findings by severity level |
| `get_unresolved_findings_by_business_unit` | List unresolved findings for a specific business unit |
| `export_finding_pdf` | Export a finding report as PDF |

### Assets (24 tools)

| Tool | Description |
|------|-------------|
| `list_asset_ips` | List discovered IP addresses |
| `get_asset_ip_details` | Full detail for a specific IP address |
| `list_ports_for_ip` | List all ports discovered on a specific IP |
| `get_ip_port_details` | Full detail for a port scoped to an IP address |
| `list_asset_domains` | List discovered root domains |
| `get_asset_domain_details` | Full detail for a specific domain |
| `list_asset_subdomains` | List discovered subdomains |
| `get_asset_subdomain_details` | Full detail for a specific subdomain |
| `list_asset_ports` | List open ports with service and banner info |
| `get_asset_port_details` | Full detail for a specific port |
| `list_asset_ip_ranges` | List discovered IP ranges with ASN and country |
| `get_asset_iprange_details` | Full detail for a specific IP range |
| `list_cloud_storage_assets` | List cloud storage buckets (S3, GCS, Azure) |
| `get_asset_cloud_storage_details` | Full detail for a specific cloud storage asset |
| `list_source_code_repositories` | List discovered code repositories |
| `get_asset_repository_details` | Full detail for a specific repository |
| `list_container_assets` | List discovered container registry images |
| `get_asset_container_details` | Full detail for a specific container image |
| `list_saas_platforms` | List discovered SaaS platform instances |
| `get_asset_saas_details` | Full detail for a specific SaaS platform |
| `list_mobile_app_assets` | List discovered mobile applications |
| `get_asset_mobile_app_details` | Full detail for a specific mobile application |
| `update_asset_status` | Update the status of any asset type |
| `add_seed_asset` | Submit a new seed asset for discovery |

### Hunts (6 tools)

| Tool | Description |
|------|-------------|
| `list_recent_hunts` | List recent hunts with finding and asset counts |
| `get_hunt_details` | Full hunt detail — description, hypothesis, references |
| `list_findings_by_hunt` | List findings discovered by a specific hunt |
| `list_assets_by_hunt` | List assets tested by a specific hunt |
| `search_hunts` | Search hunts by keyword, status, type, priority, date |
| `get_hunt_impact_summary` | Combined summary: detail, severity breakdown, assets tested |

### Threat Intelligence (6 tools)

| Tool | Description |
|------|-------------|
| `list_suspicious_domains` | List domains flagged for typosquatting or brand impersonation |
| `get_suspicious_domain_details` | Full detail including WHOIS data |
| `list_points_of_interest` | List leaked credentials, exposed configs, interesting endpoints |
| `list_certificates` | List SSL/TLS certificates with subject, issuer, and expiry |
| `get_certificate_details` | Full certificate detail including SANs and key info |
| `get_expiring_certificates` | List certificates expiring within N days |

### Services (2 tools)

| Tool | Description |
|------|-------------|
| `list_services` | List exposed services with technology stack and country |
| `search_services_by_technology` | Search services by technology, port, or service type |

### Organisation (5 tools)

| Tool | Description |
|------|-------------|
| `get_watchtowr_source_ips` | Get source IPs to whitelist for watchTowr scanning |
| `get_activity_logs` | Get recent platform activity logs |
| `search_activity_logs` | Search logs by type, user, keyword, and date range |
| `list_business_units` | List business units (useful for filtering other tools) |
| `get_business_unit_details` | Full detail for a specific business unit |

### Composite & Triage (13 tools)

| Tool | Description |
|------|-------------|
| `get_attack_surface_summary` | Asset counts by type and finding counts by severity |
| `get_new_assets_since` | All newly discovered assets across every type within N days |
| `get_attack_surface_delta` | Combined new assets + new findings within a time window |
| `get_business_unit_posture` | Full security posture for a BU: findings, assets, services, certs |
| `get_finding_with_asset_context` | Finding details enriched with the related asset's full details |
| `get_expiring_certificates_with_services` | Expiring certs cross-referenced with exposed services |
| `get_hunt_remediation_list` | Hunt findings expanded with details for remediation handoff |
| `get_critical_exposure_report` | Executive headlines: critical/high counts, CISA-KEV, expiring certs, top findings |
| `get_findings_by_asset` | Search findings associated with a specific asset |
| `get_stale_findings` | Findings open longer than N days |
| `get_unassigned_critical_findings` | Critical/high findings with no assignee |
| `get_asset_findings_count_by_type` | Unresolved findings heatmap by asset type |
| `get_shadow_it_candidates` | New assets not assigned to any business unit |

### Reporting & Compliance (11 tools)

| Tool | Description |
|------|-------------|
| `get_asset_inventory_by_business_unit` | Full asset inventory for a business unit |
| `get_out_of_scope_assets` | All assets marked as out of scope or excluded |
| `get_verified_vs_unverified_assets` | Asset verification status breakdown across all types |
| `get_finding_age_distribution` | Findings bucketed by age (0-7d, 7-30d, 30-90d, 90d+) and severity |
| `get_finding_status_timeline` | Opened vs remediated findings per week |
| `get_open_ports_summary` | Most common open ports with service counts |
| `get_assets_without_findings` | Asset types with assets but zero findings — coverage gaps |
| `get_certificate_health_report` | Certificates grouped by health: expired, expiring, valid |
| `get_executive_risk_scorecard` | Single-call executive dashboard: assets, findings, KEV, cert health |
| `get_week_over_week_delta` | Weekly trend report: new assets and findings per week |
| `get_top_findings_by_occurrence` | Most frequently recurring finding titles — systemic issues |

### Incident Response (5 tools)

| Tool | Description |
|------|-------------|
| `search_assets_by_country` | Find all IPs and services in a specific country |
| `get_internet_facing_services_summary` | Exposed services grouped by type with counts |
| `get_assets_by_technology` | Find all services running a specific technology |
| `get_cisa_kev_remediation_status` | CISA-KEV findings grouped by remediation status |
| `find_related_assets` | Blast radius mapping: subdomains, ports, services for an asset |

### Workflow & Automation (6 tools)

| Tool | Description |
|------|-------------|
| `get_recent_remediations` | Findings remediated within the last N days |
| `get_daily_digest` | 24-hour digest: new assets, new findings, activity log |
| `bulk_retest_findings` | Trigger retests for multiple findings at once |
| `bulk_update_finding_status` | Update the status of multiple findings at once |
| `get_actionable_findings_queue` | Prioritized queue of open findings by severity and age |
| `get_findings_needing_assignment` | Unassigned open findings grouped by severity — triage inbox |

## Example Prompts

```
"Give me an attack surface summary"
"Show all critical findings"
"What new assets were discovered this week?"
"List certificates expiring in the next 30 days"
"Show me suspicious domains flagged for typosquatting"
"Get the details for finding 1234 and trigger a retest"
"List all findings for business unit 5"
"What hunts have been completed recently?"
"Give me the executive risk scorecard"
"Show me stale findings older than 30 days"
"What critical findings are unassigned?"
"Run a daily digest"
"Bulk retest findings 101,102,103"
"Show me all assets in country CN"
"What services are running Apache?"
"Give me the CISA-KEV remediation status"
"Compare week-over-week changes for the last 4 weeks"
```

## Development

### Project Structure

```
watchtowr-mcp/
├── watchtowr_mcp_server/
│   ├── __init__.py
│   ├── mcp.py                 # Entry point
│   ├── client.py              # API client and shared helpers
│   └── tools/
│       ├── __init__.py        # Tool registration
│       ├── findings.py        # Finding tools
│       ├── assets.py          # Asset tools
│       ├── hunts.py           # Hunt tools
│       ├── threat_intel.py    # Suspicious domains, POI, certificates
│       ├── services.py        # Service listing tools
│       ├── organization.py    # Business units, activity logs, source IPs
│       ├── composite.py       # Cross-cutting intelligence, triage, and posture tools
│       ├── reporting.py       # Compliance, audit, executive reporting tools
│       ├── incident.py        # Incident response and threat hunting tools
│       └── workflow.py        # Bulk operations, queues, and automation tools
├── pyproject.toml
├── Dockerfile
└── README.md
```

## Support

- **API Reference**: [watchTowr Platform API Documentation](https://apidocs.watchtowr.com)
- **Technical Support**: Contact the watchTowr support team

---

*Requires a valid watchTowr Platform subscription. For more information, visit [watchtowr.com](https://watchtowr.com).*
