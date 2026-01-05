#!/bin/bash
#
# 台股數據獲取服務安裝腳本
# 用途: 在 Linux 系統上安裝 systemd service，每小時自動獲取股票數據
#

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}台股數據獲取服務安裝腳本${NC}"
echo -e "${GREEN}======================================${NC}\n"

# 檢查是否為 root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}錯誤: 此腳本需要 root 權限運行${NC}"
   echo -e "請使用: sudo bash install_service.sh"
   exit 1
fi

# 獲取當前目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${YELLOW}項目目錄: ${SCRIPT_DIR}${NC}\n"

# 獲取實際用戶（即使使用 sudo）
REAL_USER="${SUDO_USER:-$USER}"
echo -e "${YELLOW}運行用戶: ${REAL_USER}${NC}\n"

# 檢查 Python 3
echo "檢查 Python 3..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}錯誤: 未找到 Python 3${NC}"
    echo "請先安裝 Python 3: sudo apt install python3 python3-pip"
    exit 1
fi
PYTHON_PATH=$(which python3)
echo -e "${GREEN}✓ 找到 Python 3: ${PYTHON_PATH}${NC}\n"

# 檢查 pip3
echo "檢查 pip3..."
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}錯誤: 未找到 pip3${NC}"
    echo "請先安裝: sudo apt install python3-pip"
    exit 1
fi
echo -e "${GREEN}✓ 找到 pip3${NC}\n"

# 安裝 Python 依賴
echo "安裝 Python 依賴..."
pip3 install -r "${SCRIPT_DIR}/../requirements.txt" --quiet
echo -e "${GREEN}✓ Python 依賴安裝完成${NC}\n"

# 創建日誌目錄
echo "創建日誌目錄..."
mkdir -p /var/log
touch /var/log/stock-fetcher.log
chown ${REAL_USER}:${REAL_USER} /var/log/stock-fetcher.log
echo -e "${GREEN}✓ 日誌文件: /var/log/stock-fetcher.log${NC}\n"

# 創建 data 目錄
echo "創建數據目錄..."
mkdir -p "${SCRIPT_DIR}/data"
chown ${REAL_USER}:${REAL_USER} "${SCRIPT_DIR}/data"
echo -e "${GREEN}✓ 數據目錄: ${SCRIPT_DIR}/data${NC}\n"

# 复制并配置 service 文件
echo "配置 systemd service..."
SERVICE_FILE="/etc/systemd/system/stock-fetcher.service"
TIMER_FILE="/etc/systemd/system/stock-fetcher.timer"

# 替换 service 文件中的占位符
sed -e "s|YOUR_USERNAME|${REAL_USER}|g" \
    -e "s|/path/to/stock-strategy|${SCRIPT_DIR}|g" \
    -e "s|/usr/bin/python3|${PYTHON_PATH}|g" \
    "${SCRIPT_DIR}/stock-fetcher.service" > "${SERVICE_FILE}"

# 复制 timer 文件
cp "${SCRIPT_DIR}/stock-fetcher.timer" "${TIMER_FILE}"

echo -e "${GREEN}✓ Service 文件已创建:${NC}"
echo "  - ${SERVICE_FILE}"
echo "  - ${TIMER_FILE}"
echo ""

# 重载 systemd
echo "重载 systemd..."
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd 已重载${NC}\n"

# 启用并启动 timer
echo "启动 service..."
systemctl enable stock-fetcher.timer
systemctl start stock-fetcher.timer
echo -e "${GREEN}✓ Timer 已启动并设置为开机自启${NC}\n"

# 显示状态
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}安装完成！${NC}"
echo -e "${GREEN}======================================${NC}\n"

echo "服务信息:"
echo "  - Service 名称: stock-fetcher.service"
echo "  - Timer 名称: stock-fetcher.timer"
echo "  - 运行频率: 每小时一次"
echo "  - 日志文件: /var/log/stock-fetcher.log"
echo "  - 数据文件: ${SCRIPT_DIR}/data/taiwan_stocks.csv"
echo ""

echo "常用命令:"
echo "  查看 timer 状态:    sudo systemctl status stock-fetcher.timer"
echo "  查看 service 状态:  sudo systemctl status stock-fetcher.service"
echo "  查看执行历史:       sudo journalctl -u stock-fetcher.service"
echo "  查看日志:           sudo tail -f /var/log/stock-fetcher.log"
echo "  手动运行一次:       sudo systemctl start stock-fetcher.service"
echo "  停止 timer:         sudo systemctl stop stock-fetcher.timer"
echo "  禁用 timer:         sudo systemctl disable stock-fetcher.timer"
echo ""

echo -e "${YELLOW}提示: Timer 将在下一个整点运行，或者你可以手动运行一次${NC}"
echo ""
