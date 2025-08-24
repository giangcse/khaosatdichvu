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
SPREADSHEET_ID = "1LjkkEfzYKyCCF2j23n_Ikdi_-5onXBUqtI6-3lYtrSk"  # Thay bằng ID của Google Sheet của bạn
WORKSHEET_NAME = "TONGHOP"  # Tên sheet trong Google Sheet

def get_google_sheets_client():
    """Tạo client để kết nối với Google Sheets"""
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        print(f"Lỗi khi kết nối Google Sheets: {e}")
        return None


def _format_channel_speeds(data):
    """Format thông tin tốc độ kênh"""
    service_value = data.get("dich_vu_8", "")
    if service_value in ["Không"] or not service_value:
        return None

    try:
        channel_count = int(service_value.split(" ")[0])
        speeds = []
        for i in range(1, channel_count + 1):
            speed = data.get(f"toc_do_kenh_{i}", "")
            if speed:
                speeds.append(f"K{i}:{speed}Mbps")

        return ", ".join(speeds) if speeds else None
    except (ValueError, IndexError):
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

        # Hàm helper để tạo giá trị với thông tin chi tiết
        def format_service_value(
            service_value, quantity=None, additional_info=None, reason=None
        ):
            if not service_value:
                return ""

            # Xử lý trường hợp "Không" với lý do
            if service_value == "Không" and reason:
                return f"Không ({reason})"
            elif service_value == "Không":
                return "Không"

            result = service_value
            if quantity:
                result += f" (Số lượng: {quantity})"
            if additional_info:
                result += f" - {additional_info}"
            return result

        # Hàm helper đặc biệt cho Camera xã phường
        def format_camera_value(service_value, appointment_date=None, reason=None):
            if not service_value:
                return ""

            # Xử lý trường hợp "Không" với lý do
            if service_value == "Không" and reason:
                return f"Không ({reason})"
            elif service_value == "Không":
                return "Không"

            if service_value == "Có" and appointment_date:
                # Chuyển đổi format ngày từ YYYY-MM-DD sang dd/mm/YYYY
                try:
                    date_obj = datetime.strptime(appointment_date, "%Y-%m-%d")
                    formatted_date = date_obj.strftime("%d/%m/%Y")
                    return f"Hẹn ngày khảo sát ({formatted_date})"
                except:
                    return f"Hẹn ngày khảo sát ({appointment_date})"

            return service_value

        # Tạo row data theo cấu trúc thực tế của Google Sheet
        row_data = [
            data.get("xaphuong", ""),  # Tên phường xã
            data.get("diaban", ""),  # Địa bàn VNPT
            data.get("nhan_vien_khao_sat", ""),  # Nhân viên khảo sát
            data.get("so_dien_thoai_nv", ""),  # Số điện thoại nhân viên
            data.get("nguoi_dau_moi", ""),  # Người đầu mối
            data.get("chuc_vu", ""),  # Chức vụ
            data.get("so_dien_thoai_dm", ""),  # Số điện thoại đầu mối
            format_service_value(
                data.get("dich_vu_1", ""),
                data.get("so_luong_1", ""),
                None,
                data.get("ly_do_1", ""),
            ),  # Biên lai điện tử
            format_service_value(
                data.get("dich_vu_2", ""),
                data.get("so_luong_2", ""),
                None,
                data.get("ly_do_2", ""),
            ),  # Kiosk AI
            format_service_value(
                data.get("dich_vu_3", ""),
                data.get("so_luong_3", ""),
                None,
                data.get("ly_do_3", ""),
            ),  # Kiosk bắt số
            format_service_value(
                data.get("dich_vu_4", ""), None, None, data.get("ly_do_4", "")
            ),  # Hội nghị TT
            format_service_value(
                data.get("dich_vu_5", ""),
                data.get("so_luong_5", ""),
                None,
                data.get("ly_do_5", ""),
            ),  # Hệ thống Wifi
            format_service_value(
                data.get("dich_vu_6", ""),
                data.get("so_luong_6", ""),
                None,
                data.get("ly_do_6", ""),
            ),  # Camera HCC
            format_camera_value(
                data.get("dich_vu_7", ""),
                data.get("lich_hen_7", ""),
                data.get("ly_do_7", ""),
            ),  # Camera xã phường
            format_service_value(
                data.get("dich_vu_8", ""),
                None,
                (
                    _format_channel_speeds(data)
                    if data.get("dich_vu_8") not in ["Không"]
                    else None
                ),
                data.get("ly_do_8", ""),
            ),  # Kênh TSL CD
            format_service_value(
                data.get("dich_vu_9", ""),
                data.get("so_luong_9", ""),
                None,
                data.get("ly_do_9", ""),
            ),  # AI cho CCVC
            format_service_value(
                data.get("dich_vu_10", ""),
                data.get("so_luong_10", ""),
                None,
                data.get("ly_do_10", ""),
            ),  # Smart IR
            format_service_value(
                data.get("dich_vu_11", ""),
                data.get("so_luong_11", ""),
                None,
                data.get("ly_do_11", ""),
            ),  # Firewall S-Gate
            format_service_value(
                data.get("dich_vu_12", ""), None, None, data.get("ly_do_12", "")
            ),  # VNPT Money
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


@app.route("/api/xaphuong")
def get_xaphuong_data():
    """API endpoint để lấy dữ liệu xã phường"""
    try:
        with open("xaphuong.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data, "count": len(data)})
    except Exception as e:
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Lỗi khi đọc dữ liệu xã phường: {str(e)}",
                }
            ),
            500,
        )


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
