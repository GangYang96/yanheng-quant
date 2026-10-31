"""Verify actual HTTP responses and run the original subprocess backtest endpoint."""
import json
from pathlib import Path
import httpx

from paths import WORK

HERE = WORK
checks = []


def main():
    with httpx.Client(base_url="http://127.0.0.1:3018", timeout=120, trust_env=False) as client:
        for route in ("/health", "/", "/api/strategies", "/api/backtest/status"):
            r = client.get(route)
            r.raise_for_status()
            body = r.text if route == "/" else r.json()
            if route == "/":
                assert 'id="root"' in body and "/assets/" in body
            if route == "/api/strategies":
                assert any(s["id"] == "validation_ma" for s in body["strategies"])
                assert not body["load_errors"], body["load_errors"]
            checks.append({"path": route, "status": r.status_code, "content_type": r.headers.get("content-type")})
        # Populate the local sample watchlist through the existing API.
        r = client.post("/api/watchlist/batch", json={"symbols": ["688981.SH", "002371.SZ", "512480.SH"], "note": "半导体底座验证样本"})
        r.raise_for_status()
        assert len(r.json()["symbols"]) == 3
        for symbol in ("688981.SH", "002371.SZ", "512480.SH"):
            r = client.get("/api/kline/daily", params={"symbol": symbol, "start_date": "2024-01-01", "end_date": "2026-10-30", "days": 2000})
            r.raise_for_status()
            body = r.json()
            assert len(body["rows"]) > 600
            assert body["source"] == "enriched"
            checks.append({"path": "/api/kline/daily", "symbol": symbol, "status": r.status_code, "rows": len(body["rows"]), "source": body["source"]})
        for asset in ("stock", "etf"):
            saved = json.loads((HERE / f"backtest-{asset}.json").read_text(encoding="utf-8"))
            r = client.post("/api/backtest/strategy/run", json={
                "strategy_id": "validation_ma", "symbols": ["688981.SH", "002371.SZ"] if asset == "stock" else ["512480.SH"],
                "start": "2024-05-06", "end": "2026-10-30", "matching": "open_t+1",
                "commission_pct": 0.0003, "stamp_tax_pct": 0.0005 if asset == "stock" else 0,
                "slippage_bps": 5, "max_positions": 2 if asset == "stock" else 1,
                "initial_capital": 1000000, "asset_type": asset,
            })
            r.raise_for_status()
            result = r.json()
            (HERE / f"http-backtest-{asset}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            assert not result.get("error"), result.get("error")
            assert result["trades"] == saved["trades"], f"{asset}: trade mismatch between direct and HTTP worker paths"
            assert result["equity_curve"] == saved["equity_curve"], f"{asset}: equity mismatch"
            checks.append({"path": "/api/backtest/strategy/run", "asset_type": asset, "status": r.status_code, "trades": len(result["trades"]), "reproduces_saved_trades_and_equity": True})
    (HERE / "http-checks.json").write_text(json.dumps(checks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(checks, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
