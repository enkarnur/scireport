#!/usr/bin/env python3
"""从单文件 IDL（app/api/api.yaml 或 api.json）生成四端接口产物。

这是 AIME App「先写协议、再并行开发」的生成器。它把接口契约从 Go 源码里
解放出来：写完 IDL 后秒级产出全部产物，无需 go build / 重启服务，三个开发
Agent（前端 / 后端 / 集成）可立即并行。

产物：
  1. app/server-go/handler_<resource>.gen.go   Register(Route{...}) 注册（勿改）
  2. app/server-go/handler_<resource>.go        handler 函数体 stub（仅当文件不存在时创建）
  3. app/frontend/src/api/client.gen.ts         前端 typed client
  4. skills/<skill>/api_client.gen.py           command/hook typed 封装
  5. skills/<skill>/references/api-routes.index.json + api-routes.details.json

用法：
  python3 tools/gen_api.py <plugin-dir>            # 生成
  python3 tools/gen_api.py <plugin-dir> --check    # 仅校验产物是否最新（CI/verify 用）

设计约束：
  * 运行时后端/前端不引入任何新依赖；PyYAML 仅 dev-time 生成阶段用到。
  * .gen.* 文件由本脚本完全拥有，Agent 不应手改；handler_<resource>.go 一旦存在便不覆盖。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _gofmt(src: str) -> str:
    """用 gofmt 规整 Go 源码；gofmt 不可用时原样返回（不阻断生成）。"""
    tool = shutil.which("gofmt")
    if not tool:
        return src
    try:
        proc = subprocess.run([tool], input=src, capture_output=True, text=True, timeout=30)
    except Exception:
        return src
    return proc.stdout if proc.returncode == 0 and proc.stdout else src


GEN_BANNER = "CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT"

VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH"}
SCHEMA_VERSION = "1.1"


class IDLError(Exception):
    """IDL 解析或校验失败。"""


# ── IDL 加载 ────────────────────────────────────────────────────────────


def load_idl(plugin_dir: Path) -> dict:
    api_dir = plugin_dir / "app" / "api"
    yaml_path = api_dir / "api.yaml"
    json_path = api_dir / "api.json"

    if yaml_path.exists():
        try:
            import yaml  # type: ignore
        except ImportError as exc:  # pragma: no cover - env dependent
            raise IDLError(
                f"检测到 {yaml_path}，但当前环境缺少 PyYAML。"
                "请安装 pyyaml，或改用 app/api/api.json（stdlib 零依赖）。"
            ) from exc
        try:
            raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as exc:
            raise IDLError(f"{yaml_path} YAML 语法错误，请检查 flow mapping 中的值是否需要加引号：\n{exc}") from exc
        source = yaml_path
    elif json_path.exists():
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        source = json_path
    else:
        raise IDLError(f"未找到 IDL 文件：{yaml_path} 或 {json_path}")

    if not isinstance(raw, dict):
        raise IDLError(f"{source} 顶层必须是对象")
    return raw


def normalize_and_validate(idl: dict) -> list[dict]:
    """展开为扁平 route 列表，做基本校验，并按 path/method 稳定排序。"""
    resources = idl.get("resources") or []
    if not isinstance(resources, list):
        raise IDLError("resources 必须是列表")

    seen: dict[str, str] = {}
    routes: list[dict] = []
    for res in resources:
        rname = str(res.get("name") or "").strip()
        if not rname:
            raise IDLError("每个 resource 必须有 name")
        model = res.get("model") if isinstance(res.get("model"), dict) else None
        for r in res.get("routes") or []:
            method = str(r.get("method") or "").strip().upper()
            path = str(r.get("path") or "").strip()
            summary = str(r.get("summary") or "").strip()
            if method not in VALID_METHODS:
                raise IDLError(f"resource={rname} 路由 method 非法: {method!r}（仅 {'/'.join(sorted(VALID_METHODS))}）")
            if not path.startswith("/"):
                raise IDLError(f"resource={rname} 路由 path 必须以 / 开头: {path!r}")
            if not summary:
                raise IDLError(f"resource={rname} 路由 {method} {path} 缺少 summary")
            key = f"{method} {path}"
            if key in seen:
                raise IDLError(f"重复路由 {key}（resource={rname} 与 {seen[key]}）")
            seen[key] = rname
            routes.append({
                "resource": rname,
                "model": model,
                "method": method,
                "path": path,
                "summary": summary,
                "public": bool(r.get("public", False)),
                "tags": list(r.get("tags") or []),
                "query": _normalize_params(r.get("query")),
                "body": _normalize_params(r.get("body")),
                "request_example": r.get("request_example"),
                "response": r.get("response"),
                "response_model": r.get("response_model") if isinstance(r.get("response_model"), dict) else None,
            })

    routes.sort(key=lambda x: (x["path"], x["method"]))
    return routes


def _normalize_params(spec: Any) -> list[dict]:
    """把 {name: {type, required, description}} 归一化为 Param 列表。"""
    if not spec:
        return []
    out = []
    if isinstance(spec, dict):
        items = spec.items()
    elif isinstance(spec, list):  # 也接受显式列表形式
        items = [(p.get("name"), p) for p in spec]
    else:
        raise IDLError(f"参数定义必须是对象或列表，得到 {type(spec).__name__}")
    for name, meta in items:
        meta = meta or {}
        out.append({
            "name": str(name),
            "type": str(meta.get("type") or "string"),
            "required": bool(meta.get("required", False)),
            "description": str(meta.get("description") or ""),
        })
    return out


# ── 命名工具 ─────────────────────────────────────────────────────────────


def _pascal(s: str) -> str:
    parts = re.split(r"[^0-9a-zA-Z]+", s)
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


def _camel(s: str) -> str:
    p = _pascal(s)
    return p[:1].lower() + p[1:] if p else p


def _go_ident(s: str) -> str:
    return _camel(s)


def op_name(route: dict) -> str:
    """由 method+path 推导稳定的操作名，例如 GET /api/items/{id} -> ItemsGetById。"""
    segs = [s for s in route["path"].split("/") if s and s not in ("api",)]
    parts = []
    for s in segs:
        if s.startswith("{") and s.endswith("}"):
            parts.append("By" + _pascal(s[1:-1]))
        else:
            parts.append(_pascal(s))
    verb = {
        "GET": "Get" if any(p.startswith("By") for p in parts) else "List",
        "POST": "Create",
        "PUT": "Update",
        "PATCH": "Patch",
        "DELETE": "Delete",
    }[route["method"]]
    base = "".join(parts) or "Root"
    return base + verb


# ── Go 代码生成 ──────────────────────────────────────────────────────────


def _go_lit(v: Any, indent: int = 1) -> str:
    """把 JSON-like 值渲染为 Go map[string]any / []any 字面量。"""
    pad = "\t" * indent
    pad_close = "\t" * (indent - 1)
    if isinstance(v, dict):
        if not v:
            return "map[string]any{}"
        lines = ["map[string]any{"]
        for k, val in v.items():
            lines.append(f'{pad}{json.dumps(str(k))}: {_go_lit(val, indent + 1)},')
        lines.append(pad_close + "}")
        return "\n".join(lines)
    if isinstance(v, list):
        if not v:
            return "[]any{}"
        lines = ["[]any{"]
        for val in v:
            lines.append(f"{pad}{_go_lit(val, indent + 1)},")
        lines.append(pad_close + "}")
        return "\n".join(lines)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return json.dumps(v)
    return json.dumps(str(v), ensure_ascii=False)


def _go_params(params: list[dict], indent: int = 3) -> str:
    pad = "\t" * indent
    pad_close = "\t" * (indent - 1)
    lines = ["[]Param{"]
    for p in params:
        fields = [f'Name: {json.dumps(p["name"])}']
        if p["type"]:
            fields.append(f'Type: {json.dumps(p["type"])}')
        if p["required"]:
            fields.append("Required: true")
        if p["description"]:
            fields.append(f'Description: {json.dumps(p["description"], ensure_ascii=False)}')
        lines.append(f'{pad}{{{", ".join(fields)}}},')
    lines.append(pad_close + "}")
    return "\n".join(lines)


def gen_go_register(resource: str, routes: list[dict]) -> str:
    """生成 handler_<resource>.gen.go：仅 init(){Register(...)}，勿改。"""
    lines = [
        f"// {GEN_BANNER}",
        "package main",
        "",
        'import "net/http"',
        "",
        f"// 本文件由 IDL 生成，登记 {resource} 资源的路由契约。",
        f"// 业务逻辑写在 handler_{resource}.go 的 handler 函数里，不要改本文件。",
        "func init() {",
    ]
    for r in routes:
        fn = _go_ident(op_name(r))
        method_const = {
            "GET": "http.MethodGet", "POST": "http.MethodPost", "PUT": "http.MethodPut",
            "DELETE": "http.MethodDelete", "PATCH": "http.MethodPatch",
        }[r["method"]]
        lines.append("\tRegister(Route{")
        lines.append(f"\t\tMethod:  {method_const},")
        lines.append(f'\t\tPath:    {json.dumps(r["path"])},')
        lines.append(f'\t\tSummary: {json.dumps(r["summary"], ensure_ascii=False)},')
        lines.append(f"\t\tHandler: {fn},")
        if r["public"]:
            lines.append("\t\tPublic:  true,")
        if r["tags"]:
            tag_lits = ", ".join(json.dumps(t, ensure_ascii=False) for t in r["tags"])
            lines.append(f"\t\tTags:    []string{{{tag_lits}}},")
        if r["query"]:
            lines.append(f'\t\tQueryParams: {_go_params(r["query"], 3)},')
        if r["body"]:
            lines.append(f'\t\tBodyParams: {_go_params(r["body"], 3)},')
        if r["request_example"] is not None:
            lines.append(f'\t\tRequestExample: {_go_lit(r["request_example"], 3)},')
        if r["response"] is not None:
            lines.append(f'\t\tResponse: {_go_lit(r["response"], 3)},')
        lines.append("\t})")
    lines.append("}")
    return "\n".join(lines) + "\n"


def gen_go_handler_stub(resource: str, routes: list[dict]) -> str:
    """生成 handler_<resource>.go 首版 stub（仅当文件不存在时写入，之后由 Agent B 维护）。"""
    lines = [
        f"// handler_{resource}.go — {resource} 资源的业务逻辑。",
        f"// 路由契约在 handler_{resource}.gen.go（由 IDL 生成，勿改）；此文件由你填实现。",
        "//",
        "// stub 目前直接返回 IDL 里的 response，让契约先跑通；",
        "// Agent B 请用真实 store 读写替换每个 handler 内部。",
        "package main",
        "",
        'import "net/http"',
        "",
    ]
    for r in routes:
        fn = _go_ident(op_name(r))
        resp = r["response"] if r["response"] is not None else {"data": None}
        lines.append(f'// {fn} 处理 {r["method"]} {r["path"]}：{r["summary"]}')
        lines.append(f"func {fn}(w http.ResponseWriter, r *http.Request) {{")
        lines.append("\t// TODO(Agent B): 替换为真实业务逻辑（读写 store、校验参数等）。")
        lines.append(f"\twriteJSON(w, http.StatusOK, {_go_lit(resp, 2)})")
        lines.append("}")
        lines.append("")
    return "\n".join(lines) + "\n"


# ── TypeScript client 生成 ───────────────────────────────────────────────


def _ts_type(t: str) -> str:
    return {
        "string": "string", "int": "number", "number": "number",
        "bool": "boolean", "boolean": "boolean", "object": "Record<string, unknown>",
        "array": "unknown[]",
    }.get(t, "unknown")


def _ts_body_type(params: list[dict]) -> str:
    if not params:
        return "Record<string, unknown>"
    fields = []
    for p in params:
        opt = "" if p["required"] else "?"
        doc = f" /** {p['description']} */" if p["description"] else ""
        fields.append(f"  {p['name']}{opt}: {_ts_type(p['type'])};{doc}")
    return "{\n" + "\n".join(fields) + "\n}"


def _ts_path_params(path: str) -> list[str]:
    return re.findall(r"\{(\w+)\}", path)


_TS_IDENT_RE = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def _ts_key(k: str) -> str:
    return k if _TS_IDENT_RE.match(k) else json.dumps(k)


def _ts_type_from_example(value: Any) -> str:
    """把 JSON 示例值渲染为 TS 类型字面量。"""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        if not value:
            return "unknown[]"
        return f"Array<{_ts_type_from_example(value[0])}>"
    if isinstance(value, dict):
        if not value:
            return "Record<string, unknown>"
        fields = [f"{_ts_key(str(k))}: {_ts_type_from_example(v)}" for k, v in value.items()]
        return "{ " + "; ".join(fields) + " }"
    return "unknown"


def _ts_type_from_model_field(v: Any) -> str:
    """model 字段值：既可能是类型标记字符串（"string"/"int"/...），也可能是嵌套示例。"""
    if isinstance(v, str):
        mapped = {
            "string": "string",
            "int": "number",
            "integer": "number",
            "number": "number",
            "float": "number",
            "bool": "boolean",
            "boolean": "boolean",
            "object": "Record<string, unknown>",
            "array": "unknown[]",
            "any": "unknown",
        }
        if v in mapped:
            return mapped[v]
        return "string"
    return _ts_type_from_example(v)


def _model_interface_name(resource: str) -> str:
    return f"{_pascal(resource)}Model"


def _gen_model_interfaces(routes: list[dict]) -> list[str]:
    """按 resource 生成 TS interface，忽略无 model 的 resource。"""
    seen: dict[str, dict] = {}
    for r in routes:
        m = r.get("model")
        if isinstance(m, dict) and m and r["resource"] not in seen:
            seen[r["resource"]] = m
    out: list[str] = []
    for resource, model in seen.items():
        name = _model_interface_name(resource)
        lines = [f"export interface {name} {{"]
        for k, v in model.items():
            lines.append(f"  {_ts_key(str(k))}: {_ts_type_from_model_field(v)};")
        lines.append("}")
        out.append("\n".join(lines))
    return out


def _ts_response_type(route: dict) -> str:
    """为一条 route 计算响应类型。

    优先级：
      1. per-endpoint response_model → 生成独立 inline interface 作为 data 类型
      2. resource 级 model（仅当 endpoint 是资源主路径时）→ ModelName / ModelName[]
      3. 从 response 示例值推导类型字面量
    """
    resp = route.get("response")
    if resp is None:
        return "unknown"

    response_model = route.get("response_model") if isinstance(route.get("response_model"), dict) else None
    resource_model = route.get("model") if isinstance(route.get("model"), dict) else None

    if isinstance(resp, dict) and "data" in resp and (response_model or resource_model):
        data_val = resp["data"]
        # 确定用哪个 model 做 data 类型
        if response_model:
            # per-endpoint model：生成 inline interface
            inline_fields = [f"{_ts_key(str(k))}: {_ts_type_from_model_field(v)}" for k, v in response_model.items()]
            data_type_single = "{ " + "; ".join(inline_fields) + " }"
        else:
            data_type_single = _model_interface_name(route["resource"])

        fields = []
        for k, v in resp.items():
            if k == "data":
                if isinstance(data_val, list) and not data_val:
                    if response_model:
                        fields.append(f"{_ts_key(str(k))}: Array<{data_type_single}>")
                    else:
                        fields.append(f"{_ts_key(str(k))}: {data_type_single}[]")
                elif isinstance(data_val, dict) and not data_val:
                    fields.append(f"{_ts_key(str(k))}: {data_type_single}")
                else:
                    fields.append(f"{_ts_key(str(k))}: {_ts_type_from_example(v)}")
            else:
                fields.append(f"{_ts_key(str(k))}: {_ts_type_from_example(v)}")
        return "{ " + "; ".join(fields) + " }"
    return _ts_type_from_example(resp)


def gen_ts_client(routes: list[dict]) -> str:
    lines = [
        f"// {GEN_BANNER}",
        "import { apiFetch } from '../auth';",
        "",
        "export type ApiEnvelope<T = unknown> = { data: T } & Record<string, unknown>;",
        "export function unwrap<T>(res: { data: T }): T { return res.data; }",
        "",
    ]
    interfaces = _gen_model_interfaces(routes)
    for iface in interfaces:
        lines.append(iface)
        lines.append("")
    # 具名响应类型
    for r in routes:
        op = op_name(r)
        resp_ty = _ts_response_type(r)
        lines.append(f"export type {op}Response = {resp_ty};")
    if routes:
        lines.append("")
    lines += [
        "async function request<T>(method: string, path: string, body?: unknown, query?: Record<string, unknown>): Promise<T> {",
        "  let url = path;",
        "  if (query) {",
        "    const qs = new URLSearchParams();",
        "    for (const [k, v] of Object.entries(query)) {",
        "      if (v !== undefined && v !== null) qs.append(k, String(v));",
        "    }",
        "    const s = qs.toString();",
        "    if (s) url += `?${s}`;",
        "  }",
        "  const res = await apiFetch(url, {",
        "    method,",
        "    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),",
        "  });",
        "  if (!res.ok) throw new Error(`${method} ${path} failed: HTTP ${res.status}`);",
        "  const text = await res.text();",
        "  return (text ? JSON.parse(text) : {}) as T;",
        "}",
        "",
    ]
    for r in routes:
        op = op_name(r)
        fn = _camel(op)
        path_params = _ts_path_params(r["path"])
        args = [f"{pp}: string | number" for pp in path_params]
        has_body = bool(r["body"]) or r["method"] in ("POST", "PUT", "PATCH")
        has_query = bool(r["query"])
        if has_body:
            args.append(f"body: {_ts_body_type(r['body'])}")
        if has_query:
            args.append("query?: Record<string, unknown>")
        # 构造运行时 path（替换 {id}）
        ts_path = re.sub(r"\{(\w+)\}", lambda m: "${" + m.group(1) + "}", r["path"])
        ts_path_lit = f"`{ts_path}`" if path_params else f"'{r['path']}'"
        call_args = [json.dumps(r["method"]), ts_path_lit]
        call_args.append("body" if has_body else "undefined")
        if has_query:
            call_args.append("query")
        lines.append(f"/** {r['method']} {r['path']} — {r['summary']} */")
        lines.append(f"export function {fn}<T = {op}Response>({', '.join(args)}): Promise<T> {{")
        lines.append(f"  return request<T>({', '.join(call_args)});")
        lines.append("}")
        lines.append("")
    return "\n".join(lines)


# ── Python typed client 生成 ─────────────────────────────────────────────


def _infer_resource_from_path(path: str) -> str:
    """从 API 路径推导资源名，如 /api/notes/{id} → notes。"""
    skip = ("_internal", "_meta", "page-control", "aime")
    parts = [s for s in path.split("/") if s and s not in ("api",) and not s.startswith("{")]
    if parts and parts[0] in skip:
        return ""
    return parts[0] if parts else ""


def gen_py_client(routes: list[dict]) -> str:
    write_methods = {"POST", "PUT", "PATCH", "DELETE"}
    lines = [
        f"# {GEN_BANNER}",
        '"""command / hook 调用本应用后端接口的 typed 封装（基于 utils.service_client）。',
        '',
        '写操作（POST/PUT/PATCH/DELETE）成功后自动调用 notify_refresh，',
        '通知已打开的前端页面刷新数据。前端自己调用 API 时不经过此层，不会触发多余刷新。',
        '"""',
        "import sys",
        "from pathlib import Path",
        "",
        "sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))",
        "from utils.service_client import call_service, notify_refresh  # noqa: E402",
        "",
    ]
    for r in routes:
        fn = _snake(op_name(r))
        path_params = _ts_path_params(r["path"])
        args = list(path_params)
        has_body = bool(r["body"]) or r["method"] in ("POST", "PUT", "PATCH")
        if has_body:
            args.append("body=None")
        args.append("query=None")
        py_path = re.sub(r"\{(\w+)\}", lambda m: "{" + m.group(1) + "}", r["path"])
        path_expr = f'f"{py_path}"' if path_params else json.dumps(r["path"])
        call_kwargs = [f'method="{r["method"]}"']
        if has_body:
            call_kwargs.append("body=body")
        call_kwargs.append("query=query")
        resource = _infer_resource_from_path(r["path"])
        is_write = r["method"] in write_methods and resource
        lines.append(f'def {fn}({", ".join(args)}) -> dict:')
        lines.append(f'    """{r["method"]} {r["path"]} — {r["summary"]}"""')
        if is_write:
            lines.append(f'    result = call_service({path_expr}, {", ".join(call_kwargs)})')
            lines.append(f'    notify_refresh({json.dumps(resource)})')
            lines.append("    return result")
        else:
            lines.append(f'    return call_service({path_expr}, {", ".join(call_kwargs)})')
        lines.append("")
        lines.append("")
    return "\n".join(lines)


