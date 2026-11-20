"""将实验三的三份原始 CSV 一起脱敏。可在 Notebook 中导入 export_public。"""

import csv
import hashlib
import hmac
import os
import secrets
import shutil
import tempfile
from pathlib import Path


BASIC = ("发件人", "邮箱", "主题", "时间")
PAGES = ("邮件ID",) + BASIC
DETAILS = PAGES + ("正文", "附件文件")
TABLES = {
    "mail_basic": BASIC,
    "mail_pages": PAGES,
    "mail_details": DETAILS,
}
PREFIX = {"邮件ID": "邮件", "发件人": "发件人", "邮箱": "邮箱", "主题": "主题", "时间": "时间"}


def _read_table(directory, table, columns):
    try:
        with (directory / f"{table}.csv").open(encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file, strict=True)
            if tuple(next(reader, ())) != columns:
                raise ValueError(f"{table} 表头与要求的 {len(columns)} 列不一致。")
            rows = []
            seen_ids = set()
            for number, row in enumerate(reader, start=1):
                if len(row) != len(columns):
                    raise ValueError(f"{table} 第 {number} 条记录的字段数不正确。")
                if columns[0] == "邮件ID":
                    if not row[0].strip() or row[0] in seen_ids:
                        raise ValueError(f"{table} 第 {number} 条记录的邮件代号为空或重复。")
                    seen_ids.add(row[0])
                rows.append(row)
            return rows
    except (csv.Error, UnicodeError):
        raise ValueError(f"{table} 不是格式正确的 UTF-8 CSV。") from None
    except OSError:
        raise ValueError(f"无法读取 {table} 原始表。") from None


def _private_key(directory):
    # 密钥只随原始数据保留。同一密钥使代号在重跑、换序和跨表时保持一致。
    path = directory / ".pseudonym-key"
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "wb") as file:
            file.write(secrets.token_bytes(32))
    except FileExistsError:
        pass
    key = path.read_bytes()
    if len(key) != 32:
        raise ValueError("本地脱敏密钥不完整。请检查私有数据目录。")
    return key


def _mask(column, value, key):
    if value == "":
        return ""
    if column == "正文":
        return f"正文 {len(value)} 字符"
    if column == "附件文件":
        return "有附件"
    # 每列使用独立命名空间。即使原值很短或不是有效邮箱也不回显。
    payload = (column + "\0" + value).encode("utf-8")
    tag = hmac.new(key, payload, hashlib.sha256).hexdigest()[:20]
    return f"{PREFIX[column]}-{tag}"


def _publish(tables, public_dir, key):
    public_dir.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=".lab03-export-", dir=public_dir.parent))
    staged, backup = work / "new", work / "old"
    try:
        if public_dir.exists():
            # data/ 中原有的 README 等也随目录保留。
            shutil.copytree(public_dir, staged, symlinks=True)
        else:
            staged.mkdir()
        for table, columns in TABLES.items():
            target = staged / f"{table}_public.csv"
            target.unlink(missing_ok=True)
            with target.open("w", encoding="utf-8-sig", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(columns)
                for row in tables[table]:
                    writer.writerow(_mask(column, value, key) for column, value in zip(columns, row))
        if public_dir.exists():
            public_dir.rename(backup)
        try:
            staged.rename(public_dir)
        except OSError:
            if backup.exists() and not public_dir.exists():
                backup.rename(public_dir)
            raise
    finally:
        # 如果系统同时阻止发布与回滚，留下完整旧版供本地恢复。
        if public_dir.exists() or not backup.exists():
            shutil.rmtree(work, ignore_errors=True)


def export_public(private_dir="private_data", public_dir="data"):
    """校验全部源表，发布三份公开 CSV，返回 {公开文件名: 记录数}。"""
    private_dir, public_dir = Path(private_dir).resolve(), Path(public_dir).resolve()
    if private_dir == public_dir or private_dir in public_dir.parents or public_dir in private_dir.parents:
        raise ValueError("原始数据目录与公开数据目录必须独立。")
    # 长邮件正文可能超出 CSV 模块默认的 128 KiB 字段上限。
    old_limit = csv.field_size_limit()
    try:
        csv.field_size_limit(max(old_limit, 2**31 - 1))
        tables = {table: _read_table(private_dir, table, cols) for table, cols in TABLES.items()}
    finally:
        csv.field_size_limit(old_limit)
    try:
        _publish(tables, public_dir, _private_key(private_dir))
    except OSError:
        raise ValueError("导出未完成。请检查本地文件是否可读写、关闭占用公开目录的程序后重试。") from None
    return {f"{table}_public.csv": len(rows) for table, rows in tables.items()}


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    try:
        counts = export_public(base / "private_data", base / "data")
    except ValueError as error:
        raise SystemExit(str(error)) from None
    for filename, count in counts.items():
        print(f"{filename}  {count} 条")
