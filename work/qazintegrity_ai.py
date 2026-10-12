"""QazIntegrity AI: explainable procurement-risk prototype.

Run: python work/qazintegrity_ai.py
Creates a self-contained HTML dashboard from the included demo records.
The scores are triage signals for auditors, not proof of wrongdoing.
"""
from __future__ import annotations

import csv
import html
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "procurements.csv"
OUT = Path(__file__).resolve().parents[1] / "outputs" / "qazintegrity_static_dashboard.html"


def read_records():
    with DATA.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def score_records(records):
    wins = Counter(r["supplier"] for r in records)
    agency_winners = defaultdict(set)
    for r in records:
        agency_winners[r["agency"]].add(r["supplier"])
    scored = []
    for r in records:
        reasons, score = [], 0
        price = _number(r.get("bid_price"))
        benchmark = _number(r.get("market_estimate"))
        price_ratio = price / max(benchmark, 1) if price is not None and benchmark is not None else None
        if price_ratio is not None and price_ratio > 1.25:
            score += 30; reasons.append("bid is >25% above benchmark")
        bid_count = _integer(r.get("bid_count"))
        if bid_count is not None and bid_count <= 1:
            score += 25; reasons.append("single-bid tender")
        if wins[r["supplier"]] >= 3:
            score += 20; reasons.append("supplier wins repeatedly")
        if len(agency_winners[r["agency"]]) == 1:
            score += 15; reasons.append("agency has one recurring winner")
        amendments = _integer(r.get("amendments"))
        if amendments is not None and amendments != 0:
            score += 10; reasons.append("tender was amended")
        level = "high" if score >= 60 else "medium" if score >= 35 else "low"
        scored.append({**r, "score": score, "level": level, "reasons": reasons})
    return sorted(scored, key=lambda x: x["score"], reverse=True)


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _integer(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def render(rows):
    counts = Counter(r["level"] for r in rows)
    cards = "".join(f'<div class="card"><b>{html.escape(k.title())}</b><strong>{v}</strong><small>risk alerts</small></div>' for k, v in counts.items())
    body = "".join(
        f'<tr><td>{html.escape(r["id"])}</td><td>{html.escape(r["agency"])}</td><td>{html.escape(r["category"])}</td>'
        f'<td>{html.escape(r["supplier"])}</td><td>{float(r["bid_price"]):,.0f}</td><td><span class="{r["level"]}">{r["score"]} · {r["level"]}</span></td>'
        f'<td>{html.escape("; ".join(r["reasons"]) or "no major signal")}</td></tr>' for r in rows
    )
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>QazIntegrity AI</title>
    <style>body{{font:15px system-ui;margin:40px;background:#f5f7fb;color:#162033}}h1{{margin-bottom:4px}}.muted{{color:#64748b}}.cards{{display:flex;gap:14px;margin:25px 0}}.card{{background:white;padding:18px 24px;border-radius:12px;box-shadow:0 2px 10px #dbe1ec;min-width:120px}}.card strong,.card small{{display:block;margin-top:7px}}table{{width:100%;border-collapse:collapse;background:white;border-radius:12px;overflow:hidden}}th,td{{padding:12px;text-align:left;border-bottom:1px solid #e8edf4}}th{{background:#172554;color:white}}.high,.medium,.low{{padding:4px 8px;border-radius:99px;font-weight:650}}.high{{background:#fee2e2;color:#991b1b}}.medium{{background:#fef3c7;color:#92400e}}.low{{background:#dcfce7;color:#166534}}.note{{background:#e0f2fe;padding:14px;border-radius:10px}}</style></head>
    <body><h1>QazIntegrity AI</h1><p class='muted'>Explainable procurement-risk triage for Kazakhstan public auditors</p>
    <div class='note'>This prototype identifies patterns for human review. A risk score is not a finding of fraud.</div><div class='cards'>{cards}</div>
    <table><tr><th>ID</th><th>Agency</th><th>Category</th><th>Supplier</th><th>Bid price</th><th>Score</th><th>Explanation</th></tr>{body}</table>
    </body></html>"""


if __name__ == "__main__":
    rows = score_records(read_records())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(rows), encoding="utf-8")
    print(json.dumps({"records": len(rows), "output": str(OUT), "high_risk": sum(r["level"] == "high" for r in rows)}, indent=2))
