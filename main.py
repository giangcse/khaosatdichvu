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

@app.route('/sw.js')
def service_worker():
    """Serve Service Worker file"""
    try:
        with open('sw.js', 'r', encoding='utf-8') as f:
            response = app.response_class(
                f.read(),
                mimetype='application/javascript'
            )
            # Cache control for service worker
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response
    except FileNotFoundError:
        return "Service Worker not found", 404

@app.route('/offline-manager.js')
def offline_manager():
    """Serve Offline Manager JavaScript file"""
    try:
        with open('offline-manager.js', 'r', encoding='utf-8') as f:
            response = app.response_class(
                f.read(),
                mimetype='application/javascript'
            )
            return response
    except FileNotFoundError:
        return "Offline Manager not found", 404

@app.route('/manifest.json')
def manifest():
    """Serve PWA Manifest file"""
    try:
        with open('manifest.json', 'r', encoding='utf-8') as f:
            response = app.response_class(
                f.read(),
                mimetype='application/json'
            )
            return response
    except FileNotFoundError:
        return "Manifest not found", 404


@app.route("/map")
def map_page():
    """Trang bản đồ heatmap"""
    try:
        with open("map.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Map page not found", 404


@app.route("/api/map-data")
def get_map_data():
    """API endpoint để lấy dữ liệu cho bản đồ heatmap"""
    try:
        # Load boundary data from GeoJSON file
        with open("vinh_long_boundaries.geojson", "r", encoding="utf-8") as f:
            boundaries_data = json.load(f)

        # Get real survey data from Google Sheets
        # Falls back to sample data if Google Sheets is not available
        surveys_data = get_survey_data_from_sheets()

        # Process areas from boundaries
        areas = []
        for feature in boundaries_data["features"]:
            # Get area name from GeoJSON properties
            area_name = feature["properties"].get("ten_xa", "")
            province_name = feature["properties"].get("ten_tinh", "")

            # Handle MultiPolygon geometry
            geometry = feature["geometry"]
            if geometry["type"] == "MultiPolygon":
                # Use the first polygon from MultiPolygon
                coordinates = geometry["coordinates"][0][0]
            elif geometry["type"] == "Polygon":
                # Use the first ring of polygon
                coordinates = geometry["coordinates"][0]
            else:
                continue  # Skip unsupported geometry types

            if area_name:
                areas.append(
                    {
                        "name": area_name,
                        "coordinates": coordinates,
                        "province": province_name,
                    }
                )

        return jsonify(
            {
                "success": True,
                "areas": areas,
                "surveys": surveys_data,
                "total_areas": len(areas),
                "surveyed_areas": len(
                    [k for k, v in surveys_data.items() if v is not None]
                ),
            }
        )

    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu bản đồ: {e}")
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500


def get_survey_data_from_sheets():
    """Get real survey data from Google Sheets"""
    try:
        client = get_google_sheets_client()
        if not client:
            return {}

        # Mở spreadsheet
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

        # Lấy dữ liệu dạng raw để xử lý flexible hơn
        all_values = worksheet.get_all_values()

        # Kiểm tra nếu có header row
        if not all_values:
            return {}

        headers = all_values[0] if all_values else []
        data_rows = all_values[1:] if len(all_values) > 1 else []

        # Headers information (debug disabled for production)

        surveys_data = {}

        for row_idx, row in enumerate(data_rows):
            if not row or len(row) == 0:
                continue

            # Cột A (index 0) chứa tên xã/phường
            xaphuong_raw = row[0].strip() if len(row) > 0 and row[0] else ""

            if not xaphuong_raw:
                continue

            # Chuẩn hóa tên để mapping với GeoJSON
            xaphuong_normalized = normalize_area_name(xaphuong_raw)

            # Processing area (debug disabled for production)

            # Đếm số dịch vụ từ cột H-S (index 7-18) - 12 dịch vụ cụ thể
            service_count = 0
            service_details = {}
            service_raw_values = {}  # Lưu giá trị gốc để hiển thị

            # Define service column mapping (H-S = columns 7-18 in 0-based index)
            service_columns = {
                7: "Biên lai điện tử",  # Column H
                8: "Kiosk AI",  # Column I
                9: "Kiosk bắt số",  # Column J
                10: "Hội nghị TT",  # Column K
                11: "Hệ thống Wifi",  # Column L
                12: "Camera HCC",  # Column M
                13: "Camera xã phường",  # Column N
                14: "Kênh TSL CD",  # Column O
                15: "AI cho CCVC",  # Column P
                16: "Smart IR",  # Column Q
                17: "Firewall S-Gate",  # Column R
                18: "VNPT Money",  # Column S
            }

            # Duyệt qua các cột dịch vụ H-S (index 7-18)
            for col_idx, service_name in service_columns.items():
                cell_value = ""
                if col_idx < len(row):
                    cell_value = row[col_idx].strip() if row[col_idx] else ""

                # Xác định trạng thái dịch vụ, truyền thêm tên cột để xử lý đặc biệt
                service_status = extract_service_status(cell_value, service_name)
                service_key = f"dich_vu_{col_idx - 6}"  # Map to dich_vu_1-12 (H=1, I=2, ..., S=12)
                service_details[service_key] = service_status

                # Lưu giá trị gốc để hiển thị
                if cell_value:
                    service_raw_values[service_key] = cell_value

                # Đếm các dịch vụ có
                if service_status == "Có":
                    service_count += 1

                # Service processing (debug disabled for production)

            # Tạo bản ghi dữ liệu với key là tên đã chuẩn hóa
            surveys_data[xaphuong_normalized] = {
                **service_details,
                "xaphuong": xaphuong_raw,  # Giữ tên gốc
                "xaphuong_normalized": xaphuong_normalized,  # Tên đã chuẩn hóa
                "total_services": service_count,
                "service_details": service_raw_values,  # Giá trị gốc để hiển thị chi tiết
                "diaban": (row[1] if len(row) > 1 else ""),  # Cột B là địa bàn VNPT
            }

            # Total services count (debug disabled for production)

        return surveys_data
    except Exception as e:
        print(f"Lỗi khi lấy dữ liệu từ Google Sheets: {e}")
        return generate_sample_survey_data()


def normalize_area_name(area_name):
    """Chuẩn hóa tên xã/phường để mapping giữa Google Sheets và GeoJSON"""
    if not area_name:
        return ""

    # Loại bỏ khoảng trắng thừa
    normalized = area_name.strip()

    # Loại bỏ tiền tố phân loại (Xã, Phường, Thị trấn, ...)
    prefixes_to_remove = [
        "Xã ",
        "Phường ",
        "Thị trấn ",
        "Thị xã ",
        "xã ",
        "phường ",
        "thị trấn ",
        "thị xã ",
    ]

    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix) :].strip()
            break

    return normalized


