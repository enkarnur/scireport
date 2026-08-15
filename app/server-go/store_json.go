package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/google/uuid"
)

type jsonState struct {
	Collections map[string][]map[string]any `json:"collections"`
}

type jsonStore struct {
	mu   sync.Mutex
	path string
}

func newJSONStore() (*jsonStore, error) {
	dataDir, err := resolveDataDir()
	if err != nil {
		return nil, err
	}
	if err := os.MkdirAll(dataDir, 0o755); err != nil {
		return nil, err
	}
	return &jsonStore{path: filepath.Join(dataDir, "data.json")}, nil
}

func (s *jsonStore) Mode() string { return "json" }

func (s *jsonStore) load() jsonState {
	b, err := os.ReadFile(s.path)
	if err != nil {
		state := jsonState{Collections: map[string][]map[string]any{}}
		_ = s.save(state)
		return state
	}
	var state jsonState
	if err := json.Unmarshal(b, &state); err != nil {
		logMsg("[json-store] Failed to load data: "+err.Error(), "plugin")
		return jsonState{Collections: map[string][]map[string]any{}}
	}
	if state.Collections == nil {
		state.Collections = map[string][]map[string]any{}
	}
	return state
}

func (s *jsonStore) save(state jsonState) error {
	b, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(s.path, b, 0o644)
}

func (s *jsonStore) GetAll(_ context.Context, collection string) ([]map[string]any, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	items := s.load().Collections[collection]
	if items == nil {
		return []map[string]any{}, nil
	}
	return items, nil
}

func (s *jsonStore) GetByID(_ context.Context, collection string, id string) (map[string]any, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	for _, item := range s.load().Collections[collection] {
		if asString(item["id"]) == id {
			return item, nil
		}
	}
	return nil, nil
}

func (s *jsonStore) Create(_ context.Context, collection string, data map[string]any) (map[string]any, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	state := s.load()
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
	state.Collections[collection] = append(state.Collections[collection], data)
	if err := s.save(state); err != nil {
		return nil, err
	}
	return data, nil
}

func (s *jsonStore) Update(_ context.Context, collection string, id string, data map[string]any) (map[string]any, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	state := s.load()
	items := state.Collections[collection]
	for idx, item := range items {
		if asString(item["id"]) == id {
			data["id"] = id
			if data["createdAt"] == nil {
				data["createdAt"] = item["createdAt"]
			}
			data["updatedAt"] = time.Now().Format(time.RFC3339)
			state.Collections[collection][idx] = data
			if err := s.save(state); err != nil {
				return nil, err
			}
			return data, nil
		}
	}
	return nil, sql.ErrNoRows
}

func (s *jsonStore) Delete(_ context.Context, collection string, id string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	state := s.load()
	items := state.Collections[collection]
	found := false
	result := make([]map[string]any, 0, len(items))
	for _, item := range items {
		if asString(item["id"]) == id {
			found = true
			continue
		}
		result = append(result, item)
	}
	if !found {
		return sql.ErrNoRows
	}
	state.Collections[collection] = result
	return s.save(state)
}
