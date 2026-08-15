package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strings"
	"sync"
	"time"
)

const (
	authRefreshAhead = 120 * time.Second
	authCacheMax     = 100
	refreshPoolSize  = 4
)

type contextKey string

const ctxKeyUser contextKey = "user"

var (
	errMissingAppInstanceID = errors.New("missing AIME_APP_INSTANCE_ID")
	errMissingJWT           = errors.New("missing JWT")
	errForbidden            = errors.New("forbidden: no access")

	cacheMu      sync.Mutex
	jwtCache     = map[string]authCacheEntry{}
	refreshMu    sync.Mutex
	refreshing   = map[string]struct{}{}
	refreshSem   = make(chan struct{}, refreshPoolSize)
	syncMu       sync.Mutex
	inflightSync = map[string]chan struct{}{}
)

func extractJWT(r *http.Request, allowQuery bool) string {
	if cookie, err := r.Cookie("_app_jwt"); err == nil && strings.TrimSpace(cookie.Value) != "" {
		return strings.TrimSpace(cookie.Value)
	}
	authHeader := strings.TrimSpace(r.Header.Get("Authorization"))
	for _, prefix := range []string{"Byte-Cloud-JWT ", "Bearer "} {
		if strings.HasPrefix(authHeader, prefix) {
			return strings.TrimSpace(strings.TrimPrefix(authHeader, prefix))
		}
	}
	if !allowQuery {
		return ""
	}
	// Browser WebSocket clients cannot set custom Authorization headers, so
	// /ws/page-control is allowed to carry the same JWT in query string.
	for _, key := range []string{"access_token", "jwt"} {
		if v := strings.TrimSpace(r.URL.Query().Get(key)); v != "" {
			return v
		}
	}
	return ""
}

// authenticate verifies the current request and returns user information without
// writing the response. It is used by WebSocket handlers where authMiddleware's
// early JSON response would break the upgrade flow.
func authenticate(r *http.Request, allowQueryJWT bool) (authResult, error) {
	if appInstanceID == "" {
		return authResult{}, errMissingAppInstanceID
	}
	jwtToken := extractJWT(r, allowQueryJWT)
	if jwtToken == "" {
		return authResult{}, errMissingJWT
	}
	result, err := verifyWithServer(jwtToken)
	if err != nil {
		return authResult{}, err
	}
	if !result.HasAccess {
		return authResult{}, errForbidden
	}
	return result, nil
}

func authMiddleware(w http.ResponseWriter, r *http.Request) (*http.Request, bool) {
	result, err := authenticate(r, false)
	if err != nil {
		if errors.Is(err, errMissingAppInstanceID) {
			logMsg("[auth] missing AIME_APP_INSTANCE_ID, deny request", "plugin")
			writeJSON(w, http.StatusForbidden, map[string]any{"error": "Unauthorized: 缺少实例标识"})
			return r, false
		}
		if errors.Is(err, errMissingJWT) {
			writeJSON(w, http.StatusUnauthorized, map[string]any{"error": "Unauthorized: 缺少 JWT"})
			return r, false
		}
		if errors.Is(err, errForbidden) {
			writeJSON(w, http.StatusForbidden, map[string]any{"error": "无访问权限"})
			return r, false
		}
		logMsg("[auth] verify failed: "+err.Error(), "plugin")
		writeJSON(w, http.StatusUnauthorized, map[string]any{"error": "Unauthorized: 验证失败"})
		return r, false
	}
	ctx := context.WithValue(r.Context(), ctxKeyUser, result)
	return r.WithContext(ctx), true
}

func verifyWithServer(jwtToken string) (authResult, error) {
	now := time.Now()
	cacheMu.Lock()
	entry, ok := jwtCache[jwtToken]
	cacheMu.Unlock()
	if ok {
		if now.Before(entry.ExpiresAt.Add(-authRefreshAhead)) {
			return entry.Data, nil
		}
		if now.Before(entry.ExpiresAt) {
			maybeAsyncRefresh(jwtToken)
			return entry.Data, nil
		}
	}
	return syncVerifyAndCache(jwtToken)
}

