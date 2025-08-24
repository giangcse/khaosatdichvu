#!/usr/bin/env python3
"""
WSGI entry point cho production deployment
"""
import os
import sys
from pathlib import Path

# Thêm thư mục dự án vào Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import app từ main.py
from main import app

if __name__ == "__main__":
    # Chạy trực tiếp nếu được gọi từ command line
    app.run()
