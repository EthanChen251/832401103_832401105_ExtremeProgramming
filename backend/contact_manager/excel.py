"""读取和生成 API 约定的通讯录工作簿。"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any, BinaryIO
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile
from zlib import error as CompressionError

from openpyxl import Workbook, load_workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.cell.read_only import EmptyCell, ReadOnlyCell
from openpyxl.utils import get_column_letter
from openpyxl.utils.exceptions import InvalidFileException

from .validation import (
    METHOD_TYPES,
    has_invalid_characters,
    normalize_newlines,
    validate_contact,
)

if TYPE_CHECKING:
    from openpyxl.worksheet._write_only import WriteOnlyWorksheet

SHEET_NAME = "Contacts"
METHOD_COLUMNS = {
    "phones": "phone",
    "emails": "email",
    "socials": "social",
    "addresses": "address",
}
HEADERS = ("name", "notes", "favorite", *METHOD_COLUMNS)
MAX_CONTACT_ROWS = 1_048_575
WORKBOOK_PARSE_ERRORS = (
    BadZipFile,
    CompressionError,
    EOFError,
    InvalidFileException,
    LookupError,
    OSError,
    OverflowError,
    ParseError,
    SyntaxError,
    TypeError,
    ValueError,
)


def read_workbook(
    stream: BinaryIO,
) -> tuple[list[dict[str, Any]], list[dict[str, int | str]]]:
    """读取并校验 Contacts 工作表，返回联系人和按行列定位的错误。"""
    workbook = None
    try:
        workbook = load_workbook(
            stream, read_only=True, data_only=False, keep_links=False
        )
        sheet = next(
            (item for item in workbook.worksheets if item.title == SHEET_NAME),
            None,
        )
        if sheet is None:
            return [], [{"message": "缺少 Contacts 工作表。"}]

        # 按实际存在的单元格读取，以便检查表头之外是否还有数据。
        sheet.reset_dimensions()
        rows = sheet.iter_rows()
        errors = _validate_header(next(rows, ()))
        if errors:
            return [], errors

        contacts = []
        for row_number, cells in enumerate(rows, start=2):
            contact, row_errors = _parse_row(row_number, cells)
            errors.extend(row_errors)
            if contact is not None:
                contacts.append(contact)
        return ([], errors) if errors else (contacts, [])
    except WORKBOOK_PARSE_ERRORS:
        return [], [{"message": "无法读取该 XLSX 工作簿。"}]
    finally:
        if workbook is not None:
            workbook.close()


def _validate_header(
    cells: tuple[ReadOnlyCell | EmptyCell, ...],
) -> list[dict[str, int | str]]:
    """校验 A1:G1 的列名、顺序以及表头之后的单元格。"""
    errors: list[dict[str, int | str]] = []
    for index, header in enumerate(HEADERS):
        if index >= len(cells) or cells[index].value != header:
            errors.append(
                {"row": 1, "field": header, "message": f"表头必须为 {header}。"}
            )
    extra_error = _extra_column_error(1, cells)
    if extra_error is not None:
        errors.append(extra_error)
    return errors


def _extra_column_error(
    row_number: int, cells: tuple[ReadOnlyCell | EmptyCell, ...]
) -> dict[str, int | str] | None:
    """报告第一个超出 G 列且有内容的单元格。"""
    for index, cell in enumerate(cells[len(HEADERS):], start=len(HEADERS) + 1):
        if cell.value not in (None, ""):
            return {
                "row": row_number,
                "field": get_column_letter(index),
                "message": "G 列右侧不能包含数据。",
            }
    return None


def _parse_row(
    row_number: int, cells: tuple[ReadOnlyCell | EmptyCell, ...]
) -> tuple[dict[str, Any] | None, list[dict[str, int | str]]]:
    """解析一行数据，并将共用校验器的字段路径转换为 Excel 列名。"""
    errors: list[dict[str, int | str]] = []
    extra_error = _extra_column_error(row_number, cells)
    if extra_error is not None:
        errors.append(extra_error)
    data_cells = cells[:len(HEADERS)]
    if all(cell.value in (None, "") for cell in data_cells):
        return None, errors

    payload: dict[str, Any] = {
        "name": "",
        "notes": "",
        "favorite": False,
        "methods": [],
    }
    method_columns = []
    invalid_columns = set()
    for header, cell in zip(HEADERS, data_cells):
        value = cell.value
        message = None
        if cell.data_type in ("f", "e"):
            message = "不接受公式或 Excel 错误值。"
        elif value is None:
            continue
        elif header == "favorite":
            favorite = _parse_favorite(value)
            if favorite is None:
                message = "收藏状态必须是布尔值、TRUE、FALSE 或空白。"
            else:
                payload[header] = favorite
        elif not isinstance(value, str):
            message = "请将原值以文本格式重新录入。"
        elif header in METHOD_COLUMNS:
            if has_invalid_characters(value):
                message = "联系方式包含无效字符。"
            else:
                for part in normalize_newlines(value).split("\n"):
                    if part.strip():
                        payload["methods"].append(
                            {"type": METHOD_COLUMNS[header], "value": part}
                        )
                        method_columns.append(header)
        else:
            payload[header] = value

        if message is not None:
            invalid_columns.add(header)
            errors.append(
                {"row": row_number, "field": header, "message": message}
            )

    contact, validation_errors = validate_contact(payload)
    for issue in validation_errors:
        field = issue["field"]
        if field.startswith("methods["):
            index = int(field.split("[", 1)[1].split("]", 1)[0])
            field = method_columns[index]
        if field not in invalid_columns:
            errors.append(
                {
                    "row": row_number,
                    "field": field,
                    "message": issue["message"],
                }
            )
    return (None, errors) if errors else (contact, [])


def _parse_favorite(value: object) -> bool | None:
    """转换收藏列的布尔值或文本，返回 None 表示格式无效。"""
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and not has_invalid_characters(value):
        text = value.strip().upper()
        if text == "TRUE":
            return True
        if text in ("", "FALSE"):
            return False
    return None


def build_workbook(contacts: list[dict[str, Any]], *, template: bool = False) -> BytesIO:
    """按约定表头写出通讯录，返回已定位到开头的 XLSX 数据流。"""
    workbook = Workbook(write_only=True)
    sheet = workbook.create_sheet(SHEET_NAME)
    if template:
        for index, header in enumerate(HEADERS, start=1):
            column = sheet.column_dimensions[get_column_letter(index)]
            column.width = 18 if header == "favorite" else 28
            if header != "favorite":
                column.number_format = "@"
    sheet.append(HEADERS)
    for contact in contacts:
        _write_contact_row(sheet, contact)

    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return stream


def _write_contact_row(
    sheet: WriteOnlyWorksheet, contact: dict[str, Any]
) -> None:
    """写入单个联系人，保持布尔类型并将联系方式和值明确标记为文本。"""
    methods: dict[str, list[str]] = {kind: [] for kind in METHOD_TYPES}
    for method in contact["methods"]:
        methods[method["type"]].append(method["value"])

    values = [
        contact["name"],
        contact["notes"] or None,
        contact["favorite"],
        *("\n".join(methods[kind]) or None for kind in METHOD_TYPES),
    ]
    row = []
    for value in values:
        if isinstance(value, str):
            cell = WriteOnlyCell(sheet, value=value)
            cell.data_type = "s"
            cell.number_format = "@"
            row.append(cell)
        else:
            row.append(value)
    sheet.append(row)
