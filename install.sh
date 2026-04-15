#!/bin/bash

# XRARY VPN BOT - Professional Installer
# Author: thetemirbolatov
# GitHub: thetemirbolatov
# Contacts: @thetemirbolatov (Telegram, VK, Instagram)

set -e

INSTALL_DIR="/opt/xrary-vpn-bot"
SERVICE_NAME="xrary-bot"
GITHUB_REPO="https://github.com/thetemirbolatov/Telegram-Bot-VPN.git"
AUTHOR="thetemirbolatov"
VERSION="2.0.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

# Global variables for user input
BOT_TOKEN=""
ADMIN_ID=""
YOOKASSA_SHOP_ID=""
YOOKASSA_SECRET_KEY=""

# Spinner animation
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while ps -p $pid > /dev/null 2>&1; do
        local temp=${spinstr#?}
        printf " ${CYAN}%c${NC}  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

# Progress bar
progress() {
    local duration=$1
    local steps=20
    for ((i=0; i<=steps; i++)); do
        local percent=$((i * 100 / steps))
        local filled=$((i * 30 / steps))
        local empty=$((30 - filled))
        printf "\r  ${BLUE}[${NC}"
        printf "%${filled}s" | tr ' ' '█'
        printf "%${empty}s" | tr ' ' '░'
        printf "${BLUE}]${NC} %3d%%" $percent
        sleep $(echo "scale=2; $duration/$steps" | bc)
    done
    echo ""
}

print_header() {
    clear
    echo -e "${CYAN}"
    echo "   ██╗  ██╗██████╗  █████╗ ██████╗ ██╗   ██╗"
    echo "   ╚██╗██╔╝██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝"
    echo "    ╚███╔╝ ██████╔╝███████║██████╔╝ ╚████╔╝ "
    echo "    ██╔██╗ ██╔══██╗██╔══██║██╔══██╗  ╚██╔╝  "
    echo "   ██╔╝ ██╗██║  ██║██║  ██║██║  ██║   ██║   "
    echo "   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   "
    echo -e "${NC}"
    echo -e "${WHITE}            VPN Telegram Bot Installer${NC}"
    echo -e "${BLUE}           Author: ${AUTHOR} | v${VERSION}${NC}"
    echo ""
    echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
    echo ""
}

print_step() {
    echo -e "\n${CYAN}▸${NC} ${WHITE}$1${NC}"
}

print_ok() {
    echo -e "  ${GREEN}✓${NC} $1"
}

print_err() {
    echo -e "  ${RED}✗${NC} $1"
}

print_info() {
    echo -e "  ${BLUE}ℹ${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        echo -e "${RED}Error: Run with sudo${NC}"
        exit 1
    fi
}

check_net() {
    print_info "Checking internet..."
    if ! ping -c 1 google.com &> /dev/null; then
        print_err "No internet connection"
        exit 1
    fi
    print_ok "Internet OK"
}

# Function to get user configuration
get_configuration() {
    # Проверяем, запущен ли скрипт через pipe
    if [ ! -t 0 ]; then
        echo ""
        echo -e "${YELLOW}╔══════════════════════════════════════════════╗${NC}"
        echo -e "${YELLOW}║              ВНИМАНИЕ!                        ║${NC}"
        echo -e "${YELLOW}╚══════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${WHITE}Скрипт запущен через pipe (wget ... | bash).${NC}"
        echo -e "${WHITE}Для корректной работы скачайте и запустите:${NC}"
        echo ""
        echo -e "${CYAN}wget https://raw.githubusercontent.com/thetemirbolatov/Telegram-Bot-VPN/main/install.sh${NC}"
        echo -e "${CYAN}sudo bash install.sh${NC}"
        echo ""
        exit 1
    fi

    echo ""
    echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
    echo -e "${WHITE}                    CONFIGURATION SETUP${NC}"
    echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
    echo ""
    
    # Get Bot Token
    while [ -z "$BOT_TOKEN" ]; do
        echo -ne "${BLUE}▸${NC} ${WHITE}Enter Telegram Bot API Token:${NC} "
        read -r BOT_TOKEN </dev/tty
        if [ -z "$BOT_TOKEN" ]; then
            echo -e "  ${RED}✗${NC} Token cannot be empty!"
        fi
    done
    echo -e "  ${GREEN}✓${NC} Bot Token saved"
    echo ""
    
    # Get Admin ID
    while [ -z "$ADMIN_ID" ]; do
        echo -ne "${BLUE}▸${NC} ${WHITE}Enter Admin Telegram ID:${NC} "
        read -r ADMIN_ID </dev/tty
        if [ -z "$ADMIN_ID" ]; then
            echo -e "  ${RED}✗${NC} Admin ID cannot be empty!"
        elif ! [[ "$ADMIN_ID" =~ ^[0-9]+$ ]]; then
            echo -e "  ${RED}✗${NC} Admin ID must be numeric!"
            ADMIN_ID=""
        fi
    done
    echo -e "  ${GREEN}✓${NC} Admin ID saved"
    echo ""
    
    # Get YooKassa Shop ID
    while [ -z "$YOOKASSA_SHOP_ID" ]; do
        echo -ne "${BLUE}▸${NC} ${WHITE}Enter YooKassa Shop ID:${NC} "
        read -r YOOKASSA_SHOP_ID </dev/tty
        if [ -z "$YOOKASSA_SHOP_ID" ]; then
            echo -e "  ${RED}✗${NC} Shop ID cannot be empty!"
        fi
    done
    echo -e "  ${GREEN}✓${NC} YooKassa Shop ID saved"
    echo ""
    
    # Get YooKassa Secret Key
    while [ -z "$YOOKASSA_SECRET_KEY" ]; do
        echo -ne "${BLUE}▸${NC} ${WHITE}Enter YooKassa Secret Key:${NC} "
        read -r YOOKASSA_SECRET_KEY </dev/tty
        if [ -z "$YOOKASSA_SECRET_KEY" ]; then
            echo -e "  ${RED}✗${NC} Secret Key cannot be empty!"
        fi
    done
    echo -e "  ${GREEN}✓${NC} YooKassa Secret Key saved"
    echo ""
    
    echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
    echo -e "${GREEN}✓ Configuration complete! Starting installation...${NC}"
    echo -e "${CYAN}──────────────────────────────────────────────────────────────${NC}"
    sleep 2
}

install_system() {
    print_step "Installing system packages"
    
    print_info "Updating apt..."
    apt-get update -qq &
    spinner $!
    
    print_info "Installing python3, pip, git..."
    apt-get install -y python3 python3-pip python3-venv git wget curl \
        libjpeg-dev zlib1g-dev libfreetype6-dev libopenblas-dev > /dev/null 2>&1 &
    spinner $!
    
    print_ok "System packages installed"
}

clone_repo() {
    print_step "Cloning repository"
    
    if [ -d "$INSTALL_DIR" ]; then
        print_info "Removing old installation..."
        rm -rf "$INSTALL_DIR"
    fi
    
    print_info "Cloning from GitHub..."
    git clone --depth 1 "$GITHUB_REPO" "$INSTALL_DIR" > /dev/null 2>&1 &
    spinner $!
    
    print_ok "Repository cloned"
}

# Function to inject configuration into vpn.py
inject_vpn_config() {
    print_step "Injecting configuration into vpn.py"
    
    cd "$INSTALL_DIR"
    
    # Replace TOKEN in vpn.py
    if [ -f "vpn.py" ]; then
        sed -i "s/TOKEN = 'ваш токен'/TOKEN = '$BOT_TOKEN'/" vpn.py
        sed -i "s/ADMIN_ID = айди в тг ваш/ADMIN_ID = $ADMIN_ID/" vpn.py
        print_ok "Bot Token and Admin ID configured in vpn.py"
    else
        print_err "vpn.py not found!"
    fi
}

# Function to create yookassa_integration.py with configuration
create_yookassa_file() {
    print_step "Creating yookassa_integration.py"
    
    cat > "$INSTALL_DIR/yookassa_integration.py" << EOF
import uuid
import logging
from yookassa import Configuration, Payment
from datetime import datetime

logger = logging.getLogger(__name__)

# Настройки ЮKassa
YOOKASSA_SHOP_ID = "$YOOKASSA_SHOP_ID"
YOOKASSA_SECRET_KEY = "$YOOKASSA_SECRET_KEY"

# Инициализация ЮKassa
Configuration.configure(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)

def create_yookassa_payment(amount, description, payment_id, user_id, username, payment_method=None):
    """Создает платеж в ЮKassa с выбором способа оплаты"""
    try:
        # Формируем уникальный ID платежа
        idempotence_key = str(uuid.uuid4())
        
        # Базовые параметры платежа
        payment_params = {
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/karachay_aj_bot?check_payment_{payment_id}"
            },
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": str(user_id),
                "username": username,
                "amount": amount
            },
            "capture": True
        }
        
        # Добавляем метод оплаты если указан (для тестового магазина доступны карты и ЮMoney)
        if payment_method:
            payment_methods_map = {
                "bank_card": {"type": "bank_card"},
                "yoo_money": {"type": "yoo_money"},
                "sberbank": {"type": "sberbank"},
                "alfabank": {"type": "alfabank"},
                "tinkoff_bank": {"type": "tinkoff_bank"},
                "mobile_balance": {"type": "mobile_balance"}
            }
            
            if payment_method in payment_methods_map:
                payment_params["payment_method_data"] = payment_methods_map[payment_method]
        
        # Создаем платеж
        payment = Payment.create(payment_params, idempotence_key)
        
        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status
        }
    except Exception as e:
        logger.error(f"Ошибка создания платежа ЮKassa: {e}")
        return None

