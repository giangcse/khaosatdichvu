import json
import os
from datetime import datetime

try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:  # pragma: no cover
    gspread = None
    Credentials = None


SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1LjkkEfzYKyCCF2j23n_Ikdi_-5onXBUqtI6-3lYtrSk")
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "TONGHOP")


def get_google_sheets_client():
    if not gspread or not Credentials:
        return None
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception:
        return None


def normalize_area_name(area_name: str) -> str:
    if not area_name:
        return ""
    s = area_name.strip()
    for p in [
        "Xã ", "Phường ", "Thị trấn ", "Thị xã ",
        "xã ", "phường ", "thị trấn ", "thị xã ",
    ]:
        if s.startswith(p):
            s = s[len(p):].strip()
            break
    return s


def extract_service_status(service_value, service_column=None) -> str:
    if not service_value:
        return "Không"
    s = str(service_value).strip()
    if s == "":
        return "Không"
    lower = s.lower()
    if s.isdigit():
        return "Có" if int(s) > 0 else "Không"
    if lower.startswith("có"):
        return "Có"
    if lower.startswith("không"):
        return "Không"
    if (service_column and ("camera" in service_column.lower()) and ("xã" in service_column.lower())):
        if "hẹn" in lower and ("khảo sát" in lower or "ngày" in lower):
            return "Có"
    if any(w in lower for w in ["có", "yes", "đã có", "sẵn sàng", "x", "✓", "√", "true"]):
        return "Có"
    if any(w in lower for w in ["không", "no", "chưa có", "không có", "false"]):
        return "Không"
    if any(w in lower for w in ["hẹn", "đang", "dự kiến", "pending"]):
        return "Đang triển khai"
    return "Có"


def generate_sample_survey_data():
    import random
    try:
        base_static = os.path.join(os.path.dirname(__file__), '..', 'static')
        with open(os.path.join(base_static, "xaphuong.json"), "r", encoding="utf-8") as f:
            xaphuong_list = json.load(f)
    except Exception:
        xaphuong_list = []
    sample_data = {}
    sample_areas_raw = [
        "Xã Cái Nhum", "Xã An Bình", "Xã An Hiệp",
        "Phường An Hội", "Phường Bến Tre", "Xã Càng Long",
        "Phường Bình Minh", "Phường Cái Vồn", "Xã Tân Phú",
        "Xã Giồng Trôm", "Xã Long Hồ", "Xã Tam Bình",
    ]
    for raw in sample_areas_raw:
        norm = normalize_area_name(raw)
        diaban = "Vĩnh Long (cũ)"
        for item in xaphuong_list:
            if normalize_area_name(item.get("xaphuong", "")) == norm:
                diaban = item.get("diaban", diaban)
                break
        rec = {
            "xaphuong": raw,
            "xaphuong_normalized": norm,
            "diaban": diaban,
            "nhan_vien_khao_sat": f"NV{random.randint(1, 10)}",
        }
        for i in range(1, 13):
            rec[f"dich_vu_{i}"] = random.choice(["Có", "Không", "Đang triển khai"])
        sample_data[norm] = rec
    return sample_data


def get_survey_data_from_sheets():
    client = get_google_sheets_client()
    if not client:
        return generate_sample_survey_data()
    try:
        sh = client.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet(WORKSHEET_NAME)
        all_values = ws.get_all_values()
        if not all_values:
            return {}
        data_rows = all_values[1:] if len(all_values) > 1 else []
        service_columns = {
            7: "Biên lai điện tử",
            8: "Kiosk AI",
            9: "Kiosk bắt số",
            10: "Hội nghị TT",
            11: "Hệ thống Wifi",
            12: "Camera HCC",
            13: "Camera xã phường",
            14: "Kênh TSL CD",
            15: "AI cho CCVC",
            16: "Smart IR",
            17: "Firewall S-Gate",
            18: "VNPT Money",
        }
        out = {}
        for row in data_rows:
            if not row:
                continue
            raw_name = (row[0] or "").strip() if len(row) > 0 else ""
            if not raw_name:
                continue
            norm = normalize_area_name(raw_name)
            service_details = {}
            service_raw = {}
            count_yes = 0
            for col_idx, service_name in service_columns.items():
                val = (row[col_idx].strip() if col_idx < len(row) and row[col_idx] else "")
                status = extract_service_status(val, service_name)
                key = f"dich_vu_{col_idx - 6}"
                service_details[key] = status
                if val:
                    service_raw[key] = val
                if status == "Có":
                    count_yes += 1
            out[norm] = {
                **service_details,
                "xaphuong": raw_name,
                "xaphuong_normalized": norm,
                "total_services": count_yes,
                "service_details": service_raw,
                "diaban": row[1] if len(row) > 1 else "",
                "nhan_vien_khao_sat": row[2] if len(row) > 2 else "",
            }
        return out
    except Exception:
        return generate_sample_survey_data()
