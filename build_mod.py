#!/usr/bin/env python3
"""
ETS2 人民币货币 mod 构建脚本
获取 EUR -> CNY 实时汇率，生成 def/economy_data.sii（原版数据 + 追加 CNY 货币项），打包为 zip 格式的 .scs mod。

数据源优先级：
  1. frankfurter.app （欧洲央行 ECB 参考汇率，无需 key）
  2. open.er-api.com （备用，无需 key）
  3. dist/rate.json  （上一次成功构建的汇率，仅前两者都失败时使用）

仅用 Python 标准库，无第三方依赖。
"""

import json
import sys
import urllib.request
import zipfile
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "template" / "economy_data.base.sii"
ICON = ROOT / "assets" / "mod_icon.jpg"
DIST = ROOT / "dist"
MOD_NAME = "ets2_cny_currency.scs"
RATE_FILE = DIST / "rate.json"

# 汇率合理性区间（EUR/CNY 历史波动范围），超出视为接口异常
RATE_MIN, RATE_MAX = 5.0, 15.0
TIMEOUT = 30

# 追加在原版最后一个货币（RSD）之后的 CNY 货币块
CNY_BLOCK = (
    "\n"
    "\tcurrency_code[]: \"CNY\"\n"
    "\tcurrency_ratio[]: {ratio}\n"
    "\tcurrency_sign1[]: \"\"\n"
    "\tcurrency_sign2[]: \"¥\"\n"
    "\tcurrency_sign3[]: \"\"\n"
)


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "ets2-cny-mod-builder/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_rate():
    """返回 (rate, source, rate_date)。全部失败时返回 None。"""
    try:
        data = fetch_json("https://api.frankfurter.app/latest?from=EUR&to=CNY")
        rate = float(data["rates"]["CNY"])
        if RATE_MIN <= rate <= RATE_MAX:
            return rate, "frankfurter.app (ECB)", data.get("date", "")
    except Exception as e:
        print(f"[warn] frankfurter.app 获取失败: {e}")

    try:
        data = fetch_json("https://open.er-api.com/v6/latest/EUR")
        rate = float(data["rates"]["CNY"])
        if RATE_MIN <= rate <= RATE_MAX:
            return rate, "open.er-api.com", data.get("time_last_update_utc", "")[:16]
    except Exception as e:
        print(f"[warn] open.er-api.com 获取失败: {e}")

    if RATE_FILE.exists():
        try:
            last = json.loads(RATE_FILE.read_text(encoding="utf-8"))
            print(f"[warn] 接口均不可用，沿用上次汇率 {last['rate']} ({last['date']})")
            return float(last["rate"]), f"缓存 ({last['source']})", last["date"]
        except Exception as e:
            print(f"[warn] 读取本地缓存失败: {e}")

    return None


def build_def(rate: float) -> str:
    """读取原版 economy_data 模板，在最后一个货币块后追加 CNY。"""
    base = TEMPLATE.read_text(encoding="utf-8-sig")
    marker = "currency_sign3[]"
    idx = base.rindex(marker)
    line_end = base.index("\n", idx) + 1
    block = CNY_BLOCK.format(ratio=f"{rate:.4f}")
    out = base[:line_end] + block + base[line_end:]
    return "\ufeff" + out  # 与原版一致保留 UTF-8 BOM


def write_zip(path: Path, files: dict, fixed_date: tuple):
    """打 zip（固定时间戳，保证仅汇率变化时 git diff 干净）。"""
    if path.exists():
        path.unlink()
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            info = zipfile.ZipInfo(name, date_time=fixed_date)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, content)


def main() -> int:
    result = fetch_rate()
    if result is None:
        print("[error] 无法获取汇率，构建中止")
        return 1
    rate, source, rate_date = result
    if not rate_date:
        rate_date = date.today().isoformat()
    print(f"[info] EUR/CNY = {rate:.4f}  来源: {source}  汇率日期: {rate_date}")

    today = datetime.now(timezone.utc)
    DIST.mkdir(exist_ok=True)

    def_text = build_def(rate)
    year, month, day = today.year, today.month, today.day
    version = f"1.0.{year}{month:02d}{day:02d}"

    manifest = (
        "SiiNunit\n"
        "{\n"
        "mod_package : .package_name\n"
        "{\n"
        f"\tdisplay_name: \"人民币货币 Chinese Currency (CNY 实时汇率)\"\n"
        f"\tpackage_version: \"{version}\"\n"
        f"\tauthor: \"Ze\"\n"
        "\tcategory[]: \"economy\"\n"
        "\ticon: \"mod_icon.jpg\"\n"
        "\tdescription_file: \"description.txt\"\n"
        "}\n"
        "}\n"
    )
    description = (
        f"人民币货币 mod — 每日自动更新 EUR/CNY 汇率\n"
        f"当前汇率: 1 EUR = {rate:.4f} CNY ({rate_date}, 来源: {source})\n"
        f"构建时间: {today.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        "用法: 启用本 mod 后，游戏设置 → 游戏 → 区域 → 显示货币，选择 CNY。\n"
        "仅修改货币显示，不影响存档与经济系统。\n"
    )

    mod_file = DIST / MOD_NAME
    files = {
        "manifest.sii": manifest,
        "description.txt": description,
        "def/economy_data.sii": def_text,
    }
    if ICON.exists():
        files["mod_icon.jpg"] = ICON.read_bytes()
    write_zip(
        mod_file,
        files,
        fixed_date=(year, month, day, 12, 0, 0),
    )
    RATE_FILE.write_text(
        json.dumps(
            {
                "rate": f"{rate:.4f}",
                "date": rate_date,
                "source": source,
                "generated_at": today.isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"[info] 已生成 {mod_file} ({mod_file.stat().st_size} 字节)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
