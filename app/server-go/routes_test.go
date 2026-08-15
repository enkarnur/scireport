package main

import (
	"net/http"
	"reflect"
	"testing"
)

func resetRouteRegistry(t *testing.T) {
	t.Helper()
	oldRegistry := registry
	oldKeys := registeredKeys
	registry = nil
	registeredKeys = map[string]string{}
	t.Cleanup(func() {
		registry = oldRegistry
		registeredKeys = oldKeys
	})
}

func noopHandler(http.ResponseWriter, *http.Request) {}

func requirePanic(t *testing.T, fn func()) {
	t.Helper()
	defer func() {
		if recover() == nil {
			t.Fatal("expected panic")
		}
	}()
	fn()
}

func TestRegisterRejectsInvalidRoute(t *testing.T) {
	tests := []Route{
		{},
		{Method: http.MethodGet, Path: "/api/test", Summary: "test"},
		{Method: "OPTIONS", Path: "/api/test", Summary: "test", Handler: noopHandler},
	}
	for _, route := range tests {
		resetRouteRegistry(t)
		requirePanic(t, func() { Register(route) })
	}
}

func TestRegisterRejectsDuplicateMethodAndPath(t *testing.T) {
	resetRouteRegistry(t)
	route := Route{
		Method:  http.MethodGet,
		Path:    "/api/test",
		Summary: "test",
		Handler: noopHandler,
	}
	Register(route)
	requirePanic(t, func() { Register(route) })
}

func TestSnapshotRoutesIsSortedAndOmitsHandler(t *testing.T) {
	resetRouteRegistry(t)
	Register(Route{
		Method:         http.MethodPost,
		Path:           "/api/z",
		Summary:        "create z",
		Handler:        noopHandler,
		RequestExample: map[string]any{"name": "z"},
		BodyParams:     []Param{{Name: "name", Type: "string", Required: true, Description: "z name"}},
	})
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/a",
		Summary: "get a",
		Handler: noopHandler,
		Tags:    []string{"a"},
	})

	got := snapshotRoutes()
	if len(got) != 2 {
		t.Fatalf("len(snapshotRoutes()) = %d, want 2", len(got))
	}
	if got[0]["path"] != "/api/a" || got[1]["path"] != "/api/z" {
		t.Fatalf("routes not sorted: %#v", got)
	}
	for _, route := range got {
		if _, ok := route["handler"]; ok {
			t.Fatalf("handler leaked into metadata: %#v", route)
		}
	}
	if !reflect.DeepEqual(got[1]["request_example"], map[string]any{"name": "z"}) {
		t.Fatalf("request example lost: %#v", got[1])
	}
	if !reflect.DeepEqual(got[1]["body_params"], []Param{{Name: "name", Type: "string", Required: true, Description: "z name"}}) {
		t.Fatalf("body params lost: %#v", got[1])
	}
}

func TestMetaRoutesAreAuthenticated(t *testing.T) {
	for _, route := range registry {
		if route.Path == "/api/_meta/template" {
			if route.Public {
				t.Fatalf("%s must require JWT", route.Path)
			}
		}
		if route.Path == "/api/_meta/routes" {
			t.Fatalf("%s must not be registered; route discovery uses Skill references snapshot", route.Path)
		}
	}
}
