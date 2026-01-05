# 台股历史数据获取工具

一个简单高效的台股历史数据获取工具，支持**增量更新**，自动补充数据至 2000 年。

## 功能特色

- ✅ **增量更新**: 每次执行自动往前补充历史数据
- ✅ **智能续传**: 中断后再次执行会从上次进度继续
- ✅ **数据完整**: 涵盖所有上市股票（约 1200+ 支）
- ✅ **格式标准**: CSV 格式，包含 OHLCV 数据
- ✅ **自动去重**: 合并数据时自动去除重复记录

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 执行程序

```bash
python fetch_taiwan_stocks.py
```

**首次执行**: 获取最近 1 年的数据
**后续执行**: 每次往前补充 1 年，直到 2000-01-01

### 3. 等待完成

- 预计每次执行 10-30 分钟（取决于网络速度）
- 可随时按 `Ctrl+C` 中断，下次会自动续传
- 数据保存在 `data/taiwan_stocks.csv`

## Linux 自动化部署（推荐）

在 Linux 服务器上设置自动定时任务，每小时自动获取数据。

### 一键安装

```bash
# 下载项目
git clone <your-repo-url>
cd stock-strategy

# 运行安装脚本（需要 root 权限）
sudo bash install_service.sh
```

安装完成后，服务会：
- ✅ 每小时自动运行一次
- ✅ 开机自动启动
- ✅ 自动补齐数据到 2000 年
- ✅ 日志记录所有操作

### 管理命令

```bash
# 查看服务状态
bash manage.sh status

# 查看实时日志
bash manage.sh logs

# 手动运行一次
bash manage.sh run

# 查看数据信息
bash manage.sh data

# 查看所有命令
bash manage.sh help
```

### 卸载服务

```bash
sudo bash uninstall_service.sh
```

## 数据格式

### CSV 栏位说明

| 栏位 | 说明 | 类型 | 示例 |
|------|------|------|------|
| `date` | 交易日期 | String | 2025-12-08 |
| `stock_id` | 股票代码 | String | 2330 |
| `open` | 开盘价 | Float | 1035.0 |
| `high` | 最高价 | Float | 1050.0 |
| `low` | 最低价 | Float | 1032.0 |
| `close` | 收盘价 | Float | 1048.0 |
| `volume` | 成交量 | Integer | 58234567 |

### 示例数据

```csv
date,stock_id,open,high,low,close,volume
2025-12-08,2330,1035.0,1050.0,1032.0,1048.0,58234567
2025-12-08,2317,135.5,138.0,134.0,137.5,12345678
2025-12-09,2330,1050.0,1055.0,1045.0,1052.0,45678901
```

## 工作原理

```
首次执行
├─ 检查数据文件 → 不存在
├─ 获取最近 1 年数据 (2025-01-01 ~ 2026-01-05)
└─ 保存到 data/taiwan_stocks.csv

第二次执行
├─ 检查数据文件 → 存在 (最早: 2025-01-01)
├─ 往前补充 1 年 (2024-01-01 ~ 2024-12-31)
└─ 合并并去重

第三次执行
├─ 检查数据文件 → 存在 (最早: 2024-01-01)
├─ 继续往前补充 1 年
└─ ...直到 2000-01-01
```

## 预期数据量

完整获取 2000-2026 年的数据：

- **时间跨度**: 26 年 ≈ 6,500 交易日
- **股票数量**: 约 1,200 支（仅上市，不含 ETF）
- **总记录数**: 约 500 万 - 800 万条
- **文件大小**: 约 200-300 MB

## 使用 API Token（推荐）

使用 FinMind API Token 可提升 6 倍速度。

### 获取 Token

