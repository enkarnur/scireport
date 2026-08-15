package main

import (
	"fmt"
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
	language = normalizeReportLanguage(language)
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
	cfg, err := requireAISettings(r.Context())
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	sections, err := aiGenerateReportSections(r.Context(), cfg, template, question, language, papers, annotations)
	if err != nil {
		writeJSON(w, http.StatusBadGateway, map[string]any{"error": "AI 报告生成失败：" + err.Error()})
		return
	}
	enrichReportCitations(sections, template, question, language, papers, annotations)
	record := map[string]any{"title": title, "template": template, "status": "ready", "error": "", "paperIds": paperIDs, "paperCount": len(paperIDs), "researchQuestion": question, "language": language, "sections": sections, "analysisProvider": cfg.Provider, "analysisModel": cfg.Model}
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

func normalizeReportLanguage(language string) string {
	language = strings.ToLower(strings.TrimSpace(language))
	if language == "" || strings.HasPrefix(language, "zh") || strings.Contains(language, "中文") || strings.Contains(language, "chinese") {
		return "zh-CN"
	}
	return "en"
}

func isChineseReport(language string) bool {
	return strings.HasPrefix(strings.ToLower(strings.TrimSpace(language)), "zh")
}

func reportSectionSpecs(language string) []reportSectionSpec {
	if isChineseReport(language) {
		return []reportSectionSpec{{"research-question", "研究问题", "", "研究问题"}, {"background", "研究背景", "background", "研究背景"}, {"methods", "研究方法", "methods", "研究方法"}, {"results", "研究结果", "results", "研究结果"}, {"limitations", "局限与风险", "discussion", "局限与讨论"}, {"contributions", "主要贡献", "results", "贡献证据"}, {"reproducibility", "可复现性", "methods", "复现信息"}, {"discussion", "综合讨论", "discussion", "讨论"}, {"annotations", "研究批注", "", "批注"}}
	}
	return []reportSectionSpec{{"research-question", "Research Question", "", "research question"}, {"background", "Background", "background", "background"}, {"methods", "Methods", "methods", "methods"}, {"results", "Results", "results", "results"}, {"limitations", "Limitations and Risks", "discussion", "limitations and discussion"}, {"contributions", "Key Contributions", "results", "contribution evidence"}, {"reproducibility", "Reproducibility", "methods", "reproducibility information"}, {"discussion", "Synthesis and Discussion", "discussion", "discussion"}, {"annotations", "Research Annotations", "", "annotations"}}
}

func generateReportSections(template, question, language string, papers []map[string]any, annotations []map[string]any) []any {
	specs := reportSectionSpecs(language)
	zh := isChineseReport(language)
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
			contentParts = append(contentParts, reportResearchQuestionAnswer(question, papers, zh))
		case "annotations":
			for _, a := range annotations {
				if !paperSet[mapString(a, "paperId")] {
					continue
				}
				for _, p := range papers {
					if mapString(p, "id") == mapString(a, "paperId") {
						if zh {
							contentParts = append(contentParts, fmt.Sprintf("《%s》的相关批注：%s", mapString(p, "title"), mapString(a, "content")))
						} else {
							contentParts = append(contentParts, fmt.Sprintf("Annotation on %s: %s", mapString(p, "title"), mapString(a, "content")))
						}
						citations = append(citations, map[string]any{"paperId": mapString(p, "id"), "paperTitle": mapString(p, "title"), "pageNumber": mapInt(a, "pageNumber"), "section": mapString(a, "section"), "quote": mapString(a, "quote"), "startOffset": mapInt(a, "startOffset"), "endOffset": mapInt(a, "endOffset")})
						break
					}
				}
			}
			if len(contentParts) == 0 {
				if zh {
					contentParts = append(contentParts, "所选论文暂无批注。")
				} else {
					contentParts = append(contentParts, "No annotations are available for the selected papers.")
				}
			}
		default:
			for _, p := range papers {
				text := mapString(p, spec.field)
				if text == "" {
					if zh {
						contentParts = append(contentParts, "《"+mapString(p, "title")+"》未识别到可用于“"+spec.title+"”的明确原文。")
					} else {
						contentParts = append(contentParts, mapString(p, "title")+" does not contain clearly identifiable source text for "+spec.title+".")
					}
					continue
				}
				contentParts = append(contentParts, reportEvidenceParagraph(p, spec, text, zh))
				ev := pageEvidence(p, text)
				if len(ev) > 0 {
					citations = append(citations, evidenceMap(ev[0]))
				}
			}
			if spec.key == "reproducibility" {
				if zh {
					contentParts = append(contentParts, "复现时应以原文中明确给出的数据、方法和实验设置为准；未被结构化文本提及的参数不作推断。")
				} else {
					contentParts = append(contentParts, "Reproduction should rely only on data, methods, and experimental settings explicitly stated in the source text; parameters not found in structured text are not inferred.")
				}
			}
		}
		prefix := reportTemplatePrefix(template, spec.key, zh)
		sections = append(sections, map[string]any{"key": spec.key, "title": spec.title, "content": prefix + strings.Join(contentParts, "\n\n"), "citations": citations})
	}
	return sections
}

