"""
GET /api/quote?tickers=005930.KS,000660.KS&key=...
Returns current-price snapshot for one or more tickers.
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
import yfinance as yf

API_KEY = os.environ.get("API_KEY")

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        if API_KEY and q.get("key", [None])[0] != API_KEY:
            return self._send(401, {"error": "unauthorized"})
        tickers_raw = q.get("tickers", [None])[0]
        if not tickers_raw:
            return self._send(400, {"error": "missing ?tickers=..."})
        tickers = [t.strip() for t in tickers_raw.split(",") if t.strip()]
        out = {}
        for t in tickers:
            try:
                fi = yf.Ticker(t).fast_info
                last_price = _f(fi.get("last_price"))
                prev_close = _f(fi.get("previous_close"))

                # ↓ 주말/장마감 시 history로 폴백
                if last_price is None:
                    hist = yf.Ticker(t).history(period="5d")
                    if not hist.empty:
                        last_price = float(hist["Close"].iloc[-1])
                        if prev_close is None and len(hist) >= 2:
                            prev_close = float(hist["Close"].iloc[-2])

                out[t] = {
                    "last_price":     last_price,
                    "previous_close": prev_close,
                    "open":           _f(fi.get("open")),
                    "day_high":       _f(fi.get("day_high")),
                    "day_low":        _f(fi.get("day_low")),
                    "currency":       fi.get("currency"),
                }
            except Exception as e:
                out[t] = {"error": str(e)}
        self._send(200, out)

    def _send(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=60")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

def _f(v):
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None
