package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// ExecResult 封装子进程执行结果。
type ExecResult struct {
	Stdout   string `json:"stdout"`
	Stderr   string `json:"stderr"`
	ExitCode int    `json:"exit_code"`
}

// execCommand 执行任意命令，自动继承环境变量并注入 JWT 鉴权信息。
// 工作目录默认为 pluginDir，可通过 workDir 参数覆盖（空串则用 pluginDir）。
func execCommand(cmdArgs []string, stdin string, workDir string, timeout time.Duration) (*ExecResult, error) {
	if len(cmdArgs) == 0 {
		return nil, fmt.Errorf("execCommand: empty command")
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, cmdArgs[0], cmdArgs[1:]...)
	if workDir != "" {
		cmd.Dir = workDir
	} else {
		cmd.Dir = pluginDir
	}
	cmd.Env = buildExecEnv(ctx)
	cmd.Stdin = strings.NewReader(stdin)

	var stdout, stderr strings.Builder
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	err := cmd.Run()
	result := &ExecResult{
		Stdout: stdout.String(),
		Stderr: stderr.String(),
	}

	if err != nil {
		if ctx.Err() == context.DeadlineExceeded {
			return result, fmt.Errorf("command timeout (%v): %s", timeout, result.Stderr)
		}
		if exitErr, ok := err.(*exec.ExitError); ok {
			result.ExitCode = exitErr.ExitCode()
			return result, fmt.Errorf("command exited with code %d: %s", result.ExitCode, result.Stderr)
		}
		return result, fmt.Errorf("command failed: %w", err)
	}
	return result, nil
}

// callPython 执行插件目录下的 Python 脚本，通过 stdin 传入 JSON、从 stdout 读取 JSON 结果。
func callPython(scriptRelPath string, input any, timeout time.Duration) (json.RawMessage, error) {
	scriptPath := filepath.Join(pluginDir, scriptRelPath)
	if _, err := os.Stat(scriptPath); err != nil {
		return nil, fmt.Errorf("script not found: %s", scriptPath)
	}

	var stdin string
	if input != nil {
		payload, err := json.Marshal(input)
		if err != nil {
			return nil, fmt.Errorf("marshal input: %w", err)
		}
		stdin = string(payload)
	}

	result, err := execCommand([]string{"python3", scriptPath}, stdin, pluginDir, timeout)
	if err != nil {
		return nil, err
	}

	out := strings.TrimSpace(result.Stdout)
	if out == "" {
		return json.RawMessage("null"), nil
	}
	if !json.Valid([]byte(out)) {
		return nil, fmt.Errorf("python script returned invalid JSON: %s", out[:min(200, len(out))])
	}
	return json.RawMessage(out), nil
}

// callBash 执行 bash 命令字符串，返回 stdout 文本。
func callBash(script string, timeout time.Duration) (*ExecResult, error) {
	return execCommand([]string{"bash", "-c", script}, "", pluginDir, timeout)
}

// buildExecEnv 继承当前进程环境变量，并注入/覆盖鉴权和路径变量供子进程使用。
func buildExecEnv(ctx context.Context) []string {
	env := os.Environ()
	for _, key := range []string{"AIME_USER_CLOUD_JWT", "USER_CLOUD_JWT", "IRIS_USER_CLOUD_JWT"} {
		env = removeEnv(env, key)
	}
	jwt := resolveJWT(ctx)
	if jwt != "" {
		env = appendOrReplace(env, "AIME_USER_CLOUD_JWT", jwt)
	}
	env = appendOrReplace(env, "AIME_PLUGIN_DIR", pluginDir)
	pythonPath := pluginDir
	if existing := os.Getenv("PYTHONPATH"); existing != "" {
		prefix := pluginDir + string(os.PathListSeparator)
		if existing == pluginDir || strings.HasPrefix(existing, prefix) {
			pythonPath = existing
		} else {
			pythonPath = prefix + existing
		}
	}
	env = appendOrReplace(env, "PYTHONPATH", pythonPath)
	return env
}

// resolveJWT uses the shared process-local cache and never falls back to
// credentials inherited when the Service process started.
func resolveJWT(ctx context.Context) string {
	token, err := GetCloudJWT(ctx, false)
	if err != nil {
		return ""
	}
	return token
}

func appendOrReplace(env []string, key, value string) []string {
	prefix := key + "="
	for i, e := range env {
		if strings.HasPrefix(e, prefix) {
			env[i] = prefix + value
			return env
		}
	}
	return append(env, prefix+value)
}

func removeEnv(env []string, key string) []string {
	prefix := key + "="
	filtered := env[:0]
	for _, entry := range env {
		if !strings.HasPrefix(entry, prefix) {
			filtered = append(filtered, entry)
		}
	}
	return filtered
}