func enrichReportCitations(sections []any, template, question, language string, papers []map[string]any, annotations []map[string]any) {
	fallback := generateReportSections(template, question, language, papers, annotations)
	fallbackByKey := map[string][]map[string]any{}
	for _, raw := range fallback {
		section, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		citations := []map[string]any{}
		if arr, ok := section["citations"].([]map[string]any); ok {
			citations = arr
		} else if arr, ok := section["citations"].([]any); ok {
			for _, item := range arr {
				if m, yes := item.(map[string]any); yes {
					citations = append(citations, m)
				}
			}
		}
		fallbackByKey[mapString(section, "key")] = citations
	}
	for _, raw := range sections {
		section, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		if _, exists := section["citations"]; !exists {
			section["citations"] = fallbackByKey[mapString(section, "key")]
		}
	}
}

func reportResearchQuestionAnswer(question string, papers []map[string]any, zh bool) string {
	issues := inferDiscussedIssues(papers, zh)
	if zh {
		intro := "本报告围绕所选论文提炼其核心讨论问题。"
		if strings.TrimSpace(question) != "" {
			intro = "针对问题“" + strings.TrimSpace(question) + "”，本报告不再重复问题本身，而是概括论文实际讨论的核心议题。"
		}
		if len(issues) == 0 {
			return intro + "目前只能确认论文围绕研究动机、方法设计、实验结果和局限展开；更细的结论请结合各章节引用核验。"
		}
		lines := []string{intro, "主要包括："}
		for i, issue := range issues {
			lines = append(lines, fmt.Sprintf("%d. %s。", i+1, issue))
		}
		return strings.Join(lines, "\n")
	}
	intro := "This report summarizes the core issues discussed by the selected papers."
	if strings.TrimSpace(question) != "" {
		intro = "For the question \"" + strings.TrimSpace(question) + "\", this report answers by summarizing the issues actually discussed in the papers."
	}
	if len(issues) == 0 {
		return intro + " The available structured text covers motivation, methods, results, and limitations; detailed claims should be checked against the cited sections."
	}
	lines := []string{intro, "Main issues:"}
	for i, issue := range issues {
		lines = append(lines, fmt.Sprintf("%d. %s.", i+1, issue))
	}
	return strings.Join(lines, "\n")
}

