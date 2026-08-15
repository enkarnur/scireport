package main

import (
	"os"
	"path/filepath"
	"sync"
	"testing"
)

func resetTemplateMetaCache(t *testing.T, dir string) {
	t.Helper()
	oldPluginDir := pluginDir
	oldPayload := templateMetaPayload
	oldVersion := templateMetaVersion

	pluginDir = dir
	templateMetaOnce = sync.Once{}
	templateMetaPayload = nil
	templateMetaVersion = "0.0.0"

	t.Cleanup(func() {
		pluginDir = oldPluginDir
		templateMetaOnce = sync.Once{}
		templateMetaPayload = oldPayload
		templateMetaVersion = oldVersion
	})
}

func TestGetTemplateMetaCachesFirstRead(t *testing.T) {
	dir := t.TempDir()
	resetTemplateMetaCache(t, dir)
	metaPath := filepath.Join(dir, ".template_meta.json")
	if err := os.WriteFile(metaPath, []byte(`{"template_version":"0.0.1"}`), 0o600); err != nil {
		t.Fatal(err)
	}

	firstPayload, firstVersion := getTemplateMeta()
	if firstVersion != "0.0.1" {
		t.Fatalf("version = %q, want 0.0.1", firstVersion)
	}

	if err := os.WriteFile(metaPath, []byte(`{"template_version":"9.9.9"}`), 0o600); err != nil {
		t.Fatal(err)
	}
	secondPayload, secondVersion := getTemplateMeta()
	if string(secondPayload) != string(firstPayload) || secondVersion != firstVersion {
		t.Fatalf("cache changed after file update: first=(%s,%s), second=(%s,%s)",
			firstPayload, firstVersion, secondPayload, secondVersion)
	}
}

func TestGetTemplateMetaFallsBackToZeroVersion(t *testing.T) {
	resetTemplateMetaCache(t, t.TempDir())

	payload, version := getTemplateMeta()
	if version != "0.0.0" {
		t.Fatalf("version = %q, want 0.0.0", version)
	}
	if string(payload) != `{"template_version":"0.0.0","reason":"template meta file missing"}` {
		t.Fatalf("unexpected fallback payload: %s", payload)
	}
}