def _snake(s: str) -> str:
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    return s.lower()


# ── JSON references 生成（与 routes_snapshot.go 同构）────────────────────


def _route_public_stripped(r: dict) -> dict:
    item: dict[str, Any] = {
        "method": r["method"],
        "path": r["path"],
        "summary": r["summary"],
        "public": r["public"],
    }
    if r["tags"]:
        item["tags"] = r["tags"]
    if r["request_example"] is not None:
        item["request_example"] = r["request_example"]
    if r["response"] is not None:
        item["response"] = r["response"]
    if r["query"]:
        item["query_params"] = [_json_param(p) for p in r["query"]]
    if r["body"]:
        item["body_params"] = [_json_param(p) for p in r["body"]]
    return item


def _json_param(p: dict) -> dict:
    out: dict[str, Any] = {"name": p["name"]}
    if p["type"]:
        out["type"] = p["type"]
    if p["required"]:
        out["required"] = True
    if p["description"]:
        out["description"] = p["description"]
    return out


def gen_index_json(routes: list[dict], template_version: str) -> dict:
    idx = []
    for r in routes:
        item = {"method": r["method"], "path": r["path"], "summary": r["summary"]}
        if r["tags"]:
            item["tags"] = r["tags"]
        if r.get("response") is not None:
            item["response"] = r["response"]
        idx.append(item)
    return {
        "schema_version": SCHEMA_VERSION,
        "template_version": template_version,
        "generated_at": "",
        "source": "idl-gen",
        "route_count": len(routes),
        "routes": idx,
    }


