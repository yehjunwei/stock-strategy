#!/bin/bash
#
# 台股数据获取服务管理脚本
#

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

show_help() {
    echo -e "${GREEN}台股数据获取服务管理工具${NC}\n"
    echo "用法: bash manage.sh [命令]"
    echo ""
    echo "命令:"
    echo "  status      - 查看服务状态"
    echo "  logs        - 查看实时日志"
    echo "  history     - 查看执行历史"
    echo "  run         - 手动运行一次"
    echo "  start       - 启动定时服务"
    echo "  stop        - 停止定时服务"
    echo "  restart     - 重启定时服务"
    echo "  data        - 查看数据信息"
    echo "  help        - 显示此帮助"
    echo ""
}

check_service() {
    if ! systemctl list-unit-files | grep -q stock-fetcher.timer; then
        echo -e "${YELLOW}警告: 服务未安装${NC}"
        echo "请先运行: sudo bash install_service.sh"
        exit 1
    fi
}

show_status() {
    check_service
    echo -e "${BLUE}=== Timer 状态 ===${NC}"
    systemctl status stock-fetcher.timer --no-pager
    echo ""
    echo -e "${BLUE}=== Service 状态 ===${NC}"
    systemctl status stock-fetcher.service --no-pager
    echo ""
    echo -e "${BLUE}=== 下次运行时间 ===${NC}"
    systemctl list-timers stock-fetcher.timer --no-pager
}

show_logs() {
    echo -e "${BLUE}=== 实时日志 (按 Ctrl+C 退出) ===${NC}\n"
    sudo tail -f /var/log/stock-fetcher.log
}

show_history() {
    check_service
    echo -e "${BLUE}=== 最近 50 条执行记录 ===${NC}\n"
    sudo journalctl -u stock-fetcher.service -n 50 --no-pager
}

run_once() {
    check_service
    echo -e "${YELLOW}手动运行一次...${NC}\n"
    sudo systemctl start stock-fetcher.service
    echo ""
    echo -e "${GREEN}已触发运行，查看状态:${NC}"
    echo "  sudo systemctl status stock-fetcher.service"
    echo "  sudo tail -f /var/log/stock-fetcher.log"
}

start_timer() {
    check_service
    echo -e "${YELLOW}启动定时服务...${NC}"
    sudo systemctl start stock-fetcher.timer
    sudo systemctl enable stock-fetcher.timer
    echo -e "${GREEN}✓ 定时服务已启动${NC}"
}

stop_timer() {
    check_service
    echo -e "${YELLOW}停止定时服务...${NC}"
    sudo systemctl stop stock-fetcher.timer
    echo -e "${GREEN}✓ 定时服务已停止${NC}"
}

restart_timer() {
    check_service
    echo -e "${YELLOW}重启定时服务...${NC}"
    sudo systemctl restart stock-fetcher.timer
    echo -e "${GREEN}✓ 定时服务已重启${NC}"
}

show_data() {
    CSV_FILE="${SCRIPT_DIR}/data/taiwan_stocks.csv"

    if [[ ! -f "$CSV_FILE" ]]; then
        echo -e "${YELLOW}数据文件不存在: ${CSV_FILE}${NC}"
        echo "请先运行服务获取数据"
        exit 1
    fi

    echo -e "${BLUE}=== 数据文件信息 ===${NC}\n"
    echo "文件路径: ${CSV_FILE}"
    echo "文件大小: $(du -h "$CSV_FILE" | cut -f1)"
    echo "总行数: $(wc -l < "$CSV_FILE" | tr -d ' ')"
    echo ""

    echo -e "${BLUE}=== 数据统计 ===${NC}\n"
    python3 - <<EOF
import pandas as pd
df = pd.read_csv("${CSV_FILE}")
print(f"总记录数: {len(df):,}")
print(f"股票数量: {df['stock_id'].nunique()}")
print(f"日期范围: {df['date'].min()} ~ {df['date'].max()}")
print(f"\n数据预览（前 5 条）:")
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
