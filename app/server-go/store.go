package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// Store 是通用的持久化接口，不绑定特定 model。
// handler 层负责在 map[string]any 与业务 struct 之间转换。
type Store interface {
	Mode() string
	GetAll(ctx context.Context, collection string) ([]map[string]any, error)
	GetByID(ctx context.Context, collection string, id string) (map[string]any, error)
	Create(ctx context.Context, collection string, data map[string]any) (map[string]any, error)
	Update(ctx context.Context, collection string, id string, data map[string]any) (map[string]any, error)
	Delete(ctx context.Context, collection string, id string) error
}

func loadStoreConfig() string {
	path := filepath.Join(pluginDir, "app", "server-go", "store_config.json")
	b, err := os.ReadFile(path)
	if err != nil {
		return "json"
	}
	var cfg storeConfig
	if err := json.Unmarshal(b, &cfg); err != nil || strings.TrimSpace(cfg.Mode) == "" {
		return "json"
	}
	return strings.TrimSpace(cfg.Mode)
}

func resolveDataDir() (string, error) {
	if dataDir := strings.TrimSpace(os.Getenv("AIME_PLUGIN_DATA_DIR")); dataDir != "" {
		return dataDir, nil
	}
	return "", errors.New("AIME_PLUGIN_DATA_DIR is required for local persistence")
}

func initStore() (Store, error) {
	switch configuredMode {
	case "sqlite":
		return newSQLiteStore()
	case "cloud":
		st, err := newCloudStore()
		if err != nil {
			return nil, fmt.Errorf("initialize cloud store: %w", err)
		}
		return st, nil
	default:
		return newJSONStore()
	}
}

func mustInitStore() Store {
	st, err := initStore()
	if err != nil {
		panic(err)
	}
	return st
}
