package main

import (
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"sync"
)

// 约定：/api/_meta/* 是保留前缀，不要在这里挂业务接口。
func init() {
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/_meta/template",
		Summary: "查询本应用初始化时的脚手架模板版本信息（template_version 等）",
		Handler: metaTemplateHandler,
		Tags:    []string{"meta"},
	})
}

var (
	templateMetaOnce    sync.Once
	templateMetaPayload []byte
	templateMetaVersion = "0.0.0"
)

func getTemplateMeta() ([]byte, string) {
	templateMetaOnce.Do(loadTemplateMeta)
	return templateMetaPayload, templateMetaVersion
}

func loadTemplateMeta() {
	templateMetaPayload = []byte(`{"template_version":"0.0.0","reason":"template meta file missing"}`)

	data, err := os.ReadFile(filepath.Join(pluginDir, ".template_meta.json"))
	if err != nil {
		return
	}
	templateMetaPayload = data

	var meta map[string]any
	if err := json.Unmarshal(data, &meta); err == nil {
		if v, ok := meta["template_version"].(string); ok && v != "" {
			templateMetaVersion = v
		}
	}
}

// metaTemplateHandler 返回本应用初始化时的脚手架模板版本信息，供工具链做能力协商。
func metaTemplateHandler(w http.ResponseWriter, r *http.Request) {
	data, _ := getTemplateMeta()
	// 直接透传缓存的磁盘文件内容，避免二次序列化时字段丢失或顺序变化。
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write(data)
}

// metaRoutesHandler 输出全部业务路由的元数据，字段来自各 handler 文件 init() 中登记的 Route。
//
// 注意：该 handler 保留为内部/测试备用实现，但不注册 HTTP 路由；外部不允许通过 HTTP 访问。
//
// 输出示例：
//
//	{
//	  "template_version": "0.0.1",
//	  "routes": [
//	    {"method":"GET","path":"/api/items","summary":"列出所有项目","public":false,"tags":["items"]},
//	    ...
//	  ]
//	}
func metaRoutesHandler(w http.ResponseWriter, r *http.Request) {
	_, templateVersion := getTemplateMeta()
	writeJSON(w, http.StatusOK, map[string]any{
		"template_version": templateVersion,
		"routes":           snapshotRoutes(),
	})
}
