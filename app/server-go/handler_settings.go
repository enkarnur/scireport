package main

import (
	"net/http"
	"strings"
	"time"
)

func settingsAiList(w http.ResponseWriter, r *http.Request) {
	cfg, err := loadAISettings(r.Context())
	if err != nil {
		internalError(w)
		return
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": publicAISettings(cfg)})
}

func settingsAiUpdate(w http.ResponseWriter, r *http.Request) {
	body, err := decodeObject(r)
	if err != nil {
		badRequest(w, err.Error())
		return
	}
	cfg, err := loadAISettings(r.Context())
	if err != nil {
		internalError(w)
		return
	}
	if v := strings.TrimSpace(mapString(body, "provider")); v != "" {
		cfg.Provider = v
	}
	if v := strings.TrimSpace(mapString(body, "baseUrl")); v != "" {
		if !strings.HasPrefix(v, "https://") && !strings.HasPrefix(v, "http://") {
			badRequest(w, "baseUrl 必须是 http(s) URL")
			return
		}
		cfg.BaseURL = strings.TrimRight(v, "/")
	}
	if v := strings.TrimSpace(mapString(body, "model")); v != "" {
		cfg.Model = v
	}
	clear, _ := boolField(body, "clearApiKey", false)
	if clear {
		cfg.APIKey = ""
	} else if _, ok := body["apiKey"]; ok {
		if v := strings.TrimSpace(mapString(body, "apiKey")); v != "" {
			cfg.APIKey = v
		}
	}
	if strings.TrimSpace(cfg.BaseURL) == "" || strings.TrimSpace(cfg.Model) == "" {
		badRequest(w, "baseUrl 和 model 必填")
		return
	}
	cfg.UpdatedAt = time.Now().UTC().Format(time.RFC3339)
	record := map[string]any{"key": "ai", "provider": cfg.Provider, "baseUrl": cfg.BaseURL, "model": cfg.Model, "apiKey": cfg.APIKey, "updatedAt": cfg.UpdatedAt}
	existing, err := findAISettings(r.Context())
	if err != nil {
		internalError(w)
		return
	}
	if existing == nil {
		if _, err = store.Create(r.Context(), settingsCollection, record); err != nil {
			internalError(w)
			return
		}
	} else {
		if _, err = store.Update(r.Context(), settingsCollection, mapString(existing, "id"), record); err != nil {
			internalError(w)
			return
		}
	}
	writeJSON(w, http.StatusOK, map[string]any{"data": publicAISettings(cfg)})
}
