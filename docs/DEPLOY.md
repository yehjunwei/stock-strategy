# Linux 服务器部署指南

快速在 Linux 服务器上部署台股数据自动获取服务。

## 系统要求

- **操作系统**: Ubuntu 18.04+ / Debian 10+ / CentOS 7+
- **Python**: 3.7+
- **权限**: root 或 sudo
- **网络**: 可访问 FinMind API

## 快速部署

### 1. 上传项目到服务器

```bash
# 方式 1: 使用 git
git clone <your-repo-url>
cd stock-strategy

# 方式 2: 使用 scp 上传
scp -r /path/to/stock-strategy user@server:/home/user/
ssh user@server
cd ~/stock-strategy
```

### 2. 一键安装服务

```bash
sudo bash install_service.sh
```

安装脚本会自动：
- ✅ 检查 Python 3 和 pip3
- ✅ 安装依赖 (FinMind, pandas, requests)
- ✅ 创建日志文件 `/var/log/stock-fetcher.log`
- ✅ 创建数据目录 `data/`
- ✅ 配置 systemd service 和 timer
- ✅ 启动定时任务

### 3. 验证安装

```bash
# 查看服务状态
bash manage.sh status

# 手动运行一次测试
bash manage.sh run

# 查看实时日志
bash manage.sh logs
```

## 服务说明

### 运行频率

- **定时**: 每小时运行一次
- **随机延迟**: 0-5 分钟（避免同时大量请求）
- **开机启动**: 系统重启后自动启动
- **断点续传**: 每次从上次中断处继续

### 日志位置

```bash
# 系统日志（systemd）
sudo journalctl -u stock-fetcher.service -f

# 应用日志（程序输出）
sudo tail -f /var/log/stock-fetcher.log
```

### 数据位置

```
/path/to/stock-strategy/data/taiwan_stocks.csv
```

## 管理命令

### 查看状态

```bash
# Timer 和 Service 状态
bash manage.sh status

# 下次运行时间
systemctl list-timers stock-fetcher.timer
```

### 控制服务

```bash
# 启动定时任务
bash manage.sh start

# 停止定时任务
bash manage.sh stop

# 重启定时任务
bash manage.sh restart

# 手动运行一次（不影响定时）
bash manage.sh run
```

### 查看日志

```bash
# 实时日志
bash manage.sh logs

# 历史记录
bash manage.sh history

# 系统日志（最近 50 条）
sudo journalctl -u stock-fetcher.service -n 50
```

### 数据管理

```bash
# 查看数据统计
bash manage.sh data

# 手动查看 CSV
head -20 data/taiwan_stocks.csv
```

## 配置调整

### 修改运行频率

编辑 `/etc/systemd/system/stock-fetcher.timer`:

```ini
[Timer]
# 每小时 → 每 30 分钟
OnCalendar=*:0/30

# 每小时 → 每天凌晨 2 点
OnCalendar=02:00
```

然后重载：

```bash
sudo systemctl daemon-reload
sudo systemctl restart stock-fetcher.timer
```

### 修改 API Token

编辑 `fetch_taiwan_stocks.py` 第 261 行：

```python
api_token = "YOUR_NEW_TOKEN"
```

### 修改请求延迟

编辑 `fetch_taiwan_stocks.py` 第 316 行：

```python
# 600次/小时 = 0.2秒/次（当前）
# 改为更保守的 0.5 秒
new_df = fetcher.fetch_batch(stock_list, start_date, end_date, delay=0.5)
```

## 故障排查

### 服务未启动

```bash
# 检查状态
sudo systemctl status stock-fetcher.timer
sudo systemctl status stock-fetcher.service

# 查看错误日志
sudo journalctl -u stock-fetcher.service -xe

# 手动启动
sudo systemctl start stock-fetcher.timer
```

### API 限流错误

如果日志显示 API 请求过多：

1. 检查是否配置了 API Token
2. 增加请求延迟（修改 `delay` 参数）
3. 减少运行频率（修改 timer）

### 数据未更新

```bash
# 检查上次运行时间
sudo journalctl -u stock-fetcher.service | tail -20

# 检查数据文件
ls -lh data/taiwan_stocks.csv
tail -20 data/taiwan_stocks.csv

# 手动运行测试
sudo systemctl start stock-fetcher.service
sudo tail -f /var/log/stock-fetcher.log
```

### Python 依赖问题

```bash
# 重新安装依赖
pip3 install -r requirements.txt --upgrade

# 检查版本
pip3 list | grep -E "FinMind|pandas|requests"
```

## 性能优化

### API Token（必须）

已配置 API Token:
- 每小时限制: 600 次
- 约 1200 支股票
- 需要约 2 小时完成一次全量获取

### 调整批次大小

如果想更快完成，可以修改每次获取的时间跨度：

编辑 `fetch_taiwan_stocks.py` 第 80 和 85 行：

```python
# 每次获取 2 年而不是 1 年
start_date = end_date - timedelta(days=365*2)
```

注意：增加批次会增加单次运行时间。

## 卸载服务

```bash
# 停止并删除服务
sudo bash uninstall_service.sh

# 删除项目（可选）
cd ..
rm -rf stock-strategy
```

## 监控建议

### 设置告警

创建监控脚本 `/usr/local/bin/check-stock-fetcher.sh`:

```bash
#!/bin/bash
if ! systemctl is-active --quiet stock-fetcher.timer; then
    echo "Stock fetcher timer is not running!" | mail -s "Alert" admin@example.com
fi
```

添加到 crontab:

```bash
# 每天检查一次
0 9 * * * /usr/local/bin/check-stock-fetcher.sh
```

### 磁盘空间监控

```bash
# 查看数据文件大小
du -h data/taiwan_stocks.csv

# 预期: 完整 26 年数据约 200-300 MB
```

## 备份建议

### 自动备份脚本

创建 `/usr/local/bin/backup-stock-data.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/stock-data"
DATE=$(date +%Y%m%d)

mkdir -p $BACKUP_DIR
cp /path/to/stock-strategy/data/taiwan_stocks.csv \
   $BACKUP_DIR/taiwan_stocks_${DATE}.csv

# 保留最近 30 天的备份
find $BACKUP_DIR -name "*.csv" -mtime +30 -delete
```

添加到 crontab:

```bash
# 每天凌晨 3 点备份
0 3 * * * /usr/local/bin/backup-stock-data.sh
```

## 常见问题

### Q: 数据多久能补齐？

A: 从现在到 2000 年约 26 年，每次补充 1 年，每小时运行一次：
- 理论: 26 小时
- 实际: 考虑 API 限制和网络，约 2-3 天

### Q: 可以并行运行吗？

A: 不建议。程序设计为单例运行，多个实例会导致数据冲突。

### Q: 服务器重启后会继续吗？

A: 会。Timer 设置了 `Persistent=true` 和开机启动。

### Q: 如何知道数据已补齐？

A: 查看日志，当出现 "🎉 已完成！数据已涵盖到 2000-01-01" 即表示完成。

---

**需要帮助？** 查看日志文件或提交 Issue。
