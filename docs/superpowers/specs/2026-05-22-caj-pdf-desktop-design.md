# CAJ-PDF 桌面端设计规格

> 日期：2026-05-22 | 状态：已确认

## 目标

面向 Windows / macOS（Intel + Apple Silicon）用户的 CAJ 批量转 PDF 桌面应用，支持无限队列、失败跳过、应用内转换历史。

## 已确认需求

| 项目 | 决定 |
|------|------|
| 分发 | 安装包分发，非应用商店 |
| 扫描 | 递归扫描入口文件夹内所有 `.caj` |
| 出口 | PDF 平铺至出口根目录，重名自动加后缀 |
| 失败 | 跳过继续，批次结束汇总 |
| 历史 | 应用内 SQLite 持久化 |
| UI | 中文、浅/深色可切换、简洁高级 |
| 技术 | PyWebView + Vue 3 + Tailwind + Python 后端 |

## 架构

- **前端**：Vue 3 SPA，Tailwind CSS，通过 `pywebview.api` 调用 Python
- **后端**：Scanner → QueueManager（单 worker）→ Converter（caj2pdf）→ HistoryStore（SQLite）
- **打包**：PyInstaller + Inno Setup（Win）/ create-dmg（macOS）

## 数据模型

```sql
batches(id, started_at, finished_at, input_dir, output_dir, total, success_count, failed_count, status)
items(id, batch_id, source_path, output_name, status, error_msg, finished_at)
settings(key, value)
```

## 界面

单页主界面：文件夹选择、进度条、实时日志、开始/暂停；历史侧栏展示批次与明细。