func doVerify(jwtToken string) (authResult, error) {
	payload := map[string]any{"verify_type": 1, "app_id": appInstanceID}
	body, _ := json.Marshal(payload)
	logMsg(fmt.Sprintf("[auth] verify request: url=%s body={verify_type:1 app_id:%s}", authVerifyURL, appInstanceID), "plugin")

	request, err := http.NewRequest(http.MethodPost, authVerifyURL, bytes.NewReader(body))
	if err != nil {
		return authResult{}, err
	}
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("Authorization", "Byte-Cloud-JWT "+jwtToken)

	resp, err := httpClient.Do(request)
	if err != nil {
		return authResult{}, err
	}
	data, err := decodeHTTPBody(resp)
	if err != nil {
		return authResult{}, err
	}
	if resp.StatusCode == 403 {
		logMsg("[auth] verify 403: user authenticated but no access to app", "plugin")
		return authResult{HasAccess: false}, nil
	}
	if resp.StatusCode >= 400 {
		return authResult{}, fmt.Errorf("auth verify status=%d body=%s", resp.StatusCode, string(data))
	}
	return parseAuthResult(data)
}

func syncVerifyAndCache(jwtToken string) (authResult, error) {
	syncMu.Lock()
	ev, exists := inflightSync[jwtToken]
	leader := !exists
	if leader {
		ev = make(chan struct{})
		inflightSync[jwtToken] = ev
	}
	syncMu.Unlock()

	if leader {
		result, err := doVerify(jwtToken)
		if err == nil {
			storeAuthCache(jwtToken, result)
			logMsg(fmt.Sprintf("[auth] sync verify ok: username=%s, has_access=%v", result.Username, result.HasAccess), "plugin")
		}
		syncMu.Lock()
		delete(inflightSync, jwtToken)
		syncMu.Unlock()
		close(ev)
		return result, err
	}

	select {
	case <-ev:
	case <-time.After(6 * time.Second):
	}
	cacheMu.Lock()
	entry, ok := jwtCache[jwtToken]
	cacheMu.Unlock()
	if ok {
		return entry.Data, nil
	}
	return authResult{}, errors.New("auth verify timeout (follower)")
}

func maybeAsyncRefresh(jwtToken string) {
	refreshMu.Lock()
	if _, ok := refreshing[jwtToken]; ok {
		refreshMu.Unlock()
		return
	}
	refreshing[jwtToken] = struct{}{}
	refreshMu.Unlock()

	go func() {
		refreshSem <- struct{}{}
		defer func() { <-refreshSem }()
		runRefresh(jwtToken)
	}()
}

func runRefresh(jwtToken string) {
	defer func() {
		refreshMu.Lock()
		delete(refreshing, jwtToken)
		refreshMu.Unlock()
	}()
	result, err := doVerify(jwtToken)
	if err == nil {
		storeAuthCache(jwtToken, result)
		logMsg("[auth] async refresh ok: username="+result.Username, "plugin")
	} else {
		logMsg("[auth] async refresh failed, keep old cache", "plugin")
	}
}

func storeAuthCache(jwtToken string, result authResult) {
	cacheMu.Lock()
	defer cacheMu.Unlock()
	jwtCache[jwtToken] = authCacheEntry{Data: result, ExpiresAt: time.Now().Add(authCacheTTL)}
	evictAuthCache()
}

func evictAuthCache() {
	if len(jwtCache) <= authCacheMax {
		return
	}
	now := time.Now()
	for k, e := range jwtCache {
		if !now.Before(e.ExpiresAt) {
			delete(jwtCache, k)
		}
	}
}

func parseAuthResult(data []byte) (authResult, error) {
	var wrapped struct {
		Code int        `json:"code"`
		Data authResult `json:"data"`
	}
	if err := json.Unmarshal(data, &wrapped); err == nil && wrapped.Code != 0 {
		if wrapped.Code == 200 && (wrapped.Data.Valid || wrapped.Data.HasAccess) {
			return wrapped.Data, nil
		}
	}
	var direct authResult
	if err := json.Unmarshal(data, &direct); err != nil {
		return authResult{}, err
	}
	if !direct.Valid && !direct.HasAccess {
		return authResult{}, errors.New("invalid auth payload")
	}
	return direct, nil
}
