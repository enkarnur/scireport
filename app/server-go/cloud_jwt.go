package main

import (
	"context"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

const cloudJWTRefreshSkew = 5 * time.Minute

// CloudCredential is the credential envelope returned by `aime app cloud-jwt`.
type CloudCredential struct {
	AccessToken    string `json:"access_token"`
	TokenType      string `json:"token_type"`
	CredentialType string `json:"credential_type"`
}

func (credential CloudCredential) Authorization() string {
	return credential.TokenType + " " + credential.AccessToken
}

type cloudCredentialCacheEntry struct {
	Credential CloudCredential
	ExpiresAt  time.Time
	ContextKey [sha256.Size]byte
}

var (
	cloudCredentialMu    sync.Mutex
	cloudCredentialCache *cloudCredentialCacheEntry
	cloudCredentialGen   atomic.Uint64
)

// GetCloudCredential returns a process-local cached credential. A normal
// proactive refresh may fall back to an unexpired cached credential; a forced
// refresh never does.
func GetCloudCredential(ctx context.Context, forceRefresh bool) (CloudCredential, error) {
	contextKey := cloudCredentialContextKey()
	observedGeneration := cloudCredentialGen.Load()

	cloudCredentialMu.Lock()
	defer cloudCredentialMu.Unlock()
	now := time.Now()

	if forceRefresh &&
		cloudCredentialGen.Load() != observedGeneration &&
		cloudCredentialUnexpired(cloudCredentialCache, contextKey, now) {
		logMsg("[cloud-jwt] forced refresh coalesced", "plugin")
		return cloudCredentialCache.Credential, nil
	}

	if !forceRefresh && cloudCredentialFresh(cloudCredentialCache, contextKey, now) {
		remaining := max(0, int(time.Until(cloudCredentialCache.ExpiresAt).Seconds()))
		logMsg(fmt.Sprintf("[cloud-jwt] cache hit remaining_seconds=%d", remaining), "plugin")
		return cloudCredentialCache.Credential, nil
	}

	var stale *cloudCredentialCacheEntry
	if cloudCredentialUnexpired(cloudCredentialCache, contextKey, now) {
		stale = cloudCredentialCache
	}
	reason := "cache_miss"
	if forceRefresh {
		reason = "forced"
	} else if stale != nil {
		reason = "refresh_window"
	}

	startedAt := time.Now()
	logMsg("[cloud-jwt] refresh start source=aime-cli reason="+reason, "plugin")
	credential, expiresAt, err := fetchCloudCredentialViaCLI(ctx)
	if err != nil {
		duration := time.Since(startedAt).Milliseconds()
		if !forceRefresh && stale != nil {
			remaining := max(0, int(time.Until(stale.ExpiresAt).Seconds()))
			logMsg(fmt.Sprintf(
				"[cloud-jwt] refresh failed, using unexpired cache duration_ms=%d remaining_seconds=%d error_type=%T",
				duration,
				remaining,
				err,
			), "plugin")
			return stale.Credential, nil
		}
		logMsg(fmt.Sprintf(
			"[cloud-jwt] refresh failed source=aime-cli reason=%s duration_ms=%d error_type=%T",
			reason,
			duration,
			err,
		), "plugin")
		return CloudCredential{}, err
	}

	duration := time.Since(startedAt).Milliseconds()
	if expiresAt.IsZero() {
		cloudCredentialCache = nil
		logMsg(fmt.Sprintf(
			"[cloud-jwt] refresh success source=aime-cli cacheable=false reason=missing_exp duration_ms=%d token_type=%s",
			duration,
			credential.TokenType,
		), "plugin")
	} else {
		cloudCredentialCache = &cloudCredentialCacheEntry{
			Credential: credential,
			ExpiresAt:  expiresAt,
			ContextKey: contextKey,
		}
		cloudCredentialGen.Add(1)
		remaining := max(0, int(time.Until(expiresAt).Seconds()))
		logMsg(fmt.Sprintf(
			"[cloud-jwt] refresh success source=aime-cli cacheable=true duration_ms=%d remaining_seconds=%d token_type=%s",
			duration,
			remaining,
			credential.TokenType,
		), "plugin")
	}
	return credential, nil
}

func GetCloudJWT(ctx context.Context, forceRefresh bool) (string, error) {
	credential, err := GetCloudCredential(ctx, forceRefresh)
	if err != nil {
		return "", err
	}
	return credential.AccessToken, nil
}

// InvalidateCloudCredential drops the process-local cache.
func InvalidateCloudCredential() {
	cloudCredentialMu.Lock()
	cloudCredentialCache = nil
	cloudCredentialGen.Add(1)
	cloudCredentialMu.Unlock()
	logMsg("[cloud-jwt] cache invalidated", "plugin")
}

func SetCloudAuthorization(ctx context.Context, request *http.Request, forceRefresh bool) error {
	credential, err := GetCloudCredential(ctx, forceRefresh)
	if err != nil {
		return err
	}
	request.Header.Set("Authorization", credential.Authorization())
	return nil
}

func cloudCredentialContextKey() [sha256.Size]byte {
	values := []string{
		os.Getenv("AIME_CREDENTIAL_BROKER_URL"),
		os.Getenv("AIME_CREDENTIAL_BROKER_TOKEN"),
		os.Getenv("AIME_ASSISTANT_ID"),
		os.Getenv("AIME_CURRENT_USER"),
		os.Getenv("AIME_CLI_BINARY"),
	}
	return sha256.Sum256([]byte(strings.Join(values, "\x00")))
}

func cloudCredentialFresh(
	entry *cloudCredentialCacheEntry,
	contextKey [sha256.Size]byte,
	now time.Time,
) bool {
	return entry != nil &&
		entry.ContextKey == contextKey &&
		now.Before(entry.ExpiresAt.Add(-cloudJWTRefreshSkew))
}

func cloudCredentialUnexpired(
	entry *cloudCredentialCacheEntry,
	contextKey [sha256.Size]byte,
	now time.Time,
) bool {
	return entry != nil && entry.ContextKey == contextKey && now.Before(entry.ExpiresAt)
}

func fetchCloudCredentialViaCLI(ctx context.Context) (CloudCredential, time.Time, error) {
	binary := strings.TrimSpace(os.Getenv("AIME_CLI_BINARY"))
	if binary == "" {
		binary = "aime"
	}
	cmd := exec.CommandContext(ctx, binary, "app", "cloud-jwt")
	out, err := cmd.Output()
	if err != nil {
		return CloudCredential{}, time.Time{}, fmt.Errorf("aime app cloud-jwt failed: %w", err)
	}

	var credential CloudCredential
	if err := json.Unmarshal(out, &credential); err != nil {
		return CloudCredential{}, time.Time{}, fmt.Errorf("parse Cloud JWT response: %w", err)
	}
	credential.AccessToken = strings.TrimSpace(credential.AccessToken)
	credential.TokenType = strings.TrimSpace(credential.TokenType)
	credential.CredentialType = strings.TrimSpace(credential.CredentialType)
	if credential.AccessToken == "" || credential.TokenType == "" {
		return CloudCredential{}, time.Time{}, errors.New(
			"Cloud credential is missing access_token or token_type",
		)
	}

	expiresAt := jwtExpiresAt(credential.AccessToken)
	if !expiresAt.IsZero() && !time.Now().Before(expiresAt) {
		return CloudCredential{}, time.Time{}, errors.New("Cloud credential is already expired")
	}
	return credential, expiresAt, nil
}

// jwtExpiresAt reads the unverified exp claim for cache expiry decisions only.
func jwtExpiresAt(accessToken string) time.Time {
	parts := strings.Split(accessToken, ".")
	if len(parts) < 2 {
		return time.Time{}
	}
	payload, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return time.Time{}
	}
	var claims map[string]any
	if err := json.Unmarshal(payload, &claims); err != nil {
		return time.Time{}
	}
	var expiresAt int64
	switch value := claims["exp"].(type) {
	case float64:
		expiresAt = int64(value)
	case string:
		expiresAt, _ = strconv.ParseInt(value, 10, 64)
	}
	if expiresAt <= 0 {
		return time.Time{}
	}
	return time.Unix(expiresAt, 0)
}
