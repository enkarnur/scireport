// CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT
package main

import "net/http"

// 本文件由 IDL 生成，登记 qa 资源的路由契约。
// 业务逻辑写在 handler_qa.go 的 handler 函数里，不要改本文件。
func init() {
	Register(Route{
		Method:  http.MethodPost,
		Path:    "/api/qa/ask",
		Summary: "在全部或指定论文范围内问答并返回可核验定位线索",
		Handler: qaAskCreate,
		Tags:    []string{"qa"},
		BodyParams: []Param{
			{Name: "question", Type: "string", Required: true, Description: "用户问题"},
			{Name: "paperIds", Type: "array", Description: "可选论文 ID 数组；省略或空数组表示全部就绪论文"},
			{Name: "includeAnnotations", Type: "boolean", Description: "是否将相关批注纳入上下文，默认 true"},
		},
		RequestExample: map[string]any{
			"question": "这些论文采用了哪些检索增强方法？",
			"paperIds": []any{
				"paper_01",
			},
			"includeAnnotations": true,
		},
		Response: map[string]any{
			"data": map[string]any{
				"id":       "qa_01",
				"question": "这些论文采用了哪些检索增强方法？",
				"answer":   "论文采用两阶段检索，并通过重排序提高证据相关性。",
				"scope": map[string]any{
					"paperIds": []any{
						"paper_01",
					},
					"includeAnnotations": true,
				},
				"hits": []any{
					map[string]any{
						"paperId":    "paper_01",
						"paperTitle": "面向文献研析的检索增强方法",
						"score":      0.93,
					},
				},
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
				"createdAt": "2026-08-15T02:20:00Z",
			},
		},
	})
}
