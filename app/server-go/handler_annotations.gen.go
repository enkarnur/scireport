// CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT
package main

import "net/http"

// 本文件由 IDL 生成，登记 annotations 资源的路由契约。
// 业务逻辑写在 handler_annotations.go 的 handler 函数里，不要改本文件。
func init() {
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/annotations",
		Summary: "按论文、关键词或页码检索批注",
		Handler: annotationsList,
		Tags:    []string{"annotations"},
		QueryParams: []Param{
			{Name: "paperId", Type: "string", Description: "可选，限定论文 ID"},
			{Name: "q", Type: "string", Description: "可选，匹配批注内容、章节或引用片段"},
			{Name: "pageNumber", Type: "number", Description: "可选，限定 PDF 页码，从 1 开始"},
			{Name: "limit", Type: "number", Description: "每页数量，默认 50，最大 200"},
			{Name: "offset", Type: "number", Description: "分页偏移，默认 0"},
		},
		Response: map[string]any{
			"data": []any{
				map[string]any{
					"id":          "ann_01",
					"paperId":     "paper_01",
					"paperTitle":  "面向文献研析的检索增强方法",
					"content":     "该方法与基线设计相关",
					"pageNumber":  4,
					"section":     "方法",
					"quote":       "我们提出一种两阶段检索方法",
					"startOffset": 1200,
					"endOffset":   1215,
					"color":       "yellow",
					"createdAt":   "2026-08-15T02:10:00Z",
					"updatedAt":   "2026-08-15T02:10:00Z",
				},
			},
			"total":  1,
			"limit":  50,
			"offset": 0,
		},
	})
	Register(Route{
		Method:  http.MethodPost,
		Path:    "/api/annotations",
		Summary: "为论文创建可定位批注",
		Handler: annotationsCreate,
		Tags:    []string{"annotations"},
		BodyParams: []Param{
			{Name: "paperId", Type: "string", Required: true, Description: "关联论文 ID"},
			{Name: "content", Type: "string", Required: true, Description: "批注正文"},
			{Name: "pageNumber", Type: "number", Required: true, Description: "PDF 页码，从 1 开始"},
			{Name: "section", Type: "string", Description: "章节名，可选"},
			{Name: "quote", Type: "string", Description: "用于快速定位的原文短片段"},
			{Name: "startOffset", Type: "number", Description: "提取全文中的起始字符偏移"},
			{Name: "endOffset", Type: "number", Description: "提取全文中的结束字符偏移"},
			{Name: "color", Type: "string", Description: "标记颜色语义，默认 yellow"},
		},
		RequestExample: map[string]any{
			"paperId":     "paper_01",
			"content":     "该方法与基线设计相关",
			"pageNumber":  4,
			"section":     "方法",
			"quote":       "我们提出一种两阶段检索方法",
			"startOffset": 1200,
			"endOffset":   1215,
			"color":       "yellow",
		},
		Response: map[string]any{
			"data": map[string]any{
				"id":          "ann_01",
				"paperId":     "paper_01",
				"content":     "该方法与基线设计相关",
				"pageNumber":  4,
				"section":     "方法",
				"quote":       "我们提出一种两阶段检索方法",
				"startOffset": 1200,
				"endOffset":   1215,
				"color":       "yellow",
				"createdAt":   "2026-08-15T02:10:00Z",
				"updatedAt":   "2026-08-15T02:10:00Z",
			},
		},
	})
	Register(Route{
		Method:  http.MethodDelete,
		Path:    "/api/annotations/{annotationId}",
		Summary: "删除批注",
		Handler: annotationsByAnnotationIdDelete,
		Tags:    []string{"annotations"},
		Response: map[string]any{
			"success":             true,
			"deletedAnnotationId": "ann_01",
		},
	})
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/annotations/{annotationId}",
		Summary: "获取单条批注及论文定位信息",
		Handler: annotationsByAnnotationIdGet,
		Tags:    []string{"annotations"},
		Response: map[string]any{
			"data": map[string]any{
				"id":          "ann_01",
				"paperId":     "paper_01",
				"paperTitle":  "面向文献研析的检索增强方法",
				"content":     "该方法与基线设计相关",
				"pageNumber":  4,
				"section":     "方法",
				"quote":       "我们提出一种两阶段检索方法",
				"startOffset": 1200,
				"endOffset":   1215,
				"color":       "yellow",
				"createdAt":   "2026-08-15T02:10:00Z",
				"updatedAt":   "2026-08-15T02:10:00Z",
			},
		},
	})
	Register(Route{
		Method:  http.MethodPut,
		Path:    "/api/annotations/{annotationId}",
		Summary: "更新批注内容与定位信息",
		Handler: annotationsByAnnotationIdUpdate,
		Tags:    []string{"annotations"},
		BodyParams: []Param{
			{Name: "content", Type: "string", Description: "新的批注正文"},
			{Name: "pageNumber", Type: "number", Description: "新的 PDF 页码"},
			{Name: "section", Type: "string", Description: "新的章节名"},
			{Name: "quote", Type: "string", Description: "新的原文定位片段"},
			{Name: "startOffset", Type: "number", Description: "新的起始字符偏移"},
			{Name: "endOffset", Type: "number", Description: "新的结束字符偏移"},
			{Name: "color", Type: "string", Description: "新的标记颜色语义"},
		},
		RequestExample: map[string]any{
			"content": "更新后的批注",
			"color":   "blue",
		},
		Response: map[string]any{
			"data": map[string]any{
				"id":          "ann_01",
				"paperId":     "paper_01",
				"content":     "更新后的批注",
				"pageNumber":  4,
				"section":     "方法",
				"quote":       "我们提出一种两阶段检索方法",
				"startOffset": 1200,
				"endOffset":   1215,
				"color":       "blue",
				"createdAt":   "2026-08-15T02:10:00Z",
				"updatedAt":   "2026-08-15T02:12:00Z",
			},
		},
	})
}
