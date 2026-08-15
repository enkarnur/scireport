"""HTTP 响应读取工具 — 自动处理网关 gzip 压缩"""
import gzip
import json


def safe_read_response(resp):
    """读取 HTTP 响应体，自动处理 gzip 编码（泛域名网关对较大响应会自动 gzip）"""
    raw = resp.read()
    encoding = resp.headers.get('Content-Encoding', '')
    if encoding == 'gzip' or (len(raw) >= 2 and raw[:2] == b'\x1f\x8b'):
        raw = gzip.decompress(raw)
    return raw.decode('utf-8')


def safe_json_response(resp):
    """读取 HTTP 响应体并解析为 JSON，自动处理 gzip"""
    text = safe_read_response(resp)
    return json.loads(text) if text else {}
