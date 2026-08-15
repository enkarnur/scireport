package main

import (
	"net/http"
	"sort"
	"strings"
	"time"
)

func papersList(w http.ResponseWriter, r *http.Request) {
	limit, offset, err := pagination(r, 20, 100)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	status, q := strings.TrimSpace(r.URL.Query().Get("status")), strings.TrimSpace(r.URL.Query().Get("q"))
	if status != "" && status != "processing" && status != "ready" && status != "failed" {
		badRequest(w, "status 必须是 processing、ready 或 failed")
		return
	}
	items, err := store.GetAll(r.Context(), papersCollection)
	if err != nil {
		internalError(w)
		return
	}
	filtered := make([]map[string]any, 0, len(items))
	for _, item := range items {
		if status != "" && mapString(item, "processingStatus") != status {
			continue
		}
		if q != "" {
			authors := ""
			if values, ok := item["authors"].([]any); ok {
				for _, value := range values {
					authors += " " + asString(value)
				}
			}
			haystack := mapString(item, "title") + " " + authors + " " + mapString(item, "abstract") + " " + mapString(item, "fullText")
			if !containsFold(haystack, q) && relevance(q, haystack) < .12 {
				continue
			}
		}
		filtered = append(filtered, publicPaper(item, false))
	}
	sort.SliceStable(filtered, func(i, j int) bool { return mapString(filtered[i], "createdAt") > mapString(filtered[j], "createdAt") })
	writeJSON(w, http.StatusOK, map[string]any{"data": pageSlice(filtered, offset, limit), "total": len(filtered), "limit": limit, "offset": offset})
}

func papersCreate(w http.ResponseWriter, r *http.Request) {
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
	authors, err := stringArray(body, "authors", true)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	fileName, err := requiredString(body, "sourceFileName", "sourceFileName")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	if fileName != filepathBase(fileName) {
		badRequest(w, "sourceFileName 只能包含文件名，不能包含路径")
		return
	}
	pageCount, err := intField(body, "pageCount", true)
	if err != nil || pageCount < 1 || pageCount > 10000 {
		badRequest(w, "pageCount 必须是 1 到 10000 之间的整数")
		return
	}
	fullText, err := requiredString(body, "fullText", "fullText")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	pages, err := normalizePages(body["pages"], pageCount, fullText)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	year, err := intField(body, "year", false)
	if err != nil || year < 0 || year > time.Now().Year()+2 {
		badRequest(w, "year 必须是合理的年份")
		return
	}
	venue, err := optionalString(body, "venue")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	doi, err := optionalString(body, "doi")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	cfg, err := requireAISettings(r.Context())
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	structured, err := aiAnalyzePaper(r.Context(), cfg, title, fullText)
	if err != nil {
		writeJSON(w, http.StatusBadGateway, map[string]any{"error": "AI 文献解析失败：" + err.Error()})
		return
	}
	_, sections := structurePaper(title, fullText)
	item := map[string]any{"title": title, "authors": authors, "year": year, "venue": venue, "doi": doi, "sourceFileName": fileName, "pageCount": pageCount, "fullText": fullText, "pages": pages, "sections": sections, "abstract": structured["abstract"], "background": structured["background"], "methods": structured["methods"], "results": structured["results"], "discussion": structured["discussion"], "processingStatus": "ready", "processingError": "", "analysisProvider": cfg.Provider, "analysisModel": cfg.Model}
	created, err := store.Create(r.Context(), papersCollection, item)
	if err != nil {
		internalError(w)
		return
	}
	writeJSON(w, http.StatusCreated, map[string]any{"data": publicPaper(created, false)})
}

func papersByPaperIdDelete(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimSpace(r.PathValue("paperId"))
	if id == "" {
		badRequest(w, "paperId 不能为空")
		return
	}
	if err := store.Delete(r.Context(), papersCollection, id); err != nil {
		if isNotFoundError(err) {
			notFound(w, "论文")
		} else {
			internalError(w)
		}
		return
	}
	annotations, err := store.GetAll(r.Context(), annotationsCollection)
	if err != nil {
		internalError(w)
		return
	}
	for _, annotation := range annotations {
		if mapString(annotation, "paperId") == id {
			_ = store.Delete(r.Context(), annotationsCollection, mapString(annotation, "id"))
		}
	}
	writeJSON(w, http.StatusOK, map[string]any{"success": true, "deletedPaperId": id})
}

func papersByPaperIdGet(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimSpace(r.PathValue("paperId"))
	if id == "" {
		badRequest(w, "paperId 不能为空")
		return
	}
	item, err := store.GetByID(r.Context(), papersCollection, id)
	if err != nil {
		internalError(w)
		return
	}
	if item == nil {
		notFound(w, "论文")
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": publicPaper(item, true)})
}

func filepathBase(name string) string {
	name = strings.ReplaceAll(name, "\\", "/")
	parts := strings.Split(name, "/")
	return parts[len(parts)-1]
}