def extract_service_status(service_value, service_column=None):
    """Extract service status from Google Sheets cell value with complex format support

    Handles formats like:
    - "Có (số lượng 5)" -> "Có"
    - "Không (lý do xyz)" -> "Không"
    - "Hẹn ngày khảo sát (28/08/2025)" -> "Có" (for Camera xã phường only)
    """
    if not service_value:
        return "Không"

    service_str = str(service_value).strip()
    service_str_lower = service_str.lower()

    # Trường hợp rỗng hoặc chỉ có khoảng trắng
    if not service_str:
        return "Không"

    # Xử lý số (1 = Có, 0 hoặc rỗng = Không)
    if service_str.isdigit():
        return "Có" if int(service_str) > 0 else "Không"

    # Xử lý định dạng "Có (số lượng...)" hoặc "Có (...)"
    if service_str_lower.startswith("có"):
        return "Có"

    # Xử lý định dạng "Không (...)"
    if service_str_lower.startswith("không"):
        return "Không"

    # Xử lý đặc biệt cho Camera xã phường: "Hẹn ngày khảo sát (...)"
    if (
        service_column
        and "camera" in service_column.lower()
        and "xã" in service_column.lower()
    ):
        if "hẹn" in service_str_lower and (
            "khảo sát" in service_str_lower or "ngày" in service_str_lower
        ):
            return "Có"  # Camera xã phường với "Hẹn ngày khảo sát" = "Có"

    # Xử lý các từ khóa khác trong nội dung
    if any(
        word in service_str_lower
        for word in ["có", "yes", "đã có", "sẵn sàng", "x", "✓", "√", "true"]
    ):
        return "Có"
    elif any(
        word in service_str_lower
        for word in ["không", "no", "chưa có", "không có", "false"]
    ):
        return "Không"
    elif any(
        word in service_str_lower for word in ["hẹn", "đang", "dự kiến", "pending"]
    ):
        # Các dịch vụ khác với "hẹn", "đang triển khai" vẫn là trạng thái trung gian
        return "Đang triển khai"
    else:
        # Nếu có nội dung gì đó (không rỗng) và không match pattern nào thì coi như "Có"
        return "Có" if service_str else "Không"


