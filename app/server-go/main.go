package main

import (
	"errors"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

var (
	pluginDir      = resolvePluginDir()
	workspaceDir   = strings.TrimSpace(os.Getenv("AIME_WORKSPACE_PATH"))
	staticDir      = filepath.Join(pluginDir, "app", "dist")
	listenPort     = readEnvInt("PORT", 3000)
	platformHost   = strings.TrimSpace(os.Getenv("IRIS_RUNTIME_AIME_API_HOST"))
	appInstanceID  = strings.TrimSpace(os.Getenv("AIME_APP_INSTANCE_ID"))
	authVerifyURL  = resolvePlatformURL() + "/api/agents/v2/apps/auth/verify"
	authCacheTTL   = 295 * time.Second
	httpClient     = &http.Client{Timeout: 15 * time.Second}
	configuredMode = loadStoreConfig()
	store          Store
)

func main() {
	store = mustInitStore()

	mux := http.NewServeMux()

	// 业务路由：来自各 handler 文件的 init() 注册，通过 mountRoutes 一次性挂载。
	// - 非 Public 的路由会被 wrapAuth 自动包一层 JWT 校验。
	// 新增接口时不需要动 main.go，只需要在同一 handler 文件里 init() + Register。
	mountRoutes(mux)
	if err := writeRouteSnapshots(); err != nil {
		logMsg(fmt.Sprintf("Failed to write route snapshot: %v", err), "plugin")
	} else {
		logMsg("Route snapshot written to CLI Skill references", "plugin")
	}

	// 静态资源 / SPA fallback：不进 registry，直接挂在根路径。
	mux.HandleFunc("/", staticHandler)

	logMsg(fmt.Sprintf("Server starting at http://localhost:%d", listenPort), filepath.Base(pluginDir))
	logMsg(fmt.Sprintf("AIApp dir: %s", pluginDir), filepath.Base(pluginDir))
	logMsg(fmt.Sprintf("Static dir: %s", staticDir), filepath.Base(pluginDir))
	storeMode := configuredMode
	if store != nil {
		storeMode = store.Mode()
	}
	logMsg(fmt.Sprintf("Data backend: %s", storeMode), "plugin")
	logMsg(fmt.Sprintf("Registered %d business routes (route snapshot written to CLI Skill references)", len(registry)), "plugin")

	server := &http.Server{
		Addr:              fmt.Sprintf(":%d", listenPort),
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
	}
	if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		logMsg(fmt.Sprintf("server stopped unexpectedly: %v", err), filepath.Base(pluginDir))
		panic(err)
	}
}

func resolvePluginDir() string {
	if v := strings.TrimSpace(os.Getenv("AIME_PLUGIN_DIR")); v != "" {
		return v
	}
	cwd, err := os.Getwd()
	if err == nil {
		return filepath.Clean(filepath.Join(cwd, "..", ".."))
	}
	return "."
}

func resolvePlatformURL() string {
	host := platformHost
	if host == "" {
		host = "aime.bytedance.net"
	}
	return "https://" + host
}

func readEnvInt(key string, fallback int) int {
	if v := strings.TrimSpace(os.Getenv(key)); v != "" {
		if parsed, err := strconv.Atoi(v); err == nil {
			return parsed
		}
	}
	return fallback
}
