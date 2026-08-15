package main

import (
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"testing"
)

func TestWriteRouteSnapshotsWritesProgressiveCliSkillReferences(t *testing.T) {
	resetRouteRegistry(t)
	dir := t.TempDir()
	resetTemplateMetaCache(t, dir)

	if err := os.WriteFile(filepath.Join(dir, ".template_meta.json"), []byte(`{"template_version":"0.0.1"}`), 0o600); err != nil {
		t.Fatal(err)
	}
	skillDir := filepath.Join(dir, "skills", "demo-aime-app-cli")
	if err := os.MkdirAll(skillDir, 0o755); err != nil {
		t.Fatal(err)
	}
	legacySnapshotPath := filepath.Join(skillDir, "references", legacyRouteSnapshotFileName)
	if err := os.MkdirAll(filepath.Dir(legacySnapshotPath), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(legacySnapshotPath, []byte(`{"stale":true}`), 0o600); err != nil {
		t.Fatal(err)
	}

	Register(Route{
		Method:         http.MethodPost,
		Path:           "/api/items",
		Summary:        "create item",
		Handler:        noopHandler,
		Tags:           []string{"items"},
		RequestExample: map[string]any{"title": "todo"},
		Response:       map[string]any{"data": []any{}, "total": float64(0)},
		BodyParams:     []Param{{Name: "title", Type: "string", Required: true, Description: "item title"}},
	})

	if err := writeRouteSnapshots(); err != nil {
		t.Fatal(err)
	}

	indexPath := filepath.Join(skillDir, "references", routeIndexFileName)
	data, err := os.ReadFile(indexPath)
	if err != nil {
		t.Fatal(err)
	}
	var indexPayload map[string]any
	if err := json.Unmarshal(data, &indexPayload); err != nil {
		t.Fatal(err)
	}
	if indexPayload["template_version"] != "0.0.1" {
		t.Fatalf("template_version = %#v, want 0.0.1", indexPayload["template_version"])
	}
	if indexPayload["source"] != "server-startup" {
		t.Fatalf("source = %#v, want server-startup", indexPayload["source"])
	}
	routes, ok := indexPayload["routes"].([]any)
	if !ok || len(routes) != 1 {
		t.Fatalf("routes = %#v, want one route", indexPayload["routes"])
	}
	route, ok := routes[0].(map[string]any)
	if !ok || route["method"] != http.MethodPost || route["path"] != "/api/items" {
		t.Fatalf("unexpected route: %#v", routes[0])
	}
	if _, ok := route["body_params"]; ok {
		t.Fatalf("index must not include body_params: %#v", route)
	}
	if _, ok := route["request_example"]; ok {
		t.Fatalf("index must not include request_example: %#v", route)
	}
	respExample, ok := route["response"].(map[string]any)
	if !ok {
		t.Fatalf("index must include response: %#v", route)
	}
	if _, ok := respExample["data"].([]any); !ok {
		t.Fatalf("response.data expected []any: %#v", respExample)
	}
	if respExample["total"] != float64(0) {
		t.Fatalf("response.total expected 0, got %#v", respExample["total"])
	}

	detailsPath := filepath.Join(skillDir, "references", routeDetailsFileName)
	data, err = os.ReadFile(detailsPath)
	if err != nil {
		t.Fatal(err)
	}
	var detailsPayload map[string]any
	if err := json.Unmarshal(data, &detailsPayload); err != nil {
		t.Fatal(err)
	}
	routesByKey, ok := detailsPayload["routes_by_key"].(map[string]any)
	if !ok {
		t.Fatalf("routes_by_key = %#v, want object", detailsPayload["routes_by_key"])
	}
	detail, ok := routesByKey["POST /api/items"].(map[string]any)
	if !ok {
		t.Fatalf("missing detail for POST /api/items: %#v", routesByKey)
	}
	if _, leaked := detail["handler"]; leaked {
		t.Fatalf("handler leaked into route detail: %#v", detail)
	}
	bodyParams, ok := detail["body_params"].([]any)
	if !ok || len(bodyParams) != 1 {
		t.Fatalf("body_params = %#v, want one param", detail["body_params"])
	}
	bodyParam, ok := bodyParams[0].(map[string]any)
	if !ok || bodyParam["name"] != "title" || bodyParam["required"] != true {
		t.Fatalf("unexpected body param: %#v", bodyParams[0])
	}
	if _, err := os.Stat(legacySnapshotPath); !os.IsNotExist(err) {
		t.Fatalf("legacy snapshot should be removed, stat err = %v", err)
	}
}

func TestWriteRouteSnapshotsIgnoresMissingSkillsDir(t *testing.T) {
	oldPluginDir := pluginDir
	oldPayload := templateMetaPayload
	oldVersion := templateMetaVersion
	pluginDir = t.TempDir()
	templateMetaOnce = sync.Once{}
	templateMetaPayload = nil
	templateMetaVersion = "0.0.0"
	t.Cleanup(func() {
		pluginDir = oldPluginDir
		templateMetaOnce = sync.Once{}
		templateMetaPayload = oldPayload
		templateMetaVersion = oldVersion
	})

	if err := writeRouteSnapshots(); err != nil {
		t.Fatal(err)
	}
}
