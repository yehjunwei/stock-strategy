#!/bin/bash
#
# 臺股數據獲取服務安裝腳本
# 用途: 在 Linux 系統上安裝 systemd service，每小時自動獲取股票數據
#

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}臺股數據獲取服務安裝腳本${NC}"
echo -e "${GREEN}======================================${NC}\n"

# 檢查是否為 root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}錯誤: 此腳本需要 root 權限運行${NC}"
   echo -e "請使用: sudo bash install_service.sh"
   exit 1
fi

# 獲取當前目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
echo -e "${YELLOW}項目目錄: ${PROJECT_ROOT}${NC}\n"

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

# 創建虛擬環境
echo "創建 Python 虛擬環境..."
VENV_DIR="${PROJECT_ROOT}/venv"
if [ ! -d "${VENV_DIR}" ]; then
    sudo -u ${REAL_USER} python3 -m venv "${VENV_DIR}"
    echo -e "${GREEN}✓ 虛擬環境已創建: ${VENV_DIR}${NC}\n"
else
    echo -e "${YELLOW}虛擬環境已存在，跳過創建${NC}\n"
fi

# 安裝 Python 依賴
echo "安裝 Python 依賴到虛擬環境..."
sudo -u ${REAL_USER} "${VENV_DIR}/bin/pip" install -r "${PROJECT_ROOT}/requirements.txt" --quiet
echo -e "${GREEN}✓ Python 依賴安裝完成${NC}\n"

# 創建日誌目錄
echo "創建日誌目錄..."
mkdir -p /var/log
touch /var/log/stock-fetcher.log
touch /var/log/check-new-high.log
chown ${REAL_USER}:${REAL_USER} /var/log/stock-fetcher.log
chown ${REAL_USER}:${REAL_USER} /var/log/check-new-high.log
echo -e "${GREEN}✓ 日誌文件已創建:${NC}"
echo "  - /var/log/stock-fetcher.log"
echo "  - /var/log/check-new-high.log"
echo ""

# 創建 data 目錄
echo "創建數據目錄..."
mkdir -p "${PROJECT_ROOT}/data"
chown ${REAL_USER}:${REAL_USER} "${PROJECT_ROOT}/data"
echo -e "${GREEN}✓ 數據目錄: ${PROJECT_ROOT}/data${NC}\n"

# 檢查 .env 文件
echo "檢查 Line Messaging API 配置..."
if [ ! -f "${PROJECT_ROOT}/.env" ]; then
    echo -e "${YELLOW}警告: 未找到 .env 文件${NC}"
    echo "如果需要 Line 通知功能，請在項目根目錄創建 .env 文件並填入您的憑證:"
    echo "LINE_CHANNEL_ACCESS_TOKEN=YOUR_TOKEN"
    echo "LINE_USER_ID=YOUR_USER_ID"
    echo ""
else
    echo -e "${GREEN}✓ 找到 .env 文件${NC}\n"
fi

# 複製並配置 service 文件
echo "配置 systemd services..."
STOCK_FETCHER_SERVICE="/etc/systemd/system/stock-fetcher.service"
STOCK_FETCHER_TIMER="/etc/systemd/system/stock-fetcher.timer"
CHECK_HIGH_SERVICE="/etc/systemd/system/check-new-high.service"
CHECK_HIGH_TIMER="/etc/systemd/system/check-new-high.timer"

# 替換 service 文件中的佔位符
VENV_PYTHON="${PROJECT_ROOT}/venv/bin/python3"

# 配置 stock-fetcher service
sed -e "s|YOUR_USERNAME|${REAL_USER}|g" \
    -e "s|/path/to/stock-strategy|${PROJECT_ROOT}|g" \
    -e "s|/usr/bin/python3|${VENV_PYTHON}|g" \
    "${SCRIPT_DIR}/stock-fetcher.service" > "${STOCK_FETCHER_SERVICE}"

cp "${SCRIPT_DIR}/stock-fetcher.timer" "${STOCK_FETCHER_TIMER}"

# 配置 check-new-high service
sed -e "s|YOUR_USERNAME|${REAL_USER}|g" \
    -e "s|/path/to/stock-strategy|${PROJECT_ROOT}|g" \
    -e "s|/usr/bin/python3|${VENV_PYTHON}|g" \
    "${SCRIPT_DIR}/check-new-high.service" > "${CHECK_HIGH_SERVICE}"

cp "${SCRIPT_DIR}/check-new-high.timer" "${CHECK_HIGH_TIMER}"

echo -e "${GREEN}✓ Service 文件已創建:${NC}"
echo "  - ${STOCK_FETCHER_SERVICE}"
echo "  - ${STOCK_FETCHER_TIMER}"
echo "  - ${CHECK_HIGH_SERVICE}"
echo "  - ${CHECK_HIGH_TIMER}"
echo ""

# 重載 systemd
echo "重載 systemd..."
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd 已重載${NC}\n"

# 啓用並啓動 timers
echo "啓動 services..."
systemctl enable stock-fetcher.timer
systemctl start stock-fetcher.timer
systemctl enable check-new-high.timer
systemctl start check-new-high.timer
echo -e "${GREEN}✓ 所有 Timer 已啓動並設置爲開機自啓${NC}\n"

# 顯示狀態
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}安裝完成！${NC}"
echo -e "${GREEN}======================================${NC}\n"

echo "服務信息:"
echo ""
echo "  【股票資料獲取服務】"
echo "  - Service: stock-fetcher.service"
echo "  - Timer: stock-fetcher.timer"
echo "  - 運行頻率: 每小時一次"
echo "  - 日誌文件: /var/log/stock-fetcher.log"
echo ""
echo "  【三年新高檢查服務】"
echo "  - Service: check-new-high.service"
echo "  - Timer: check-new-high.timer"
echo "  - 運行頻率: 每天下午 3:30"
echo "  - 日誌文件: /var/log/check-new-high.log"
echo ""
echo "  【共用設定】"
echo "  - Python 環境: ${PROJECT_ROOT}/venv"
echo "  - 數據文件: ${PROJECT_ROOT}/data/taiwan_stocks.csv"
echo ""

echo "常用命令:"
echo ""
echo "  【查看狀態】"
echo "  股票資料獲取:       sudo systemctl status stock-fetcher.timer"
echo "  三年新高檢查:       sudo systemctl status check-new-high.timer"
echo ""
echo "  【查看日誌】"
echo "  股票資料獲取:       sudo tail -f /var/log/stock-fetcher.log"
echo "  三年新高檢查:       sudo tail -f /var/log/check-new-high.log"
echo "  執行歷史:           sudo journalctl -u stock-fetcher.service"
echo "                      sudo journalctl -u check-new-high.service"
echo ""
echo "  【手動執行】"
echo "  股票資料獲取:       sudo systemctl start stock-fetcher.service"
echo "  三年新高檢查:       sudo systemctl start check-new-high.service"
echo ""
echo "  【停止/禁用】"
echo "  停止所有 timers:    sudo systemctl stop stock-fetcher.timer check-new-high.timer"
echo "  禁用所有 timers:    sudo systemctl disable stock-fetcher.timer check-new-high.timer"
echo ""

echo -e "${YELLOW}提示:${NC}"
echo "  - stock-fetcher 將在下一個整點運行（每小時）"
echo "  - check-new-high 將在每天下午 3:30 運行"
echo "  - 你也可以隨時手動運行"
echo ""
