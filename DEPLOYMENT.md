# Hướng dẫn Deploy Production

## 🚀 Tổng quan

Hướng dẫn này sẽ giúp bạn deploy hệ thống khảo sát lên production một cách an toàn và hiệu quả.

## 📋 Yêu cầu hệ thống

### Server Requirements
- **OS**: Ubuntu 20.04+ hoặc CentOS 8+
- **RAM**: Tối thiểu 2GB (khuyến nghị 4GB+)
- **CPU**: 2 cores trở lên
- **Storage**: 20GB trống
- **Domain**: Có domain name và SSL certificate

### Software Requirements
- Python 3.8+
- Nginx
- Redis (optional, cho caching và rate limiting)
- Certbot (cho SSL)

## 🔧 Cài đặt ban đầu

### 1. Cập nhật hệ thống
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Cài đặt Python và dependencies
```bash
sudo apt install python3 python3-pip python3-venv nginx redis-server -y
```

### 3. Cài đặt Certbot (cho SSL)
```bash
sudo apt install certbot python3-certbot-nginx -y
```

## 📁 Cấu trúc thư mục

```
/var/www/khaosat/
├── venv/                 # Virtual environment
├── logs/                 # Application logs
├── static/              # Static files (nếu có)
├── main.py              # Application code
├── wsgi.py              # WSGI entry point
├── gunicorn.conf.py     # Gunicorn config
├── requirements.txt     # Dependencies
├── credentials.json     # Google API credentials
└── xaphuong.json        # Data file
```

## 🔐 Bảo mật

### 1. Tạo user riêng
```bash
sudo useradd -r -s /bin/false khaosat
sudo usermod -aG www-data khaosat
```

### 2. Cấu hình firewall
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 3. Tạo SSL certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## 🚀 Deploy tự động

### Sử dụng script deploy
```bash
# Clone repository
git clone <your-repo-url> /tmp/khaosat
cd /tmp/khaosat

# Chạy script deploy
chmod +x deploy.sh
sudo ./deploy.sh
```

### Deploy thủ công

#### 1. Tạo thư mục ứng dụng
```bash
sudo mkdir -p /var/www/khaosat
sudo chown www-data:www-data /var/www/khaosat
```

#### 2. Copy code
```bash
sudo cp -r . /var/www/khaosat/
sudo chown -R www-data:www-data /var/www/khaosat
```

#### 3. Tạo virtual environment
```bash
cd /var/www/khaosat
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install -r requirements_production.txt
```

#### 4. Cấu hình environment variables
```bash
sudo cp env.example /var/www/khaosat/.env
sudo nano /var/www/khaosat/.env
```

#### 5. Cấu hình systemd service
```bash
sudo cp systemd/khaosat.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable khaosat
```

#### 6. Cấu hình Nginx
```bash
sudo cp nginx.conf /etc/nginx/sites-available/khaosat
sudo ln -s /etc/nginx/sites-available/khaosat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 7. Khởi động ứng dụng
```bash
sudo systemctl start khaosat
sudo systemctl status khaosat
```

## 🔍 Monitoring và Logs

### Kiểm tra logs
```bash
# Application logs
sudo journalctl -u khaosat -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Application specific logs
sudo tail -f /var/log/khaosat/app.log
```

### Health check
```bash
curl -f https://yourdomain.com/health
```

### Kiểm tra status
```bash
sudo systemctl status khaosat
sudo systemctl status nginx
```

## 🔄 Backup và Recovery

### Backup tự động
```bash
# Tạo script backup
sudo nano /usr/local/bin/backup-khaosat.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/khaosat"
DATE=$(date +%Y%m%d-%H%M%S)
tar -czf "$BACKUP_DIR/backup-$DATE.tar.gz" -C /var/www khaosat
find $BACKUP_DIR -name "backup-*.tar.gz" -mtime +7 -delete
```

### Restore từ backup
```bash
sudo systemctl stop khaosat
sudo tar -xzf backup-YYYYMMDD-HHMMSS.tar.gz -C /var/www/
sudo systemctl start khaosat
```

## 🔧 Maintenance

### Update ứng dụng
```bash
# Backup trước khi update
sudo /usr/local/bin/backup-khaosat.sh

# Pull code mới
cd /var/www/khaosat
sudo -u www-data git pull

# Update dependencies
sudo -u www-data venv/bin/pip install -r requirements_production.txt

# Restart service
sudo systemctl restart khaosat
```

### SSL renewal
```bash
sudo certbot renew --dry-run
```

## 🚨 Troubleshooting

### Lỗi thường gặp

#### 1. Permission denied
```bash
sudo chown -R www-data:www-data /var/www/khaosat
```

#### 2. Port already in use
```bash
sudo netstat -tlnp | grep :8000
sudo systemctl restart khaosat
```

#### 3. Google API errors
- Kiểm tra file `credentials.json`
- Kiểm tra quyền truy cập Google Sheet
- Kiểm tra environment variables

#### 4. Nginx errors
```bash
sudo nginx -t
sudo systemctl status nginx
```

## 📊 Performance Optimization

### 1. Enable caching
```bash
# Cài đặt Redis
sudo apt install redis-server
sudo systemctl enable redis
```

### 2. Optimize Nginx
```bash
# Thêm vào nginx.conf
gzip on;
gzip_types text/plain text/css application/json application/javascript;
```

### 3. Monitor performance
```bash
# Cài đặt monitoring tools
sudo apt install htop iotop
```

## 🔒 Security Checklist

- [ ] SSL certificate đã cài đặt
- [ ] Firewall đã cấu hình
- [ ] User permissions đã set đúng
- [ ] Environment variables đã bảo mật
- [ ] Logs đã được rotate
- [ ] Backup đã được cấu hình
- [ ] Monitoring đã được setup

## 📞 Support

Nếu gặp vấn đề, kiểm tra:
1. Logs của application và nginx
2. Status của các services
3. Network connectivity
4. Google API credentials
5. File permissions