def gen_details_json(routes: list[dict], template_version: str) -> dict:
    by_key = {f"{r['method']} {r['path']}": _route_public_stripped(r) for r in routes}
    return {
        "schema_version": SCHEMA_VERSION,
        "template_version": template_version,
        "generated_at": "",
        "source": "idl-gen",
        "route_count": len(routes),
        "lookup_hint": '先读 api-routes.index.json 定位接口，再在本文件 grep_search 精确搜索 "METHOD PATH" 附近上下文，例如 "POST /api/items"。',
        "routes_by_key": by_key,
        "refresh_semantics": "generated from app/api IDL; also overwritten by Go service startup",
        "progressive_loading": True,
    }


# ── 落盘与协调 ────────────────────────────────────────────────────────────


def _read_template_version(plugin_dir: Path) -> str:
    meta = plugin_dir / ".template_meta.json"
    try:
        return str(json.loads(meta.read_text(encoding="utf-8")).get("template_version") or "0.0.1")
    except Exception:
        return "0.0.1"


def _cli_skill_dirs(plugin_dir: Path) -> list[Path]:
    skills_dir = plugin_dir / "skills"
    if not skills_dir.exists():
        return []
    return [d for d in sorted(skills_dir.iterdir()) if d.is_dir() and d.name.endswith("-aime-app-cli")]


