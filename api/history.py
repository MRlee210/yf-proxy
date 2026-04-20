"""
GET /api/history?ticker=005930.KS&period=1mo&interval=1d&key=...
Returns OHLCV rows.
period examples: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
interval examples: 1m, 5m, 15m, 30m, 60m, 1d, 1wk, 1mo
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os

import yfinance as yf

API_KEY = os.environ.get("API_KEY")


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        if API_KEY and q.get("key", [None])[0] != API_KEY:
            return self._send(401, {"error": "unauthorized"})

        ticker = q.get("ticker", [None])[0]
        if not ticker:
            return self._send(400, {"error": "missing ?ticker=..."})

        period = q.get("period", ["1mo"])[0]
        interval = q.get("interval", ["1d"])[0]

        try:
            df = yf.Ticker(ticker).history(
                period=period, interval=interval, auto_adjust=False
            )
            rows = []
            for idx, r in df.iterrows():
                rows.append({
                    "date": str(idx.date()) if hasattr(idx, "date") else str(idx),
                    "open": _f(r.get("Open")),
                    "high": _f(r.get("High")),
                    "low": _f(r.get("Low")),
                    "close": _f(r.get("Close")),
                    "volume": int(r.get("Volume")) if r.get("Volume") == r.get("Volume") else None,
                })
            self._send(200, {
                "ticker": ticker,
                "period": period,
                "interval": interval,
                "rows": rows,
            })
        except Exception as e:
            self._send(500, {"error": str(e)})

    def _send(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))


def _f(v):
    try:
        f = float(v)
        return f if f == f else None
    except (TypeError, ValueError):
        return None
