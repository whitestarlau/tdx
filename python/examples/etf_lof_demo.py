"""ETF/LOF 行情演示。

前置：先启动 Go HTTP 服务，例如
    go run ./example/HTTPServer
然后
    python examples/etf_lof_demo.py
"""

from tdx_go import Quotes


def main() -> None:
    client = Quotes.factory()

    print("== 健康检查 ==")
    try:
        print(client.health())
    except Exception as e:
        print(f"服务未就绪: {e}")
        print("请先启动: go run ./example/HTTPServer")
        return

    print("\n== ETF / LOF 代码统计 ==")
    etfs = client.etf_codes()
    lofs = client.lof_codes()
    funds = client.fund_codes()
    print(f"纯ETF: {len(etfs)}  LOF: {len(lofs)}  场内基金合计: {len(funds)}")
    print("ETF 样例:", list(etfs[:5]))
    print("LOF 样例:", list(lofs[:5]))

    # 沪深300ETF + 一只常见 LOF
    symbols = ["sh510300", "sz160105"]

    print("\n== 实时行情 ==")
    q = client.quotes(*symbols)
    cols = [c for c in ["code", "price", "last_close", "open", "high", "low", "vol", "amount", "bid1", "ask1"] if c in q.columns]
    print(q[cols].to_string(index=False))

    print("\n== 日K（最近10根）==")
    for code in symbols:
        df = client.etf_bars(code, frequency=9, offset=10)
        print(f"\n--- {code} ---")
        print(df.tail(10).to_string())


if __name__ == "__main__":
    main()
