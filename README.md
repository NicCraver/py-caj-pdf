# CAJ 转 PDF 桌面端

批量将中国知网 CAJ 文献转换为 PDF 的跨平台桌面应用（Windows / macOS）。

## 功能

- 选择入口 / 出口文件夹，递归扫描所有 `.caj` 文件
- 无上限队列，顺序转换，支持暂停 / 继续 / 取消
- 失败自动跳过，批次结束汇总
- 应用内转换历史（SQLite 持久化）
- 浅色 / 深色 / 跟随系统主题

## 开发环境

### 依赖

- Python 3.10+
- Node.js 18+
- [MuPDF](https://mupdf.com/)（提供 `mutool` 命令）

macOS 安装 mutool：

```bash
brew install mupdf
```

### 安装与运行

```bash
# Python 依赖
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 前端构建
cd frontend && npm install && npm run build && cd ..

# 启动应用（macOS 推荐，Dock / 菜单栏显示正确名称）
./scripts/run_macos.sh

# 或直接运行 Python 模块（改前端后需先 npm run build）
python -m backend.main
```

> **说明**：应用加载的是 `frontend/dist` 静态文件，不是 Vue 源码。`run_macos.sh` 会在启动前自动执行 `npm run build`；若用 `python -m backend.main`，改前端后需手动构建。**「打开文件夹」按钮仅在当前批次转换结束（已完成 / 已取消）后显示。**

## 打包分发

### 本地打包

```bash
# 先构建前端
cd frontend && npm run build && cd ..

# macOS
./scripts/build_macos.sh

# Windows（在 Windows 上运行）
.\scripts\build_windows.ps1
```

打包前请将各平台 `mutool` 二进制放入 `resources/bin/<platform>/`（CI 会自动下载）。

### GitHub Actions 自动打包（推荐）

Mac 上无法直接打 Windows 包，可推送到 GitHub 后由 Actions 在云端构建：

1. 创建 GitHub 仓库并推送代码
2. push 到 `main` / `master` 后会自动构建，并更新 GitHub Releases 里的 `latest` 预发布包
3. 也可以打开 **Actions** → **Build** → **Run workflow** 手动构建，构建完成后在 **Artifacts** 下载：
   - `CAJ-PDF-Windows-Setup.exe`（Windows 安装程序）
   - `CAJ-PDF-macOS.dmg`（macOS 磁盘映像）

打 tag（如 `v0.1.0`）并 push 后，仍会自动创建对应版本的 GitHub Release 并附上上述安装包。

## 技术栈

- 前端：Vue 3 + Vite + Tailwind CSS
- 壳层：PyWebView
- 后端：Python + caj2pdf（vendor）
- 存储：SQLite

## 说明

CAJ 格式多样，转换成功率取决于文件类型。不支持的文件会跳过并在历史中记录原因。

## 许可证

应用代码 MIT。caj2pdf 遵循其原项目许可证（GLWTPL）。
