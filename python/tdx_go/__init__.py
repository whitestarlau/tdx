"""tdx-go Python 客户端：通过本地 HTTP 服务调用 Go 版通达信协议实现。

用法（对齐 mootdx 风格）::

    from tdx_go import Quotes

    client = Quotes.factory()  # 默认 http://127.0.0.1:8080
    df = client.bars(symbol="510300", frequency=9, offset=100)
    df = client.quotes("sh510300", "sz159919")
"""

from .client import Quotes, TdxError

__all__ = ["Quotes", "TdxError"]
__version__ = "0.1.0"
