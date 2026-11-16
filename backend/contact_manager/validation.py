"""校验 JSON 与 Excel 共用的联系人数据。"""

import re
from typing import Any

METHOD_TYPES = ("phone", "email", "social", "address")
WRITABLE_FIELDS = {"name", "notes", "favorite", "methods"}
INVALID_CHARACTERS = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]"
)
PHONE_PATTERN = re.compile(r"[0-9+() .-]+")
ASCII_DIGIT = re.compile(r"[0-9]")
EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def normalize_newlines(value: str) -> str:
    """把 Windows 和旧式换行转换为 LF，保留其他字符。"""
    return value.replace("\r\n", "\n").replace("\r", "\n")


def has_invalid_characters(value: str) -> bool:
    """检查原始文本是否含无效 Unicode 码点或 Excel 禁止的控制字符。"""
    return INVALID_CHARACTERS.search(value) is not None


def validate_contact(
    payload: object, *, partial: bool = False
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """校验联系人对象，返回规范化后的字段和可定位的错误列表。"""
    if not isinstance(payload, dict):
        return {}, [{"message": "联系人数据必须是 JSON 对象。"}]
    if partial and not payload:
        return {}, [{"message": "编辑时至少提供一个可写字段。"}]

    data: dict[str, Any] = {}
    errors = [
        {"field": field, "message": "此字段不存在或不可写。"}
        for field in payload
        if field not in WRITABLE_FIELDS
    ]

    if "name" not in payload and not partial:
        errors.append({"field": "name", "message": "姓名不能为空。"})
    if "name" in payload:
        name, error = _normalize_text(payload["name"], "姓名", 100)
        if error is not None:
            errors.append({"field": "name", "message": error})
        else:
            data["name"] = name

    if "notes" in payload:
        notes, error = _normalize_text(
            payload["notes"], "备注", 2000, multiline=True
        )
        if error is not None:
            errors.append({"field": "notes", "message": error})
        else:
            data["notes"] = notes
    elif not partial:
        data["notes"] = ""

    if "favorite" in payload:
        if isinstance(payload["favorite"], bool):
            data["favorite"] = payload["favorite"]
        else:
            errors.append({"field": "favorite", "message": "收藏状态必须是布尔值。"})
    elif not partial:
        data["favorite"] = False

    if "methods" in payload:
        data["methods"], method_errors = _validate_methods(payload["methods"])
        errors.extend(method_errors)
    elif not partial:
        data["methods"] = []

    return data, errors


def _normalize_text(
    value: object, label: str, max_length: int, *, multiline: bool = False
) -> tuple[str, str | None]:
    """先检查原始文本，再按字段规则整理空白、换行和长度。"""
    if not isinstance(value, str):
        return "", f"{label}必须是文本。"
    if has_invalid_characters(value):
        return "", f"{label}包含无效字符。"

    if multiline:
        text = normalize_newlines(value)
    else:
        text = value.strip()
        if not text:
            return "", f"{label}不能为空。"
        if "\r" in text or "\n" in text:
            return "", f"{label}不能包含换行。"

    if len(text) > max_length:
        return "", f"{label}最多包含 {max_length} 个字符。"
    return text, None


def _validate_methods(
    payload: object,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """校验联系方式数组，并检查单个类别的数量上限和重复值。"""
    if not isinstance(payload, list):
        return [], [{"field": "methods", "message": "联系方式必须是数组。"}]

    methods = []
    errors = []
    counts: dict[str, int] = {}
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(payload):
        field = f"methods[{index}]"
        method, method_errors = _validate_method(item, field)
        errors.extend(method_errors)
        if method is None:
            continue

        method_type, value = method["type"], method["value"]
        counts[method_type] = counts.get(method_type, 0) + 1
        if counts[method_type] > 20:
            errors.append({"field": field, "message": "同一类型最多保存 20 条。"})
        if (method_type, value) in seen:
            errors.append(
                {"field": f"{field}.value", "message": "同一类型的值不能重复。"}
            )
        else:
            seen.add((method_type, value))
            methods.append(method)

    return methods, errors


def _validate_method(
    item: object, field: str
) -> tuple[dict[str, str] | None, list[dict[str, str]]]:
    """校验一条联系方式的字段、类别和具体格式。"""
    if not isinstance(item, dict) or set(item) != {"type", "value"}:
        return None, [{"field": field, "message": "每条联系方式只能包含 type 和 value。"}]

    method_type = item["type"]
    if not isinstance(method_type, str) or method_type not in METHOD_TYPES:
        return None, [{"field": f"{field}.type", "message": "联系方式类型无效。"}]

    value, error = _normalize_text(item["value"], "联系方式", 500)
    if error is None and method_type == "phone":
        if not PHONE_PATTERN.fullmatch(value) or not ASCII_DIGIT.search(value):
            error = "电话号码格式无效，必须包含至少一个数字。"
    if error is None and method_type == "email":
        if not EMAIL_PATTERN.fullmatch(value):
            error = "邮箱格式无效。"
    if error is not None:
        return None, [{"field": f"{field}.value", "message": error}]
    return {"type": method_type, "value": value}, []