def build_artifacts(plugin_dir: Path) -> dict[Path, str]:
    """返回 {目标路径: 内容} 映射（不含只在缺失时写的 stub）。"""
    idl = load_idl(plugin_dir)
    routes = normalize_and_validate(idl)
    template_version = _read_template_version(plugin_dir)

    by_resource: dict[str, list[dict]] = {}
    for r in routes:
        by_resource.setdefault(r["resource"], []).append(r)

    artifacts: dict[Path, str] = {}
    server_dir = plugin_dir / "app" / "server-go"
    if server_dir.exists():
        for resource, rs in by_resource.items():
            artifacts[server_dir / f"handler_{_snake(resource)}.gen.go"] = _gofmt(gen_go_register(resource, rs))

    fe_api_dir = plugin_dir / "app" / "frontend" / "src" / "api"
    if (plugin_dir / "app" / "frontend").exists():
        artifacts[fe_api_dir / "client.gen.ts"] = gen_ts_client(routes)

    for skill_dir in _cli_skill_dirs(plugin_dir):
        artifacts[skill_dir / "api_client.gen.py"] = gen_py_client(routes)
        ref_dir = skill_dir / "references"
        artifacts[ref_dir / "api-routes.index.json"] = json.dumps(
            gen_index_json(routes, template_version), indent=2, ensure_ascii=False) + "\n"
        artifacts[ref_dir / "api-routes.details.json"] = json.dumps(
            gen_details_json(routes, template_version), indent=2, ensure_ascii=False) + "\n"

    return artifacts


