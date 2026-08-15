package main

import (
	"bytes"
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/google/uuid"
)

type cloudStore struct {
	baseURL    string
	appID      string
	apiKey     string
	instanceID string
}

const cloudDBAPIPrefix = "/api/v2"

func newCloudStore() (*cloudStore, error) {
	appID := strings.TrimSpace(os.Getenv("DB_APP_ID"))
	apiKey := strings.TrimSpace(os.Getenv("DB_API_KEY"))
	baseURL := strings.TrimSpace(os.Getenv("DB_BASE_URL"))
	if baseURL == "" {
		if os.Getenv("IRIS_RUNTIME_AIME_API_HOST") == "aime.byted.org" {
			baseURL = "https://elfzl04s.sg-fn.bytedance.net"
		} else {
			baseURL = "https://ju82g6bb.fn.bytedance.net"
		}
	}
	if appID == "" || apiKey == "" {
		return nil, errors.New("cloud db credentials missing")
	}
	st := &cloudStore{
		baseURL:    strings.TrimRight(baseURL, "/"),
		appID:      appID,
		apiKey:     apiKey,
		instanceID: appInstanceID,
	}
	logMsg(fmt.Sprintf("[store] 使用云端 DB (DB_APP_ID=%s...)", appID[:min(8, len(appID))]), "plugin")
	return st, nil
}

func (s *cloudStore) Mode() string { return "cloud" }

func (s *cloudStore) headers() http.Header {
	h := make(http.Header)
	h.Set("Content-Type", "application/json")
	h.Set("X-App-Id", s.appID)
	h.Set("X-Api-Key", s.apiKey)
	if s.instanceID != "" {
		h.Set("X-App-Instance-Id", s.instanceID)
	}
	return h
}

func (s *cloudStore) doJSON(ctx context.Context, method string, path string, body any) (map[string]any, error) {
	var reqBody io.Reader
	if body != nil {
		payload, err := json.Marshal(body)
		if err != nil {
			return nil, err
		}
		reqBody = bytes.NewReader(payload)
	}
	request, err := http.NewRequestWithContext(ctx, method, s.baseURL+path, reqBody)
	if err != nil {
		return nil, err
	}
	request.Header = s.headers()
	resp, err := httpClient.Do(request)
	if err != nil {
		return nil, err
	}
	data, err := decodeHTTPBody(resp)
	if err != nil {
		return nil, err
	}
	var parsed map[string]any
	if len(data) > 0 {
		if err := json.Unmarshal(data, &parsed); err != nil {
			return nil, err
		}
	} else {
		parsed = map[string]any{}
	}
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("db status=%d body=%s", resp.StatusCode, string(data))
	}
	if code, ok := parsed["code"].(float64); ok && int(code) != 0 && int(code) != 200 {
		return nil, fmt.Errorf("db code=%d body=%s", int(code), string(data))
	}
	return parsed, nil
}

func (s *cloudStore) GetAll(ctx context.Context, collection string) ([]map[string]any, error) {
	query := map[string]any{"limit": 100, "offset": 0, "filters": []any{}, "sort": []any{}}
	resp, err := s.doJSON(ctx, http.MethodPost, cloudDBAPIPrefix+"/tables/"+collection+"/query", query)
	if err != nil {
		return nil, err
	}
	data, _ := resp["data"].(map[string]any)
	records, _ := data["records"].([]any)
	items := make([]map[string]any, 0, len(records))
	for _, record := range records {
		if m, ok := toMap(record); ok {
			items = append(items, s.decodeRecord(m))
		}
	}
	return items, nil
}

func (s *cloudStore) GetByID(ctx context.Context, collection string, id string) (map[string]any, error) {
	resp, err := s.doJSON(ctx, http.MethodGet, cloudDBAPIPrefix+"/tables/"+collection+"/records/"+id, nil)
	if err != nil {
		if strings.Contains(err.Error(), "404") {
			return nil, nil
		}
		return nil, err
	}
	if m, ok := toMap(resp["data"]); ok {
		return s.decodeRecord(m), nil
	}
	return nil, nil
}

func (s *cloudStore) Create(ctx context.Context, collection string, data map[string]any) (map[string]any, error) {
	now := time.Now().Format(time.RFC3339)
	if data["id"] == nil || asString(data["id"]) == "" {
		data["id"] = uuid.NewString()
	}
	if data["createdAt"] == nil {
		data["createdAt"] = now
	}
	if data["updatedAt"] == nil {
		data["updatedAt"] = now
	}
	requestData := map[string]any{"data": data}
	resp, err := s.doJSON(ctx, http.MethodPost, cloudDBAPIPrefix+"/tables/"+collection+"/records", requestData)
	if err != nil {
		return nil, err
	}
	if m, ok := toMap(resp["data"]); ok {
		return s.decodeRecord(m), nil
	}
	return data, nil
}

func (s *cloudStore) Update(ctx context.Context, collection string, id string, data map[string]any) (map[string]any, error) {
	existing, err := s.GetByID(ctx, collection, id)
	if err != nil {
		return nil, err
	}
	if existing == nil {
		return nil, sql.ErrNoRows
	}
	data["id"] = id
	if data["createdAt"] == nil {
		data["createdAt"] = existing["createdAt"]
	}
	data["updatedAt"] = time.Now().Format(time.RFC3339)
	requestData := map[string]any{"data": data}
	resp, err := s.doJSON(ctx, http.MethodPut, cloudDBAPIPrefix+"/tables/"+collection+"/records/"+id, requestData)
	if err != nil {
		if strings.Contains(err.Error(), "404") {
			return nil, sql.ErrNoRows
		}
		return nil, err
	}
	if m, ok := toMap(resp["data"]); ok {
		return s.decodeRecord(m), nil
	}
	return data, nil
}

func (s *cloudStore) Delete(ctx context.Context, collection string, id string) error {
	_, err := s.doJSON(ctx, http.MethodDelete, cloudDBAPIPrefix+"/tables/"+collection+"/records/"+id, nil)
	if err != nil && strings.Contains(err.Error(), "404") {
		return sql.ErrNoRows
	}
	return err
}

func (s *cloudStore) decodeRecord(record map[string]any) map[string]any {
	data, ok := toMap(record["data"])
	if !ok {
		data = map[string]any{}
	}
	if recordID := asString(record["_id"]); recordID != "" {
		data["id"] = recordID
		data["_id"] = recordID
	}
	if data["createdAt"] == nil && record["create_time"] != nil {
		data["createdAt"] = record["create_time"]
	}
	if data["updatedAt"] == nil && record["update_time"] != nil {
		data["updatedAt"] = record["update_time"]
	}
	data["create_time"] = record["create_time"]
	data["update_time"] = record["update_time"]
	return data
}

func toMap(v any) (map[string]any, bool) {
	switch val := v.(type) {
	case map[string]any:
		return val, true
	default:
		payload, err := json.Marshal(v)
		if err != nil {
			return nil, false
		}
		var m map[string]any
		if err := json.Unmarshal(payload, &m); err != nil {
			return nil, false
		}
		return m, true
	}
}
