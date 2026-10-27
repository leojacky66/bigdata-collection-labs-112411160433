"""用 Firecrawl 顺序读取教学站，或回放已保存的真实 HTML。

在线：python fetch_firecrawl.py
回放：python fetch_firecrawl.py --replay

在线运行需要已安装并完成认证的 Firecrawl CLI，以及 PATH 中的 Node.js。
可通过 FIRECRAWL_COMMAND 环境变量指定 firecrawl 可执行文件的完整路径；
认证信息交由 CLI 管理，本程序不保存密钥。回放不调用 CLI、不请求网络，
写入 replay_summary.json，保留真实在线采集的 collection_summary.json。
"""

import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from urllib.parse import urldefrag, urlparse

try:
    from collect_houseinfo import FIELDS, parse_page, save_csv
except ModuleNotFoundError as error:
    raise SystemExit(
        "缺少 Python 依赖。请先安装 requirements.txt 中的依赖，例如："
        "python -m pip install requests beautifulsoup4 pymysql"
    ) from error


ROOT = Path(__file__).resolve().parent
START_URL = "http://www.bspider.top/anjuke/"
PAGE_LIMIT = 20


def now():
    """记录带时区的实际时间，便于区分原始抓取与离线回放。"""
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()


def check_url(url):
    parts = urlparse(url)
    if (
        parts.scheme not in ("http", "https")
        or parts.hostname != "www.bspider.top"
        or not parts.path.startswith("/anjuke/")
        or parts.username is not None
        or parts.password is not None
        or parts.port not in (None, 80, 443)
    ):
        raise ValueError(f"分页地址超出教学站范围，停止：{url}")
    return urldefrag(url)[0]


def resolve_cli():
    configured = os.environ.get("FIRECRAWL_COMMAND", "").strip()
    command = shutil.which(configured or "firecrawl")
    if not command:
        raise RuntimeError(
            "找不到 Firecrawl CLI。请先安装并完成认证，将 firecrawl 加入 PATH，"
            "或设置 FIRECRAWL_COMMAND 为可执行文件的完整路径。"
            "已有 HTML 可改用 --replay，无须联网或安装 CLI。"
        )
    return command


def write_summary(summary, path):
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def collect(replay=False, html_dir=None, data_dir=None):
    html_dir = Path(html_dir or ROOT / "html" / "online").resolve()
    data_dir = Path(data_dir or ROOT / "data").resolve()
    data_dir.mkdir(parents=True, exist_ok=True)
    summary_path = data_dir / ("replay_summary.json" if replay else "collection_summary.json")
    summary = {
        "mode": "replay" if replay else "online_firecrawl",
        "source": "已保存的真实在线 HTML 回放" if replay else "Firecrawl 直接读取教学网站",
        "started_at": now(),
        "start_url": START_URL,
        "fields": list(FIELDS),
        "maximum_pages": PAGE_LIMIT,
        "interval_seconds": 1.1,
        "complete": False,
        "csv_written": False,
        "pages": [],
        "parsed": 0,
        "csv_rows": 0,
        "duplicates": 0,
    }
    records, signatures, visited = [], set(), set()
    current_url = START_URL
    command = None
    environment = dict(os.environ)
    environment["FIRECRAWL_NO_ENDPOINT_FEEDBACK"] = "1"
    try:
        # --replay 不执行此分支，因此没有 Firecrawl、认证或网络依赖。
        if not replay:
            command = resolve_cli()
            html_dir.mkdir(parents=True, exist_ok=True)
        for number in range(1, PAGE_LIMIT + 1):
            current_url = check_url(current_url)
            if current_url in visited:
                raise ValueError("重复的分页 URL，停止")
            visited.add(current_url)
            target = html_dir / f"page_{number:02}.html"
            requested_at = None
            if replay:
                if not target.is_file():
                    raise FileNotFoundError(f"缺少第 {number} 页真实 HTML：{target}")
            else:
                # 串行执行，每一请求开始前至少距上一请求结束 1.1 秒。
                if number > 1:
                    time.sleep(1.1)
                requested_at = now()
                result = subprocess.run(
                    [command, "scrape", current_url, "--format", "html", "-o", str(target)],
                    capture_output=True, text=True, timeout=180, env=environment,
                )
                if result.returncode != 0:
                    # 不循环重试，不继续翻页；CLI 的错误详情只显示在本地。
                    detail = (result.stderr or result.stdout).strip()[-1000:]
                    raise RuntimeError(f"Firecrawl 请求失败，停止：{detail}")
                if not target.is_file():
                    raise RuntimeError("Firecrawl 未保存 HTML，停止")
            html = target.read_text(encoding="utf-8")
            # 复用同一个已验证的八字段与分页解析器；验证页或空记录会抛错。
            page_records, page_info = parse_page(html, current_url)
            signature = hashlib.sha256(
                json.dumps(page_records, ensure_ascii=False).encode("utf-8")
            ).hexdigest()
            if signature in signatures:
                raise ValueError("检测到重复的整页记录，停止")
            signatures.add(signature)
            records.extend(page_records)
            entry = {
                "page": number,
                "url": current_url,
                "html": str(target.relative_to(ROOT)) if target.is_relative_to(ROOT) else str(target),
                "count": len(page_records),
                "unique_in_page": len(set(page_records)),
                "html_sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
                "records_sha256": signature,
                **page_info,
            }
            if replay:
                entry["replayed_at"] = now()
            else:
                entry["requested_at"] = requested_at
            summary["pages"].append(entry)
            summary.update(
                parsed=len(records), csv_rows=len(set(records)),
                duplicates=len(records) - len(set(records)),
            )
            write_summary(summary, summary_path)
            print(
                f"第 {number} 页：{len(page_records)} 条，累计 {len(records)} 条，"
                f"八字段去重 {len(set(records))} 条；末页={page_info['last_page']}",
                flush=True,
            )
            if page_info["last_page"]:
                summary["complete"] = True
                summary["stop_reason"] = "下一页按钮明确禁用，已到达真实末页"
                break
            current_url = check_url(page_info["next_url"])
        else:
            raise ValueError("达到 20 页安全上限，采集未完成")

        # 只有确认末页后才覆盖正式 CSV，避免失败时用部分数据替换已完成文件。
        unique = save_csv(records, data_dir / "houseinfo.csv")
        summary.update(csv_written=True, csv_rows=len(unique))
    except Exception as error:
        summary["stop_reason"] = str(error)
        raise
    finally:
        summary["finished_at"] = now()
        write_summary(summary, summary_path)
    print(json.dumps({k: v for k, v in summary.items() if k != "pages"}, ensure_ascii=False, indent=2))
    return unique, summary


def main():
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument("--replay", action="store_true", help="只回放已保存的真实 HTML，不访问网络")
    argument_parser.add_argument("--html-dir", type=Path, help="HTML 目录，默认 lab02/html/online")
    argument_parser.add_argument("--data-dir", type=Path, help="结果目录，默认 lab02/data")
    arguments = argument_parser.parse_args()
    try:
        collect(arguments.replay, arguments.html_dir, arguments.data_dir)
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        raise SystemExit(f"采集停止：{error}") from error


if __name__ == "__main__":
    main()