def stub_artifacts(plugin_dir: Path) -> dict[Path, str]:
    """只在文件不存在时写入的 handler stub。"""
    idl = load_idl(plugin_dir)
    routes = normalize_and_validate(idl)
    by_resource: dict[str, list[dict]] = {}
    for r in routes:
        by_resource.setdefault(r["resource"], []).append(r)
    out: dict[Path, str] = {}
    server_dir = plugin_dir / "app" / "server-go"
    if server_dir.exists():
        for resource, rs in by_resource.items():
            out[server_dir / f"handler_{_snake(resource)}.go"] = _gofmt(gen_go_handler_stub(resource, rs))
    return out


def _append_missing_stubs(handler_path: Path, plugin_dir: Path) -> int:
    """扫描已有 handler 文件，为 IDL 中新增但文件中缺失的函数追加 stub。返回追加数量。"""
    existing_src = handler_path.read_text(encoding="utf-8")
    existing_funcs = set(re.findall(r'^func\s+(\w+)\s*\(', existing_src, re.MULTILINE))

    resource = handler_path.stem.removeprefix("handler_")
    idl = load_idl(plugin_dir)
    routes = normalize_and_validate(idl)
    resource_routes = [r for r in routes if _snake(r["resource"]) == resource]

    missing = []
    for r in resource_routes:
        fn = _go_ident(op_name(r))
        if fn not in existing_funcs:
            missing.append((fn, r))

    if not missing:
        return 0

    lines = ["", "// ── 以下由 gen_api.py 自动追加（IDL 新增接口） ──"]
    for fn, r in missing:
        resp = r["response"] if r["response"] is not None else {"data": None}
        lines.append("")
        lines.append(f'// {fn} 处理 {r["method"]} {r["path"]}：{r["summary"]}')
        lines.append(f"func {fn}(w http.ResponseWriter, r *http.Request) {{")
        lines.append("\t// TODO(Agent B): 替换为真实业务逻辑（读写 store、校验参数等）。")
        lines.append(f"\twriteJSON(w, http.StatusOK, {_go_lit(resp, 2)})")
        lines.append("}")

    appended_src = existing_src.rstrip() + "\n" + "\n".join(lines) + "\n"
    handler_path.write_text(appended_src, encoding="utf-8")
    print(f"  ✓ 追加 {len(missing)} 个 stub 到 {handler_path.name}：{', '.join(fn for fn, _ in missing)}")
    return len(missing)


