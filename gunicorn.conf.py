"""
Cấu hình Gunicorn cho production deployment
"""
import multiprocessing
import os

# Cấu hình worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Cấu hình binding
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:8000')

# Cấu hình timeout
timeout = 30
keepalive = 2
graceful_timeout = 30

# Cấu hình logging
accesslog = os.environ.get('GUNICORN_ACCESS_LOG', '-')
errorlog = os.environ.get('GUNICORN_ERROR_LOG', '-')
loglevel = os.environ.get('GUNICORN_LOG_LEVEL', 'info')

# Cấu hình security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Cấu hình performance
preload_app = True
sendfile = True
reuse_port = True

# Cấu hình SSL (nếu cần)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Cấu hình user/group (nếu chạy với quyền root)
# user = 'www-data'
# group = 'www-data'

# Cấu hình temporary directory
tmp_upload_dir = None
