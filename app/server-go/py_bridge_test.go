package main

import (
	"context"
	"path/filepath"
	"strings"
	"testing"
)

func TestBuildExecEnvDropsStaticJWTWhenCLIUnavailable(t *testing.T) {
	t.Setenv("AIME_CLI_BINARY", filepath.Join(t.TempDir(), "missing-aime"))
	t.Setenv("AIME_USER_CLOUD_JWT", "stale-aime-token")
	t.Setenv("USER_CLOUD_JWT", "stale-user-token")
	t.Setenv("IRIS_USER_CLOUD_JWT", "stale-iris-token")

	env := buildExecEnv(context.Background())
	for _, key := range []string{"AIME_USER_CLOUD_JWT", "USER_CLOUD_JWT", "IRIS_USER_CLOUD_JWT"} {
		prefix := key + "="
		for _, entry := range env {
			if strings.HasPrefix(entry, prefix) {
				t.Fatalf("%s should not be inherited when Cloud JWT acquisition fails", key)
			}
		}
	}
}
