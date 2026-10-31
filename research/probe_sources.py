"""Bounded, read-only checks of public sources; save original responses locally."""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import httpx
from tickflow import TickFlow

from paths import WORK

ROOT = WORK
RAW = ROOT / "source-responses"
RAW.mkdir(parents=True, exist_ok=True)
SYMBOLS = ("688981.SH", "002371.SZ", "512480.SH")
START = datetime(2024, 1, 1, tzinfo=ZoneInfo("Asia/Shanghai"))
END = datetime(2026, 10, 31, tzinfo=ZoneInfo("Asia/Shanghai"))


def persist(name, payload):
    data = json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")
    path = RAW / (name + ".json")
    path.write_bytes(data)
    return {"file": path.name, "sha256": hashlib.sha256(data).hexdigest()}


def daily(symbol):
    started = time.monotonic()
    result = {"kind": "daily", "symbol": symbol,
              "source": "https://free-api.tickflow.org", "status": "error"}
    try:
        client = TickFlow.free(timeout=20, max_retries=0, cache_dir=str(ROOT / "sdk-cache"))
        payload = client.klines.get(symbol, period="1d", adjust="none", count=10000,
                                   start_time=int(START.timestamp() * 1000),
                                   end_time=int(END.timestamp() * 1000), as_dataframe=False)
        result.update(persist("daily-" + symbol, payload))
        timestamps = payload.get("timestamp", [])
        result.update(status="ok" if timestamps else "empty", count=len(timestamps),
                      fields=list(payload), first_timestamp=timestamps[0] if timestamps else None,
                      last_timestamp=timestamps[-1] if timestamps else None)
        if timestamps:
            result["first_date"] = datetime.fromtimestamp(timestamps[0] / 1000, ZoneInfo("Asia/Shanghai")).isoformat()
            result["last_date"] = datetime.fromtimestamp(timestamps[-1] / 1000, ZoneInfo("Asia/Shanghai")).isoformat()
        try:
            adj = client.klines.ex_factors([symbol], as_dataframe=False)
            result["adjustment"] = persist("adjustment-" + symbol, adj)
            result["adjustment"]["status"] = "ok"
        except Exception as exc:
            result["adjustment"] = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    result["elapsed_s"] = round(time.monotonic() - started, 2)
    return result


def financial(symbol, report):
    result = {"kind": "financial", "symbol": symbol, "report": report,
              "source": "https://datacenter-web.eastmoney.com/api/data/v1/get", "status": "error"}
    params = {"reportName": report, "columns": "ALL", "filter": f'(SECURITY_CODE="{symbol.split(".")[0]}")',
              "pageNumber": 1, "pageSize": 12, "sortColumns": "REPORT_DATE", "sortTypes": "-1",
              "source": "WEB", "client": "WEB"}
    try:
        response = httpx.get(result["source"], params=params, timeout=20, follow_redirects=True)
        result["http_status"] = response.status_code
        result["request_url"] = str(response.url)
        response.raise_for_status()
        payload = response.json()
        result.update(persist(f"{report}-{symbol}", payload))
        records = (payload.get("result") or {}).get("data") or []
        result.update(status="ok" if records else "empty", count=len(records),
                      message=payload.get("message"), fields=list(records[0]) if records else [])
        if records:
            result["dates"] = [{k: row.get(k) for k in ("REPORT_DATE", "NOTICE_DATE", "PUBLISH_DATE", "UPDATE_DATE") if k in row} for row in records]
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def industry():
    url = "https://www.semiconductors.org/category/press-releases/"
    result = {"kind": "industry_publication_index", "source": url, "status": "error"}
    try:
        response = httpx.get(url, timeout=20, follow_redirects=True)
        result["http_status"] = response.status_code
        response.raise_for_status()
        (RAW / "sia-press-releases.html").write_text(response.text, encoding="utf-8")
        result.update(status="ok", bytes=len(response.content),
                      sha256=hashlib.sha256(response.content).hexdigest(),
                      contains_sales="sales" in response.text.lower(),
                      note="HTTP availability only; time-series extraction not validated.")
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def main():
    jobs = [(daily, (symbol,)) for symbol in SYMBOLS]
    jobs += [(financial, (symbol, report)) for symbol in SYMBOLS[:2]
             for report in ("RPT_DMSK_FN_INCOME", "RPT_DMSK_FN_BALANCE", "RPT_DMSK_FN_CASHFLOW")]
    jobs += [(industry, ())]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fn, *args) for fn, args in jobs]
        for future in concurrent.futures.as_completed(futures):
            row = future.result()
            results.append(row)
            print(json.dumps({k: v for k, v in row.items() if k not in ("fields", "dates", "request_url")}, ensure_ascii=False), flush=True)
    summary = {"checked_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
               "requested_interval": [START.isoformat(), END.isoformat()], "checks": results}
    (ROOT / "source-checks.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
