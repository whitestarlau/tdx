"""mootdx 风格客户端，底层走 tdx httpserver。"""

from __future__ import annotations

import os
from typing import Iterable

import pandas as pd
import requests

from .frames import FREQUENCY_MAP, codes_to_series, klines_to_df, quotes_to_df

DEFAULT_BASE_URL = os.environ.get("TDX_GO_BASE_URL", "http://127.0.0.1:8080")


class TdxError(RuntimeError):
    """服务返回 code != 0 时抛出。"""


class Quotes:
    """通达信行情客户端（HTTP）。

    与 mootdx 对齐的主方法：
    - bars(symbol, frequency, offset) → DataFrame
    - quotes(*symbols) → DataFrame
    - index(symbol, frequency, offset) → DataFrame（指数K线）
    - minute(symbol) → DataFrame（当日分时）

    ETF/LOF 便捷方法：
    - etf_codes() / lof_codes() / fund_codes()
    """

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0, session: requests.Session | None = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()

    @classmethod
    def factory(cls, base_url: str | None = None, **kwargs) -> "Quotes":
        return cls(base_url=base_url or DEFAULT_BASE_URL, **kwargs)

    # ---- 基础 ----

    def _get(self, path: str, **params) -> dict:
        cleaned = {k: v for k, v in params.items() if v is not None}
        resp = self._session.get(f"{self.base_url}{path}", params=cleaned, timeout=self.timeout)
        resp.raise_for_status()
        body = resp.json()
        if body.get("code") != 0:
            raise TdxError(body.get("msg") or f"request failed: {path}")
        return body.get("data")

    def health(self) -> dict:
        return self._get("/")

    # ---- K线 ----

    def bars(self, symbol: str, frequency: int = 9, offset: int = 100, start: int = 0) -> pd.DataFrame:
        """获取股票/ETF/LOF K 线。

        frequency: 0=5分 1=15分 2=30分 3=60分 7=1分 9=日 5=周 6=月 10=季 11=年
        offset: 返回数量（与 mootdx offset 语义一致，从最新往回取）
        """
        if frequency not in FREQUENCY_MAP:
            raise ValueError(f"不支持的 frequency={frequency}，可选 {sorted(FREQUENCY_MAP)}")
        path, _ = FREQUENCY_MAP[frequency]
        data = self._get(f"/kline/{path}", code=symbol, start=start, count=offset)
        return klines_to_df(data)

    def bars_all(self, symbol: str, frequency: int = 9) -> pd.DataFrame:
        if frequency not in FREQUENCY_MAP:
            raise ValueError(f"不支持的 frequency={frequency}")
        path, _ = FREQUENCY_MAP[frequency]
        data = self._get(f"/kline/{path}/all", code=symbol)
        return klines_to_df(data)

    def minute(self, symbol: str, offset: int = 100, start: int = 0) -> pd.DataFrame:
        data = self._get("/minute", code=symbol)
        # 分时接口结构可能与 K 线不同，尽量转
        if isinstance(data, dict) and ("List" in data or "list" in data):
            return klines_to_df(data)
        return pd.DataFrame(data) if data is not None else pd.DataFrame()

    def index(self, symbol: str, frequency: int = 9, offset: int = 100, start: int = 0) -> pd.DataFrame:
        """指数 K 线。"""
        if frequency not in FREQUENCY_MAP:
            raise ValueError(f"指数不支持 frequency={frequency}")
        path, _ = FREQUENCY_MAP[frequency]
        data = self._get(f"/index/{path}", code=symbol, start=start, count=offset)
        return klines_to_df(data)

    def index_all(self, symbol: str, frequency: int = 9) -> pd.DataFrame:
        """指数全量 K 线（对应 /index/{path}/all）。"""
        if frequency not in FREQUENCY_MAP:
            raise ValueError(f"指数不支持 frequency={frequency}")
        path, _ = FREQUENCY_MAP[frequency]
        data = self._get(f"/index/{path}/all", code=symbol)
        return klines_to_df(data)

    # ---- 实时行情 ----

    def quotes(self, *symbols: str | Iterable[str]) -> pd.DataFrame:
        """实时五档。支持 quotes("sh510300","sz159919") 或 quotes(["sh510300", ...])。"""
        codes: list[str] = []
        for s in symbols:
            if isinstance(s, str):
                codes.extend([x.strip() for x in s.split(",") if x.strip()])
            else:
                codes.extend([str(x) for x in s])
        if not codes:
            raise ValueError("codes 不能为空")
        data = self._get("/quote", codes=",".join(codes))
        return quotes_to_df(data)

    # ---- 代码列表 ----

    def _codes(self, path: str) -> pd.Series:
        return codes_to_series(self._get(path))

    def etf_codes(self) -> pd.Series:
        """纯 ETF 代码（不含 LOF），如 sh510300 / sz159919。"""
        return self._codes("/code/listed-etfs")

    def lof_codes(self) -> pd.Series:
        """LOF 代码，如 sz160105 / sh501050。"""
        return self._codes("/code/lofs")

    def fund_codes(self) -> pd.Series:
        """全部场内基金（ETF+LOF+传统封闭式）。"""
        return self._codes("/code/funds")

    def stock_codes(self) -> pd.Series:
        return self._codes("/code/stocks")

    def index_codes(self) -> pd.Series:
        return self._codes("/code/indexes")

    # ---- ETF/LOF 行情便捷封装 ----

    def etf_bars(self, symbol: str, frequency: int = 9, offset: int = 100, start: int = 0) -> pd.DataFrame:
        """ETF/LOF K 线（与 bars 相同，语义标注）。"""
        return self.bars(symbol, frequency=frequency, offset=offset, start=start)

    def etf_quotes(self, *symbols: str | Iterable[str]) -> pd.DataFrame:
        """ETF/LOF 实时行情。"""
        return self.quotes(*symbols)
