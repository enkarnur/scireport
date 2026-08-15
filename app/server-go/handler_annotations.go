package main

import (
	"errors"
	"net/http"
	"sort"
	"strconv"
	"strings"
)

func annotationWithTitle(ctxPaper map[string]any, item map[string]any) map[string]any {
	out := map[string]any{}
	for key, value := range item {
		out[key] = value
	}
	if ctxPaper != nil {
		out["paperTitle"] = mapString(ctxPaper, "title")
	}
	return out
}

func annotationsList(w http.ResponseWriter, r *http.Request) {
	limit, offset, err := pagination(r, 50, 200)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	paperID, q := strings.TrimSpace(r.URL.Query().Get("paperId")), strings.TrimSpace(r.URL.Query().Get("q"))
	pageNumber := 0
	if raw := r.URL.Query().Get("pageNumber"); raw != "" {
		pageNumber, err = parsePositiveInt(raw)
		if err != nil {
			badRequest(w, "pageNumber 必须是正整数")
			return
		}
	}
	items, err := store.GetAll(r.Context(), annotationsCollection)
	if err != nil {
		internalError(w)
		return
	}
	papers, err := store.GetAll(r.Context(), papersCollection)
	if err != nil {
		internalError(w)
		return
	}
	titles := map[string]map[string]any{}
	for _, p := range papers {
		titles[mapString(p, "id")] = p
	}
	filtered := []map[string]any{}
	for _, item := range items {
		if paperID != "" && mapString(item, "paperId") != paperID {
			continue
		}
		if pageNumber > 0 && mapInt(item, "pageNumber") != pageNumber {
			continue
		}
		if q != "" && !containsFold(mapString(item, "content")+" "+mapString(item, "section")+" "+mapString(item, "quote"), q) {
			continue
		}
		filtered = append(filtered, annotationWithTitle(titles[mapString(item, "paperId")], item))
	}
	sort.SliceStable(filtered, func(i, j int) bool { return mapString(filtered[i], "createdAt") > mapString(filtered[j], "createdAt") })
	writeJSON(w, http.StatusOK, map[string]any{"data": pageSlice(filtered, offset, limit), "total": len(filtered), "limit": limit, "offset": offset})
}

func annotationsCreate(w http.ResponseWriter, r *http.Request) {
	body, err := decodeObject(r)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	paperID, err := requiredString(body, "paperId", "paperId")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	content, err := requiredString(body, "content", "content")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	paper, err := store.GetByID(r.Context(), papersCollection, paperID)
	if err != nil {
		internalError(w)
		return
	}
	if paper == nil {
		badRequest(w, "关联论文不存在")
		return
	}
	item, err := validatedAnnotation(body, paper, nil)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	item["paperId"], item["content"] = paperID, content
	created, err := store.Create(r.Context(), annotationsCollection, item)
	if err != nil {
		internalError(w)
		return
	}
	writeJSON(w, http.StatusCreated, map[string]any{"data": annotationWithTitle(paper, created)})
}

func annotationsByAnnotationIdDelete(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimSpace(r.PathValue("annotationId"))
	if id == "" {
		badRequest(w, "annotationId 不能为空")
		return
	}
	if err := store.Delete(r.Context(), annotationsCollection, id); err != nil {
		if isNotFoundError(err) {
			notFound(w, "批注")
		} else {
			internalError(w)
		}
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"success": true, "deletedAnnotationId": id})
}

func annotationsByAnnotationIdGet(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimSpace(r.PathValue("annotationId"))
	if id == "" {
		badRequest(w, "annotationId 不能为空")
		return
	}
	item, err := store.GetByID(r.Context(), annotationsCollection, id)
	if err != nil {
		internalError(w)
		return
	}
	if item == nil {
		notFound(w, "批注")
		return
	}
	paper, _ := store.GetByID(r.Context(), papersCollection, mapString(item, "paperId"))
	writeJSON(w, http.StatusOK, map[string]any{"data": annotationWithTitle(paper, item)})
}

func annotationsByAnnotationIdUpdate(w http.ResponseWriter, r *http.Request) {
	id := strings.TrimSpace(r.PathValue("annotationId"))
	if id == "" {
		badRequest(w, "annotationId 不能为空")
		return
	}
	body, err := decodeObject(r)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	if len(body) == 0 {
		badRequest(w, "至少提供一个可更新字段")
		return
	}
	existing, err := store.GetByID(r.Context(), annotationsCollection, id)
	if err != nil {
		internalError(w)
		return
	}
	if existing == nil {
		notFound(w, "批注")
		return
	}
	paper, err := store.GetByID(r.Context(), papersCollection, mapString(existing, "paperId"))
	if err != nil {
		internalError(w)
		return
	}
	if paper == nil {
		badRequest(w, "关联论文不存在")
		return
	}
	allowed := map[string]bool{"content": true, "pageNumber": true, "section": true, "quote": true, "startOffset": true, "endOffset": true, "color": true}
	for key := range body {
		if !allowed[key] {
			badRequest(w, "包含不可更新字段："+key)
			return
		}
	}
	updated, err := validatedAnnotation(body, paper, existing)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	updated["paperId"] = existing["paperId"]
	if value, ok := body["content"]; ok {
		s, yes := value.(string)
		if !yes || strings.TrimSpace(s) == "" {
			badRequest(w, "content 不能为空")
			return
		}
		updated["content"] = strings.TrimSpace(s)
	}
	result, err := store.Update(r.Context(), annotationsCollection, id, updated)
	if err != nil {
		internalError(w)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": annotationWithTitle(paper, result)})
}

func validatedAnnotation(body, paper, existing map[string]any) (map[string]any, error) {
	out := map[string]any{}
	if existing != nil {
		for k, v := range existing {
			out[k] = v
		}
	}
	page, err := intField(body, "pageNumber", existing == nil)
	if err != nil {
		return nil, err
	}
	if _, ok := body["pageNumber"]; ok {
		out["pageNumber"] = page
	} else {
		page = mapInt(out, "pageNumber")
	}
	if page < 1 || page > mapInt(paper, "pageCount") {
		return nil, errors.New("pageNumber 超出论文页码范围")
	}
	for _, key := range []string{"section", "quote", "color"} {
		if _, ok := body[key]; ok {
			s, err := optionalString(body, key)
			if err != nil {
				return nil, err
			}
			out[key] = s
		}
	}
	if mapString(out, "color") == "" {
		out["color"] = "yellow"
	}
	if len([]rune(mapString(out, "quote"))) > 500 {
		return nil, errors.New("quote 不能超过 500 个字符")
	}
	start, err := intField(body, "startOffset", false)
	if err != nil {
		return nil, err
	}
	end, err := intField(body, "endOffset", false)
	if err != nil {
		return nil, err
	}
	if _, ok := body["startOffset"]; ok {
		out["startOffset"] = start
	}
	if _, ok := body["endOffset"]; ok {
		out["endOffset"] = end
	}
	start = mapInt(out, "startOffset")
	end = mapInt(out, "endOffset")
	if start < 0 || end < 0 || end < start || end > len(mapString(paper, "fullText")) {
		return nil, errors.New("字符偏移必须满足 0 <= startOffset <= endOffset <= 全文长度")
	}
	return out, nil
}

func parsePositiveInt(raw string) (int, error) {
	n, err := strconv.Atoi(raw)
	if err != nil || n < 1 {
		return 0, errors.New("invalid")
	}
	return n, nil
}
