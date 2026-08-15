package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
)

func TestNewCloudStoreOnlyLoadsCredentials(t *testing.T) {
	var requests atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		requests.Add(1)
		http.Error(w, "unexpected request", http.StatusInternalServerError)
	}))
	defer server.Close()
	t.Setenv("DB_APP_ID", "db-app-1")
	t.Setenv("DB_API_KEY", "secret")
	t.Setenv("DB_BASE_URL", server.URL+"/")
	oldAppInstanceID := appInstanceID
	appInstanceID = "template-instance"
	t.Cleanup(func() { appInstanceID = oldAppInstanceID })

	store, err := newCloudStore()
	if err != nil {
		t.Fatalf("newCloudStore() error = %v", err)
	}
	if store.baseURL != server.URL {
		t.Fatalf("baseURL = %q, want %q", store.baseURL, server.URL)
	}
	if store.appID != "db-app-1" || store.apiKey != "secret" {
		t.Fatalf("store credentials = appID %q, apiKey %q", store.appID, store.apiKey)
	}
	if store.instanceID != "template-instance" {
		t.Fatalf("store instanceID = %q, want template-instance", store.instanceID)
	}
	if got := requests.Load(); got != 0 {
		t.Fatalf("newCloudStore() sent %d HTTP requests, want 0", got)
	}
}

func TestCloudStoreSendsAppInstanceHeader(t *testing.T) {
	var gotInstanceID string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/v2/tables/items/records" {
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
		gotInstanceID = r.Header.Get("X-App-Instance-Id")
		if got := r.Header.Get("X-App-Id"); got != "db-app-1" {
			t.Fatalf("X-App-Id = %q", got)
		}
		if got := r.Header.Get("X-Api-Key"); got != "secret" {
			t.Fatalf("X-Api-Key = %q", got)
		}
		_ = json.NewEncoder(w).Encode(map[string]any{
			"code": 0,
			"data": map[string]any{
				"_id":         "record-1",
				"create_time": "2026-08-02T00:00:00Z",
				"update_time": "2026-08-02T00:00:00Z",
				"data":        map[string]any{"title": "test"},
			},
		})
	}))
	defer server.Close()

	store := &cloudStore{baseURL: server.URL, appID: "db-app-1", apiKey: "secret", instanceID: "template-instance"}
	if _, err := store.Create(context.Background(), "items", map[string]any{"title": "test"}); err != nil {
		t.Fatalf("Create() error = %v", err)
	}
	if gotInstanceID != "template-instance" {
		t.Fatalf("X-App-Instance-Id = %q, want template-instance", gotInstanceID)
	}
}

func TestCloudStoreUsesV2RoutesAndPayload(t *testing.T) {
	var paths []string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		paths = append(paths, r.URL.Path)
		switch r.URL.Path {
		case "/api/v2/tables/items/records":
			var body map[string]any
			if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
				t.Fatalf("decode request: %v", err)
			}
			if _, ok := body["data"].(map[string]any); !ok {
				t.Fatalf("record body = %#v, want data wrapper", body)
			}
			_ = json.NewEncoder(w).Encode(map[string]any{
				"code": 0,
				"data": map[string]any{
					"_id":         "record-1",
					"create_time": "2026-08-02T00:00:00Z",
					"update_time": "2026-08-02T00:00:00Z",
					"data":        body["data"],
				},
			})
		default:
			t.Fatalf("unexpected path: %s", r.URL.Path)
		}
	}))
	defer server.Close()

	store := &cloudStore{baseURL: server.URL, appID: "db-app-1", apiKey: "secret"}
	record, err := store.Create(context.Background(), "items", map[string]any{"title": "test"})
	if err != nil {
		t.Fatalf("Create() error = %v", err)
	}
	if record["title"] != "test" || record["id"] != "record-1" || record["_id"] != "record-1" {
		t.Fatalf("Create() record = %#v", record)
	}
	for _, path := range paths {
		if !strings.HasPrefix(path, "/api/v2/") {
			t.Fatalf("non-V2 path used: %s", path)
		}
		if path == "/api/v2/tables" {
			t.Fatalf("Create() should not create table on CRUD path, paths=%v", paths)
		}
	}
}