def generate_sample_survey_data():
    """Generate sample survey data for demonstration when Google Sheets is not available"""
    import random

    # Load xaphuong data để tạo sample data
    try:
        with open("xaphuong.json", "r", encoding="utf-8") as f:
            xaphuong_list = json.load(f)
    except:
        xaphuong_list = []

    sample_data = {}

    # Tạo dữ liệu mẫu cho một số xã/phường (sử dụng tên từ GeoJSON)
    sample_areas_raw = [
        "Xã Cái Nhum",
        "Xã An Bình",
        "Xã An Hiệp",
        "Phường An Hội",
        "Phường Bến Tre",
        "Xã Càng Long",
        "Phường Bình Minh",
        "Phường Cái Vồn",
        "Xã Tân Phú",
        "Xã Giồng Trôm",
        "Xã Long Hồ",
        "Xã Tam Bình",
    ]

    for area_name_raw in sample_areas_raw:
        # Chuẩn hóa tên
        area_name_normalized = normalize_area_name(area_name_raw)

        # Tìm diaban tương ứng
        diaban = "Vĩnh Long (cũ)"  # Default
        for item in xaphuong_list:
            # So sánh với tên đã chuẩn hóa
            if normalize_area_name(item.get("xaphuong", "")) == area_name_normalized:
                diaban = item["diaban"]
                break

        # Random số dịch vụ (6-12 dịch vụ)
        num_services = random.randint(6, 12)
        service_indices = random.sample(range(1, 13), num_services)

        area_data = {
            "xaphuong": area_name_raw,  # Tên gốc
            "xaphuong_normalized": area_name_normalized,  # Tên chuẩn hóa
            "diaban": diaban,
        }

        # Khởi tạo tất cả dịch vụ là "Không"
        for i in range(1, 13):
            area_data[f"dich_vu_{i}"] = "Không"

        # Set các dịch vụ được chọn là "Có"
        for i in service_indices:
            area_data[f"dich_vu_{i}"] = "Có"

        # Demo case đặc biệt với format phức tạp - mapping cột H-S
        if area_name_normalized == "Cái Nhum":
            # Map theo cột H-S: H=1, I=2, J=3, K=4, L=5, M=6, N=7, O=8, P=9, Q=10, R=11, S=12
            area_data["dich_vu_1"] = "Có"  # H: Biên lai điện tử
            area_data["dich_vu_2"] = "Có"  # I: Kiosk AI
            area_data["dich_vu_3"] = "Không"  # J: Kiosk bắt số
            area_data["dich_vu_4"] = "Có"  # K: Hội nghị TT
            area_data["dich_vu_5"] = "Không"  # L: Hệ thống Wifi
            area_data["dich_vu_6"] = "Không"  # M: Camera HCC
            area_data["dich_vu_7"] = (
                "Có"  # N: Camera xã phường (Hẹn ngày khảo sát = Có)
            )
            area_data["dich_vu_8"] = "Không"  # O: Kênh TSL CD
            area_data["dich_vu_9"] = "Không"  # P: AI cho CCVC
            area_data["dich_vu_10"] = "Không"  # Q: Smart IR
            area_data["dich_vu_11"] = "Không"  # R: Firewall S-Gate
            area_data["dich_vu_12"] = "Không"  # S: VNPT Money

            # Lưu thông tin chi tiết để demo
            area_data["service_details"] = {
                "dich_vu_1": "Có (số lượng 5)",
                "dich_vu_2": "Có (số lượng 3)",
                "dich_vu_3": "Không (chưa triển khai)",
                "dich_vu_4": "Có",
                "dich_vu_7": "Hẹn ngày khảo sát (28/08/2025)",
            }
        elif area_name_normalized == "Trà Vinh":
            # Demo với dữ liệu thực từ Phường Trà Vinh
            area_data["dich_vu_1"] = "Không"  # H: Biên lai điện tử
            area_data["dich_vu_2"] = "Không"  # I: Kiosk AI
            area_data["dich_vu_3"] = "Không"  # J: Kiosk bắt số
            area_data["dich_vu_4"] = "Có"  # K: Hội nghị TT
            area_data["dich_vu_5"] = "Không"  # L: Hệ thống Wifi
            area_data["dich_vu_6"] = "Không"  # M: Camera HCC
            area_data["dich_vu_7"] = (
                "Có"  # N: Camera xã phường (Hẹn ngày khảo sát = Có)
            )
            area_data["dich_vu_8"] = "Không"  # O: Kênh TSL CD
            area_data["dich_vu_9"] = "Không"  # P: AI cho CCVC
            area_data["dich_vu_10"] = "Không"  # Q: Smart IR
            area_data["dich_vu_11"] = "Không"  # R: Firewall S-Gate
            area_data["dich_vu_12"] = "Không"  # S: VNPT Money

            area_data["service_details"] = {
                "dich_vu_1": "Không (Chưa có nhu cầu)",
                "dich_vu_2": "Không (Chưa có nhu cầu)",
                "dich_vu_3": "Không (Chưa có nhu cầu)",
                "dich_vu_4": "Có",
                "dich_vu_5": "Không (Chưa có nhu cầu)",
                "dich_vu_6": "Không (Chưa có nhu cầu)",
                "dich_vu_7": "Hẹn ngày khảo sát (28/08/2025)",
                "dich_vu_8": "Không (Chưa có nhu cầu)",
                "dich_vu_9": "Không (Chưa có nhu cầu)",
                "dich_vu_10": "Không (Đã ký hợp đồng với nhà cung cấp khác)",
                "dich_vu_11": "Không (Đã ký hợp đồng với nhà cung cấp khác)",
                "dich_vu_12": "Không (Chưa có nhu cầu)",
            }

        # Sử dụng tên chuẩn hóa làm key
        sample_data[area_name_normalized] = area_data

    return sample_data


