package main

import (
	"net/http/httptest"
	"strings"
	"testing"
)

func TestPaperCreateRequiresUserAIKey(t *testing.T) {
	useTestSQLite(t)
	payload := `{"title":"No Key Paper","authors":["A"],"year":2026,"sourceFileName":"paper.pdf","pageCount":1,"fullText":"Abstract\nThis paper studies AI.","pages":[{"pageNumber":1,"text":"Abstract\nThis paper studies AI."}]}`
	req := httptest.NewRequest("POST", "/api/papers", strings.NewReader(payload))
	rec := httptest.NewRecorder()
	papersCreate(rec, req)
	if rec.Code != 400 || !strings.Contains(rec.Body.String(), "AI API Key") {
		t.Fatalf("expected missing AI key error, status=%d body=%s", rec.Code, rec.Body.String())
	}
}

func TestAISettingsNeverReturnsPlainKey(t *testing.T) {
	useTestSQLite(t)
	body := `{"provider":"openai-compatible","baseUrl":"https://api.example.com/v1","model":"demo-model","apiKey":"sk-test-secret-value"}`
	req := httptest.NewRequest("PUT", "/api/settings/ai", strings.NewReader(body))
	rec := httptest.NewRecorder()
	settingsAiUpdate(rec, req)
	if rec.Code != 200 {
		t.Fatalf("settings update failed: %d %s", rec.Code, rec.Body.String())
	}
	if strings.Contains(rec.Body.String(), "sk-test-secret-value") || !strings.Contains(rec.Body.String(), "sk-t…alue") {
		t.Fatalf("settings response leaked or failed to mask key: %s", rec.Body.String())
	}
	req = httptest.NewRequest("GET", "/api/settings/ai", nil)
	rec = httptest.NewRecorder()
	settingsAiList(rec, req)
	if strings.Contains(rec.Body.String(), "sk-test-secret-value") {
		t.Fatalf("settings list leaked key: %s", rec.Body.String())
	}
}
