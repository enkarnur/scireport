# CODE GENERATED FROM app/api/api.yaml BY tools/gen_api.py — DO NOT EDIT
"""command / hook 调用本应用后端接口的 typed 封装（基于 utils.service_client）。

写操作（POST/PUT/PATCH/DELETE）成功后自动调用 notify_refresh，
通知已打开的前端页面刷新数据。前端自己调用 API 时不经过此层，不会触发多余刷新。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from utils.service_client import call_service, notify_refresh  # noqa: E402

def annotations_list(query=None) -> dict:
    """GET /api/annotations — 按论文、关键词或页码检索批注"""
    return call_service("/api/annotations", method="GET", query=query)


def annotations_create(body=None, query=None) -> dict:
    """POST /api/annotations — 为论文创建可定位批注"""
    result = call_service("/api/annotations", method="POST", body=body, query=query)
    notify_refresh("annotations")
    return result


def annotations_by_annotation_id_delete(annotationId, query=None) -> dict:
    """DELETE /api/annotations/{annotationId} — 删除批注"""
    result = call_service(f"/api/annotations/{annotationId}", method="DELETE", query=query)
    notify_refresh("annotations")
    return result


def annotations_by_annotation_id_get(annotationId, query=None) -> dict:
    """GET /api/annotations/{annotationId} — 获取单条批注及论文定位信息"""
    return call_service(f"/api/annotations/{annotationId}", method="GET", query=query)


def annotations_by_annotation_id_update(annotationId, body=None, query=None) -> dict:
    """PUT /api/annotations/{annotationId} — 更新批注内容与定位信息"""
    result = call_service(f"/api/annotations/{annotationId}", method="PUT", body=body, query=query)
    notify_refresh("annotations")
    return result


def papers_list(query=None) -> dict:
    """GET /api/papers — 检索并分页列出文献库论文"""
    return call_service("/api/papers", method="GET", query=query)


def papers_create(body=None, query=None) -> dict:
    """POST /api/papers — 将浏览器本地提取的 PDF 文本与元数据入库并启动结构化研析"""
    result = call_service("/api/papers", method="POST", body=body, query=query)
    notify_refresh("papers")
    return result


def papers_by_paper_id_delete(paperId, query=None) -> dict:
    """DELETE /api/papers/{paperId} — 删除论文及其关联批注"""
    result = call_service(f"/api/papers/{paperId}", method="DELETE", query=query)
    notify_refresh("papers")
    return result


def papers_by_paper_id_get(paperId, query=None) -> dict:
    """GET /api/papers/{paperId} — 获取论文详情、结构化研析内容与页级定位文本"""
    return call_service(f"/api/papers/{paperId}", method="GET", query=query)


def qa_ask_create(body=None, query=None) -> dict:
    """POST /api/qa/ask — 在全部或指定论文范围内问答并返回可核验定位线索"""
    result = call_service("/api/qa/ask", method="POST", body=body, query=query)
    notify_refresh("qa")
    return result


def reports_list(query=None) -> dict:
    """GET /api/reports — 分页查询系统文献汇报记录"""
    return call_service("/api/reports", method="GET", query=query)


def reports_create(body=None, query=None) -> dict:
    """POST /api/reports — 按模板和论文范围生成系统文献汇报"""
    result = call_service("/api/reports", method="POST", body=body, query=query)
    notify_refresh("reports")
    return result


def reports_by_report_id_get(reportId, query=None) -> dict:
    """GET /api/reports/{reportId} — 获取报告生成状态、模板化章节与引用线索"""
    return call_service(f"/api/reports/{reportId}", method="GET", query=query)


def reports_by_report_id_export_create(reportId, body=None, query=None) -> dict:
    """POST /api/reports/{reportId}/export — 将已完成报告导出为 Word DOCX"""
    result = call_service(f"/api/reports/{reportId}/export", method="POST", body=body, query=query)
    notify_refresh("reports")
    return result

