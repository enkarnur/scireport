package main

import (
	"net/http"
	"sort"
	"strings"
	"time"
)

var reportTemplates = map[string]bool{"systematic-review": true, "comparison": true, "evidence-summary": true}

func reportsList(w http.ResponseWriter, r *http.Request) {
	limit, offset, err := pagination(r, 20, 100)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	status := strings.TrimSpace(r.URL.Query().Get("status"))
	if status != "" && status != "generating" && status != "ready" && status != "failed" {
		badRequest(w, "status 必须是 generating、ready 或 failed")
		return
	}
	items, err := store.GetAll(r.Context(), reportsCollection)
	if err != nil {
		internalError(w)
		return
	}
	filtered := []map[string]any{}
	for _, item := range items {
		if status != "" && mapString(item, "status") != status {
			continue
		}
		filtered = append(filtered, publicReport(item, false))
	}
	sort.SliceStable(filtered, func(i, j int) bool { return mapString(filtered[i], "createdAt") > mapString(filtered[j], "createdAt") })
	writeJSON(w, http.StatusOK, map[string]any{"data": pageSlice(filtered, offset, limit), "total": len(filtered), "limit": limit, "offset": offset})
}

func reportsCreate(w http.ResponseWriter, r *http.Request) {
	body, err := decodeObject(r)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	title, err := requiredString(body, "title", "title")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	template, err := requiredString(body, "template", "template")
	if err != nil || !reportTemplates[template] {
		badRequest(w, "template 必须是 systematic-review、comparison 或 evidence-summary")
		return
	}
	paperIDs, err := stringArray(body, "paperIds", true)
	if err != nil || len(paperIDs) == 0 {
		badRequest(w, "paperIds 必须是非空字符串数组")
		return
	}
	question, err := optionalString(body, "researchQuestion")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	language, err := optionalString(body, "language")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	if language == "" {
		language = "zh-CN"
	}
	papers := []map[string]any{}
	for _, id := range paperIDs {
		paper, err := store.GetByID(r.Context(), papersCollection, id)
		if err != nil {
			internalError(w)
			return
		}
		if paper == nil {
			badRequest(w, "论文不存在："+id)
			return
		}
		if mapString(paper, "processingStatus") != "ready" {
			badRequest(w, "论文尚未完成结构化处理："+id)
			return
		}
		papers = append(papers, paper)
	}
	annotations, err := store.GetAll(r.Context(), annotationsCollection)
	if err != nil {
		internalError(w)
		return
	}
	sections := generateReportSections(template, question, papers, annotations)
	record := map[string]any{"title": title, "template": template, "status": "ready", "error": "", "paperIds": paperIDs, "paperCount": len(paperIDs), "researchQuestion": question, "language": language, "sections": sections}
	created, err := store.Create(r.Context(), reportsCollection, record)
	if err != nil {
		internalError(w)
		return
	}
	writeJSON(w, http.StatusCreated, map[string]any{"data": publicReport(created, true)})
}

func reportsByReportIdGet(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimSpace(r.PathValue("reportId"))
	if id == "" {
		badRequest(w, "reportId 不能为空")
		return
	}
	item, err := store.GetByID(r.Context(), reportsCollection, id)
	if err != nil {
		internalError(w)
		return
	}
	if item == nil {
		notFound(w, "报告")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": publicReport(item, true)})
}

func reportsByReportIdExportCreate(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimSpace(r.PathValue("reportId"))
	if id == "" {
		badRequest(w, "reportId 不能为空")
		return
	}
	report, err := store.GetByID(r.Context(), reportsCollection, id)
	if err != nil {
		internalError(w)
		return
	}
	if report == nil {
		notFound(w, "报告")
		return
	}
	if mapString(report, "status") != "ready" {
		writeJSON(w, http.StatusConflict, map[string]any{"error": "报告尚未生成完成"})
		return
	}
	body, err := decodeOptionalObject(r)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	requested, err := optionalString(body, "fileName")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	name, err := safeFileName(requested, mapString(report, "title")+".docx")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	content, err := buildDOCX(report)
	if err != nil {
		internalError(w)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": map[string]any{"reportId": id, "fileName": name, "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "encoding": "base64", "contentBase64": content, "generatedAt": time.Now().UTC().Format(time.RFC3339)}})
}

