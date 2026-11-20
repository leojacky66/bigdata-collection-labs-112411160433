#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实验三脱敏脚本：把 private_data/*.csv 脱敏成 data/*_public.csv

用法（在 Docker 的 JupyterLab 里，或在任意装了 pandas 的环境里运行）：
    python desensitize.py
或直接在 Notebook 里粘贴运行。

脱敏规则（可按需修改）：
- 发件人/主题/正文：保留前2个字符 + 打码 "***"
- 邮箱：保留 @ 前第1个字符 + "***" + @域名
- 时间：保留 "年月日"，时分秒打码（如 "11-20 12:00" -> "11-20 **:**"）
- 邮件ID：保留前8位，其余打码（避免暴露完整 mailid，同时保持唯一性便于核对）
说明：以上为默认规则，实际请按老师要求调整；只要不暴露真实私人内容即可。
"""
from pathlib import Path
import pandas as pd

PRIVATE = Path("private_data")
PUBLIC = Path("data")
PUBLIC.mkdir(exist_ok=True)

# 字段 -> 脱敏函数
def mask_text(v, keep=2):
    v = str(v)
    if not v:
        return v
    return v[:keep] + "***" if len(v) > keep else v

def mask_email(v):
    v = str(v)
    if not v or "@" not in v:
        return v
    local, _, domain = v.partition("@")
    return (local[:1] + "***@" + domain) if local else v

def mask_time(v):
    v = str(v)
    # 形如 "11-20 12:00" 或 "2026-11-20 12:00"，打码时分秒
    import re
    return re.sub(r"(\d{2}:\d{2}(?::\d{2})?)", "**:**", v)

def mask_id(v, keep=8):
    v = str(v)
    return v[:keep] + "***" if len(v) > keep else v

COLUMN_MASKERS = {
    "发件人": mask_text,
    "邮箱": mask_email,
    "主题": lambda v: mask_text(v, keep=3),
    "时间": mask_time,
    "正文": lambda v: mask_text(v, keep=0) if str(v) else v,  # 正文整段打码，只留"***"占位
    "附件文件": mask_text,
    "邮件ID": mask_id,
}

FILES = {
    "mail_basic.csv": "mail_basic_public.csv",
    "mail_pages.csv": "mail_pages_public.csv",
    "mail_details.csv": "mail_details_public.csv",
}

for src, dst in FILES.items():
    p = PRIVATE / src
    if not p.exists():
        print(f"跳过（不存在）: {p}")
        continue
    df = pd.read_csv(p, dtype=str, keep_default_na=False)
    for col in df.columns:
        if col in COLUMN_MASKERS:
            df[col] = df[col].map(COLUMN_MASKERS[col])
    out = PUBLIC / dst
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"已生成 {out}（{len(df)} 行，{len(df.columns)} 列：{list(df.columns)}）")

print("脱敏完成。请核对 data/ 下三个 *_public.csv 是否不含任何真实私人信息后再提交。")
