package main

import (
	"net/http"
	"os"
	"path/filepath"
	"strings"
)

func staticHandler(w http.ResponseWriter, r *http.Request) {
	if strings.HasPrefix(r.URL.Path, "/api/") {
		writeJSON(w, http.StatusNotFound, map[string]any{"error": "Not Found"})
		return
	}
	path := strings.TrimPrefix(r.URL.Path, "/")
	if path != "" {
		candidate := filepath.Join(staticDir, filepath.Clean(path))
		if info, err := os.Stat(candidate); err == nil && !info.IsDir() {
			if strings.HasPrefix(path, "assets/") {
				w.Header().Set("Cache-Control", "public, max-age=604800, immutable")
			}
			http.ServeFile(w, r, candidate)
			return
		}
	}
	index := filepath.Join(staticDir, "index.html")
	if _, err := os.Stat(index); err == nil {
		w.Header().Set("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
		w.Header().Set("Pragma", "no-cache")
		w.Header().Set("Expires", "0")
		http.ServeFile(w, r, index)
		return
	}
	http.Error(w, "Not Found - Run \"pnpm run build\" in app/frontend to generate frontend assets.", http.StatusNotFound)
}
