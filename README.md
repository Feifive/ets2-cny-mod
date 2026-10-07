# ETS2 人民币货币 Mod（每日自动更新汇率）

《欧卡2 (Euro Truck Simulator 2)》人民币货币显示 mod。通过 GitHub Actions 每天自动获取
欧洲央行 (ECB) 的 EUR/CNY 参考汇率，重新构建 mod 并提交回本仓库 —— 仓库里的
`dist/ets2_cny_currency.scs` 永远是最新汇率版本。

- 当前汇率见 [dist/rate.json](dist/rate.json)
- 每日构建记录见 Actions 页面和 git 提交历史（每一天的汇率都被永久记录）

## 玩家使用方法

### 1. 获取 mod

**方式 A：自动更新脚本（推荐）**

把 [`tools/update_mod.ps1`](tools/update_mod.ps1) 下载到本地，右键"使用 PowerShell 运行"，
它会自动下载最新 mod 到 `文档\Euro Truck Simulator 2\mod\` 文件夹。想每天自动更新可以
把它加入开机启动或任务计划。

**方式 B：手动下载**

直接下载 [dist/ets2_cny_currency.scs](dist/ets2_cny_currency.scs)（点击页面右侧
Raw/Download 按钮），放进 `C:\Users\<用户名>\Documents\Euro Truck Simulator 2\mod\`。

### 2. 游戏内设置

1. 启动游戏 → 模组管理器 → 启用「人民币货币 Chinese Currency (CNY 实时汇率)」→ 确认更改
2. 选项 → 游戏 → 区域 → **显示货币** → 选择 **CNY**

之后所有运价、油费、罚款、余额都会按最新汇率以 ¥ 显示。

> 说明：汇率换算只发生在显示层，游戏内部经济仍以欧元结算，
> 不影响存档、收入或游戏平衡，随时可切回其他货币。

## 维护者指南（Ze）

### 首次发布

```bash
cd E:\Projects\ets2-cny-mod
git init -b main
git add .
git commit -m "init: 人民币货币mod每日自动构建"
# 在 GitHub 上新建空仓库后：
git remote add origin https://github.com/<你的用户名>/<仓库名>.git
git push -u origin main
```

推送后 Actions 会立即构建一次；之后每天北京时间早上 8:30 自动运行，
也可在 Actions → 每日更新汇率并构建mod → Run workflow 手动触发。

### 游戏大版本更新后刷新模板

mod 覆盖的是 `def/economy_data.sii`（含全游戏经济参数）。游戏更新可能调整该文件，
建议每个大版本更新一次模板：

1. 用 [SCS 官方解包工具](https://modding.scssoft.com/wiki/Documentation/Tools/Game_Archive_Extractor)
   解包游戏目录下的 `def.scs`
2. 用解出来的 `def/economy_data.sii` 覆盖 `template/economy_data.base.sii`
3. 本地跑 `python build_mod.py` 确认无报错后提交推送

构建脚本会自动在模板末尾（最后一个货币 RSD 之后）追加 CNY 货币块，
只要未来版本仍以 `currency_sign3[]` 结尾货币数组，脚本无需改动。

### 项目结构

```
ets2-cny-mod/
├── build_mod.py                  # 构建脚本：抓汇率 → 生成def → 打包mod
├── template/economy_data.base.sii# 原版 def/economy_data.sii（游戏 1.61）
├── dist/
│   ├── ets2_cny_currency.scs     # 构建产物（zip格式），玩家直接下载使用
│   └── rate.json                 # 当前汇率与构建信息
├── workshop/                     # SCS Workshop Uploader 上传用文件夹格式
├── assets/                       # 预览图与模组图标
├── tools/update_mod.ps1          # 玩家本地自动下载脚本
└── .github/workflows/update.yml  # 每日定时构建工作流
```

## 发布到 Steam 创意工坊

GitHub 上的 mod 每日自动更新；创意工坊版本使用官方工具手动发布/更新（游戏内订阅与
GitHub 版本内容完全一致）。

1. **安装上传工具**：Steam → 库 → 上方筛选"工具" → 搜索 **SCS Workshop Uploader** → 安装
2. **运行并登录**：启动 SCS Workshop Uploader，用 Steam 账号登录（需要输入 Steam 令牌验证码）
3. **创建条目**：点 "Create New Mod" → 游戏选 Euro Truck Simulator 2 → 选择
   **`workshop/` 文件夹**（注意是文件夹，不是dist里的scs文件——Uploader要求包含
   `versions.sii` 的mod文件夹）→ 填写标题/描述 → 预览图用
   [`assets/workshop_preview.jpg`](assets/workshop_preview.jpg) → 可见性先设
   **Private** 自测，没问题再改 Public
4. **验证**：游戏内模组管理器能看到并启用该 mod（与本地版二选一，不要同时启用）
5. **日常更新**：打开 Uploader → 选中该 mod → 重新选择最新的 `workshop/` 文件夹 →
   Upload 即可，工坊订阅者会自动收到更新

> 提示：创意工坊的标题、描述、预览图在 Uploader 里维护，与 mod 包内的 manifest 相互独立。
> 工坊描述里可以附上本仓库链接，玩家即可获得每日更新的 GitHub 版和 `update_mod.ps1` 脚本。

## 致谢与版权

- `template/economy_data.base.sii` 提取自 Euro Truck Simulator 2 的 `def.scs`
  （© SCS Software），仅供个人 mod 制作使用，请勿单独分发游戏原始数据。
- 货币 def 的实现方式参考了 [ExtraCurrencies](https://github.com/justalemon/ExtraCurrencies)（MIT 协议）。
- 汇率数据来自 [frankfurter.app](https://frankfurter.app)（欧洲央行参考汇率）及
  [open.er-api.com](https://www.exchangerate-api.com) 备用源。
- 本项目代码以 MIT 协议开源，见 [LICENSE](LICENSE)。
