package main

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func useTestSQLite(t *testing.T) {
	t.Helper()
	t.Setenv("AIME_PLUGIN_DATA_DIR", t.TempDir())
	st, err := newSQLiteStore()
	if err != nil {
		t.Fatal(err)
	}
	old := store
	store = st
	t.Cleanup(func() { store = old; _ = st.db.Close() })
}

func decodeResponse(t *testing.T, recorder *httptest.ResponseRecorder) map[string]any {
	t.Helper()
	var result map[string]any
	if err := json.Unmarshal(recorder.Body.Bytes(), &result); err != nil {
		t.Fatalf("invalid JSON response: %v", err)
	}
	return result
}

func setupMockAI(t *testing.T) *httptest.Server {
	t.Helper()
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != "Bearer test-key" {
			w.WriteHeader(http.StatusUnauthorized)
			_, _ = w.Write([]byte(`{"error":"missing key"}`))
			return
		}
		var body map[string]any
		_ = json.NewDecoder(r.Body).Decode(&body)
		messages, _ := body["messages"].([]any)
		prompt := ""
		if len(messages) > 0 {
			if last, ok := messages[len(messages)-1].(map[string]any); ok {
				prompt = mapString(last, "content")
			}
		}
		content := "这是基于模拟 AI 的中文回答 [1]。"
		if strings.Contains(prompt, "abstract") || strings.Contains(prompt, "字段必须是") {
			content = `{"abstract":"AI 摘要：研究检索增强问答。","background":"AI 背景：已有方法存在证据定位不足。","methods":"AI 方法：使用两阶段检索和重排序。","results":"AI 结果：准确率提升。","discussion":"AI 讨论：仍受数据规模限制。"}`
		} else if strings.Contains(prompt, "sections") {
			content = `{"sections":[{"key":"research-question","title":"研究问题","content":"AI 报告：论文讨论检索增强问答的核心问题。"},{"key":"background","title":"研究背景","content":"AI 报告：背景强调可靠证据定位。"},{"key":"methods","title":"研究方法","content":"AI 报告：方法采用检索和重排序。"}]}`
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"choices": []map[string]any{{"message": map[string]any{"content": content}}}})
	}))
	_, err := store.Create(contextWithTODO(), settingsCollection, map[string]any{"key": "ai", "provider": "openai-compatible", "baseUrl": server.URL, "model": "test-model", "apiKey": "test-key"})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(server.Close)
	return server
}

func contextWithTODO() context.Context { return context.Background() }

func createTestPaper(t *testing.T) map[string]any {
	t.Helper()
	payload := `{"title":"检索增强实验","authors":["研究者"],"year":2026,"sourceFileName":"paper.pdf","pageCount":1,"fullText":"摘要\n本文研究检索增强问答。\n方法\n我们使用两阶段检索和重排序算法。\n结果\n准确率提升百分之十。\n讨论\n该实验受数据规模限制。","pages":[{"pageNumber":1,"text":"摘要\n本文研究检索增强问答。\n方法\n我们使用两阶段检索和重排序算法。\n结果\n准确率提升百分之十。\n讨论\n该实验受数据规模限制。"}]}`
	req := httptest.NewRequest("POST", "/api/papers", strings.NewReader(payload))
	rec := httptest.NewRecorder()
	papersCreate(rec, req)
	if rec.Code != 201 {
		t.Fatalf("create paper status=%d body=%s", rec.Code, rec.Body.String())
	}
	return decodeResponse(t, rec)["data"].(map[string]any)
}

func TestPaperCreateStructuresAndLocatesPages(t *testing.T) {
	useTestSQLite(t)
	setupMockAI(t)
	paper := createTestPaper(t)
	if paper["processingStatus"] != "ready" || paper["methods"] == "" || paper["results"] == "" {
		t.Fatalf("paper was not structured: %#v", paper)
	}
	id := paper["id"].(string)
	req := httptest.NewRequest("GET", "/api/papers/"+id, nil)
	req.SetPathValue("paperId", id)
	rec := httptest.NewRecorder()
	papersByPaperIdGet(rec, req)
	if rec.Code != 200 {
		t.Fatalf("get status=%d", rec.Code)
	}
	detail := decodeResponse(t, rec)["data"].(map[string]any)
	pages := detail["pages"].([]any)
	page := pages[0].(map[string]any)
	if page["startOffset"].(float64) != 0 || page["endOffset"].(float64) <= 0 {
		t.Fatalf("missing page offsets: %#v", page)
	}
}