func inferDiscussedIssues(papers []map[string]any, zh bool) []string {
	seen := map[string]bool{}
	issues := []string{}
	add := func(zhText, enText string) {
		text := zhText
		if !zh {
			text = enText
		}
		if text != "" && !seen[text] {
			seen[text] = true
			issues = append(issues, text)
		}
	}
	for _, p := range papers {
		all := strings.ToLower(strings.Join([]string{mapString(p, "title"), mapString(p, "abstract"), mapString(p, "background"), mapString(p, "methods"), mapString(p, "results"), mapString(p, "discussion")}, " "))
		if strings.Contains(all, "medical") || strings.Contains(all, "clinician") || strings.Contains(all, "clinical") || strings.Contains(all, "patient") || strings.Contains(all, "医疗") || strings.Contains(all, "临床") || strings.Contains(all, "患者") {
			add("医疗 AI 如何在真实临床问诊中达到接近专家医生的表现", "how medical AI can approach expert clinician performance in real consultation settings")
		}
		if strings.Contains(all, "video") || strings.Contains(all, "audio-visual") || strings.Contains(all, "real-time") || strings.Contains(all, "consultation") || strings.Contains(all, "视频") || strings.Contains(all, "实时") || strings.Contains(all, "问诊") {
			add("实时视频问诊中的多模态交互、信息获取和沟通质量", "multimodal interaction, information gathering, and communication quality in real-time video consultations")
		}
		if strings.Contains(all, "amie") || strings.Contains(all, "gemini") || strings.Contains(all, "model") || strings.Contains(all, "模型") {
			add("模型系统的配置、能力边界以及与专家基准的差距", "model configuration, capability boundaries, and gaps against expert baselines")
		}
		if strings.Contains(all, "evaluation") || strings.Contains(all, "performance") || strings.Contains(all, "benchmark") || strings.Contains(all, "accuracy") || strings.Contains(all, "评估") || strings.Contains(all, "性能") || strings.Contains(all, "准确") {
			add("如何设计评估标准并证明系统表现是否可靠", "how to design evaluation criteria and demonstrate whether system performance is reliable")
		}
		if strings.Contains(all, "safety") || strings.Contains(all, "risk") || strings.Contains(all, "limitation") || strings.Contains(all, "bias") || strings.Contains(all, "安全") || strings.Contains(all, "风险") || strings.Contains(all, "局限") || strings.Contains(all, "偏差") {
			add("安全性、偏差、局限性和临床落地风险", "safety, bias, limitations, and deployment risks")
		}
		if len(issues) == 0 {
			if title := mapString(p, "title"); title != "" {
				add("论文《"+title+"》所界定的研究问题、方法路径和证据结论", "the research problem, method, and evidence claims defined by "+title)
			}
		}
		if len(issues) >= 6 {
			break
		}
	}
	return issues
}

func reportEvidenceParagraph(p map[string]any, spec reportSectionSpec, text string, zh bool) string {
	if zh {
		return fmt.Sprintf("《%s》的%s表明：%s。相关原文已保留在本节引用中，便于回到 PDF 页码核验。", mapString(p, "title"), spec.stringLabel, chineseFieldInsight(p, spec.key, text))
	}
	return fmt.Sprintf("%s provides locatable evidence for %s: \"%s\"", mapString(p, "title"), spec.stringLabel, compactText(text, 700))
}

func chineseFieldInsight(p map[string]any, key, text string) string {
	issues := inferDiscussedIssues([]map[string]any{p}, true)
	topic := "论文主题"
	if len(issues) > 0 {
		topic = issues[0]
	}
	switch key {
	case "background":
		return "研究背景主要解释为什么需要关注“" + topic + "”，并指出既有工作仍存在能力、场景或可靠性上的不足"
	case "methods":
		return "方法部分重点说明作者为解决上述问题设计了系统、数据流程、评估方案或实验配置"
	case "results":
		return "结果部分主要回答该方案在目标任务中是否有效，以及相较基线或专家表现有哪些变化"
	case "limitations", "discussion":
		return "讨论部分进一步说明该研究的适用边界、潜在风险、未解决问题和后续改进方向"
	case "contributions":
		return "主要贡献集中在提出新的系统能力、验证路径或实证证据，并服务于“" + topic + "”这一核心问题"
	case "reproducibility":
		return "可复现信息主要来自方法和实验设置，复现时应优先核对数据来源、模型配置、评价指标和实验条件"
	default:
		return "该部分围绕“" + topic + "”展开，具体证据见引用"
	}
}

func reportTemplatePrefix(template, sectionKey string, zh bool) string {
	if sectionKey == "research-question" {
		return ""
	}
	if zh {
		if template == "comparison" {
			return "以下按论文逐项对照：\n"
		}
		if template == "evidence-summary" {
			return "以下仅汇总可定位的文献证据：\n"
		}
		return ""
	}
	if template == "comparison" {
		return "The following compares the selected papers item by item:\n"
	}
	if template == "evidence-summary" {
		return "The following summarizes only locatable evidence from the papers:\n"
	}
	return ""
}