def _is_json_reference(path: Path) -> bool:
    return path.name in ("api-routes.index.json", "api-routes.details.json")


def _routes_json_matches(expected: str, actual_path: Path) -> bool:
    """比较渐进式 API 引用，兼容服务启动写入的内置路由快照。

    ``gen_api.py`` 生成的引用只包含 IDL 声明的业务路由；Go 服务启动后会在同
    一位置写入完整运行时注册表，其中还包括模板内置的 ``/api/me``、``/api/_meta``
    等路由。运行时快照因此可以是 IDL 的超集，但绝不能丢失或改写任一 IDL 路由。
    非运行时来源仍保持严格全量比较，避免把普通生成产物漂移放过。
    """
    try:
        exp = json.loads(expected)
        act = json.loads(actual_path.read_text(encoding="utf-8"))
    except Exception:
        return False

    actual_source = act.get("source")
    for d in (exp, act):
        d.pop("generated_at", None)
        d.pop("source", None)
        d.pop("refresh_semantics", None)

    if actual_source != "server-startup":
        return exp == act

    for key, value in exp.items():
        if key in {"route_count", "routes", "routes_by_key"}:
            continue
        if act.get(key) != value:
            return False

    if "routes" in exp:
        expected_routes = {
            (route.get("method"), route.get("path")): route
            for route in exp.get("routes", [])
            if isinstance(route, dict)
        }
        actual_routes = {
            (route.get("method"), route.get("path")): route
            for route in act.get("routes", [])
            if isinstance(route, dict)
        }
    elif "routes_by_key" in exp:
        expected_routes = exp.get("routes_by_key", {})
        actual_routes = act.get("routes_by_key", {})
    else:
        return False

    if not isinstance(expected_routes, dict) or not isinstance(actual_routes, dict):
        return False
    return all(actual_routes.get(key) == route for key, route in expected_routes.items())


