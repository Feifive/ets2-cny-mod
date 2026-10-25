# AGENTS.md

ETS2 人民币货币 mod（每日汇率自动构建）。详见 README.md。

## 日常更新

**用户说"日常更新"时，依次执行：**

1. `python build_mod.py` —— 获取最新 EUR/CNY 汇率，重建 `dist/` 与 `workshop/`
2. 验证产物：`dist/ets2_cny_currency.scs` 中 CNY 块的 `currency_sign2` 必须是
   全角 ￥（UTF-8 字节 `EF BF A5`）；不得出现半角 ¥（`C2 A5`，游戏 UI 字体
   无此字形，会被引擎静默跳过导致人民币无货币符号）
3. 汇率有变化则提交推送：`chore: 更新汇率 YYYY-MM-DD`；无 diff 则跳过（周末
   和节假日 ECB 无新汇率，属正常）
4. `python tools/workshop_upload.py --change-note "更新汇率 ..."` —— 无头发布
   创意工坊（需本机 Steam 客户端已登录；上传结果以 Web API 的 time_updated
   为准，内容完全相同的重复提交不会刷新时间戳）

## 注意事项

- 工坊页面元数据（标题/描述/预览图）独立于 mod 内容，日常更新不要动它们
- 数字千位分隔符（3 位一组）是游戏引擎按语言写死的，mod 改不了
- CI（`.github/workflows/update.yml`）每日自动构建并提交；其 `publish-workshop`
  job 需要配置 Steam Secrets 才会运行，未配置时静默跳过
