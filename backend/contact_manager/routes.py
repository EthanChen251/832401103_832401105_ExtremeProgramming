"""提供通讯录 REST 路由和统一的 API 错误响应。"""

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, NoReturn

from flask import Blueprint, Response, g, jsonify, request, send_file, url_for
from werkzeug.exceptions import HTTPException, InternalServerError

from . import db, excel
from .accounts import current_user
from .validation import validate_contact

api = Blueprint("contacts", __name__, url_prefix="/api/v1/contacts")
CONTACT_PATH = "/<int(min=1,max=9007199254740991):contact_id>"
XLSX_MIMETYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
HTTP_ERRORS = {
    400: ("BAD_REQUEST", "请求格式无效。"),
    404: ("NOT_FOUND", "联系人或 API 路径不存在。"),
    405: ("METHOD_NOT_ALLOWED", "此 API 路径不支持该请求方法。"),
    415: ("UNSUPPORTED_MEDIA_TYPE", "请求的媒体类型不受支持。"),
}


@api.before_request
def require_account():
    g.user = current_user()
    if g.user is None:
        return _error_response(401, "UNAUTHORIZED", "请先登录。")


@api.after_request
def private_response(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@api.get("")
def list_contacts() -> Response:
    """按 ID 升序列出联系人，并支持收藏状态筛选。"""
    filters = request.args.getlist("favorite")
    if len(filters) > 1 or (filters and filters[0] not in ("true", "false")):
        return _error_response(
            400, "BAD_REQUEST", "favorite 必须是 true 或 false。"
        )

    favorite = filters[0] == "true" if filters else None
    return jsonify(items=db.select_contacts(favorite=favorite))


@api.post("")
def create_contact() -> Response:
    """校验新联系人，写入数据库并返回新资源及其 Location。"""
    data, error = _read_json()
    if error is not None:
        return error

    contact = db.create_contact(data)
    response = jsonify(contact)
    response.status_code = 201
    response.headers["Location"] = url_for(
        "contacts.get_contact", contact_id=contact["id"]
    )
    return response


@api.get(CONTACT_PATH)
def get_contact(contact_id: int) -> Response:
    """返回指定联系人的完整信息或资源不存在的错误。"""
    contacts = db.select_contacts(contact_id=contact_id)
    if not contacts:
        return _error_response(404, "NOT_FOUND", "联系人不存在。")
    return jsonify(contacts[0])


@api.patch(CONTACT_PATH)
def update_contact(contact_id: int) -> Response:
    """修改提交的字段，并在提交 methods 时整体替换联系方式。"""
    data, error = _read_json(partial=True)
    if error is not None:
        return error

    contact = db.update_contact(contact_id, data)
    if contact is None:
        return _error_response(404, "NOT_FOUND", "联系人不存在。")
    return jsonify(contact)


@api.delete(CONTACT_PATH)
def delete_contact(contact_id: int) -> Response:
    """删除联系人及其联系方式，成功时返回无响应体的 204。"""
    if not db.delete_contact(contact_id):
        return _error_response(404, "NOT_FOUND", "联系人不存在。")
    return Response(status=204)


@api.post("/import")
def import_contacts() -> Response:
    """校验上传的 XLSX 文件，整批追加通过校验的联系人。"""
    if request.mimetype != "multipart/form-data":
        return _error_response(
            415,
            "UNSUPPORTED_MEDIA_TYPE",
            "请使用 multipart/form-data 上传文件。",
        )

    files = request.files.getlist("file")
    if (
        len(files) != 1
        or len(request.files) != 1
        or request.form.getlist("file")
    ):
        return _error_response(400, "BAD_REQUEST", "请在 file 字段上传一个文件。")
    upload = files[0]
    if not upload.filename:
        return _error_response(400, "BAD_REQUEST", "未选择上传文件。")
    if Path(upload.filename).suffix.lower() != ".xlsx":
        return _error_response(415, "UNSUPPORTED_MEDIA_TYPE", "只接受 .xlsx 文件。")

    contacts, errors = excel.read_workbook(upload.stream)
    if errors:
        return _error_response(
            422, "INVALID_WORKBOOK", "工作簿校验失败，未导入任何联系人。", errors
        )
    return jsonify(imported_count=db.insert_contacts(contacts))


@api.get("/export")
def export_contacts() -> Response:
    """从一次数据库查询生成整个通讯录的 XLSX 文件。"""
    contacts = db.select_contacts()
    if len(contacts) > excel.MAX_CONTACT_ROWS:
        return _error_response(
            422, "EXPORT_LIMIT_EXCEEDED", "联系人数超出一个 Excel 工作表的容纳上限。"
        )

    stream = excel.build_workbook(contacts)
    return send_file(
        stream,
        mimetype=XLSX_MIMETYPE,
        as_attachment=True,
        download_name="contacts.xlsx",
        conditional=False,
    )


@api.get("/template")
def download_template() -> Response:
    return send_file(
        excel.build_workbook([], template=True),
        mimetype=XLSX_MIMETYPE,
        as_attachment=True,
        download_name="contacts-template.xlsx",
        conditional=False,
    )


def _read_json(
    *, partial: bool = False
) -> tuple[dict[str, Any], Response | None]:
    """读取 JSON 请求，分别报告媒体类型、语法和业务字段错误。"""
    if request.mimetype != "application/json":
        return {}, _error_response(
            415,
            "UNSUPPORTED_MEDIA_TYPE",
            "请使用 application/json 提交数据。",
        )
    try:
        payload = json.loads(
            request.get_data(), parse_constant=_reject_json_constant
        )
    except (ValueError, RecursionError):
        return {}, _error_response(400, "BAD_REQUEST", "JSON 语法错误。")

    data, errors = validate_contact(payload, partial=partial)
    if errors:
        return {}, _error_response(
            422, "VALIDATION_ERROR", "联系人数据校验失败。", errors
        )
    return data, None


def _reject_json_constant(value: str) -> NoReturn:
    """拒绝 Python JSON 解析器额外接受的 NaN 和 Infinity。"""
    raise ValueError(f"Invalid JSON constant: {value}")


def _error_response(
    status: int,
    code: str,
    message: str,
    details: Sequence[Mapping[str, int | str]] = (),
) -> Response:
    """生成包含错误代码、消息和详情的标准 JSON 响应。"""
    response = jsonify(
        error={"code": code, "message": message, "details": list(details)}
    )
    response.status_code = status
    return response


@api.app_errorhandler(HTTPException)
def _handle_http_error(error: HTTPException) -> Response:
    """将 Flask 路由和请求错误转为 JSON，并为 405 保留 Allow 响应头。"""
    status = error.code or 500
    code, message = HTTP_ERRORS.get(status, ("HTTP_ERROR", "请求无法完成。"))
    response = _error_response(status, code, message)
    if status == 405:
        allowed = error.get_response().headers.get("Allow")
        if allowed is not None:
            response.headers["Allow"] = allowed
    return response


@api.app_errorhandler(500)
def _handle_internal_error(_error: InternalServerError) -> Response:
    """返回不包含内部异常和文件路径的 500 响应。"""
    return _error_response(500, "INTERNAL_ERROR", "服务器处理请求时发生错误。")
