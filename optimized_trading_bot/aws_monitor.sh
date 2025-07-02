#!/bin/bash

# AWS Trading Bot Monitoring Script
# Monitors the trading bot and provides management functions

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONFIG_FILE="aws_deployment_config.txt"

# Load configuration
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Configuration file not found: $CONFIG_FILE${NC}"
    echo "Run aws_deploy_automation.sh first to create the configuration."
    exit 1
fi

source "$CONFIG_FILE"

# Functions
check_instance_status() {
    echo -e "${BLUE}📊 Checking AWS instance status...${NC}"
    
    STATE=$(aws ec2 describe-instances \
        --instance-ids "$INSTANCE_ID" \
        --region "$REGION" \
        --query 'Reservations[0].Instances[0].State.Name' \
        --output text)
    
    case $STATE in
        "running")
            echo -e "${GREEN}✅ Instance is running${NC}"
            ;;
        "stopped")
            echo -e "${RED}❌ Instance is stopped${NC}"
            echo "Starting instance..."
            aws ec2 start-instances --instance-ids "$INSTANCE_ID" --region "$REGION"
            echo "Waiting for instance to start..."
            aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"
            
            # Update public IP (may have changed)
            NEW_PUBLIC_IP=$(aws ec2 describe-instances \
                --instance-ids "$INSTANCE_ID" \
                --region "$REGION" \
                --query 'Reservations[0].Instances[0].PublicIpAddress' \
                --output text)
            
            if [ "$NEW_PUBLIC_IP" != "$PUBLIC_IP" ]; then
                echo -e "${YELLOW}⚠️ Public IP changed: $PUBLIC_IP -> $NEW_PUBLIC_IP${NC}"
                # Update config file
                sed -i.bak "s/PUBLIC_IP=.*/PUBLIC_IP=$NEW_PUBLIC_IP/" "$CONFIG_FILE"
                sed -i.bak "s|DASHBOARD_URL=.*|DASHBOARD_URL=http://$NEW_PUBLIC_IP|" "$CONFIG_FILE"
                PUBLIC_IP=$NEW_PUBLIC_IP
            fi
            echo -e "${GREEN}✅ Instance started successfully${NC}"
            ;;
        "pending")
            echo -e "${YELLOW}⏳ Instance is starting...${NC}"
            ;;
        "stopping")
            echo -e "${YELLOW}⏳ Instance is stopping...${NC}"
            ;;
        *)
            echo -e "${RED}❌ Instance state: $STATE${NC}"
            ;;
    esac
}

check_trading_bot_status() {
    echo -e "${BLUE}📊 Checking trading bot status...${NC}"
    
    if ! ssh -i "$KEY_FILE" -o ConnectTimeout=10 -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "echo 'SSH OK'" &> /dev/null; then
        echo -e "${RED}❌ Cannot connect via SSH${NC}"
        return 1
    fi
    
    # Check if Docker container is running
    CONTAINER_STATUS=$(ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "docker ps --filter name=trading-bot --format '{{.Status}}'" 2>/dev/null || echo "Not found")
    
    if [[ $CONTAINER_STATUS == *"Up"* ]]; then
        echo -e "${GREEN}✅ Trading bot container is running${NC}"
        echo "   Status: $CONTAINER_STATUS"
    else
        echo -e "${RED}❌ Trading bot container is not running${NC}"
        echo "   Status: $CONTAINER_STATUS"
        return 1
    fi
    
    # Check if dashboard is accessible
    if curl -f -s "http://$PUBLIC_IP" > /dev/null; then
        echo -e "${GREEN}✅ Dashboard is accessible${NC}"
    else
        echo -e "${RED}❌ Dashboard is not accessible${NC}"
        return 1
    fi
}

restart_trading_bot() {
    echo -e "${BLUE}🔄 Restarting trading bot...${NC}"
    
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP << 'EOF'
        echo "Restarting trading bot container..."
        docker restart trading-bot
        sleep 5
        
        echo "Checking container status..."
        docker ps | grep trading-bot
        
        echo "Checking logs..."
        docker logs trading-bot --tail 5
EOF
    
    echo -e "${GREEN}✅ Trading bot restarted${NC}"
}

view_logs() {
    echo -e "${BLUE}📋 Viewing trading bot logs...${NC}"
    echo "Press Ctrl+C to exit log viewing"
    echo ""
    
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP "docker logs trading-bot -f"
}

