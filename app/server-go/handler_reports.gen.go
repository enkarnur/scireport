// CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT
package main

import "net/http"

// 本文件由 IDL 生成，登记 reports 资源的路由契约。
// 业务逻辑写在 handler_reports.go 的 handler 函数里，不要改本文件。
func init() {
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/reports",
		Summary: "分页查询系统文献汇报记录",
		Handler: reportsList,
		Tags:    []string{"reports"},
		QueryParams: []Param{
			{Name: "status", Type: "string", Description: "可选，按 generating/ready/failed 筛选"},
			{Name: "limit", Type: "number", Description: "每页数量，默认 20，最大 100"},
			{Name: "offset", Type: "number", Description: "分页偏移，默认 0"},
		},
		Response: map[string]any{
			"data": []any{
				map[string]any{
					"id":       "report_01",
					"title":    "检索增强研究系统综述",
					"template": "systematic-review",
					"status":   "ready",
					"paperIds": []any{
						"paper_01",
					},
					"paperCount": 1,
					"createdAt":  "2026-08-15T02:30:00Z",
					"updatedAt":  "2026-08-15T02:31:00Z",
				},
			},
			"total":  1,
			"limit":  20,
			"offset": 0,
		},
	})
	Register(Route{
		Method:  http.MethodPost,
		Path:    "/api/reports",
		Summary: "按模板和论文范围生成系统文献汇报",
		Handler: reportsCreate,
		Tags:    []string{"reports"},
		BodyParams: []Param{
			{Name: "title", Type: "string", Required: true, Description: "报告标题"},
			{Name: "template", Type: "string", Required: true, Description: "模板标识：systematic-review/comparison/evidence-summary"},
			{Name: "paperIds", Type: "array", Required: true, Description: "参与报告生成的论文 ID 数组，不能为空"},
			{Name: "researchQuestion", Type: "string", Description: "可选，报告聚焦的研究问题"},
			{Name: "language", Type: "string", Description: "报告语言，默认 zh-CN"},
		},
		RequestExample: map[string]any{
			"title":    "检索增强研究系统综述",
			"template": "systematic-review",
			"paperIds": []any{
				"paper_01",
			},
			"researchQuestion": "检索增强方法如何改善文献问答？",
			"language":         "zh-CN",
		},
		Response: map[string]any{
			"data": map[string]any{
				"id":       "report_01",
				"title":    "检索增强研究系统综述",
				"template": "systematic-review",
				"status":   "generating",
				"paperIds": []any{
					"paper_01",
				},
				"researchQuestion": "检索增强方法如何改善文献问答？",
				"language":         "zh-CN",
				"createdAt":        "2026-08-15T02:30:00Z",
				"updatedAt":        "2026-08-15T02:30:00Z",
			},
		},
	})
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/reports/{reportId}",
		Summary: "获取报告生成状态、模板化章节与引用线索",
		Handler: reportsByReportIdGet,
		Tags:    []string{"reports"},
		Response: map[string]any{
			"data": map[string]any{
				"id":       "report_01",
				"title":    "检索增强研究系统综述",
				"template": "systematic-review",
				"status":   "ready",
				"error":    "",
				"paperIds": []any{
					"paper_01",
				},
				"researchQuestion": "检索增强方法如何改善文献问答？",
				"language":         "zh-CN",
				"sections": []any{
					map[string]any{
						"key":     "abstract",
						"title":   "摘要",
						"content": "本报告系统梳理了检索增强研究。",
						"citations": []any{
							map[string]any{
								"paperId":     "paper_01",
								"paperTitle":  "面向文献研析的检索增强方法",
								"pageNumber":  4,
								"section":     "方法",
								"quote":       "我们提出一种两阶段检索方法",
								"startOffset": 1200,
								"endOffset":   1215,
							},
						},
					},
				},
				"createdAt": "2026-08-15T02:30:00Z",
				"updatedAt": "2026-08-15T02:31:00Z",
			},
		},
	})
	Register(Route{
		Method:  http.MethodPost,
		Path:    "/api/reports/{reportId}/export",
		Summary: "将已完成报告导出为 Word DOCX",
		Handler: reportsByReportIdExportCreate,
		Tags:    []string{"reports"},
		BodyParams: []Param{
			{Name: "fileName", Type: "string", Description: "可选下载文件名，不含本地路径"},
		},
		RequestExample: map[string]any{
			"fileName": "检索增强研究系统综述.docx",
		},
		Response: map[string]any{
			"data": map[string]any{
				"reportId":      "report_01",
				"fileName":      "检索增强研究系统综述.docx",
				"mimeType":      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
				"encoding":      "base64",
				"contentBase64": "UEsDBBQAAAAI...",
				"generatedAt":   "2026-08-15T02:35:00Z",
			},
		},
	})
}
