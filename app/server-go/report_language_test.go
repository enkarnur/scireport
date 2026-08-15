package main

import (
	"net/http/httptest"
	"strings"
	"testing"
)

func TestChineseReportLanguageWrapsEnglishEvidenceInChinese(t *testing.T) {
	useTestSQLite(t)
	payload := `{"title":"Retrieval Augmented Literature QA","authors":["Researcher"],"year":2026,"sourceFileName":"english.pdf","pageCount":1,"fullText":"Abstract\nThis paper studies retrieval augmented question answering.\nMethods\nWe use two-stage retrieval and reranking.\nResults\nAccuracy improves by ten percent.\nDiscussion\nThe experiment is limited by data scale.","pages":[{"pageNumber":1,"text":"Abstract\nThis paper studies retrieval augmented question answering.\nMethods\nWe use two-stage retrieval and reranking.\nResults\nAccuracy improves by ten percent.\nDiscussion\nThe experiment is limited by data scale."}]}`
	req := httptest.NewRequest("POST", "/api/papers", strings.NewReader(payload))
	rec := httptest.NewRecorder()
	papersCreate(rec, req)
	if rec.Code != 201 {
		t.Fatalf("create paper status=%d body=%s", rec.Code, rec.Body.String())
	}
	paper := decodeResponse(t, rec)["data"].(map[string]any)
	id := paper["id"].(string)

	reportBody := `{"title":"中文系统报告","template":"systematic-review","paperIds":["` + id + `"],"researchQuestion":"检索增强问答如何提升效果？","language":"zh-CN"}`
	req = httptest.NewRequest("POST", "/api/reports", strings.NewReader(reportBody))
	rec = httptest.NewRecorder()
	reportsCreate(rec, req)
	if rec.Code != 201 {
		t.Fatalf("report status=%d body=%s", rec.Code, rec.Body.String())
	}
	report := decodeResponse(t, rec)["data"].(map[string]any)
	if report["language"] != "zh-CN" {
		t.Fatalf("language was not normalized to zh-CN: %#v", report["language"])
	}
	sections := report["sections"].([]any)
	first := sections[0].(map[string]any)
	if first["title"] != "研究问题" || !strings.Contains(first["content"].(string), "不再重复问题本身") || !strings.Contains(first["content"].(string), "主要包括") {
		t.Fatalf("research question section is not an actual Chinese answer: %#v", first)
	}
	methodSection := sections[2].(map[string]any)
	content := methodSection["content"].(string)
	if methodSection["title"] != "研究方法" || !strings.Contains(content, "方法部分重点说明") || strings.Contains(content, "We use two-stage retrieval") {
		t.Fatalf("method section is not Chinese-synthesized: %#v", methodSection)
	}
}
