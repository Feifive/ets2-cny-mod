# ETS2 人民币货币 mod 自动更新脚本
# 运行一次 = 下载最新汇率版 mod 到游戏 mod 文件夹（旧文件会被覆盖）
#
# 首次使用：把下面两行改成你的 GitHub 仓库地址
$Owner = "你的GitHub用户名"
$Repo  = "ets2-cny-mod"

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$url = "https://raw.githubusercontent.com/$Owner/$Repo/main/dist/ets2_cny_currency.scs"
$modDir = Join-Path ([Environment]::GetFolderPath("MyDocuments")) "Euro Truck Simulator 2\mod"

if (-not (Test-Path $modDir)) {
    New-Item -ItemType Directory -Path $modDir -Force | Out-Null
}

$dest = Join-Path $modDir "ets2_cny_currency.scs"
Write-Host "正在下载最新人民币货币mod..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing
Write-Host "已更新: $dest" -ForegroundColor Green
Write-Host "启动游戏后在模组管理器启用，然后到 选项-游戏-区域-显示货币 选择 CNY。"
Pause
