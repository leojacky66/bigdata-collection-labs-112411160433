"""实验二第三阶段：读取 CSV 并写入 MySQL。仅在取得真实采集数据后运行。"""
import csv
import os
from getpass import getpass
from pathlib import Path

FIELDS = ("title", "house", "address", "struct", "area", "floor", "maketime", "price")
CSV_PATH = Path(__file__).parent / "data" / "houseinfo.csv"


def read_records(path):
    """读取并按 8 个字段去重，不改变字段文字。"""
    records, seen = [], set()
    with Path(path).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("CSV 表头与规定的 8 个字段不一致")
        for row in reader:
            if None in row or any(row[field] is None for field in FIELDS):
                raise ValueError("CSV 存在字段数量不正确的行")
            record = tuple(row[field] for field in FIELDS)
            if record not in seen:
                records.append(record)
                seen.add(record)
    if not records:
        raise ValueError("CSV 没有数据，停止入库")
    return records


def import_records(connection, records):
    """比较现有的 8 字段记录，插入不存在的记录并提交。"""
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM houseinfo")
        before = cursor.fetchone()[0]
        cursor.execute("SELECT title, house, address, `struct`, area, floor, maketime, price FROM houseinfo")
        existing = set(cursor.fetchall())
        pending = []
        for record in records:
            if record not in existing:
                pending.append(record)
                existing.add(record)
        if pending:
            cursor.executemany(
                "INSERT INTO houseinfo (title, house, address, `struct`, area, floor, maketime, price) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", pending
            )
        connection.commit()
        cursor.execute("SELECT COUNT(*) FROM houseinfo")
        return before, len(pending), cursor.fetchone()[0]
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def main():
    import pymysql
    records = read_records(CSV_PATH)
    password = os.environ.get("LAB02_MYSQL_PASSWORD") or getpass("MySQL 密码：")
    connection = pymysql.connect(host=os.environ.get("LAB02_MYSQL_HOST", "127.0.0.1"),
                                 port=3306, user="student", password=password,
                                 database="smartpark_lab", charset="utf8mb4", autocommit=False)
    try:
        before, inserted, after = import_records(connection, records)
        print(f"CSV 去重后：{len(records)} 条；入库前：{before} 条；新增：{inserted} 条；入库后：{after} 条")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