1. 前往 [FinMind 官网](https://finmindtrade.com/) 注册
2. 登录后在个人中心获取 API Token

### 设置 Token

编辑 `fetch_taiwan_stocks.py` 的第 261 行：

```python
api_token = "YOUR_API_TOKEN_HERE"  # 替换成你的 token
```

## 常见问题

### Q1: 需要执行多少次才能完成？

约 25-26 次（每次补充 1 年，从现在到 2000 年）

### Q2: 可以一次获取全部数据吗？

可以，但不推荐。理由：
- 需要 5+ 小时连续运行
- 容易因网络问题中断
- 增量更新更稳定可靠

### Q3: 如何修改目标年份？

编辑 `fetch_taiwan_stocks.py` 的第 25 行：

```python
TARGET_START_DATE = "2000-01-01"  # 改成你想要的日期
```

### Q4: 数据会自动更新吗？

目前只支持往前补充历史数据。如需更新最新数据，需要手动修改逻辑。

### Q5: 为什么有些股票没有完整数据？

- 新上市股票：上市时间晚于 2000 年
- 已下市股票：FinMind 可能无数据
- 暂停交易：某些日期可能停牌

## 进阶使用

### 只获取特定股票

修改 `get_stock_list()` 函数返回值：

```python
def get_stock_list(self):
    return ['2330', '2317', '2454']  # 台积电、鸿海、联发科
```

### 修改每次获取的时间跨度

修改 `calculate_fetch_range()` 函数：

```python
# 第 80 行和 85 行
start_date = end_date - timedelta(days=365*2)  # 改为 2 年
```

### 调整请求延迟

修改 `main()` 函数：

```python
# 第 315 行
new_df = fetcher.fetch_batch(stock_list, start_date, end_date, delay=1.0)
```

## 项目结构

```
stock-strategy/
├── fetch_taiwan_stocks.py   # 主程序
├── requirements.txt          # 依赖列表
├── README.md                 # 本文档
├── install_service.sh        # Linux 服务安装脚本
├── uninstall_service.sh      # Linux 服务卸载脚本
├── manage.sh                 # 服务管理脚本
├── stock-fetcher.service     # Systemd service 文件
├── stock-fetcher.timer       # Systemd timer 文件
└── data/
    └── taiwan_stocks.csv     # 数据文件（自动生成）
```

## 数据来源

本工具使用 [FinMind](https://finmindtrade.com/) API 获取数据：

- 官方文档: https://finmind.github.io/
- 数据来源: 台湾证券交易所（TWSE）
- 数据质量: 专业级，广泛用于量化交易

## 授权声明

- 本工具仅供学习和研究使用
- 数据版权归台湾证券交易所及 FinMind 所有
- 请遵守 FinMind 使用条款
- 使用数据进行交易需自行承担风险

## 后续应用

获取数据后，可以进行：

1. **回测交易策略**: 验证技术分析指标的有效性
2. **统计分析**: 研究股票走势、波动率、相关性等
3. **机器学习**: 训练股价预测模型
4. **数据可视化**: 绘制K线图、趋势图等

## 学习资源

- Pandas 教学: https://leemeng.tw/practical-pandas-tutorial-for-aspiring-data-scientists.html
- Pandas_ta 教学: https://blog.csdn.net/ndhtou222/article/details/132157873
- 用 Python 实作买卖指标: https://python.plainenglish.io/generating-buy-sell-trade-signals-in-python-1153b1a543c4
- FinMind 官方文档: https://finmind.github.io/
- FinMind 策略分析: https://finmindtrade.com/analysis/#/dashboards/strategy-analysis

## 技术支持

- **问题回报**: [GitHub Issues](https://github.com/finmind/FinMind/issues)
- **FinMind 文档**: https://finmind.github.io/
- **API 使用**: https://finmindtrade.com/

## 更新日志

### v2.0 (2026-01-05)

- ✨ 实现增量更新功能
- ✨ 自动检测现有数据并续传
- ✨ 智能去重和数据合并
- 🔄 重构代码结构
- 📝 完善文档说明

### v1.0

- 初始版本
- 基本数据获取功能

---

**Made with ❤️ for Taiwan Stock Traders**
