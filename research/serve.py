"""Launch Yanheng Quant on localhost with isolated research data."""
import os
import sys
from pathlib import Path

from paths import REPO, WORK

HERE = WORK
SOURCE = REPO
os.environ["DATA_DIR"] = str(HERE / "runtime-data")
os.environ["STATIC_DIR"] = str(SOURCE / "frontend" / "dist")
os.environ["TICKFLOW_ENV_FILE"] = str(REPO / ".env")
os.environ["BACKTEST_MATRIX_CACHE_PREWARM"] = "false"
os.environ["PYTHONUTF8"] = "1"
sys.path.insert(0, str(SOURCE / "backend"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=3018, log_level="info")