def run(plugin_dir: Path, check: bool) -> int:
    artifacts = build_artifacts(plugin_dir)

    if check:
        stale = []
        for path, content in artifacts.items():
            if _is_json_reference(path):
                # references JSON 由服务启动合法覆盖（仅 generated_at/source 变），做语义比较。
                if not path.exists() or not _routes_json_matches(content, path):
                    stale.append(path)
            elif not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        if stale:
            print("[gen_api] 以下生成产物与 IDL 不一致，请重新运行 gen_api.py：", file=sys.stderr)
            for p in stale:
                print(f"  - {p.relative_to(plugin_dir)}", file=sys.stderr)
            return 1
        print(f"[gen_api] 全部 {len(artifacts)} 个产物与 IDL 一致。")
        return 0

    written = 0
    written_files: list[Path] = []
    for path, content in artifacts.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            path.write_text(content, encoding="utf-8")
            written += 1
            written_files.append(path)

    stub_written = 0
    stub_appended = 0
    for path, content in stub_artifacts(plugin_dir).items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            stub_written += 1
            written_files.append(path)
        else:
            appended = _append_missing_stubs(path, plugin_dir)
            stub_appended += appended
            if appended:
                written_files.append(path)

    # 清理 IDL 中已不存在的旧 resource 的产物
    removed_files: list[Path] = []
    server_dir = plugin_dir / "app" / "server-go"
    if server_dir.exists():
        for gen_file in sorted(server_dir.glob("handler_*.gen.go")):
            if gen_file not in artifacts:
                gen_file.unlink()
                removed_files.append(gen_file)
                stub_file = server_dir / gen_file.name.replace(".gen.go", ".go")
                if stub_file.exists():
                    stub_file.unlink()
                    removed_files.append(stub_file)

    # 输出产物清单
    print(f"[gen_api] 生成完成：{written} 个产物更新，{stub_written} 个 stub 新建。")
    if written_files:
        print("  生成/更新：")
        for p in written_files:
            print(f"    {p.relative_to(plugin_dir)}")
    if removed_files:
        print("  已删除（资源从 IDL 移除）：")
        for p in removed_files:
            print(f"    {p.relative_to(plugin_dir)}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="从 app/api IDL 生成四端接口产物")
    parser.add_argument("plugin_dir", help="插件根目录（含 app/api/api.yaml）")
    parser.add_argument("--check", action="store_true", help="仅校验产物是否最新，不写文件（CI/verify 用）")
    args = parser.parse_args(argv)

    plugin_dir = Path(args.plugin_dir).expanduser().resolve()
    if not plugin_dir.exists():
        print(f"[gen_api] 插件目录不存在: {plugin_dir}", file=sys.stderr)
        return 2
    try:
        return run(plugin_dir, args.check)
    except IDLError as exc:
        print(f"[gen_api] IDL 错误: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
