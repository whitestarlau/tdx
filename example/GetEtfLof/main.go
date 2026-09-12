package main

import (
	"github.com/injoyai/logs"
	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/example/common"
	"github.com/injoyai/tdx/protocol"
)

// 演示 ETF / LOF 代码分类与行情获取。
func main() {
	common.Test(func(c *tdx.Client) {
		// GetQuote 需要 DefaultCodes 做 Decimal 价格修正（ETF Decimal=4）
		var err error
		tdx.DefaultCodes, err = tdx.NewCodesSqlite(tdx.WithCodesClient(c))
		logs.PanicErr(err)

		funds, err := c.GetFundCodeAll()
		logs.PanicErr(err)
		etfs, err := c.GetListedETFCodeAll()
		logs.PanicErr(err)
		lofs, err := c.GetLOFCodeAll()
		logs.PanicErr(err)
		logs.Debug("场内基金=", len(funds), " 纯ETF=", len(etfs), " LOF=", len(lofs))
		logs.Debug("ETF样例:", etfs[:min(5, len(etfs))])
		logs.Debug("LOF样例:", lofs[:min(5, len(lofs))])

		// 沪深300ETF + 深市LOF
		for _, code := range []string{"sh510300", "sz160105"} {
			logs.Debug(code,
				" IsFund=", protocol.IsFund(code),
				" IsListedETF=", protocol.IsListedETF(code),
				" IsLOF=", protocol.IsLOF(code))

			quote, err := c.GetQuote(code)
			logs.PanicErr(err)
			for _, q := range quote {
				logs.Debug(q)
			}

			resp, err := c.GetKlineDay(code, 0, 5)
			logs.PanicErr(err)
			for _, k := range resp.List {
				logs.Debug(k)
			}
		}
	})
}
