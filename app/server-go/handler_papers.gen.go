// CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT
package main

import "net/http"

// 本文件由 IDL 生成，登记 papers 资源的路由契约。
// 业务逻辑写在 handler_papers.go 的 handler 函数里，不要改本文件。
func init() {
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/papers",
		Summary: "检索并分页列出文献库论文",
		Handler: papersList,
		Tags:    []string{"papers"},
		QueryParams: []Param{
			{Name: "q", Type: "string", Description: "可选，匹配标题、作者、摘要或全文"},
			{Name: "status", Type: "string", Description: "可选，按 processing/ready/failed 筛选"},
			{Name: "limit", Type: "number", Description: "每页数量，默认 20，最大 100"},
			{Name: "offset", Type: "number", Description: "分页偏移，默认 0"},
		},
		Response: map[string]any{
			"data": []any{
				map[string]any{
					"id":    "paper_01",
					"title": "面向文献研析的检索增强方法",
					"authors": []any{
						"张三",
						"李四",
					},
					"year":             2026,
					"venue":            "示例期刊",
					"doi":              "10.0000/example",
					"abstract":         "论文摘要",
					"background":       "研究背景概述",
					"methods":          "研究方法概述",
					"results":          "研究结果概述",
					"discussion":       "讨论概述",
					"processingStatus": "ready",
					"pageCount":        12,
					"sourceFileName":   "example.pdf",
					"createdAt":        "2026-08-15T02:00:00Z",
					"updatedAt":        "2026-08-15T02:01:00Z",
				},
			},
			"total":  1,
			"limit":  20,
			"offset": 0,
		},
	})
	Register(Route{
		Method:  http.MethodPost,
		Path:    "/api/papers",
		Summary: "将浏览器本地提取的 PDF 文本与元数据入库并启动结构化研析",
		Handler: papersCreate,
		Tags:    []string{"papers"},
		BodyParams: []Param{
			{Name: "title", Type: "string", Required: true, Description: "论文标题"},
			{Name: "authors", Type: "array", Required: true, Description: "作者姓名字符串数组，可为空数组"},
			{Name: "year", Type: "number", Description: "发表年份"},
			{Name: "venue", Type: "string", Description: "期刊、会议或来源"},
			{Name: "doi", Type: "string", Description: "DOI，可选"},
			{Name: "sourceFileName", Type: "string", Required: true, Description: "仅保存原 PDF 文件名，不保存本地绝对路径"},
			{Name: "pageCount", Type: "number", Required: true, Description: "PDF 总页数"},
			{Name: "fullText", Type: "string", Required: true, Description: "浏览器从 PDF 提取的全文，不包含 PDF 二进制"},
			{Name: "pages", Type: "array", Required: true, Description: "页级文本对象数组，每项含 pageNumber 与 text，用于定位"},
		},
		RequestExample: map[string]any{
			"title": "面向文献研析的检索增强方法",
			"authors": []any{
				"张三",
				"李四",
			},
			"year":           2026,
			"venue":          "示例期刊",
			"doi":            "10.0000/example",
			"sourceFileName": "example.pdf",
			"pageCount":      2,
			"fullText":       "第一页文本\n第二页文本",
			"pages": []any{
				map[string]any{
					"pageNumber": 1,
					"text":       "第一页文本",
				},
				map[string]any{
					"pageNumber": 2,
					"text":       "第二页文本",
				},
			},
		},
		Response: map[string]any{
			"data": map[string]any{
				"id":    "paper_01",
				"title": "面向文献研析的检索增强方法",
				"authors": []any{
					"张三",
					"李四",
				},
				"year":             2026,
				"venue":            "示例期刊",
				"doi":              "10.0000/example",
				"abstract":         "",
				"background":       "",
				"methods":          "",
				"results":          "",
				"discussion":       "",
				"processingStatus": "processing",
				"processingError":  "",
				"pageCount":        2,
				"sourceFileName":   "example.pdf",
				"createdAt":        "2026-08-15T02:00:00Z",
				"updatedAt":        "2026-08-15T02:00:00Z",
			},
		},
	})
	Register(Route{
		Method:  http.MethodDelete,
		Path:    "/api/papers/{paperId}",
		Summary: "删除论文及其关联批注",
		Handler: papersByPaperIdDelete,
		Tags:    []string{"papers"},
		Response: map[string]any{
			"success":        true,
			"deletedPaperId": "paper_01",
		},
	})
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/papers/{paperId}",
		Summary: "获取论文详情、结构化研析内容与页级定位文本",
		Handler: papersByPaperIdGet,
		Tags:    []string{"papers"},
		Response: map[string]any{
			"data": map[string]any{
				"id":    "paper_01",
				"title": "面向文献研析的检索增强方法",
				"authors": []any{
					"张三",
					"李四",
				},
				"year":             2026,
				"venue":            "示例期刊",
				"doi":              "10.0000/example",
				"abstract":         "论文摘要",
				"background":       "研究背景概述",
				"methods":          "研究方法概述",
				"results":          "研究结果概述",
				"discussion":       "讨论概述",
				"processingStatus": "ready",
				"processingError":  "",
				"pageCount":        2,
				"sourceFileName":   "example.pdf",
				"fullText":         "第一页文本\n第二页文本",
				"pages": []any{
					map[string]any{
						"pageNumber": 1,
						"text":       "第一页文本",
					},
					map[string]any{
						"pageNumber": 2,
						"text":       "第二页文本",
					},
				},
				"createdAt": "2026-08-15T02:00:00Z",
				"updatedAt": "2026-08-15T02:01:00Z",
			},
		},
	})
}
