#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

FRONTEND_DIR="../frontend"
DIST_DIR="../dist"
PLUGIN_ROOT="$(cd ../.. && pwd)"
# 发布包内的预编译二进制（pack_plugin.py 交叉编译产物；默认只打二进制不含源码）
PREBUILT_BIN="$(pwd)/bin/server"

# Python 子进程需要从插件根目录导入内置 aime_sdk，同时保留外部已有搜索路径。
export PYTHONPATH="$PLUGIN_ROOT${PYTHONPATH:+:$PYTHONPATH}"

# 前端：仅当存在源码且 dist 缺失/过期时才构建；发布态（无 frontend 源码）直接用包内 dist
if [ -f "$FRONTEND_DIR/package.json" ]; then
  NEEDS_BUILD=false
  if [ ! -d "$DIST_DIR" ]; then
    NEEDS_BUILD=true
  elif [ -n "$(find "$FRONTEND_DIR/src" "$FRONTEND_DIR/index.html" -newer "$DIST_DIR" 2>/dev/null | head -1)" ]; then
    NEEDS_BUILD=true
  fi

  if [ "$NEEDS_BUILD" = true ]; then
    echo "[start] Installing frontend dependencies..."
    pnpm --dir "$FRONTEND_DIR" install --silent
    echo "[start] Building frontend..."
    pnpm --dir "$FRONTEND_DIR" run build
  else
    echo "[start] Frontend dist up-to-date, skipping build."
  fi
fi

# 后台异步刷新内置 AIME Toolbox SDK 快照（存在脚本 & python3 时）
# 使用 double-fork：中间子 shell 立即退出，实际工作进程被 init 收养，
# 避免 exec 后 Go server 继承未 wait 的子进程导致僵尸。
## 风险太高，自动刷新先去掉
# GEN_SDK_SCRIPT="$PLUGIN_ROOT/tools/gen_toolbox_sdk.py"
# if [ -f "$GEN_SDK_SCRIPT" ] && command -v python3 >/dev/null 2>&1; then
#   GEN_SDK_LOG_DIR="${AIME_PLUGIN_RUNTIME_DIR:-$PLUGIN_ROOT/.aime_build}"
#   mkdir -p "$GEN_SDK_LOG_DIR"
#   ( ( python3 "$GEN_SDK_SCRIPT" >"$GEN_SDK_LOG_DIR/gen_toolbox_sdk.log" 2>&1 || true ) & )
# fi

# 接口契约：当 IDL（app/api/api.yaml）比生成产物新时，先同步生成四端产物，
# 保证服务态与 IDL 一致（防止改了 yaml 忘了跑 gen_api.py）。同步执行以便随后 go build 拿到最新 .gen.go。
GEN_API_SCRIPT="$PLUGIN_ROOT/tools/gen_api.py"
API_IDL="$PLUGIN_ROOT/app/api/api.yaml"
[ -f "$API_IDL" ] || API_IDL="$PLUGIN_ROOT/app/api/api.json"
GEN_API_STAMP="$PLUGIN_ROOT/app/server-go/handler_items.gen.go"
if [ -f "$GEN_API_SCRIPT" ] && [ -f "$API_IDL" ] && command -v python3 >/dev/null 2>&1; then
  if [ ! -f "$GEN_API_STAMP" ] || [ "$API_IDL" -nt "$GEN_API_STAMP" ]; then
    echo "[start] IDL changed, regenerating API artifacts..."
    python3 "$GEN_API_SCRIPT" "$PLUGIN_ROOT" || echo "[start] gen_api.py failed (continuing with existing artifacts)"
  fi
fi

# 快速路径：有 .build_stamp（pack_plugin.py 打包时写入）+ 预编译二进制 → 直接启动
BUILD_STAMP="$(pwd)/.build_stamp"
if [ -f "$BUILD_STAMP" ] && [ -x "$PREBUILT_BIN" ]; then
  exec "$PREBUILT_BIN"
fi

# 无源码且无 stamp：缺少二进制则报错
if [ ! -f "main.go" ]; then
  if [ -x "$PREBUILT_BIN" ]; then
    exec "$PREBUILT_BIN"
  fi
  echo "[start] ERROR: no source code and no prebuilt binary." >&2
  exit 1
fi

# 开发态：按需编译（mtime 检测）
DEV_BIN="$PLUGIN_ROOT/.aime_build/bin/server"
mkdir -p "$(dirname "$DEV_BIN")"

REF_BIN=""
[ -x "$DEV_BIN" ] && REF_BIN="$DEV_BIN"
[ -z "$REF_BIN" ] && [ -x "$PREBUILT_BIN" ] && REF_BIN="$PREBUILT_BIN"

if [ -z "$REF_BIN" ] || \
   [ -n "$(find . -name '*.go' -newer "$REF_BIN" 2>/dev/null | head -1)" ] || \
   [ "$PLUGIN_ROOT/go.mod" -nt "$REF_BIN" ] || \
   [ -n "$(find "$PLUGIN_ROOT/internal" -type f -newer "$REF_BIN" 2>/dev/null | head -1)" ]; then
  echo "[start] Building Go server..."
  export GOWORK=off
  (cd "$PLUGIN_ROOT" && go build -o "$DEV_BIN" ./app/server-go)
  exec "$DEV_BIN"
fi

exec "$REF_BIN"
