#!/usr/bin/env python3
"""
生成 steamcmd workshop_build_item 所需的 VDF 描述文件（仅更新内容与更新说明，
不写 title/description/preview，保留工坊页面现有元数据）。

用法：python tools/workshop_vdf.py <输出路径.vdf> [--changenote "..."]
不传 --changenote 时自动用 dist/rate.json 组一条（汇率 + 日期）。
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RATE_FILE = ROOT / "dist" / "rate.json"

APP_ID = 227300        # Euro Truck Simulator 2
PUBLISHED_FILE_ID = 3815224566
CONTENT_FOLDER = ROOT / "workshop"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", help="输出的 .vdf 路径")
    parser.add_argument("--changenote", default=None)
    args = parser.parse_args()

    if args.changenote:
        note = args.changenote
    else:
        rate = json.loads(RATE_FILE.read_text(encoding="utf-8"))
        note = f"更新汇率 1 EUR = {rate['rate']} CNY ({rate['date']})"

    if '"' in note or "\n" in note:
        print("[error] changenote 不能包含引号或换行")
        return 1

    vdf = (
        '"workshopitem"\n'
        "{\n"
        f'\t"appid"\t\t\t"{APP_ID}"\n'
        f'\t"publishedfileid"\t"{PUBLISHED_FILE_ID}"\n'
        f'\t"contentfolder"\t\t"{CONTENT_FOLDER.as_posix()}"\n'
        f'\t"changenote"\t\t"{note}"\n'
        "}\n"
    )
    Path(args.output).write_text(vdf, encoding="utf-8")
    print(f"[info] 已生成 {args.output}")
    print(vdf)
    return 0


if __name__ == "__main__":
    sys.exit(main())
