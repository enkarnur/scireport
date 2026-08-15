// CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT
package main

import "net/http"

// 本文件由 IDL 生成，登记 items 资源的路由契约。
// 业务逻辑写在 handler_items.go 的 handler 函数里，不要改本文件。
func init() {
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/items",
		Summary: "列出所有项目",
		Handler: itemsList,
		Tags:    []string{"items"},
		Response: map[string]any{
			"data":    []any{},
			"total":   0,
			"backend": "json",
		},
	})
	Register(Route{
		Method:  http.MethodPost,
		Path:    "/api/items",
		Summary: "创建项目",
		Handler: itemsCreate,
		Tags:    []string{"items"},
		BodyParams: []Param{
			{Name: "title", Type: "string", Required: true, Description: "项目标题，不能为空"},
			{Name: "description", Type: "string", Description: "项目描述，可选"},
			{Name: "status", Type: "string", Description: "项目状态，例如 todo/done"},
		},
		RequestExample: map[string]any{
			"title":       "示例任务",
			"description": "补充说明（可选）",
			"status":      "todo",
		},
		Response: map[string]any{
			"data": map[string]any{
				"id":     "1",
				"title":  "示例任务",
				"status": "todo",
			},
			"backend": "json",
		},
	})
	Register(Route{
		Method:  http.MethodDelete,
		Path:    "/api/items/{id}",
		Summary: "删除项目",
		Handler: itemsByIdDelete,
		Tags:    []string{"items"},
		Response: map[string]any{
			"success": true,
			"backend": "json",
		},
	})
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/items/{id}",
		Summary: "获取单个项目",
		Handler: itemsByIdGet,
		Tags:    []string{"items"},
		Response: map[string]any{
			"data": map[string]any{
				"id":     "1",
				"title":  "示例任务",
				"status": "todo",
			},
			"backend": "json",
		},
	})
	Register(Route{
		Method:  http.MethodPut,
		Path:    "/api/items/{id}",
		Summary: "更新项目（字段可选）",
		Handler: itemsByIdUpdate,
		Tags:    []string{"items"},
		BodyParams: []Param{
			{Name: "title", Type: "string", Description: "新项目标题，可选"},
			{Name: "description", Type: "string", Description: "新项目描述，可选"},
			{Name: "status", Type: "string", Description: "新项目状态，可选，例如 todo/done"},
		},
		RequestExample: map[string]any{
			"title":  "新标题",
			"status": "done",
		},
		Response: map[string]any{
			"data": map[string]any{
				"id":     "1",
				"title":  "新标题",
				"status": "done",
			},
			"backend": "json",
		},
	})
}
