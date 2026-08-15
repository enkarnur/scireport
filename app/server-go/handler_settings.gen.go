// CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT
package main

import "net/http"

// 本文件由 IDL 生成，登记 settings 资源的路由契约。
// 业务逻辑写在 handler_settings.go 的 handler 函数里，不要改本文件。
func init() {
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/settings/ai",
		Summary: "获取 AI API 配置状态（不返回明文密钥）",
		Handler: settingsAiList,
		Tags:    []string{"settings"},
		Response: map[string]any{
			"data": map[string]any{
				"provider":     "openai-compatible",
				"baseUrl":      "https://api.openai.com/v1",
				"model":        "gpt-4o-mini",
				"hasApiKey":    false,
				"maskedApiKey": "",
				"updatedAt":    "2026-08-15T03:00:00Z",
			},
		},
	})
	Register(Route{
		Method:  http.MethodPut,
		Path:    "/api/settings/ai",
		Summary: "保存用户自己的 AI API 配置",
		Handler: settingsAiUpdate,
		Tags:    []string{"settings"},
		BodyParams: []Param{
			{Name: "provider", Type: "string", Description: "供应商标识，默认 openai-compatible"},
			{Name: "baseUrl", Type: "string", Required: true, Description: "OpenAI 兼容 API Base URL，例如 https://api.openai.com/v1"},
			{Name: "model", Type: "string", Required: true, Description: "模型名称"},
			{Name: "apiKey", Type: "string", Description: "用户自己的 API Key；为空则保留原 key"},
			{Name: "clearApiKey", Type: "boolean", Description: "是否清除已保存 API Key"},
		},
		RequestExample: map[string]any{
			"provider": "openai-compatible",
			"baseUrl":  "https://api.openai.com/v1",
			"model":    "gpt-4o-mini",
			"apiKey":   "",
		},
		Response: map[string]any{
			"data": map[string]any{
				"provider":     "openai-compatible",
				"baseUrl":      "https://api.openai.com/v1",
				"model":        "gpt-4o-mini",
				"hasApiKey":    true,
				"maskedApiKey": "sk-…abcd",
				"updatedAt":    "2026-08-15T03:00:00Z",
			},
		},
	})
}
