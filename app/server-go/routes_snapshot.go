package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const (
	routeIndexFileName          = "api-routes.index.json"
	routeDetailsFileName        = "api-routes.details.json"
	legacyRouteSnapshotFileName = "api-routes.snapshot.json"
)

// writeRouteSnapshots 把当前 Go 进程已注册的后端路由写入默认 CLI Skill 的 references。
//
// references/api-routes.index.json 是短列表，只用于先定位候选接口；
// references/api-routes.details.json 是全量详情，Agent 应在定位候选接口后用 grep_search
// 搜索 "METHOD PATH" 附近上下文读取对应接口详情，避免一次性读取过多内容。
// 两个文件都会在服务每次启动时覆盖刷新，Agent / Skill 不再为了“发现接口”调用后端路由或 CLI 命令。
func writeRouteSnapshots() error {
	dirs, err := routeReferenceDirs()
	if err != nil {
		return err
	}
	if len(dirs) == 0 {
		return nil
	}

	// IDL 生成的产物优先级高于服务启动快照，避免覆盖后导致 verify IDL 一致性检查失败
	if len(dirs) > 0 {
		idxPath := filepath.Join(dirs[0], routeIndexFileName)
		if data, err := os.ReadFile(idxPath); err == nil {
			var existing map[string]any
			if json.Unmarshal(data, &existing) == nil {
				if src, _ := existing["source"].(string); src == "idl-gen" {
					return nil
				}
			}
		}
	}

	_, templateVersion := getTemplateMeta()
	generatedAt := time.Now().Format(time.RFC3339)
	indexPayload := map[string]any{
		"schema_version":   "1.1",
		"template_version": templateVersion,
		"generated_at":     generatedAt,
		"source":           "server-startup",
		"route_count":      len(registry),
		"routes":           snapshotRouteIndex(),
	}
	detailsPayload := map[string]any{
		"schema_version":      "1.1",
		"template_version":    templateVersion,
		"generated_at":        generatedAt,
		"source":              "server-startup",
		"route_count":         len(registry),
		"lookup_hint":         "先读 api-routes.index.json 定位接口，再在本文件 grep_search 精确搜索 \"METHOD PATH\" 附近上下文，例如 \"POST /api/items\"。",
		"routes_by_key":       snapshotRoutesByKey(),
		"refresh_semantics":   "overwritten by Go service startup",
		"progressive_loading": true,
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return fmt.Errorf("create route reference dir %s: %w", dir, err)
		}
		if err := writeJSONFile(filepath.Join(dir, routeIndexFileName), indexPayload); err != nil {
			return err
		}
		if err := writeJSONFile(filepath.Join(dir, routeDetailsFileName), detailsPayload); err != nil {
			return err
		}
		if err := removeLegacyRouteSnapshot(dir); err != nil {
			return err
		}
	}
	return nil
}

func writeJSONFile(path string, payload any) error {
	data, err := json.MarshalIndent(payload, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return fmt.Errorf("write route reference %s: %w", path, err)
	}
	return nil
}

func removeLegacyRouteSnapshot(dir string) error {
	path := filepath.Join(dir, legacyRouteSnapshotFileName)
	if err := os.Remove(path); err != nil && !os.IsNotExist(err) {
		return fmt.Errorf("remove legacy route snapshot %s: %w", path, err)
	}
	return nil
}

func routeReferenceDirs() ([]string, error) {
	skillsDir := filepath.Join(pluginDir, "skills")
	entries, err := os.ReadDir(skillsDir)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("read skills dir %s: %w", skillsDir, err)
	}

	var dirs []string
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		name := entry.Name()
		if !strings.HasSuffix(name, "-aime-app-cli") {
			continue
		}
		dirs = append(dirs, filepath.Join(skillsDir, name, "references"))
	}
	return dirs, nil
}
