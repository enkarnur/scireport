package main

import (
	"fmt"
	"os"
	"path/filepath"
	"time"
)

func resolveLogDir() string {
	if runtimeDir := os.Getenv("AIME_PLUGIN_RUNTIME_DIR"); runtimeDir != "" {
		return filepath.Join(runtimeDir, "logs")
	}
	workspace := os.Getenv("AIME_WORKSPACE_PATH")
	pluginDir := os.Getenv("AIME_PLUGIN_DIR")
	if workspace != "" && pluginDir != "" {
		return filepath.Join(workspace, ".aime", "plugin_runtime", filepath.Base(pluginDir), "logs")
	}
	if pluginDir != "" {
		return filepath.Join(pluginDir, "logs")
	}
	cwd, err := os.Getwd()
	if err != nil {
		return "logs"
	}
	return filepath.Join(cwd, "logs")
}

func logFilePath(name string) string {
	if name == "" {
		name = "plugin"
	}
	return filepath.Join(resolveLogDir(), name+".log")
}

func logMsg(msg string, name string) {
	path := logFilePath(name)
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return
	}
	f, err := os.OpenFile(path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		return
	}
	defer f.Close()
	_, _ = fmt.Fprintf(f, "[%s] %s\n", time.Now().Format("2006-01-02 15:04:05"), msg)
	_ = f.Sync()
}
