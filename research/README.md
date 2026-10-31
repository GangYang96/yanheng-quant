# 数据采集与研究复现

从仓库根目录运行以下命令。先按根 README 安装锁定的后端与前端依赖，并构建前端。所有响应、日志和结果位于 `data/research-validation/`，不提交到 Git。

## 准备固定样本

```powershell
uv run --project backend --frozen python research/probe_sources.py
uv run --project backend --frozen python research/probe_adjusted.py
uv run --project backend --frozen python research/bootstrap_and_backtest.py
```

前两步访问公开接口，保存原始响应与采集记录；请先检查输出中的 `status`，缺失权限、空数据与网络失败都会明确记录。未成功采集日线时，第三步会报出缺失文件。第三步复用上游标准化、指标与回测引擎，检查数据并生成策略结果；运行时应先停止使用同一数据目录的服务，避免并发写入。

股票 / ETF 下载区间固定为 2024-01-01—2026-10-31（北京时间），回测参数写在脚本中。财报请求为供应商当前最近 12 条，未锁定历史首次披露版本；指数补数使用运行当日向前 1,100 天的窗口。后续下载的数据可能变化。保留本地响应和 SHA-256，可对同一快照离线重建；仓库摘要不替代原始输入数据。

## 启动与 HTTP 对比

```powershell
uv run --project backend --frozen python research/serve.py
```

打开 <http://127.0.0.1:3018/watchlist> 并完成引导；另一个终端执行：

```powershell
uv run --project backend --frozen python research/check_local.py
uv run --project backend --frozen python research/populate_core_indices.py
```

HTTP 脚本使用没有设置共享密码的隔离验证实例，会加入三只样本自选并执行股票 / ETF 回测，核对先前保存的交易与净值。若已开启密码保护，请通过应用界面运行；这些脚本不自动绕过认证。指数脚本通过应用数据源取数，并刷新视图和缓存。用 Ctrl+C 停止前台服务。

## 定向测试

```powershell
uv run --directory backend --frozen --extra dev python -m pytest tests/test_backtest_etf.py tests/backtest/test_cost_model.py tests/backtest/test_strategy_backtest_correctness.py tests/backtest/test_limit_up_close_fill.py tests/backtest/test_limit_down_close_exit.py -q
pnpm --dir frontend test:indices
pnpm --dir frontend build
```

CI 运行相同的定向回归与构建，不访问实时金融供应商；公开接口数据检查需单独运行。测试数量描述的是此次选定范围，不代表上游全量测试已经通过。
