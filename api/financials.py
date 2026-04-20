"""
GET /api/financials?ticker=005930.KS&statement=income&freq=annual&key=...
statement: income | cashflow | balance
freq:      annual | quarterly
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

        statement = q.get("statement", ["income"])[0].lower()
        freq = q.get("freq", ["annual"])[0].lower()

        try:
            t = yf.Ticker(ticker)
            if statement == "income":
                df = t.income_stmt if freq == "annual" else t.quarterly_income_stmt
            elif statement == "cashflow":
                df = t.cashflow if freq == "annual" else t.quarterly_cashflow
            elif statement == "balance":
                df = t.balance_sheet if freq == "annual" else t.quarterly_balance_sheet
            else:
                return self._send(400, {"error": "statement must be income|cashflow|balance"})

            out = {}
            for col in df.columns:
                col_key = str(col.date()) if hasattr(col, "date") else str(col)
                period = {}
                for idx, v in df[col].items():
                    try:
                        fv = float(v)
                        period[str(idx)] = fv if fv == fv else None
                    except (TypeError, ValueError):
                        period[str(idx)] = None
                out[col_key] = period

            self._send(200, {
                "ticker": ticker,
                "statement": statement,
                "freq": freq,
                "data": out,
            })
        except Exception as e:
            self._send(500, {"error": str(e)})

    def _send(self, status, payload):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "public, max-age=3600")
        self.end_headers()
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