def create_payment_with_methods_menu(user_id, amount, description, payment_id, username):
    """Создает платеж с выбором способа оплаты через меню"""
    try:
        # Создаем платеж с возможностью выбора способа
        idempotence_key = str(uuid.uuid4())
        
        payment_params = {
            "amount": {
                "value": amount,
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/karachay_aj_bot?check_payment_{payment_id}"
            },
            "description": description,
            "metadata": {
                "payment_id": payment_id,
                "user_id": str(user_id),
                "username": username,
                "amount": amount
            },
            "capture": True
        }
        
        payment = Payment.create(payment_params, idempotence_key)
        
        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status
        }
    except Exception as e:
        logger.error(f"Ошибка создания платежа: {e}")
        return None

def check_payment_status(payment_id):
    """Проверяет статус платежа в ЮKassa"""
    try:
        payment = Payment.find_one(payment_id)
        return {
            "status": payment.status,
            "paid": payment.paid,
            "amount": payment.amount.value if hasattr(payment, 'amount') else None
        }
    except Exception as e:
        logger.error(f"Ошибка проверки платежа: {e}")
        return None

def capture_payment(payment_id):
    """Подтверждает платеж (если нужно)"""
    try:
        payment = Payment.capture(payment_id)
        return payment.status == "succeeded"
    except Exception as e:
        logger.error(f"Ошибка подтверждения платежа: {e}")
        return False