@app.route("/api/survey-details/<area_name>")
def get_survey_details(area_name):
    """API endpoint để lấy chi tiết khảo sát của một khu vực"""
    try:
        surveys_data = get_survey_data_from_sheets()

        # Thử tìm với tên gốc trước, sau đó với tên chuẩn hóa
        survey = surveys_data.get(area_name)
        if not survey:
            # Thử với tên đã chuẩn hóa
            normalized_name = normalize_area_name(area_name)
            survey = surveys_data.get(normalized_name)

        if not survey:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Không tìm thấy dữ liệu khảo sát cho khu vực này",
                    }
                ),
                404,
            )

        # Calculate statistics
        total_services = 12
        completed_services = sum(
            1 for i in range(1, 13) if survey.get(f"dich_vu_{i}") == "Có"
        )
        completion_rate = (completed_services / total_services) * 100

        # Service details
        services = []
        service_names = {
            "dich_vu_1": "Biên lai điện tử",
            "dich_vu_2": "Kiosk AI",
            "dich_vu_3": "Kiosk bắt số",
            "dich_vu_4": "Hội nghị trực tuyến",
            "dich_vu_5": "Hệ thống WiFi",
            "dich_vu_6": "Camera Hành chính công",
            "dich_vu_7": "Camera xã phường",
            "dich_vu_8": "Kênh truyền số liệu chuyên dụng",
            "dich_vu_9": "AI cho Công chức viên chức",
            "dich_vu_10": "Smart IR",
            "dich_vu_11": "Firewall S-Gate",
            "dich_vu_12": "VNPT-Money",
        }

        for i in range(1, 13):
            service_key = f"dich_vu_{i}"
            services.append(
                {
                    "id": i,
                    "name": service_names[service_key],
                    "status": survey.get(service_key, "Chưa khảo sát"),
                    "available": survey.get(service_key) == "Có",
                }
            )

        return jsonify(
            {
                "success": True,
                "area_name": area_name,
                "survey_data": survey,
                "statistics": {
                    "total_services": total_services,
                    "completed_services": completed_services,
                    "completion_rate": completion_rate,
                },
                "services": services,
            }
        )

    except Exception as e:
        print(f"Lỗi khi lấy chi tiết khảo sát: {e}")
        return jsonify({"success": False, "message": f"Lỗi server: {str(e)}"}), 500


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


@app.route('/api/sync', methods=['POST'])
def sync_offline_data():
    """API endpoint để đồng bộ dữ liệu offline"""
    try:
        data = request.get_json()
        
        if not data or not isinstance(data, list):
            return jsonify({
                'success': False,
                'message': 'Dữ liệu không hợp lệ'
            }), 400
        
        successful_syncs = 0
        failed_syncs = 0
        
        for submission in data:
            try:
                # Loại bỏ các trường metadata offline
                clean_submission = {k: v for k, v in submission.items() 
                                  if k not in ['id', 'timestamp', 'synced', 'syncedAt']}
                
                success, message = submit_to_google_sheet(clean_submission)
                if success:
                    successful_syncs += 1
                else:
                    failed_syncs += 1
                    print(f"Lỗi đồng bộ submission: {message}")
            except Exception as e:
                failed_syncs += 1
                print(f"Lỗi xử lý submission: {e}")
        
        return jsonify({
            'success': True,
            'message': f'Đã đồng bộ {successful_syncs} khảo sát thành công',
            'successful': successful_syncs,
            'failed': failed_syncs
        })
        
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
        'message': 'Server đang hoạt động bình thường',
        'offline_support': True
    })

if __name__ == '__main__':
    print("Khởi động server khảo sát...")
    print("Truy cập: http://localhost:5000")
    app.run(debug=False, host="0.0.0.0", port=5000)