func TestCloudStoreDecodeRecordUsesDatabasePrimaryKeyAsStoreID(t *testing.T) {
	store := &cloudStore{}
	source := map[string]any{
		"_id":         "record-1",
		"create_time": "2026-08-02T00:00:00Z",
		"update_time": "2026-08-02T01:00:00Z",
		"data": map[string]any{
			"id":    "business-id",
			"title": "test",
		},
	}

	record := store.decodeRecord(source)
	if record["id"] != "record-1" || record["_id"] != "record-1" {
		t.Fatalf("decodeRecord() IDs = id %#v, _id %#v", record["id"], record["_id"])
	}
	if record["title"] != "test" {
		t.Fatalf("decodeRecord() = %#v", record)
	}
	if record["createdAt"] != source["create_time"] || record["updatedAt"] != source["update_time"] {
		t.Fatalf("decodeRecord() timestamps = createdAt %#v, updatedAt %#v", record["createdAt"], record["updatedAt"])
	}
}

func TestCloudStoreDecodeRecordPreservesExplicitBusinessTimestamps(t *testing.T) {
	store := &cloudStore{}
	record := store.decodeRecord(map[string]any{
		"_id":         "record-1",
		"create_time": "database-created",
		"update_time": "database-updated",
		"data": map[string]any{
			"createdAt": "business-created",
			"updatedAt": "business-updated",
		},
	})
	if record["createdAt"] != "business-created" || record["updatedAt"] != "business-updated" {
		t.Fatalf("decodeRecord() overwrote explicit timestamps: %#v", record)
	}
}

func TestCloudStoreUpdatePreservesCreatedAt(t *testing.T) {
	const (
		recordID  = "record-1"
		createdAt = "2026-08-02T00:00:00Z"
	)
	var putBody map[string]any
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.URL.Path == "/api/v2/tables/items/records/"+recordID && r.Method == http.MethodGet:
			_ = json.NewEncoder(w).Encode(map[string]any{
				"code": 0,
				"data": map[string]any{
					"_id":         recordID,
					"create_time": createdAt,
					"update_time": createdAt,
					"data": map[string]any{
						"id":          recordID,
						"createdAt":   createdAt,
						"title":       "old title",
						"legacyField": "not implicitly merged",
					},
				},
			})
		case r.URL.Path == "/api/v2/tables/items/records/"+recordID && r.Method == http.MethodPut:
			if err := json.NewDecoder(r.Body).Decode(&putBody); err != nil {
				t.Fatalf("decode update request: %v", err)
			}
			_ = json.NewEncoder(w).Encode(map[string]any{
				"code": 0,
				"data": map[string]any{
					"_id":         recordID,
					"create_time": createdAt,
					"update_time": "2026-08-03T00:00:00Z",
					"data":        putBody["data"],
				},
			})
		default:
			t.Fatalf("unexpected request: %s %s", r.Method, r.URL.Path)
		}
	}))
	defer server.Close()

	store := &cloudStore{baseURL: server.URL, appID: "db-app-1", apiKey: "secret"}
	updated, err := store.Update(context.Background(), "items", recordID, map[string]any{"title": "new title"})
	if err != nil {
		t.Fatalf("Update() error = %v", err)
	}

	requestData, ok := putBody["data"].(map[string]any)
	if !ok {
		t.Fatalf("PUT body = %#v, want data object", putBody)
	}
	if requestData["createdAt"] != createdAt {
		t.Fatalf("PUT createdAt = %#v, want %q", requestData["createdAt"], createdAt)
	}
	if requestData["id"] != recordID || requestData["title"] != "new title" {
		t.Fatalf("PUT data = %#v", requestData)
	}
	if _, exists := requestData["legacyField"]; exists {
		t.Fatalf("Update unexpectedly changed replacement semantics: %#v", requestData)
	}
	if updated["createdAt"] != createdAt || updated["id"] != recordID || updated["title"] != "new title" {
		t.Fatalf("Update() = %#v", updated)
	}
}
