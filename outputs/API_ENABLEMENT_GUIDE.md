# QazIntegrity API Enablement Guide

This guide explains how to connect QazIntegrity AI to the official Kazakhstan public-procurement API without exposing the access token in the project.

## 1. Request developer access

The official procurement API documentation is available at:

https://procurement.gov.kz/ru/developer/ows_v3

The portal requires a developer token for its REST and GraphQL services. Use the portal's developer-access process to request a token.

### Access request template

Subject: Request for developer token for public procurement API

Hello,

We are developing QazIntegrity AI, a research and public-interest prototype for explainable analysis of Kazakhstan public-procurement data. The system is intended to help auditors and researchers identify unusual procurement patterns for human review. It does not make legal findings or automatically accuse suppliers or government organisations.

Please issue a developer token for the official public-procurement API. We plan to use the contract and procurement registries for non-destructive read-only requests, limited-rate testing, data-quality research, and a demonstration dashboard.

Project contact: [your full name]
Organisation or university: [your organisation]
Email: [your email]
Expected request volume: low-volume development requests

Thank you.

## 2. Store the token safely

Do not paste the token into `README.md`, source code, screenshots, or a public repository. Set it in the server environment instead.

In PowerShell, replace `YOUR_PORTAL_TOKEN` locally with the credential issued to you:

```powershell
$env:QAZINTEGRITY_API_TOKEN = "YOUR_PORTAL_TOKEN"
python work/api_server.py
```

The token is read only by `work/api_server.py` and sent to the upstream service in a server-side `Authorization: Bearer` header. The browser never receives the token.

## 3. Start the API dashboard

From the project folder:

```powershell
python work/api_server.py
```

Open http://127.0.0.1:8765. The dashboard should show `LIVE API` when the token is accepted. Without a token, it shows `DEMO DATA` and uses the included synthetic records.

## 4. Verify the connection

```powershell
Invoke-RestMethod http://127.0.0.1:8765/api/v1/health
Invoke-RestMethod http://127.0.0.1:8765/api/v1/stats
Invoke-RestMethod -Method Post http://127.0.0.1:8765/api/v1/refresh
```

Expected live response fields include:

```json
{
  "data": {
    "source": "live",
    "records": 50,
    "upstream_error": null
  }
}
```

## 5. Live field mapping

| Official field | QazIntegrity field |
|---|---|
| `id` | `source_id` and `id` |
| `customer_bin` | `agency` |
| `supplier_biin` | `supplier` |
| `contract_sum_wnds` or `contract_sum` | `bid_price` |

The contract endpoint does not provide every field needed by every risk rule. For live records, the MVP activates only signals supported by the available response. Tender-level bid counts, benchmark prices, supplier names, amendments, and audit labels should be added in the next data-integration phase.

## Security notes

- Revoke the credential immediately if it was ever placed in a repository, screenshot, chat, or shared document.
- Use a read-only developer token when the portal supports that scope.
- Never commit the token to Git.
- Keep request volume within the portal's limits.
- Treat risk scores as review-prioritisation signals, not proof of wrongdoing.
- Before production use, add authentication, rate limiting, logging controls, and a database cache.
