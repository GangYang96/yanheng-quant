# 研衡量化 · Yanheng Quant

面向 A 股 / ETF 的金融数据分析与策略验证系统，基于 [Tick Stock Panel](https://github.com/shy3130/tick-stock-panel) 的开源二次开发项目。采用 React / TypeScript 前端与 Python / FastAPI 后端，以半导体作为首批验证样本，后续面向多个行业扩展。

**当前交付：可本地运行的行情与回测应用、公开数据验证脚本、可复查的工程记录。** 行业指标研究页、双评分、阈值研究与社区属于后续规划。

[个人主页](https://gangyang96.github.io/?lang=zh#yanheng-quant) · [个人贡献与来源](docs/yanheng/contributions.md) · [验证报告](docs/yanheng/validation.md) · [复现步骤](research/README.md) · [MIT 许可证](LICENSE)

## 当前功能

| 模块 | 当前实现与来源 |
| --- | --- |
| 自选与行情 | 复用上游自选、股票 / ETF K 线与技术指标功能，导入真实样本验证前后端链路 |
| 策略与回测 | 复用上游策略加载、交易成本及撮合引擎；新增透明均线样例及直接调用 / HTTP 子进程结果一致性验证 |
| 指数展示 | 按数据源能力展示日线或分时，区分最近收盘与实时行情，显示数据日期、同步失败及空结果 |
| 数据验证 | 采集公开日线与财报样本，保存来源、时间、参数与 SHA-256；保留不复权与前复权价格口径 |
| 工程交付 | 品牌适配、隔离数据目录、可移植复现脚本、定向回归测试与贡献说明 |

财报目前仅完成采集与口径检查，未进入研究界面或策略。行业材料仅验证部分公开入口，未建立历史指标库。当前应用为单用户研究原型。

## 验证结果

2026-11-01 的本地验证覆盖：

- 2 只股票、1 只 ETF 与 4 只指数，共 **4,955 条日线**；两家公司三类财报共 **72 条表记录**。
- 股票样例 35 笔、ETF 样例 16 笔交易；直接调用与真实 HTTP 子进程回测的交易和净值序列一致。
- 40 项选定上游后端测试、3 项指数页测试通过，前端构建通过。

这些数字用于说明数据与执行链路的验证范围，不构成策略有效性结论。原始第三方响应不随仓库分发；[验证摘要](docs/yanheng/validation-summary.json) 提供数量、范围与样本哈希。重新下载可能因来源修订而产生差异。

## 本地运行

需要 Python 3.12、[uv](https://docs.astral.sh/uv/)、Node.js 22 或更新版本，以及 pnpm 9.10.0。

```powershell
git clone https://github.com/GangYang96/yanheng-quant.git
cd yanheng-quant
uv sync --project backend --frozen --extra dev
pnpm --dir frontend install --frozen-lockfile
pnpm --dir frontend build
uv run --project backend --frozen python research/serve.py
```

打开 <http://127.0.0.1:3018>，完成首次引导并选择免费数据模式。无需付费密钥即可尝试受数据源支持的历史日线；分钟与实时行情取决于供应商权限。克隆后没有预装行情数据库，载入本文验证样本请按 [research/README.md](research/README.md) 操作。

启动器绑定本机，数据保存在被 Git 忽略的 `data/research-validation/`。可选配置写入根目录 `.env`，示例见 `.env.example`。主页提供项目介绍和源码入口，GitHub Pages 不运行本项目的 Python 后端。

## 目录与技术

```text
frontend/          React / TypeScript / Vite 界面
backend/           FastAPI、Polars、DuckDB 与上游策略回测能力
research/          本项目的数据探测、样本策略、复现和启动脚本
docs/yanheng/      来源、贡献、验证结果与实现边界
data/              本地数据、缓存和结果（不提交）
```

## 研究与扩展方向

后续计划以来源更新频率驱动采集，关联行业与公司指标，区分“当前策略匹配度”与“历史表现及稳定性”，研究手工阈值与历史候选阈值，并建设支持策略版本和结果复现的社区。半导体是首个验证板块，不是平台的行业限制。

接入历史财务与产业指标前，需要核验首次披露时间、修订版本、单位及累计 / 单季口径，避免未来信息进入历史策略。当前未完成历史时点复权因子、分红送转记账、全市场标的池或样本外收益验证。

## 来源与许可

本仓库以 Tick Stock Panel `v0.3.24` 的提交 [`864bbc49`](https://github.com/shy3130/tick-stock-panel/tree/864bbc49d86f7f48ed3e4d194ffc15eaaebbb25d) 为源快照，保留 MIT 许可证及原作者署名。行情、策略、回测等核心引擎来自上游；本项目贡献集中于应用适配、数据验证、复现工具与指数页修复，详见 [贡献映射](docs/yanheng/contributions.md)。上游的桌面打包资源及发布流水线未随此 Web 源码快照导出，目录清单见 [source-export.json](docs/yanheng/source-export.json)。

## English overview

Yanheng Quant is an A-share / ETF data-analysis and strategy-validation application developed on top of Tick Stock Panel. The first validation samples cover semiconductors, while the intended research scope spans multiple industries. This repository preserves the MIT-licensed upstream web application and adds capability-aware index presentation, public-data probes, portable research scripts and reproducibility checks. The trading and backtesting engines are upstream work.

Local validation covered 4,955 daily bars and 72 financial-table records. Direct and HTTP-worker backtests produced identical trades and equity curves. Financial and industry factors are not yet strategy inputs; scoring, threshold research and community features remain planned. See the [validation report](docs/yanheng/validation.md) for the exact scope and limitations.