EOF

    print_ok "yookassa_integration.py created with configuration"
}

setup_venv() {
    print_step "Setting up Python environment"
    
    cd "$INSTALL_DIR"
    
    print_info "Creating virtual environment..."
    python3 -m venv venv &
    spinner $!
    
    source venv/bin/activate
    
    print_info "Upgrading pip..."
    pip install --upgrade pip -q &
    spinner $!
    
    print_ok "Virtual environment ready"
}

install_python() {
    print_step "Installing Python packages"
    
    cd "$INSTALL_DIR"
    source venv/bin/activate
    
    local pkgs=(
        "pyTelegramBotAPI"
        "qrcode"
        "Pillow"
        "openpyxl"
        "pandas"
        "numpy"
        "yookassa"
        "python-dotenv"
        "requests"
    )
    
    for pkg in "${pkgs[@]}"; do
        print_info "Installing ${pkg}..."
        pip install --no-cache-dir "$pkg" -q &
        spinner $!
    done
    
    print_ok "All Python packages installed"
}

create_req() {
    print_step "Creating requirements.txt"
    
    cat > "$INSTALL_DIR/requirements.txt" << 'EOF'
telebot
qrcode
Pillow
openpyxl
pandas
numpy
yookassa
python-dotenv
EOF

    print_ok "requirements.txt created"
}

create_dirs() {
    print_step "Creating directories"
    
    cd "$INSTALL_DIR"
    mkdir -p backups exports
    chmod 755 backups exports
    
    print_ok "Directories created"
}

create_service() {
    print_step "Creating systemd service"
    
    cat > "/etc/systemd/system/${SERVICE_NAME}.service" << EOF
[Unit]
Description=Xrary VPN Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin"
ExecStart=${INSTALL_DIR}/venv/bin/python3 ${INSTALL_DIR}/vpn.py
Restart=always
RestartSec=10
StandardOutput=append:${INSTALL_DIR}/bot.log
StandardError=append:${INSTALL_DIR}/bot_error.log

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    print_ok "Service created"
}

