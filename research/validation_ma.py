"""仅验证数据和引擎链路，不构成半导体基本面策略或收益承诺。"""
import polars as pl

META = {
    "id": "validation_ma",
    "name": "链路验证：20/60 日均线",
    "description": "收盘价 > MA20 > MA60 时允许入场，次日开盘成交，最多持仓20个交易日。仅限固定的三个样本；使用采集时的前复权快照，不代表已完成基本面或样本外验证。",
    "asset_types": ["stock", "etf"],
    "timeframes": ["1d"],
    "params": [],
    "scoring": {},
    "limit": 3,
    "tags": ["验证样例", "非投资建议"],
}
BASIC_FILTER = {"enabled": False}
REQUIRED_FEATURES = ["close", "ma20", "ma60"]
MAX_HOLD_DAYS = 20


def filter(df, params):
    return (pl.col("close") > pl.col("ma20")) & (pl.col("ma20") > pl.col("ma60"))