get_performance_metrics() {
    echo -e "${BLUE}📊 Getting performance metrics...${NC}"
    
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP << 'EOF'
        echo "=== System Resources ==="
        free -h
        echo ""
        
        echo "=== Disk Usage ==="
        df -h / | tail -1
        echo ""
        
        echo "=== Docker Container Stats ==="
        docker stats trading-bot --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
        echo ""
        
        echo "=== Trading Bot Health ==="
        curl -s http://localhost:80/api/status 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"Bot Status: {data.get('status', 'Unknown')}\")
    print(f\"Uptime: {data.get('uptime', 'Unknown')}\")
    print(f\"Last Update: {data.get('last_update', 'Unknown')}\")
except:
    print('Health data not available')
" || echo "Health check failed"
EOF
}

connect_ssh() {
    echo -e "${BLUE}🔗 Connecting to AWS instance via SSH...${NC}"
    echo "You will be connected to ubuntu@$PUBLIC_IP"
    echo "Use 'exit' to return to your local machine"
    echo ""
    
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no ubuntu@$PUBLIC_IP
}

show_dashboard_url() {
    echo -e "${BLUE}🌐 Dashboard Information:${NC}"
    echo "  Main Dashboard: http://$PUBLIC_IP"
    echo "  API Status: http://$PUBLIC_IP/api/status"
    echo "  Health Check: curl http://$PUBLIC_IP/api/status"
    echo ""
    echo -e "${GREEN}💡 Bookmark this URL: http://$PUBLIC_IP${NC}"
}

auto_monitor() {
    echo -e "${BLUE}🔄 Starting automated monitoring...${NC}"
    echo "Press Ctrl+C to stop monitoring"
    echo ""
    
    while true; do
        clear
        echo -e "${GREEN}📊 AWS Trading Bot - Automated Monitoring${NC}"
        echo "=============================================="
        echo "Time: $(date)"
        echo ""
        
        check_instance_status
        echo ""
        
        if check_trading_bot_status; then
            echo ""
            get_performance_metrics
        else
            echo -e "${YELLOW}⚠️ Attempting to restart trading bot...${NC}"
            restart_trading_bot
        fi
        
        echo ""
        echo -e "${BLUE}Next check in 60 seconds... (Ctrl+C to stop)${NC}"
        sleep 60
    done
}

# Main menu
show_menu() {
    echo -e "${GREEN}🤖 AWS Trading Bot Management${NC}"
    echo "=============================="
    echo "1. Check Status"
    echo "2. Restart Trading Bot"
    echo "3. View Logs"
    echo "4. Performance Metrics"
    echo "5. Connect via SSH"
    echo "6. Show Dashboard URL"
    echo "7. Auto Monitor (60s intervals)"
    echo "8. Exit"
    echo ""
    echo -e "${BLUE}Current Instance: $INSTANCE_ID${NC}"
    echo -e "${BLUE}Dashboard URL: http://$PUBLIC_IP${NC}"
    echo ""
}

# Main execution
if [ $# -eq 0 ]; then
    # Interactive mode
    while true; do
        show_menu
        read -p "Select an option (1-8): " choice
        
        case $choice in
            1)
                check_instance_status
                echo ""
                check_trading_bot_status
                echo ""
                read -p "Press Enter to continue..."
                ;;
            2)
                restart_trading_bot
                echo ""
                read -p "Press Enter to continue..."
                ;;
            3)
                view_logs
                ;;
            4)
                get_performance_metrics
                echo ""
                read -p "Press Enter to continue..."
                ;;
            5)
                connect_ssh
                ;;
            6)
                show_dashboard_url
                echo ""
                read -p "Press Enter to continue..."
                ;;
            7)
                auto_monitor
                ;;
            8)
                echo -e "${GREEN}👋 Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Invalid option. Please choose 1-8.${NC}"
                sleep 2
                ;;
        esac
        
        clear
    done
else
    # Command line mode
    case "$1" in
        "status")
            check_instance_status
            check_trading_bot_status
            ;;
        "restart")
            restart_trading_bot
            ;;
        "logs")
            view_logs
            ;;
        "metrics")
            get_performance_metrics
            ;;
        "ssh")
            connect_ssh
            ;;
        "url")
            show_dashboard_url
            ;;
        "monitor")
            auto_monitor
            ;;
        *)
            echo "Usage: $0 {status|restart|logs|metrics|ssh|url|monitor}"
            echo "Or run without arguments for interactive mode"
            ;;
    esac
fi