create_cmd() {
    print_step "Creating global command 'xrary'"
    
    cat > "/usr/local/bin/xrary" << 'EOF'
#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

SERVICE_NAME="xrary-bot"
INSTALL_DIR="/opt/xrary-vpn-bot"

show_header() {
    echo -e "${CYAN}"
    echo "   ██╗  ██╗██████╗  █████╗ ██████╗ ██╗   ██╗"
    echo "   ╚██╗██╔╝██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝"
    echo "    ╚███╔╝ ██████╔╝███████║██████╔╝ ╚████╔╝ "
    echo "    ██╔██╗ ██╔══██╗██╔══██║██╔══██╗  ╚██╔╝  "
    echo "   ██╔╝ ██╗██║  ██║██║  ██║██║  ██║   ██║   "
    echo "   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   "
    echo -e "${NC}"
    echo -e "${WHITE}            VPN Telegram Bot Manager${NC}"
    echo -e "${BLUE}                 thetemirbolatov${NC}"
    echo ""
}

case "$1" in
    start)
        echo -e "${CYAN}▸ Starting bot...${NC}"
        systemctl start ${SERVICE_NAME}
        sleep 2
        if systemctl is-active --quiet ${SERVICE_NAME}; then
            echo -e "${GREEN}✓ Bot started${NC}"
        else
            echo -e "${RED}✗ Failed to start${NC}"
        fi
        ;;
    stop)
        echo -e "${YELLOW}▸ Stopping bot...${NC}"
        systemctl stop ${SERVICE_NAME}
        echo -e "${GREEN}✓ Bot stopped${NC}"
        ;;
    restart)
        echo -e "${CYAN}↻ Restarting bot...${NC}"
        systemctl restart ${SERVICE_NAME}
        sleep 2
        if systemctl is-active --quiet ${SERVICE_NAME}; then
            echo -e "${GREEN}✓ Bot restarted${NC}"
        else
            echo -e "${RED}✗ Failed to restart${NC}"
        fi
        ;;
    status)
        show_header
        systemctl status ${SERVICE_NAME}
        ;;
    logs)
        echo -e "${CYAN}▸ Showing logs (Ctrl+C to exit)...${NC}"
        journalctl -u ${SERVICE_NAME} -f
        ;;
    info)
        show_header
        echo -e "${WHITE}Bot Information:${NC}\n"
        echo -e "  ${BLUE}Author:${NC}     thetemirbolatov"
        echo -e "  ${BLUE}GitHub:${NC}     thetemirbolatov"
        echo -e "  ${BLUE}Version:${NC}    2.0.0"
        echo -e "  ${BLUE}Directory:${NC}  ${INSTALL_DIR}"
        echo ""
        if systemctl is-active --quiet ${SERVICE_NAME}; then
            echo -e "  ${GREEN}● Status:${NC}    Running"
            PID=$(systemctl show --property=MainPID --value ${SERVICE_NAME})
            echo -e "  ${GREEN}● PID:${NC}       ${PID}"
        else
            echo -e "  ${RED}● Status:${NC}    Stopped"
        fi
        echo ""
        echo -e "${CYAN}Contacts:${NC} @thetemirbolatov"
        echo ""
        ;;
    config)
        show_header
        echo -e "${WHITE}Current Configuration:${NC}\n"
        if [ -f "${INSTALL_DIR}/vpn.py" ]; then
            TOKEN=$(grep "^TOKEN = " "${INSTALL_DIR}/vpn.py" 2>/dev/null | cut -d"'" -f2)
            ADMIN=$(grep "^ADMIN_ID = " "${INSTALL_DIR}/vpn.py" 2>/dev/null | grep -o '[0-9]*')
            if [ -n "$TOKEN" ]; then
                echo -e "  ${BLUE}Bot Token:${NC}    ${TOKEN:0:15}..."
            fi
            if [ -n "$ADMIN" ]; then
                echo -e "  ${BLUE}Admin ID:${NC}     ${ADMIN}"
            fi
        fi
        if [ -f "${INSTALL_DIR}/yookassa_integration.py" ]; then
            SHOP_ID=$(grep "^YOOKASSA_SHOP_ID = " "${INSTALL_DIR}/yookassa_integration.py" 2>/dev/null | cut -d'"' -f2)
            if [ -n "$SHOP_ID" ]; then
                echo -e "  ${BLUE}Shop ID:${NC}      ${SHOP_ID}"
            fi
        fi
        echo ""
        ;;
    uninstall)
        echo -e "${RED}╔══════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║              WARNING! UNINSTALL               ║${NC}"
        echo -e "${RED}╚══════════════════════════════════════════════╝${NC}"
        echo ""
        read -p "Type 'YES' to confirm: " confirm
        if [ "$confirm" = "YES" ]; then
            systemctl stop ${SERVICE_NAME} 2>/dev/null
            systemctl disable ${SERVICE_NAME} 2>/dev/null
            rm -f /etc/systemd/system/${SERVICE_NAME}.service
            rm -f /usr/local/bin/xrary
            rm -rf ${INSTALL_DIR}
            systemctl daemon-reload
            echo -e "${GREEN}✓ Xrary VPN Bot removed${NC}"
        else
            echo -e "${CYAN}▸ Cancelled${NC}"
        fi
        ;;
    *)
        show_header
        echo -e "${WHITE}Usage:${NC} xrary {command}\n"
        echo -e "${CYAN}Commands:${NC}"
        echo -e "  ${GREEN}start${NC}      Start bot"
        echo -e "  ${GREEN}stop${NC}       Stop bot"
        echo -e "  ${GREEN}restart${NC}    Restart bot"
        echo -e "  ${GREEN}status${NC}     Check status"
        echo -e "  ${GREEN}logs${NC}       View logs"
        echo -e "  ${GREEN}info${NC}       Bot info"
        echo -e "  ${GREEN}config${NC}     Show config"
        echo -e "  ${GREEN}uninstall${NC}  Remove bot"
        echo ""
        echo -e "${BLUE}────────────────────────────────────────────${NC}"
        echo -e "${WHITE}Author:${NC} thetemirbolatov"
        echo -e "${WHITE}GitHub:${NC} thetemirbolatov"
        echo ""
        ;;
