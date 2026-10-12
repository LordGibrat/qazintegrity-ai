# QazIntegrity AI

An explainable AI prototype for prioritising Kazakhstan public-procurement records for human review.

## What it does

QazIntegrity turns procurement records into an auditable risk score using signals such as:

- deviation from a benchmark price;
- low competition;
- repeat-winner concentration;
- agency concentration;
- contract amendments.

The output is a prioritisation aid for auditors—not a finding of misconduct. Every demo record is synthetic and the score is designed to show why a record was prioritised.

## Run the demo

```powershell
python work/api_server.py
```

Open <http://127.0.0.1:8765>.

Useful endpoints:

```text
GET  /api/v1/health
GET  /api/v1/stats
GET  /api/v1/procurements?limit=20&q=road
POST /api/v1/refresh
```

The demo works without credentials and uses the clearly labelled synthetic dataset.

## Optional live-data mode

The server can normalize records from the official Kazakhstan procurement API when a valid token is supplied through the environment:

```powershell
$env:QAZINTEGRITY_API_TOKEN = "your-token"
python work/api_server.py
```

Never commit the token or place it in frontend code. Setup details are in [`outputs/API_ENABLEMENT_GUIDE.md`](outputs/API_ENABLEMENT_GUIDE.md).

## Limitations and next steps

The MVP is not an automated investigation system. A production version would need auditor-validated labels, precision/recall and false-positive measurement, Kazakh/Russian text support, authentication, rate limiting, a database cache, and appeal and privacy controls. Live procurement records may not contain every field required by every signal, so unsupported signals are not fabricated.
