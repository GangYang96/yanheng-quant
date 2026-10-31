"""Cache the four real index daily series fetched by the local application's provider.

Uses the normal repository writers; no synthetic bars and no full-market download.
"""
from datetime import datetime
import hashlib
import json
from zoneinfo import ZoneInfo

import serve  # sets this validation's DATA_DIR and upstream import path
import httpx
import polars as pl

from app.data_providers.normalizer import normalize_daily, normalize_instruments
from app.services.index_const import CORE_INDEX_NAMES
from app.tickflow.repository import DataStore, KlineRepository


def main():
    store = DataStore(serve.HERE / "runtime-data")
    repo = KlineRepository(store)
    repo.refresh_cache(background=False)
    labels = normalize_instruments([
        {"symbol": symbol, "name": name, "exchange": symbol.split(".")[1]}
        for symbol, name in CORE_INDEX_NAMES.items()
    ], asset_type="index", source="upstream_core_index_labels")
    existing = repo.get_index_instruments()
    if not existing.is_empty():
        labels = pl.concat([existing, labels], how="diagonal_relaxed").unique(subset=["symbol"], keep="first")
    repo.save_index_instruments(labels)
    checks = []
    with httpx.Client(base_url="http://127.0.0.1:3018", timeout=60, trust_env=False) as client:
        for symbol, name in CORE_INDEX_NAMES.items():
            response = client.get("/api/index/daily", params={"symbol": symbol, "days": 1100})
            response.raise_for_status()
            body = response.json()
            assert body["rows"], f"No index daily data: {symbol}"
            raw = pl.from_dicts(body["rows"], infer_schema_length=None)
            raw = raw.with_columns(pl.col("date").str.to_date())
            daily = normalize_daily(raw, default_symbol=symbol)
            assert daily["date"].null_count() == 0
            assert daily.unique(subset=["symbol", "date"]).height == daily.height
            repo.append_index_daily(daily)
            repo.append_index_enriched(raw)
            path = serve.HERE / "source-responses" / f"http-index-{symbol}.json"
            path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
            check = {"symbol": symbol, "name": name, "rows": daily.height,
                     "first": str(daily["date"].min()), "last": str(daily["date"].max()),
                     "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "file": path.name}
            checks.append(check)
            print(json.dumps(check, ensure_ascii=False), flush=True)
        repo.refresh_index_views()
        views = client.post("/api/kline/refresh_views")
        views.raise_for_status()
        refreshed = client.post("/api/data/refresh-cache")
        refreshed.raise_for_status()
        quotes = client.get("/api/intraday/indices").json()
        assert set(CORE_INDEX_NAMES) <= {r["symbol"] for r in quotes["rows"]}
        assert quotes["source"] == "index_daily"
    (serve.HERE / "index-data-checks.json").write_text(json.dumps({
        "checked_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
        "source": "TickFlow free daily via original local /api/index/daily endpoint",
        "indices": checks, "quote_source": quotes["source"],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    store.db.close()


if __name__ == "__main__":
    main()
