#!/bin/bash
#
# 台股数据获取服务卸载脚本
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}======================================${NC}"
echo -e "${YELLOW}台股数据获取服务卸载脚本${NC}"
echo -e "${YELLOW}======================================${NC}\n"

# 检查是否为 root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}错误: 此脚本需要 root 权限运行${NC}"
   echo -e "请使用: sudo bash uninstall_service.sh"
   exit 1
fi

# 停止并禁用服务
echo "停止服务..."
systemctl stop stock-fetcher.timer 2>/dev/null || true
systemctl stop stock-fetcher.service 2>/dev/null || true
systemctl disable stock-fetcher.timer 2>/dev/null || true
echo -e "${GREEN}✓ 服务已停止${NC}\n"

# 删除 systemd 文件
echo "删除 systemd 文件..."
rm -f /etc/systemd/system/stock-fetcher.service
rm -f /etc/systemd/system/stock-fetcher.timer
echo -e "${GREEN}✓ Systemd 文件已删除${NC}\n"

# 重载 systemd
echo "重载 systemd..."
systemctl daemon-reload
systemctl reset-failed
echo -e "${GREEN}✓ Systemd 已重载${NC}\n"

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}卸载完成！${NC}"
echo -e "${GREEN}======================================${NC}\n"

echo -e "${YELLOW}注意: 以下内容未删除（如需要请手动删除）:${NC}"
echo "  - 项目目录和数据文件"
echo "  - 日志文件: /var/log/stock-fetcher.log"
echo "  - Python 依赖包"
echo ""
