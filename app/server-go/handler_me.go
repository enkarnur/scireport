package main

import "net/http"

func init() {
	Register(Route{
		Method:  http.MethodGet,
		Path:    "/api/me",
		Summary: "获取当前登录用户信息",
		Handler: meHandler,
		Tags:    []string{"me"},
		Response: map[string]any{
			"user": map[string]any{"username": "alice"},
		},
	})
}

// meHandler 返回当前登录用户的基础信息，用户信息由 authMiddleware 写入 request context。
func meHandler(w http.ResponseWriter, r *http.Request) {
	user, _ := r.Context().Value(ctxKeyUser).(authResult)
	username := user.Username
	if username == "" {
		username = "Anonymous"
	}
	writeJSON(w, http.StatusOK, map[string]any{
		"user": map[string]any{
			"username": username,
		},
	})
}