esac
EOF

    chmod +x /usr/local/bin/xrary
    print_ok "Command 'xrary' created"
}

start_bot() {
    print_step "Starting bot"
    
    systemctl enable ${SERVICE_NAME} > /dev/null 2>&1
    systemctl start ${SERVICE_NAME}
    
    print_info "Waiting for bot..."
    progress 2
    
    if systemctl is-active --quiet ${SERVICE_NAME}; then
        print_ok "Bot started successfully"
    else
        print_err "Failed to start"
        print_info "Check logs: journalctl -u ${SERVICE_NAME} -n 20"
    fi
}

show_done() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           INSTALLATION COMPLETE!              ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${WHITE}XRARY VPN BOT${NC} ${BLUE}v${VERSION}${NC}"
    echo -e "${CYAN}Author:${NC} thetemirbolatov"
    echo ""
    echo -e "${WHITE}Configuration:${NC}"
    echo -e "  ${BLUE}Bot Token:${NC}   ${BOT_TOKEN:0:15}..."
    echo -e "  ${BLUE}Admin ID:${NC}    ${ADMIN_ID}"
    echo -e "  ${BLUE}Shop ID:${NC}     ${YOOKASSA_SHOP_ID}"
    echo ""
    echo -e "${WHITE}Commands:${NC}"
    echo -e "  ${GREEN}xrary start${NC}     Start bot"
    echo -e "  ${GREEN}xrary stop${NC}      Stop bot"
    echo -e "  ${GREEN}xrary restart${NC}   Restart bot"
    echo -e "  ${GREEN}xrary status${NC}    Check status"
    echo -e "  ${GREEN}xrary logs${NC}      View logs"
    echo -e "  ${GREEN}xrary info${NC}      Bot info"
    echo -e "  ${GREEN}xrary config${NC}    Show config"
    echo -e "  ${GREEN}xrary uninstall${NC} Remove bot"
    echo ""
    echo -e "${CYAN}Contacts:${NC} @thetemirbolatov (Telegram, VK, Instagram)"
    echo -e "${CYAN}GitHub:${NC} thetemirbolatov"
    echo ""
}

main() {
    print_header
    check_root
    check_net
    get_configuration
    install_system
    clone_repo
    inject_vpn_config
    create_yookassa_file
    setup_venv
    install_python
    create_req
    create_dirs
    create_service
    create_cmd
    start_bot
    show_done
}

main "$@"
