"""HTTP JSON → pandas.DataFrame 转换。

列名对齐 mootdx/pytdx 习惯：K 线用 open/close/high/low/amount/vol + 年月日时分。
价格字段：Go 侧 protocol.Price 单位为厘(元×1000)，此处统一除以 1000 得元。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

PRICE_SCALE = 1000.0

# 与 mootdx/pytdx frequency 一致；路径为相对 /kline/ 或 /index/ 的后缀
FREQUENCY_MAP = {
    0: ("5minute", "5分钟"),
    1: ("15minute", "15分钟"),
    2: ("30minute", "30分钟"),
    3: ("60minute", "60分钟"),
    7: ("minute", "1分钟"),
    9: ("day", "日K"),
    5: ("week", "周K"),
    6: ("month", "月K"),
    10: ("quarter", "季K"),
    11: ("year", "年K"),
}

KLINE_COLUMNS = ["open", "close", "high", "low", "amount", "vol", "year", "month", "day", "hour", "minute"]


def _to_yuan(v: Any) -> float:
    if v is None:
        return 0.0
    return float(v) / PRICE_SCALE


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    s = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
        # mootdx 使用 naive datetime；去掉时区便于与 A 股日历对齐
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        return dt
    except ValueError:
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y%m%d"):
            try:
                if fmt == "%Y%m%d":
                    return datetime.strptime(s[:8], fmt)
                return datetime.strptime(s[:19], fmt)
            except ValueError:
                continue
    return None


def klines_to_df(payload: dict | list | None) -> pd.DataFrame:
    """把 KlineResp / list 转成 mootdx 风格 DataFrame。"""
    if payload is None:
        return pd.DataFrame(columns=KLINE_COLUMNS)

    if isinstance(payload, dict):
        items = payload.get("List") or payload.get("list") or []
    else:
        items = payload

    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        ts = _parse_time(item.get("Time") or item.get("time"))
        rows.append(
            {
                "open": _to_yuan(item.get("Open", item.get("open"))),
                "close": _to_yuan(item.get("Close", item.get("close"))),
                "high": _to_yuan(item.get("High", item.get("high"))),
                "low": _to_yuan(item.get("Low", item.get("low"))),
                "amount": _to_yuan(item.get("Amount", item.get("amount"))),
                "vol": float(item.get("Volume", item.get("volume", 0)) or 0),
                "year": ts.year if ts else None,
                "month": ts.month if ts else None,
                "day": ts.day if ts else None,
                "hour": ts.hour if ts else None,
                "minute": ts.minute if ts else None,
                "datetime": ts,
            }
        )

    if not rows:
        return pd.DataFrame(columns=KLINE_COLUMNS)

    df = pd.DataFrame(rows)
    df = df.set_index("datetime")
    df.index.name = "datetime"
    return df[KLINE_COLUMNS]


def quotes_to_df(payload: list | None) -> pd.DataFrame:
    """实时五档 → DataFrame，一代码一行。"""
    if not payload:
        return pd.DataFrame()

    rows = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        k = item.get("Kline") or {}
        buy = item.get("BuyLevel") or []
        sell = item.get("SellLevel") or []
        ex = item.get("Exchange")
        code = str(item.get("Code") or "")
        prefix = {0: "sz", 1: "sh", 2: "bj"}.get(ex, "")
        row = {
            "code": f"{prefix}{code}" if prefix and not code.startswith(("sh", "sz", "bj")) else code,
            "open": _to_yuan(k.get("Open")),
            "high": _to_yuan(k.get("High")),
            "low": _to_yuan(k.get("Low")),
            "price": _to_yuan(k.get("Close")),
            "last_close": _to_yuan(k.get("Last")),
            "vol": float(k.get("Volume") or 0),
            "amount": _to_yuan(k.get("Amount")),
            "server_time": item.get("ServerTime"),
            "active1": item.get("Active1"),
            "active2": item.get("Active2"),
        }
        for i in range(5):
            b = buy[i] if i < len(buy) else {}
            s = sell[i] if i < len(sell) else {}
            row[f"bid{i + 1}"] = _to_yuan(b.get("Price"))
            row[f"bid_vol{i + 1}"] = float(b.get("Number") or 0)
            row[f"ask{i + 1}"] = _to_yuan(s.get("Price"))
            row[f"ask_vol{i + 1}"] = float(s.get("Number") or 0)
        rows.append(row)

    return pd.DataFrame(rows)


def codes_to_series(payload: list | None, name: str = "code") -> pd.Series:
    if not payload:
        return pd.Series([], dtype="string", name=name)
    return pd.Series([str(x) for x in payload], dtype="string", name=name)
