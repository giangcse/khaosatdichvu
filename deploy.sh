#!/bin/bash

# Script deploy tự động cho Khaosat Survey Application
set -e

# Cấu hình
APP_NAME="khaosat"
APP_DIR="/var/www/$APP_NAME"
BACKUP_DIR="/var/backups/$APP_NAME"
LOG_DIR="/var/log/$APP_NAME"
VENV_DIR="$APP_DIR/venv"

# Màu sắc cho output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Hàm log
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Kiểm tra quyền root
if [[ $EUID -ne 0 ]]; then
   error "Script này cần chạy với quyền root"
fi

# Tạo thư mục cần thiết
log "Tạo thư mục cần thiết..."
mkdir -p "$APP_DIR" "$BACKUP_DIR" "$LOG_DIR"

# Backup phiên bản cũ (nếu có)
if [ -d "$APP_DIR" ] && [ "$(ls -A $APP_DIR)" ]; then
    log "Tạo backup phiên bản cũ..."
    BACKUP_FILE="$BACKUP_DIR/backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    tar -czf "$BACKUP_FILE" -C "$APP_DIR" .
    log "Backup đã lưu tại: $BACKUP_FILE"
fi

# Copy files mới
log "Copy files mới..."
cp -r . "$APP_DIR/"
chown -R www-data:www-data "$APP_DIR"

# Tạo virtual environment
log "Tạo virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment và cài đặt dependencies
log "Cài đặt dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"

# Cài đặt Gunicorn
log "Cài đặt Gunicorn..."
pip install gunicorn

# Tạo thư mục logs
mkdir -p "$LOG_DIR"
chown -R www-data:www-data "$LOG_DIR"

# Cấu hình systemd service
log "Cấu hình systemd service..."
cp "$APP_DIR/systemd/khaosat.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable khaosat

# Cấu hình Nginx
log "Cấu hình Nginx..."
cp "$APP_DIR/nginx.conf" /etc/nginx/sites-available/khaosat
ln -sf /etc/nginx/sites-available/khaosat /etc/nginx/sites-enabled/

# Kiểm tra cấu hình Nginx
nginx -t || error "Cấu hình Nginx không hợp lệ"

# Restart services
log "Restart services..."
systemctl restart khaosat
systemctl restart nginx

# Kiểm tra trạng thái
log "Kiểm tra trạng thái services..."
sleep 5

if systemctl is-active --quiet khaosat; then
    log "✅ Khaosat service đang chạy"
else
    error "❌ Khaosat service không chạy được"
fi

if systemctl is-active --quiet nginx; then
    log "✅ Nginx service đang chạy"
else
    error "❌ Nginx service không chạy được"
fi

# Kiểm tra health endpoint
log "Kiểm tra health endpoint..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    log "✅ Health check thành công"
else
    warn "⚠️ Health check thất bại - kiểm tra logs"
fi

log "🎉 Deploy hoàn tất!"
log "📝 Lưu ý:"
log "   - Kiểm tra logs: journalctl -u khaosat -f"
log "   - Restart service: systemctl restart khaosat"
log "   - Kiểm tra status: systemctl status khaosat"
log "   - Backup được lưu tại: $BACKUP_DIR"
