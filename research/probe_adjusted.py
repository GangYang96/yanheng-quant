"""Check adjusted prices independently of the separately gated factor endpoint."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from tickflow import TickFlow

from probe_sources import END, RAW, ROOT, START, SYMBOLS, persist

client = TickFlow.free(timeout=20, max_retries=0, cache_dir=str(ROOT / "sdk-cache"))
results = []
for symbol in SYMBOLS:
    row = {"symbol": symbol, "adjust": "forward", "status": "error"}
    try:
        payload = client.klines.get(symbol, period="1d", adjust="forward", count=10000,
                                   start_time=int(START.timestamp() * 1000),
                                   end_time=int(END.timestamp() * 1000), as_dataframe=False)
        row.update(persist("forward-" + symbol, payload))
        row.update(status="ok", count=len(payload.get("timestamp", [])))
        raw = json.loads((RAW / ("daily-" + symbol + ".json")).read_text(encoding="utf-8"))
        if raw.get("timestamp") == payload.get("timestamp"):
            row["different_close_count"] = sum(abs(a-b) > 0.000001 for a, b in zip(raw["close"], payload["close"]))
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
    results.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)

try:
    response = httpx.get("https://www.wsts.org/", timeout=20, follow_redirects=True)
    response.raise_for_status()
    (RAW / "wsts-home.html").write_text(response.text, encoding="utf-8")
    results.append({"kind": "industry_publication_index", "source": str(response.url),
                    "status": "ok", "http_status": response.status_code, "bytes": len(response.content),
                    "note": "Homepage availability only; no historical series verified."})
except Exception as exc:
    results.append({"kind": "industry_publication_index", "source": "https://www.wsts.org/",
                    "status": "error", "error": f"{type(exc).__name__}: {exc}"})

(ROOT / "adjusted-checks.json").write_text(json.dumps({
    "checked_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(), "checks": results,
}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(results[-1], ensure_ascii=False))
