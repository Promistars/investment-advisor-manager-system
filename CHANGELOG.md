# Changelog

## [1.4.0] — 2026-06-17

### 绩效引擎与数据一致性

- 新增 `portfolio_engine.py`：统一持仓模拟、批量账户快照与磁盘缓存（`.cache/hall_snapshots/`）
- 大厅卡片盈亏与 Analytics 看板共用同一引擎，消除口径不一致
- `db_manager.get_all_trades_for_user()` 批量查询；交易/账户变更时自动失效快照缓存

### 国际化与用户设置

- 新增 `iams_i18n.py`、`iams_prefs.py`、`iams_ui.py`：中英双语与可持久化偏好
- 设置项：语言、盈亏配色（中/西）、日期格式、默认报告视图、紧凑布局、Emoji 开关
- URL 参数 `?lang=en` 支持客户链接直达英文界面

### UI / 交互

- 登录页分段切换（身份登录 / 注册）全宽布局；主界面浅色卡片风格
- 侧边栏设置与底部「系统维护」面板（刷新盈亏缓存、清空数据缓存、恢复默认设置），操作前二次确认
- Analytics 与客户大屏 sticky 吸顶、KPI 对齐等布局优化

---

## [1.3.0] — 2026-06-04

### 数据引擎与网络

- 新增 `stock_fetch.py` 统一 K 线抓取：新浪 → 东财（可达时）→ BaoStock 三级容灾
- 新增 `iams_network.py` 与 `config/network.env`：项目级代理策略，默认直连
- `auto_fetch.py` 重构为复用 `fetch_stock_kline`，侧边栏新股票即时入库走同一引擎
- 东财 `push2his` 不可达时自动降级新浪日线，分红等其它东财接口仍可用

### 看板与绩效

- 收益图成本线改为 0% 盈亏平衡参考线；资产图叠加累计净本金曲线
- 管理费（内扣/外付）不再计入净本金与成本线，仅转入/提取影响净本金
- KPI 六宫格等高布局；移除卡片底部冗余「净流入」「年化波动」副指标
- 管理员历史指令账本：增删行、批量删除、保存校验

### UI / 侧边栏

- 侧边栏暗色主题：导航、Expander、表单、按钮统一浅色文字与单层底色
- 修复 Expander 内按钮（确认修改、联网抓取）层级与样式

### 运维

- 新增 systemd 用户服务：`iams-web`、`iams-fetch`、`iams-healthcheck.timer`
- 新增 `setup_systemd.sh`、`iams_healthcheck.sh`、`scripts/run_with_iams_env.sh`
- `restart_all.sh` 优先 systemd 重启，未安装时回退 nohup

---

## [1.2.x] — 此前版本

- 双渠道容灾（BaoStock + AKShare）、看板布局与客户链接等特性见历史提交记录。
