"""实验二：解析用户提供的教学网页；支持在线采集，遇验证页立即停止。"""
import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

FIELDS = ("title", "house", "address", "struct", "area", "floor", "maketime", "price")
BASE_URL = "https://www.bspider.top/anjuke/"
ROOT = Path(__file__).parent


def text_of(row, selector, required=True):
    node = row.select_one(selector)
    if node is None:
        if required:
            raise ValueError(f"缺少字段节点：{selector}")
        return ""
    return node.get_text(strip=True)


def parse_house(row):
    attributes = [p.get_text(strip=True) for p in row.select(".property-content-info > p.property-content-info-text")]
    areas = [value for value in attributes if re.fullmatch(r"\d+(?:\.\d+)?(?:㎡|m²|平米)", value)]
    floors = [value for value in attributes if "层" in value]
    years = [value for value in attributes if "年建造" in value]
    if len(areas) != 1 or len(floors) != 1:
        raise ValueError(f"面积或楼层定位异常：{attributes}")
    price = text_of(row, ".property-price-average")
    if "元/" not in price:
        raise ValueError(f"单价单位异常：{price}")
    return (
        text_of(row, "h3"),
        text_of(row, ".property-content-info-comm-name"),
        text_of(row, ".property-content-info-comm-address"),
        text_of(row, ".property-content-info-attribute"),
        areas[0], floors[0], years[0] if years else "", price,
    )


def parse_page(html, current_url):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else ""
    if "验证" in title:
        raise ValueError(f"收到验证页面，停止采集：{title}")
    rows = soup.select("div.property")
    if not rows:
        raise ValueError("房源节点为 0，停止采集")
    records = [parse_house(row) for row in rows]
    pagination = soup.select_one(".pagination")
    next_node = pagination.select_one("a.next") if pagination else None
    if next_node is None:
        raise ValueError("分页区域或下一页按钮缺失，不能视为末页")
    active = "next-active" in next_node.get("class", [])
    href = next_node.get("href", "")
    if active and (not href or href == "#"):
        raise ValueError("下一页按钮可用但地址缺失")
    # 页面抓取服务可能把原始 # 补全为“当前页面完整地址#”。
    target_parts = urlparse(urljoin(current_url, href))
    current_parts = urlparse(current_url)
    self_fragment = "#" in href and (
        target_parts.hostname, target_parts.path, target_parts.query
    ) == (current_parts.hostname, current_parts.path, current_parts.query)
    if not active and href not in ("", "#") and not self_fragment:
        raise ValueError("下一页状态与链接不一致，不能判断为末页")
    next_url = urljoin(current_url, href) if active else None
    if next_url:
        parts = urlparse(next_url)
        if parts.hostname != "www.bspider.top" or not parts.path.startswith("/anjuke/"):
            raise ValueError("下一页超出教学站范围")
    return records, {"title": title, "next_href": href, "next_url": next_url, "last_page": not active}


def save_csv(records, target):
    unique = list(dict.fromkeys(records))
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.writer(output)
        writer.writerow(FIELDS)
        writer.writerows(unique)
    with target.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("回读表头不一致")
        loaded = [tuple(row[field] for field in FIELDS) for row in reader]
    if loaded != unique:
        raise ValueError("CSV 回读结果不一致")
    return unique


def collect_online(max_pages=100):
    records, logs, visited, page_signatures = [], [], set(), set()
    current_url = BASE_URL
    with requests.Session() as session:
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        for page in range(1, max_pages + 1):
            if current_url in visited:
                raise ValueError("重复的分页 URL，停止")
            visited.add(current_url)
            response = session.get(current_url, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            page_records, info = parse_page(response.text, current_url)
            signature = tuple(page_records)
            if signature in page_signatures:
                raise ValueError("重复的整页房源，停止")
            page_signatures.add(signature)
            records.extend(page_records)
            log = dict(page=page, url=current_url, count=len(page_records), total=len(records), **info)
            logs.append(log)
            print(json.dumps(log, ensure_ascii=False))
            if info["last_page"]:
                return records, logs
            current_url = info["next_url"]
            time.sleep(1)
    raise ValueError("达到安全页数上限；采集未完成")


def parse_user_snapshot():
    sources = sorted((ROOT / "html").glob("page_*.html"))
    if not sources:
        raise ValueError("没有用户提供的 HTML 文件")
    records, logs = [], []
    for source in sources:
        number = int(source.stem.split("_")[-1])
        current_url = BASE_URL if number == 1 else f"{BASE_URL}?page={number}"
        page_records, info = parse_page(source.read_text(encoding="utf-8"), current_url)
        soup = BeautifulSoup(source.read_text(encoding="utf-8"), "html.parser")
        active_page = soup.select_one(".pagination .page-item.active")
        if active_page and active_page.get_text(strip=True) != str(number):
            raise ValueError(f"文件编号与页面页码不符：{source.name}")
        records.extend(page_records)
        logs.append(dict(page=number, source=str(source.relative_to(ROOT)), url=current_url,
                         parsed=len(page_records), unique_in_file=len(set(page_records)), **info))
        print(f"本地页面 {number}：节点 {len(page_records)}，本文件唯一记录 {len(set(page_records))}")
    unique = save_csv(records, ROOT / "data" / "houseinfo.csv")
    available = [log["page"] for log in logs]
    missing = [number for number in range(1, 10) if number not in available]
    summary = dict(mode="用户提供 HTML 的本地解析", pages=logs, available_pages=available,
                   requested_page_range="1-9", missing_requested_pages=missing, parsed=len(records),
                   duplicates=len(records)-len(unique), csv_rows=len(unique),
                   complete=not missing and info["last_page"], next_url=info["next_url"])
    (ROOT / "data" / "collection_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    for index in (0, len(unique)//2, len(unique)-1):
        print(f"样本 {index+1}：", dict(zip(FIELDS, unique[index])))
    return unique, summary


if __name__ == "__main__":
    parse_user_snapshot()
