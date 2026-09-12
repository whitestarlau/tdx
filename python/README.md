# tdx-go Python 客户端

通过本地 HTTP 服务调用 Go 版通达信协议实现，返回 **pandas DataFrame**（列名对齐 mootdx）。

## 前置

1. 启动 Go HTTP 服务：

```bash
# 默认 :8080；端口被占用时用 TDX_HTTP_ADDR
go run ./example/HTTPServer
TDX_HTTP_ADDR=:18080 go run ./example/HTTPServer
```

客户端默认连 `http://127.0.0.1:8080`，可用环境变量覆盖：

```bash
export TDX_GO_BASE_URL=http://127.0.0.1:18080
```

2. 安装 Python 依赖：

```bash
cd python
pip install -e .
```

## 快速上手

```python
from tdx_go import Quotes

client = Quotes.factory()  # 或 Quotes.factory("http://127.0.0.1:8080")

# 日K（frequency=9，与 mootdx 一致）
df = client.bars("sh510300", frequency=9, offset=100)
print(df.head())
# open  close  high  low  amount      vol  year month day hour minute
# ...   沪深300ETF 日K，价格单位为元，vol 为手

# 实时五档
q = client.quotes("sh510300", "sz159919")
print(q[["code", "price", "last_close", "vol", "bid1", "ask1"]])

# ETF / LOF 代码
etfs = client.etf_codes()   # 纯 ETF
lofs = client.lof_codes()   # LOF
funds = client.fund_codes() # 场内基金（ETF+LOF+封闭式）
```

## API 对照

| 方法 | 说明 | 返回 |
|------|------|------|
| `bars(symbol, frequency=9, offset=100)` | K线 | DataFrame：open/close/high/low/amount/vol + 年月日时分，index=datetime |
| `bars_all(symbol, frequency=9)` | 全量K线 | 同上 |
| `quotes(*symbols)` | 实时五档 | DataFrame：price/bid1-5/ask1-5 等 |
| `index(symbol, frequency, offset)` | 指数K线 | 同 bars |
| `etf_codes()` | 纯 ETF 代码 | Series |
| `lof_codes()` | LOF 代码 | Series |
| `fund_codes()` | 场内基金全部 | Series |
| `etf_bars` / `etf_quotes` | ETF/LOF 行情别名 | 同 bars/quotes |

### frequency 对照（与 mootdx 相同）

| 值 | 周期 |
|----|------|
| 0 | 5分钟 |
| 1 | 15分钟 |
| 2 | 30分钟 |
| 3 | 60分钟 |
| 7 | 1分钟 |
| 9 | 日K |
| 5 | 周K |
| 6 | 月K |
| 10 | 季K |
| 11 | 年K |

## 单位约定

- 价格：元（Go 内部厘 ÷ 1000）
- 成交量 `vol`：手（与标准行情协议一致；股票/ETF 1手=100股）
- 成交额 `amount`：元

## 代码格式

支持带交易所前缀：`sh510300`、`sz159919`、`sz160105`。  
服务端会自动补前缀，裸代码如 `510300` 一般也可用。

## 与 mootdx 的关系

| | mootdx | tdx-go Python |
|--|--------|---------------|
| 协议实现 | 纯 Python | Go（本仓库） |
| 调用方式 | 直连 7709 | 本地 HTTP → Go → 7709 |
| 返回类型 | pandas DataFrame | pandas DataFrame |
| 安装 | `pip install mootdx` | 需先跑 Go 服务 + `pip install -e python/` |

选择本方案的价值：复用 Go 侧已实现的 pull/复权/板块/扩展行情等能力，Python 只做 DataFrame 层。
