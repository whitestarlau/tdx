package main

import (
	"log"
	"os"

	"github.com/injoyai/tdx"
	"github.com/injoyai/tdx/extend/httpserver"
)

// 启动 HTTP 行情服务，供 Python 客户端(python/)调用。
// 默认 :8080，可用环境变量 TDX_HTTP_ADDR 覆盖。
func main() {
	addr := os.Getenv("TDX_HTTP_ADDR")
	if addr == "" {
		addr = ":8080"
	}
	s, err := httpserver.New(
		httpserver.WithAddr(addr),
		httpserver.WithPoolSize(2),
		httpserver.WithExHqHosts(tdx.ExHosts...),
		httpserver.WithOptions(tdx.WithRedial()),
	)
	if err != nil {
		log.Fatal(err)
	}
	log.Println("tdx http server listening on", addr)
	log.Fatal(s.Run())
}
