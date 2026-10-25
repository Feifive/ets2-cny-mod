#!/usr/bin/env python3
"""
无头更新 Steam 创意工坊条目（替代 SCS Workshop Uploader GUI 的 Upload 按钮）。

原理：直接调用 mod_tools.exe 自带 steam_api64.dll 的 flat API
(StartItemUpdate → SetItemContent → SubmitItemUpdate)，登录态复用
本机已登录的 Steam 客户端。仅更新内容，不改动工坊页面的
标题/描述/标签/可见性。

用法（需 Steam 客户端正在运行且已登录）：
  python tools/workshop_upload.py
  python tools/workshop_upload.py --change-note "fix: xxx"

注意：
- 需要读取 dist/rate.json 确认要发布的内容与仓库一致；
- 上传目录固定为本仓库的 workshop/（含 versions.sii + universal/）；
- SteamAPI 异步 CallResult 在非 Steam 启动的进程上可能投递失败
  (IO failure)，属已知现象：内容上传与提交本身是同步完成的。
  因此本脚本用 Steam Web API 查询条目 time_updated 作为最终判据；
  注意内容完全相同的幂等提交不会刷新 time_updated，此判据仅在
  内容有实际变化时有效。

前提文件：脚本同目录的 steam_appid.txt（内容为 421800，
SCS Workshop Uploader 的 app id）会自动创建。
"""

import argparse
import ctypes
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STEAM_API_DLL = Path(
    r"E:\VideoGames\Steam\steamapps\common\SCS Workshop Uploader\bin\win_x64\steam_api64.dll"
)
CONTENT_DIR = ROOT / "workshop"
RATE_FILE = ROOT / "dist" / "rate.json"
APP_ID = 227300          # Euro Truck Simulator 2（条目所属 app）
UPLOADER_APP_ID = 421800  # SCS Workshop Uploader（API 初始化用的 app id）
FILE_ID = 3815224566      # 本 mod 的工坊条目 id

SUBMIT_ITEM_UPDATE_RESULT = 1617  # SubmitItemUpdateResult_t::k_iCallback


