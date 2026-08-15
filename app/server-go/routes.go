package main

import (
	"fmt"
	"net/http"
	"sort"
)

// Route 描述一条业务路由，供本模板的“自注册路由”能力使用（template_version >= 0.0.1）。
//
// 用法：在同一 handler 文件里用 init() 调用 Register(Route{...})。
//
//	func init() {
//		Register(Route{
//			Method:  "POST",
//			Path:    "/api/items",
//			Summary: "创建项目",
//			Handler: itemsCreate,
//			BodyParams: []Param{
//				{Name: "title", Type: "string", Required: true, Description: "项目标题"},
//			},
//			RequestExample: map[string]any{"title": "示例", "status": "todo"},
//		})
//	}
//
// 只要 handler 文件被编译进来，init() 就会执行；服务启动时会把注册表写入 CLI Skill references 的 api-routes.index.json / api-routes.details.json。
type Route struct {
	// Method 必填。目前仅接受 GET / POST / PUT / DELETE / PATCH。
	Method string
	// Path 必填。走 Go 1.22+ enhanced ServeMux 模式：
	Path string
	// Summary 必填。一句话描述接口意图，会出现在 route snapshot 里给 Agent / CLI 看。
	Summary string
	// Handler 必填。业务函数。
	Handler http.HandlerFunc
	// Public 默认 false：会被 wrapAuth 包一层强制走 JWT 校验。
	// 仅健康检查等确实不需要身份的接口才设 true；/api/_meta/* 默认也走 JWT。
	Public bool
	// Tags 可选：接口分组，例如 ["items"]。
	Tags []string
	// RequestExample / Response / QueryParams / BodyParams 是 OpenAPI-lite 元数据。
	// 新增或修改接口时必须把 QueryParams / BodyParams 填完整清晰；RequestExample 用于给 Agent 可直接照抄的请求示例。
	// Response 是响应契约，用于生成 TS 类型与 progressive CLI reference。
	RequestExample any     `json:",omitempty"`
	Response       any     `json:",omitempty"`
	QueryParams    []Param `json:",omitempty"`
	BodyParams     []Param `json:",omitempty"`
}

// Param 描述一个请求参数，可用于 query_params 或 body_params。
type Param struct {
	Name        string  `json:"name"`
	Type        string  `json:"type,omitempty"` // "string" | "int" | "number" | "bool" | "object" | "array" ...
	Required    bool    `json:"required,omitempty"`
	Description string  `json:"description,omitempty"`
	Children    []Param `json:"children,omitempty"`
}

// registry 是全局注册表；由各 handler 文件的 init() 通过 Register 添加。
var registry []Route

// registeredKeys 用于查重：同一 method+path 只能注册一次。
var registeredKeys = map[string]string{}

// Register 把 Route 加入全局 registry。
// 校验失败直接 panic：模板期望"启动即失败"胜过"上线后 404 才发现"。
func Register(r Route) {
	if r.Method == "" || r.Path == "" || r.Summary == "" || r.Handler == nil {
		panic(fmt.Sprintf("Register: Route 必填字段缺失: %+v", r))
	}
	switch r.Method {
	case http.MethodGet, http.MethodPost, http.MethodPut, http.MethodDelete, http.MethodPatch:
	default:
		panic(fmt.Sprintf("Register: 不支持的 Method %q（仅 GET/POST/PUT/DELETE/PATCH）", r.Method))
	}
	key := r.Method + " " + r.Path
	if existing, dup := registeredKeys[key]; dup {
		panic(fmt.Sprintf("Register: 重复注册路由 %q（已有 handler=%s）", key, existing))
	}
	registeredKeys[key] = fmt.Sprintf("%p", r.Handler)
	registry = append(registry, r)
}

// mountRoutes 把 registry 中所有路由挂到给定 mux 上。
// 非 Public 的路由会包一层 auth：走 authMiddleware，鉴权失败直接由中间件写响应并返回 false。
func mountRoutes(mux *http.ServeMux) {
	for _, r := range registry {
		pattern := r.Method + " " + r.Path
		handler := r.Handler
		if !r.Public {
			handler = wrapAuth(handler)
		}
		mux.HandleFunc(pattern, handler)
	}
}

// wrapAuth 用现有的 authMiddleware（返回 (*http.Request, bool)）包住业务 handler。
// authMiddleware 已经会在鉴权失败时写响应，这里只负责在鉴权通过时把带 user context 的 request 转发下去。
func wrapAuth(h http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		authedReq, ok := authMiddleware(w, r)
		if !ok {
			return
		}
		h(w, authedReq)
	}
}

// snapshotRoutes 返回 registry 的副本，按 Path/Method 排序，供 route snapshot 输出。
// Handler 字段被剔除（不可序列化，也不该暴露）。
func snapshotRoutes() []map[string]any {
	out := make([]map[string]any, 0, len(registry))
	for _, r := range registry {
		item := map[string]any{
			"method":  r.Method,
			"path":    r.Path,
			"summary": r.Summary,
			"public":  r.Public,
		}
		if len(r.Tags) > 0 {
			item["tags"] = r.Tags
		}
		if r.RequestExample != nil {
			item["request_example"] = r.RequestExample
		}
		if r.Response != nil {
			item["response"] = r.Response
		}
		if len(r.QueryParams) > 0 {
			item["query_params"] = r.QueryParams
		}
		if len(r.BodyParams) > 0 {
			item["body_params"] = r.BodyParams
		}
		out = append(out, item)
	}
	sort.SliceStable(out, func(i, j int) bool {
		pi, _ := out[i]["path"].(string)
		pj, _ := out[j]["path"].(string)
		if pi != pj {
			return pi < pj
		}
		mi, _ := out[i]["method"].(string)
		mj, _ := out[j]["method"].(string)
		return mi < mj
	})
	return out
}

// snapshotRouteIndex 返回轻量路由索引，只包含 Agent 定位接口所需的信息。
// 完整 query/body/example 信息在 api-routes.details.json 中按 "METHOD PATH" key 保存。
func snapshotRouteIndex() []map[string]any {
	routes := snapshotRoutes()
	out := make([]map[string]any, 0, len(routes))
	for _, r := range routes {
		item := map[string]any{
			"method":  r["method"],
			"path":    r["path"],
			"summary": r["summary"],
		}
		if tags, ok := r["tags"]; ok {
			item["tags"] = tags
		}
		if resp, ok := r["response"]; ok {
			item["response"] = resp
		}
		out = append(out, item)
	}
	return out
}

// snapshotRoutesByKey 返回全量路由详情，key 形如 "POST /api/items"。
// 这样 Agent 可先在短索引里定位 method/path，再 grep_search 细节文件中的同名 key 附近上下文。
func snapshotRoutesByKey() map[string]map[string]any {
	routes := snapshotRoutes()
	out := make(map[string]map[string]any, len(routes))
	for _, r := range routes {
		method, _ := r["method"].(string)
		path, _ := r["path"].(string)
		out[method+" "+path] = r
	}
	return out
}
