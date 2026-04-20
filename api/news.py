"""
GET /api/news?ticker=005930.KS&limit=10&key=...
Returns recent news headlines from yfinance.
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

        try:
            limit = int(q.get("limit", ["10"])[0])
        except ValueError:
            limit = 10

        try:
            raw = yf.Ticker(ticker).news or []
            out = []
            for n in raw[:limit]:
                content = n.get("content") or {}
                out.append({
                    "title": n.get("title") or content.get("title"),
                    "link": n.get("link") or (content.get("clickThroughUrl") or {}).get("url"),
                    "publisher": n.get("publisher") or (content.get("provider") or {}).get("displayName"),
                    "published_at": n.get("providerPublishTime") or content.get("pubDate"),
                    "summary": content.get("summary"),
                })
            self._send(200, {"ticker": ticker, "news": out})
        except Exception as e:
            self._send(500, {"error": str(e)})

    def _send(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=300")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