def wait_file_id_result() -> float:
    """通过 Web API 取条目当前 time_updated（失败返回 -1）。"""
    body = f"itemcount=1&publishedfileids[0]={FILE_ID}".encode()
    req = urllib.request.Request(
        "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            details = json.load(resp)["response"]["publishedfiledetails"][0]
            return float(details["time_updated"])
    except Exception as e:
        print(f"[warn] Web API 查询失败: {e}")
        return -1.0


def main() -> int:
    parser = argparse.ArgumentParser(description="无头更新 ETS2 人民币货币 mod 的创意工坊条目")
    parser.add_argument("--change-note", default="update", help="更新说明（change note）")
    args = parser.parse_args()

    if not STEAM_API_DLL.exists():
        print(f"[error] 找不到 steam_api64.dll: {STEAM_API_DLL}")
        return 1
    rate = json.loads(RATE_FILE.read_text(encoding="utf-8"))
    print(f"[info] 仓库当前构建汇率: {rate['rate']} ({rate['date']})")

    # steam_appid.txt 必须在进程 cwd（决定 API 初始化的 app id）
    tools_dir = Path(__file__).resolve().parent
    (tools_dir / "steam_appid.txt").write_text(f"{UPLOADER_APP_ID}\n")
    saved = os.getcwd()
    os.chdir(tools_dir)
    try:
        return _run(args.change_note)
    finally:
        os.chdir(saved)


def _run(change_note: str) -> int:
    steam = ctypes.WinDLL(str(STEAM_API_DLL))
    steam.SteamAPI_Init.restype = ctypes.c_bool
    if not steam.SteamAPI_Init():
        print("[error] SteamAPI_Init 失败：Steam 客户端未运行或未登录")
        return 1

    try:
        # ManualDispatch 必须紧跟 Init、先于其他 API 调用，否则回调管道异常
        steam.SteamAPI_ManualDispatch_Init.argtypes = []
        steam.SteamAPI_ManualDispatch_Init()
        steam.SteamAPI_GetHSteamPipe.restype = ctypes.c_int32
        pipe = steam.SteamAPI_GetHSteamPipe()
        steam.SteamAPI_ManualDispatch_RunFrame.argtypes = [ctypes.c_int32]
        steam.SteamAPI_ManualDispatch_GetNextCallback.restype = ctypes.c_bool
        steam.SteamAPI_ManualDispatch_GetNextCallback.argtypes = [ctypes.c_int32, ctypes.c_void_p]
        steam.SteamAPI_ManualDispatch_FreeLastCallback.argtypes = [ctypes.c_int32]
        steam.SteamAPI_ManualDispatch_GetAPICallResult.restype = ctypes.c_bool
        steam.SteamAPI_ManualDispatch_GetAPICallResult.argtypes = [
            ctypes.c_int32, ctypes.c_uint64, ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
            ctypes.POINTER(ctypes.c_bool),
        ]

        steam.SteamAPI_SteamUGC_v017.restype = ctypes.c_void_p
        ugc = steam.SteamAPI_SteamUGC_v017()
        if not ugc:
            print("[error] 无法获取 ISteamUGC")
            return 1

        steam.SteamAPI_ISteamUGC_StartItemUpdate.restype = ctypes.c_uint64
        steam.SteamAPI_ISteamUGC_StartItemUpdate.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint64]
        handle = steam.SteamAPI_ISteamUGC_StartItemUpdate(ugc, APP_ID, FILE_ID)
        if not handle:
            print("[error] StartItemUpdate 失败（无权更新该条目？）")
            return 1

        steam.SteamAPI_ISteamUGC_SetItemContent.restype = ctypes.c_bool
        steam.SteamAPI_ISteamUGC_SetItemContent.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_char_p]
        if not steam.SteamAPI_ISteamUGC_SetItemContent(ugc, handle, str(CONTENT_DIR).encode("utf-8")):
            print("[error] SetItemContent 失败")
            return 1

        before = wait_file_id_result()
        if before < 0:
            print("[warn] 无法获取提交前 time_updated，跳过时间戳判据")

        steam.SteamAPI_ISteamUGC_SubmitItemUpdate.restype = ctypes.c_uint64
        steam.SteamAPI_ISteamUGC_SubmitItemUpdate.argtypes = [ctypes.c_void_p, ctypes.c_uint64, ctypes.c_char_p]
        apicall = steam.SteamAPI_ISteamUGC_SubmitItemUpdate(ugc, handle, change_note.encode("utf-8"))
        print(f"[info] 已提交 (apicall {apicall:#x})，上传中...")

        steam.SteamAPI_ISteamUGC_GetItemUpdateProgress.restype = ctypes.c_int
        steam.SteamAPI_ISteamUGC_GetItemUpdateProgress.argtypes = [
            ctypes.c_void_p, ctypes.c_uint64,
            ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64),
        ]
        STATUS = {1: "Preparing config", 2: "Preparing content", 3: "Uploading content",
                  4: "Uploading preview", 5: "Committing changes"}

        class CallbackMsg(ctypes.Structure):
            _fields_ = [("m_iCallback", ctypes.c_int), ("m_pubParam", ctypes.c_void_p), ("m_cubParam", ctypes.c_int)]

        eresult = None
        deadline = time.time() + 900
        while time.time() < deadline:
            steam.SteamAPI_ManualDispatch_RunFrame(pipe)
            msg = CallbackMsg()
            while steam.SteamAPI_ManualDispatch_GetNextCallback(pipe, ctypes.byref(msg)):
                steam.SteamAPI_ManualDispatch_FreeLastCallback(pipe)

            failed = ctypes.c_bool(False)
            buf = ctypes.create_string_buffer(32)
            if steam.SteamAPI_ManualDispatch_GetAPICallResult(
                pipe, apicall, buf, 32, SUBMIT_ITEM_UPDATE_RESULT, ctypes.byref(failed)
            ):
                if failed.value:
                    print("\n[warn] CallResult 投递失败(IO failure)——已知现象，改用时间戳判据")
                else:
                    eresult = ctypes.cast(buf, ctypes.POINTER(ctypes.c_int))[0]
                break

            processed, total = ctypes.c_uint64(0), ctypes.c_uint64(0)
            st = steam.SteamAPI_ISteamUGC_GetItemUpdateProgress(ugc, handle, ctypes.byref(processed), ctypes.byref(total))
            suffix = f": {processed.value}/{total.value}" if total.value else "..."
            print(f"\r[info] {STATUS.get(st, st)}{suffix}   ", end="", flush=True)
            time.sleep(0.5)

        print()
        if eresult == 1:
            print("[OK] Steam 返回 EResult=1 (OK)，更新成功")
            return 0
        if eresult is not None:
            print(f"[error] EResult={eresult}，更新失败")
            return 1

        # CallResult 未送达：以服务器 time_updated 变化为准
        time.sleep(5)
        after = wait_file_id_result()
        if before > 0 and after > before:
            lt = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(after))
            print(f"[OK] 服务器条目更新时间已变为 {lt}，更新成功")
            return 0
        print("[error] 无法确认更新是否生效（time_updated 未变化且 CallResult 未送达），请开 Uploader GUI 核实")
        return 1
    finally:
        steam.SteamAPI_Shutdown()


if __name__ == "__main__":
    sys.exit(main())
