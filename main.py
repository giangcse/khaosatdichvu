from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Cấu hình Google Sheets API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Đường dẫn đến file credentials (bạn cần tạo file này)
CREDENTIALS_FILE = 'credentials.json'
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID'  # Thay bằng ID của Google Sheet của bạn
WORKSHEET_NAME = 'Sheet1'  # Tên sheet trong Google Sheet

def get_google_sheets_client():
    """Tạo client để kết nối với Google Sheets"""
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Lỗi khi kết nối Google Sheets: {e}")
        return None

def submit_to_google_sheet(data):
    """Gửi dữ liệu lên Google Sheet"""
    try:
        client = get_google_sheets_client()
        if not client:
            return False, "Không thể kết nối với Google Sheets"
        
        # Mở spreadsheet
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        # Chuẩn bị dữ liệu để gửi
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Tạo row data
        row_data = [
            timestamp,  # Thời gian gửi
            data.get('diaban', ''),
            data.get('xaphuong', ''),
            data.get('dich_vu_1', ''),
            data.get('so_luong_1', ''),
            data.get('dich_vu_2', ''),
            data.get('so_luong_2', ''),
            data.get('dich_vu_3', ''),
            data.get('so_luong_3', ''),
            data.get('dich_vu_4', ''),
            data.get('dich_vu_5', ''),
            data.get('dich_vu_6', ''),
            data.get('dich_vu_7', ''),
            data.get('lich_hen_7', ''),
            data.get('dich_vu_8', ''),
            data.get('toc_do_kenh_1', ''),
            data.get('toc_do_kenh_2', ''),
            data.get('toc_do_kenh_3', ''),
            data.get('toc_do_kenh_4', ''),
            data.get('toc_do_kenh_5', ''),
            data.get('dich_vu_9', ''),
            data.get('dich_vu_10', ''),
            data.get('dich_vu_11', ''),
            data.get('dich_vu_12', '')
        ]
        
        # Thêm row mới vào sheet
        worksheet.append_row(row_data)
        
        return True, "Dữ liệu đã được gửi thành công!"
        
    except Exception as e:
        print(f"Lỗi khi gửi dữ liệu: {e}")
        return False, f"Lỗi khi gửi dữ liệu: {str(e)}"

@app.route('/')
def index():
    """Trang chủ - hiển thị form khảo sát"""
    with open('index.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/submit', methods=['POST'])
def submit_form():
    """Endpoint để nhận và xử lý dữ liệu form"""
    try:
        # Lấy dữ liệu từ request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Không có dữ liệu được gửi'
            }), 400
        
        # Gửi dữ liệu lên Google Sheet
        success, message = submit_to_google_sheet(data)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Lỗi server: {str(e)}'
        }), 500

@app.route('/health')
def health_check():
    """Endpoint kiểm tra trạng thái server"""
    return jsonify({
        'status': 'healthy',
        'message': 'Server đang hoạt động bình thường'
    })

if __name__ == '__main__':
    print("Khởi động server khảo sát...")
    print("Truy cập: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
