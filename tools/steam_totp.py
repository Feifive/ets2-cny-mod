#!/usr/bin/env python3
"""
生成 Steam Guard 手机令牌的 5 位验证码（用于 steamcmd CI 登录）。

Steam 的码不是标准 6 位数字 TOTP：取 HMAC-SHA1 截断值的 31 bit，
按 26 字符表 "23456789BCDFGHJKMNPQRTVWXY" 转成 5 位字母数字。
算法与 SteamKit / steamguard 社区实现一致。

用法：设置环境变量 STEAM_TOTP_SECRET（手机令牌导出的 shared_secret，
base64 编码）后运行，验证码打印到 stdout。
"""

import base64
import hashlib
import hmac
import os
import struct
import sys
import time

ALPHABET = "23456789BCDFGHJKMNPQRTVWXY"


def steam_totp(secret_b64: str, timestamp: float | None = None) -> str:
    key = base64.b64decode(secret_b64 + "=" * (-len(secret_b64) % 4))
    counter = int((timestamp if timestamp is not None else time.time()) // 30)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    full = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    code = ""
    for _ in range(5):
        code += ALPHABET[full % 26]
        full //= 26
    return code


def main() -> int:
    secret = os.environ.get("STEAM_TOTP_SECRET", "")
    if not secret:
        print("[error] 未设置 STEAM_TOTP_SECRET", file=sys.stderr)
        return 1
    print(steam_totp(secret))
    return 0


if __name__ == "__main__":
    sys.exit(main())
