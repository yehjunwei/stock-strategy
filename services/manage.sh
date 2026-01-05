#!/bin/bash
#
# 臺股資料獲取服務管理腳本
#

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_help() {
    echo -e "${GREEN}臺股資料獲取服務管理工具${NC}\n"
    echo "用法: bash manage.sh [命令]"
    echo ""
    echo "命令:"
    echo "  status      - 查看服務狀態"
    echo "  logs        - 查看即時日誌"
    echo "  history     - 查看執行歷史"
    echo "  run         - 手動執行一次"
    echo "  start       - 啟動定時服務"
    echo "  stop        - 停止定時服務"
    echo "  restart     - 重啟定時服務"
    echo "  data        - 查看資料資訊"
    echo "  help        - 顯示此幫助"
    echo ""
}

check_service() {
    if ! systemctl list-unit-files | grep -q stock-fetcher.timer; then
        echo -e "${YELLOW}警告: 服務未安裝${NC}"
        echo "請先執行: sudo bash install_service.sh"
        exit 1
    fi
}

show_status() {
    check_service
    echo -e "${BLUE}=== Timer 狀態 ===${NC}"
    systemctl status stock-fetcher.timer --no-pager
    echo ""
    echo -e "${BLUE}=== Service 狀態 ===${NC}"
    systemctl status stock-fetcher.service --no-pager
    echo ""
    echo -e "${BLUE}=== 下次執行時間 ===${NC}"
    systemctl list-timers stock-fetcher.timer --no-pager
}

show_logs() {
    echo -e "${BLUE}=== 即時日誌 (按 Ctrl+C 退出) ===${NC}\n"
    sudo tail -f /var/log/stock-fetcher.log
}

show_history() {
    check_service
    echo -e "${BLUE}=== 最近 50 條執行記錄 ===${NC}\n"
    sudo journalctl -u stock-fetcher.service -n 50 --no-pager
}

run_once() {
    check_service
    echo -e "${YELLOW}手動執行一次...${NC}\n"
    sudo systemctl start stock-fetcher.service
    echo ""
    echo -e "${GREEN}已觸發執行，請查看狀態:${NC}"
    echo "  sudo systemctl status stock-fetcher.service"
    echo "  sudo tail -f /var/log/stock-fetcher.log"
}

start_timer() {
    check_service
    echo -e "${YELLOW}啟動定時服務...${NC}"
    sudo systemctl start stock-fetcher.timer
    sudo systemctl enable stock-fetcher.timer
    echo -e "${GREEN}✓ 定時服務已啟動${NC}"
}

stop_timer() {
    check_service
    echo -e "${YELLOW}停止定時服務...${NC}"
    sudo systemctl stop stock-fetcher.timer
    echo -e "${GREEN}✓ 定時服務已停止${NC}"
}

restart_timer() {
    check_service
    echo -e "${YELLOW}重啟定時服務...${NC}"
    sudo systemctl restart stock-fetcher.timer
    echo -e "${GREEN}✓ 定時服務已重啟${NC}"
}

show_data() {
    CSV_FILE="${SCRIPT_DIR}/../data/taiwan_stocks.csv"

    if [[ ! -f "$CSV_FILE" ]]; then
        echo -e "${YELLOW}資料檔案不存在: ${CSV_FILE}${NC}"
        echo "請先執行服務獲取資料"
        exit 1
    fi

    echo -e "${BLUE}=== 資料檔案資訊 ===${NC}\n"
    echo "檔案路徑: ${CSV_FILE}"
    echo "檔案大小: $(du -h "$CSV_FILE" | cut -f1)"
    echo "總行數: $(wc -l < "$CSV_FILE" | tr -d ' ')"
    echo ""

    echo -e "${BLUE}=== 資料統計 ===${NC}\n"
    python3 - <<EOF
import pandas as pd
df = pd.read_csv("${CSV_FILE}")
print(f"總記錄數: {len(df):,}")
print(f"股票數量: {df['stock_id'].nunique()}")
print(f"日期範圍: {df['date'].min()} ~ {df['date'].max()}")
print(f"\n資料預覽（前 5 條）:")
print(df.head(5).to_string(index=False))
EOF
}

# 主程序
case "${1}" in
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    history)
        show_history
        ;;
    run)
        run_once
        ;;
    start)
        start_timer
        ;;
    stop)
        stop_timer
        ;;
    restart)
        restart_timer
        ;;
    data)
        show_data
        ;;
    help|--help|-h|"")
        show_help
        ;;
    *)
        echo -e "${YELLOW}未知命令: ${1}${NC}\n"
        show_help
        exit 1
        ;;
esac
