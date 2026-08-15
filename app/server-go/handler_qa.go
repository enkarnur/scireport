package main

import (
	"net/http"
	"sort"
)

func qaAskCreate(w http.ResponseWriter, r *http.Request) {
	body, err := decodeObject(r)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	question, err := requiredString(body, "question", "question")
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	if len([]rune(question)) > 1000 {
		badRequest(w, "question 不能超过 1000 个字符")
		return
	}
	paperIDs, err := stringArray(body, "paperIds", false)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	includeAnnotations, err := boolField(body, "includeAnnotations", true)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	all, err := store.GetAll(r.Context(), papersCollection)
	if err != nil {
		internalError(w)
		return
	}
	selected := map[string]bool{}
	for _, id := range paperIDs {
		selected[id] = true
	}
	papers := []map[string]any{}
	found := map[string]bool{}
	for _, paper := range all {
		id := mapString(paper, "id")
		if len(selected) > 0 && !selected[id] {
			continue
		}
		found[id] = true
		if mapString(paper, "processingStatus") == "ready" {
			papers = append(papers, paper)
		}
	}
	for _, id := range paperIDs {
		if !found[id] {
			badRequest(w, "论文不存在："+id)
			return
		}
	}
	evidences := []evidence{}
	for _, paper := range papers {
		evidences = append(evidences, pageEvidence(paper, question)...)
	}
	if includeAnnotations {
		annotations, _ := store.GetAll(r.Context(), annotationsCollection)
		paperMap := map[string]map[string]any{}
		for _, p := range papers {
			paperMap[mapString(p, "id")] = p
		}
		for _, a := range annotations {
			p := paperMap[mapString(a, "paperId")]
			if p == nil {
				continue
			}
			text := mapString(a, "content") + " " + mapString(a, "quote")
			score := relevance(question, text)
			if score < .12 {
				continue
			}
			quote := mapString(a, "quote")
			if quote == "" {
				quote = mapString(a, "content")
			}
			evidences = append(evidences, evidence{mapString(p, "id"), mapString(p, "title"), mapString(a, "section"), compactText(quote, 240), mapInt(a, "pageNumber"), mapInt(a, "startOffset"), mapInt(a, "endOffset"), score * .9})
		}
	}
	sort.SliceStable(evidences, func(i, j int) bool { return evidences[i].Score > evidences[j].Score })
	if len(evidences) > 8 {
		evidences = evidences[:8]
	}
	hitScores := map[string]float64{}
	titles := map[string]string{}
	for _, e := range evidences {
		if e.Score > hitScores[e.PaperID] {
			hitScores[e.PaperID] = e.Score
		}
		titles[e.PaperID] = e.PaperTitle
	}
	hits := []map[string]any{}
	for id, score := range hitScores {
		hits = append(hits, map[string]any{"paperId": id, "paperTitle": titles[id], "score": mathRound(score, 3)})
	}
	sort.SliceStable(hits, func(i, j int) bool { return hits[i]["score"].(float64) > hits[j]["score"].(float64) })
	citations := []map[string]any{}
	for _, e := range evidences {
		citations = append(citations, evidenceMap(e))
	}
	answer := "未在所选文献中找到与问题足够相关的原文证据。请调整问题关键词或扩大论文范围。"
	if len(evidences) > 0 {
		cfg, err := requireAISettings(r.Context())
		if err != nil {
			badRequest(w, err.Error())
			return
		}
		answer, err = aiAnswerQuestion(r.Context(), cfg, question, evidences)
		if err != nil {
			writeJSON(w, http.StatusBadGateway, map[string]any{"error": "AI 问答失败：" + err.Error()})
			return
		}
	}
	scopeIDs := paperIDs
	if len(scopeIDs) == 0 {
		for _, p := range papers {
			scopeIDs = append(scopeIDs, mapString(p, "id"))
		}
	}
	record := map[string]any{"question": question, "answer": answer, "scope": map[string]any{"paperIds": scopeIDs, "includeAnnotations": includeAnnotations}, "paperIds": scopeIDs, "hits": hits, "citations": citations}
	created, err := store.Create(r.Context(), qaCollection, record)
	if err != nil {
		internalError(w)
		return
	}
	writeJSON(w, http.StatusCreated, map[string]any{"data": created})
}

func mathRound(value float64, places int) float64 {
	factor := 1.0
	for i := 0; i < places; i++ {
		factor *= 10
	}
	return float64(int(value*factor+.5)) / factor
}