func TestAnnotationQAAndReportFlow(t *testing.T) {
	useTestSQLite(t)
	setupMockAI(t)
	paper := createTestPaper(t)
	id := paper["id"].(string)
	annotationBody := `{"paperId":"` + id + `","content":"关注重排序设计","pageNumber":1,"section":"方法","quote":"我们使用两阶段检索和重排序算法。","startOffset":20,"endOffset":38}`
	req := httptest.NewRequest("POST", "/api/annotations", strings.NewReader(annotationBody))
	rec := httptest.NewRecorder()
	annotationsCreate(rec, req)
	if rec.Code != 201 {
		t.Fatalf("annotation status=%d body=%s", rec.Code, rec.Body.String())
	}
	qaBody := `{"question":"采用了什么检索方法？","paperIds":["` + id + `"],"includeAnnotations":true}`
	req = httptest.NewRequest("POST", "/api/qa/ask", strings.NewReader(qaBody))
	rec = httptest.NewRecorder()
	qaAskCreate(rec, req)
	if rec.Code != 201 {
		t.Fatalf("qa status=%d body=%s", rec.Code, rec.Body.String())
	}
	qa := decodeResponse(t, rec)["data"].(map[string]any)
	if len(qa["citations"].([]any)) == 0 {
		t.Fatalf("qa has no citations: %#v", qa)
	}
	reportBody := `{"title":"检索研究报告","template":"systematic-review","paperIds":["` + id + `"],"researchQuestion":"检索方法效果如何？"}`
	req = httptest.NewRequest("POST", "/api/reports", strings.NewReader(reportBody))
	rec = httptest.NewRecorder()
	reportsCreate(rec, req)
	if rec.Code != 201 {
		t.Fatalf("report status=%d body=%s", rec.Code, rec.Body.String())
	}
	report := decodeResponse(t, rec)["data"].(map[string]any)
	if len(report["sections"].([]any)) < 3 {
		t.Fatalf("unexpected report sections: %#v", report["sections"])
	}
	reportID := report["id"].(string)
	req = httptest.NewRequest("POST", "/api/reports/"+reportID+"/export", nil)
	req.SetPathValue("reportId", reportID)
	rec = httptest.NewRecorder()
	reportsByReportIdExportCreate(rec, req)
	if rec.Code != 200 {
		t.Fatalf("export status=%d body=%s", rec.Code, rec.Body.String())
	}
	export := decodeResponse(t, rec)["data"].(map[string]any)
	raw, err := base64.StdEncoding.DecodeString(export["contentBase64"].(string))
	if err != nil || len(raw) < 4 || string(raw[:2]) != "PK" {
		t.Fatalf("invalid DOCX payload")
	}
}

func TestQANoMatchDoesNotInventCitation(t *testing.T) {
	useTestSQLite(t)
	setupMockAI(t)
	paper := createTestPaper(t)
	id := paper["id"].(string)
	body := `{"question":"量子引力黑洞熵弦理论？","paperIds":["` + id + `"]}`
	req := httptest.NewRequest("POST", "/api/qa/ask", strings.NewReader(body))
	rec := httptest.NewRecorder()
	qaAskCreate(rec, req)
	if rec.Code != 201 {
		t.Fatalf("status=%d", rec.Code)
	}
	data := decodeResponse(t, rec)["data"].(map[string]any)
	if len(data["citations"].([]any)) != 0 || !strings.Contains(data["answer"].(string), "未在所选文献中找到") {
		t.Fatalf("unexpected no-hit answer: %#v", data)
	}
}
