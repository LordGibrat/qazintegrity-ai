"""Zero-dependency API for the QazIntegrity AI MVP.

Demo mode works immediately. Live mode uses the official Kazakhstan
procurement API when QAZINTEGRITY_API_TOKEN is configured.
"""
from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from qazintegrity_ai import read_records, score_records

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT.parent / "outputs" / "qazintegrity_dashboard.html"
LIVE_URL = "https://ows.goszakup.gov.kz/v3/contract"
LOCK = threading.Lock()
STATE = {"records": None, "source": "demo", "last_error": None}


def normalize_live(item):
    """Map official contract fields to the stable QazIntegrity schema."""
    amount = item.get("contract_sum_wnds") or item.get("contract_sum") or 0
    return {
        "id": f"KZ-CONTRACT-{item.get('id', 'unknown')}",
        "agency": item.get("customer_bin") or "Unknown agency",
        "category": "public contract",
        "supplier": item.get("supplier_biin") or "Unknown supplier",
        "bid_price": amount,
        "market_estimate": amount,
        "bid_count": None,
        "amendments": None,
        "data_source": "Kazakhstan official procurement API",
        "source_id": item.get("id"),
    }


def fetch_live(limit=50):
    token = os.getenv("QAZINTEGRITY_API_TOKEN")
    if not token:
        raise RuntimeError("QAZINTEGRITY_API_TOKEN is not configured")
    request = urllib.request.Request(
        f"{LIVE_URL}?limit={min(max(limit, 1), 100)}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=12) as response:
        payload = json.loads(response.read().decode("utf-8"))
    items = payload.get("items", payload if isinstance(payload, list) else [])
    return [normalize_live(item) for item in items if isinstance(item, dict)]


def get_records(source="auto"):
    with LOCK:
        if source == "live" or (source == "auto" and os.getenv("QAZINTEGRITY_API_TOKEN")):
            try:
                records = fetch_live()
                if records:
                    STATE.update(records=records, source="live", last_error=None)
            except (RuntimeError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
                STATE["last_error"] = str(error)
        if STATE["records"] is None or source == "demo":
            STATE.update(records=read_records(), source="demo")
        return list(STATE["records"]), STATE["source"], STATE["last_error"]


def response_payload(records, source, error, query):
    rows = score_records(records)
    if query:
        needle = query.lower()
        rows = [r for r in rows if needle in " ".join(str(r.get(k, "")) for k in ("id", "agency", "category", "supplier")).lower()]
    return rows, source, error


class Handler(BaseHTTPRequestHandler):
    server_version = "QazIntegrity/1.0"

    def send_json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if parsed.path == "/":
            self.send_file(OUTPUT, "text/html; charset=utf-8")
            return
        if parsed.path == "/api/v1/health":
            self.send_json(200, {"data": {"status": "ok", "service": "qazintegrity-api", "version": "1.0"}})
            return
        if parsed.path == "/api/v1/procurements":
            params = parse_qs(parsed.query)
            try:
                page = max(int(params.get("page", ["1"])[0]), 1)
                limit = min(max(int(params.get("limit", ["20"])[0]), 1), 100)
            except ValueError:
                self.send_json(400, {"error": {"code": "invalid_pagination", "message": "page and limit must be integers"}})
                return
            records, source, error = get_records(params.get("source", ["auto"])[0])
            rows, source, error = response_payload(records, source, error, params.get("q", [""])[0])
            start, end = (page - 1) * limit, page * limit
            self.send_json(200, {"data": rows[start:end], "meta": {"total": len(rows), "page": page, "limit": limit, "has_next": end < len(rows), "source": source, "upstream_error": error}})
            return
        if parsed.path == "/api/v1/stats":
            records, source, error = get_records("auto")
            rows, source, error = response_payload(records, source, error, "")
            self.send_json(200, {"data": {"total": len(rows), "risk_levels": dict(Counter(r["level"] for r in rows)), "total_value": sum(float(r.get("bid_price") or 0) for r in rows), "source": source, "upstream_error": error}})
            return
        self.send_json(404, {"error": {"code": "not_found", "message": "Endpoint not found"}})

    def do_POST(self):
        if urlparse(self.path).path != "/api/v1/refresh":
            self.send_json(404, {"error": {"code": "not_found", "message": "Endpoint not found"}})
            return
        records, source, error = get_records("live")
        self.send_json(200 if source == "live" else 503, {"data": {"source": source, "records": len(records), "upstream_error": error}})

    def send_file(self, path, content_type):
        if not path.exists():
            self.send_json(500, {"error": {"code": "dashboard_missing", "message": "Dashboard file is missing"}})
            return
        raw = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")


if __name__ == "__main__":
    port = int(os.getenv("QAZINTEGRITY_PORT", "8765"))
    print(f"QazIntegrity API running at http://127.0.0.1:{port}")
    print("Live connector: enabled" if os.getenv("QAZINTEGRITY_API_TOKEN") else "Live connector: set QAZINTEGRITY_API_TOKEN to enable")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
