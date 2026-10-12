# QazIntegrity AI

An explainable AI prototype for prioritising public-procurement records for human audit in Kazakhstan.

## Run the API-powered MVP

```powershell
python work/api_server.py
```

Open `http://127.0.0.1:8765` in a browser. The dashboard now calls the API endpoints instead of embedding records.

For the complete token-request template, environment setup, and verification steps, see [API Enablement Guide](outputs/API_ENABLEMENT_GUIDE.md).

### Connect the official Kazakhstan procurement API

The official developer API is documented at `https://procurement.gov.kz/ru/developer/ows_v3` and requires a token. After requesting one from the procurement portal, set it only in the server environment:

```powershell
$env:QAZINTEGRITY_API_TOKEN = "your-token"
python work/api_server.py
```

The connector calls the official contract registry and normalizes the response into QazIntegrity records. When no token is present—or the upstream service fails—the API uses the clearly-labelled synthetic demo dataset.

Useful endpoints:

* `GET /api/v1/health`
* `GET /api/v1/stats`
* `GET /api/v1/procurements?limit=20&q=road`
* `POST /api/v1/refresh`

## Research contribution

The prototype combines benchmark-price deviation, low competition, repeat-winner concentration, agency concentration, and tender amendments into an interpretable risk score. A production version should use official open data, validate labels with auditors, measure false-positive rates, support Kazakh/Russian text, and include privacy and appeal controls.

The included records are synthetic demo data; they are not allegations about real organisations. Live contract records do not contain all fields needed for every risk rule, so the MVP only activates signals supported by the available fields. A production version should add tender-level bids, benchmark prices, official supplier names, audit labels, authentication, rate limiting, and a database cache.