func publicReport(item map[string]any, detail bool) map[string]any {
	keys := []string{"id", "title", "template", "status", "error", "paperIds", "paperCount", "researchQuestion", "language", "createdAt", "updatedAt"}
	if detail {
		keys = append(keys, "sections")
	}
	out := map[string]any{}
	for _, key := range keys {
		if value, ok := item[key]; ok {
			out[key] = value
		}
	}
	if _, ok := out["paperCount"]; !ok {
		if ids, yes := item["paperIds"].([]any); yes {
			out["paperCount"] = len(ids)
		}
	}
	return out
}

type reportSectionSpec struct{ key, title, field, stringLabel string }

func generateReportSections(template, question string, papers []map[string]any, annotations []map[string]any) []any {
	specs := []reportSectionSpec{{"research-question", "研究问题", "", "研究问题"}, {"background", "研究背景", "background", "研究背景"}, {"methods", "研究方法", "methods", "研究方法"}, {"results", "研究结果", "results", "研究结果"}, {"limitations", "局限与风险", "discussion", "局限与讨论"}, {"contributions", "主要贡献", "results", "贡献证据"}, {"reproducibility", "可复现性", "methods", "复现信息"}, {"discussion", "综合讨论", "discussion", "讨论"}, {"annotations", "研究批注", "", "批注"}}
	sections := make([]any, 0, len(specs))
	paperSet := map[string]bool{}
	for _, p := range papers {
		paperSet[mapString(p, "id")] = true
	}
	for _, spec := range specs {
		contentParts := []string{}
		citations := []map[string]any{}
		switch spec.key {
		case "research-question":
			if question != "" {
				contentParts = append(contentParts, question)
			} else {
				contentParts = append(contentParts, "未提供额外研究问题；报告围绕所选论文的研究目标、方法与证据展开。")
			}
		case "annotations":
			for _, a := range annotations {
				if !paperSet[mapString(a, "paperId")] {
					continue
				}
				for _, p := range papers {
					if mapString(p, "id") == mapString(a, "paperId") {
						contentParts = append(contentParts, "《"+mapString(p, "title")+"》："+mapString(a, "content"))
						citations = append(citations, map[string]any{"paperId": mapString(p, "id"), "paperTitle": mapString(p, "title"), "pageNumber": mapInt(a, "pageNumber"), "section": mapString(a, "section"), "quote": mapString(a, "quote"), "startOffset": mapInt(a, "startOffset"), "endOffset": mapInt(a, "endOffset")})
						break
					}
				}
			}
			if len(contentParts) == 0 {
				contentParts = append(contentParts, "所选论文暂无批注。")
			}
		default:
			for _, p := range papers {
				text := mapString(p, spec.field)
				if text == "" {
					contentParts = append(contentParts, "《"+mapString(p, "title")+"》未识别到可用于“"+spec.title+"”的明确原文。")
					continue
				}
				contentParts = append(contentParts, "《"+mapString(p, "title")+"》："+text)
				ev := pageEvidence(p, text)
				if len(ev) > 0 {
					citations = append(citations, evidenceMap(ev[0]))
				}
			}
			if spec.key == "reproducibility" {
				contentParts = append(contentParts, "复现时应以原文中明确给出的数据、方法和实验设置为准；未被结构化文本提及的参数不作推断。")
			}
		}
		prefix := ""
		if template == "comparison" && spec.key != "research-question" {
			prefix = "以下按论文逐项对照：\n"
		} else if template == "evidence-summary" && spec.key != "research-question" {
			prefix = "以下仅汇总可定位的文献证据：\n"
		}
		sections = append(sections, map[string]any{"key": spec.key, "title": spec.title, "content": prefix + strings.Join(contentParts, "\n\n"), "citations": citations})
	}
	return sections
}
