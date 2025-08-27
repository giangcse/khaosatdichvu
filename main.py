from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import json
import os
from datetime import datetime, timezone

# -------- Google Sheets (optional) --------
try:
    import gspread
    from google.oauth2.service_account import Credentials
except Exception:
    gspread = None
    Credentials = None

app = Flask(__name__, static_folder=".")
CORS(app)

# =========================
# Config
# =========================
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
CREDENTIALS_FILE = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
SPREADSHEET_ID = os.getenv(
    "SPREADSHEET_ID", "1LjkkEfzYKyCCF2j23n_Ikdi_-5onXBUqtI6-3lYtrSk"
)
WORKSHEET_NAME = os.getenv("WORKSHEET_NAME", "TONGHOP")

# =========================
# Google Sheets helpers
# =========================

def get_google_sheets_client():
    """Create a Sheets client if credentials & libs are available; else return None."""
    if not gspread or not Credentials:
        return None
    if not os.path.exists(CREDENTIALS_FILE):
        return None
    try:
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        print(f"[Sheets] Auth error: {e}")
        return None


def submit_to_google_sheet(data):
    """Append one row to the spreadsheet. Returns (success: bool, message: str)."""
    try:
        client = get_google_sheets_client()
        if not client:
            return False, "Không thể kết nối với Google Sheets"

        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def format_service_value(
            service_value, quantity=None, additional_info=None, reason=None
        ):
            if not service_value:
                return ""
            if service_value == "Không" and reason:
                return f"Không ({reason})"
            if service_value == "Không":
                return "Không"
            result = service_value
            if quantity:
                result += f" (Số lượng: {quantity})"
            if additional_info:
                result += f" - {additional_info}"
            return result

        def _format_channel_speeds(row):
            service_value = row.get("dich_vu_8", "")
            if service_value in ["Không", ""]:
                return None
            try:
                channel_count = int(str(service_value).split(" ")[0])
            except Exception:
                return None
            speeds = []
            for i in range(1, channel_count + 1):
                sp = row.get(f"toc_do_kenh_{i}", "")
                if sp:
                    speeds.append(f"K{i}:{sp}Mbps")
            return ", ".join(speeds) if speeds else None

        def format_camera_value(service_value, appointment_date=None, reason=None):
            if not service_value:
                return ""
            if service_value == "Không" and reason:
                return f"Không ({reason})"
            if service_value == "Không":
                return "Không"
            if service_value == "Có" and appointment_date:
                try:
                    from datetime import datetime as _dt

                    d = _dt.strptime(appointment_date, "%Y-%m-%d")
                    return f"Hẹn ngày khảo sát ({d.strftime('%d/%m/%Y')})"
                except Exception:
                    return f"Hẹn ngày khảo sát ({appointment_date})"
            return service_value

        row_data = [
            data.get("xaphuong", ""),
            data.get("diaban", ""),
            data.get("nhan_vien_khao_sat", ""),
            data.get("so_dien_thoai_nv", ""),
            data.get("nguoi_dau_moi", ""),
            data.get("chuc_vu", ""),
            data.get("so_dien_thoai_dm", ""),
            format_service_value(
                data.get("dich_vu_1", ""),
                data.get("so_luong_1", ""),
                None,
                data.get("ly_do_1", ""),
            ),
            format_service_value(
                data.get("dich_vu_2", ""),
                data.get("so_luong_2", ""),
                None,
                data.get("ly_do_2", ""),
            ),
            format_service_value(
                data.get("dich_vu_3", ""),
                data.get("so_luong_3", ""),
                None,
                data.get("ly_do_3", ""),
            ),
            format_service_value(
                data.get("dich_vu_4", ""), None, None, data.get("ly_do_4", "")
            ),
            format_service_value(
                data.get("dich_vu_5", ""),
                data.get("so_luong_5", ""),
                None,
                data.get("ly_do_5", ""),
            ),
            format_service_value(
                data.get("dich_vu_6", ""),
                data.get("so_luong_6", ""),
                None,
                data.get("ly_do_6", ""),
            ),
            format_camera_value(
                data.get("dich_vu_7", ""),
                data.get("lich_hen_7", ""),
                data.get("ly_do_7", ""),
            ),
            format_service_value(
                data.get("dich_vu_8", ""),
                None,
                (
                    _format_channel_speeds(data)
                    if data.get("dich_vu_8") not in ["Không", ""]
                    else None
                ),
                data.get("ly_do_8", ""),
            ),
            format_service_value(
                data.get("dich_vu_9", ""),
                data.get("so_luong_9", ""),
                None,
                data.get("ly_do_9", ""),
            ),
            format_service_value(
                data.get("dich_vu_10", ""),
                data.get("so_luong_10", ""),
                None,
                data.get("ly_do_10", ""),
            ),
            format_service_value(
                data.get("dich_vu_11", ""),
                data.get("so_luong_11", ""),
                None,
                data.get("ly_do_11", ""),
            ),
            format_service_value(
                data.get("dich_vu_12", ""), None, None, data.get("ly_do_12", "")
            ),
        ]

        worksheet.append_row(row_data)
        return True, "Dữ liệu đã được gửi thành công!"
    except Exception as e:
        print(f"[Sheets] Append error: {e}")
        return False, f"Lỗi khi gửi dữ liệu: {e}"

# =========================
# Domain helpers (names & services)
# =========================


def normalize_area_name(area_name: str) -> str:
    if not area_name:
        return ""
    s = area_name.strip()
    for p in [
        "Xã ",
        "Phường ",
        "Thị trấn ",
        "Thị xã ",
        "xã ",
        "phường ",
        "thị trấn ",
        "thị xã ",
    ]:
        if s.startswith(p):
            s = s[len(p) :].strip()
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
    if (
        service_column
        and ("camera" in service_column.lower())
        and ("xã" in service_column.lower())
    ):
        if "hẹn" in lower and ("khảo sát" in lower or "ngày" in lower):
            return "Có"
    if any(
        w in lower for w in ["có", "yes", "đã có", "sẵn sàng", "x", "✓", "√", "true"]
    ):
        return "Có"
    if any(w in lower for w in ["không", "no", "chưa có", "không có", "false"]):
        return "Không"
    if any(w in lower for w in ["hẹn", "đang", "dự kiến", "pending"]):
        return "Đang triển khai"
    return "Có"


# =========================
# Survey data provider
# =========================


def generate_sample_survey_data():
    import random

    # Attempt to load xaphuong list to set diaban if available
    try:
        with open("xaphuong.json", "r", encoding="utf-8") as f:
            xaphuong_list = json.load(f)
    except Exception:
        xaphuong_list = []

    sample_data = {}
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
    for raw in sample_areas_raw:
        norm = normalize_area_name(raw)
        diaban = "Vĩnh Long (cũ)"
        for item in xaphuong_list:
            if normalize_area_name(item.get("xaphuong", "")) == norm:
                diaban = item.get("diaban", diaban)
                break
        rec = {"xaphuong": raw, "xaphuong_normalized": norm, "diaban": diaban}
        for i in range(1, 13):
            rec[f"dich_vu_{i}"] = random.choice(["Có", "Không", "Đang triển khai"])
        sample_data[norm] = rec
    return sample_data


def get_survey_data_from_sheets():
    """Read survey grid from the Sheet; fall back to sample data when unavailable."""
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
                val = (
                    row[col_idx].strip() if col_idx < len(row) and row[col_idx] else ""
                )
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
            }
        return out
    except Exception as e:
        print(f"[Sheets] Fetch error: {e}")
        return generate_sample_survey_data()


# =========================
# Routes – static pages & assets
# =========================
@app.route("/")
def home():
    # Prefer serving index.html if present; otherwise redirect to /map
    index_path = os.path.join(app.static_folder, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return redirect("/map")


@app.route("/sw.js")
def service_worker():
    try:
        with open("sw.js", "r", encoding="utf-8") as f:
            resp = app.response_class(f.read(), mimetype="application/javascript")
            resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
            return resp
    except FileNotFoundError:
        return "Service Worker not found", 404


@app.route("/offline-manager.js")
def offline_manager():
    try:
        with open("offline-manager.js", "r", encoding="utf-8") as f:
            return app.response_class(f.read(), mimetype="application/javascript")
    except FileNotFoundError:
        return "Offline Manager not found", 404


@app.route("/manifest.json")
def manifest():
    try:
        with open("manifest.json", "r", encoding="utf-8") as f:
            return app.response_class(f.read(), mimetype="application/json")
    except FileNotFoundError:
        return "Manifest not found", 404


# =========================
# Routes – map pages
# =========================
@app.route("/map")
def page_map():
    # Serve map.html placed alongside this file
    return send_from_directory(app.static_folder, "map.html")


@app.route("/map.geojson")
def serve_geojson():
    return send_from_directory(app.static_folder, "map.geojson")


# =========================
# Routes – APIs to power the map & forms
# =========================
@app.route("/api/map-data")
def api_map_data():
    """Return simplified areas (outer ring) + survey mapping for the map UI."""
    try:
        with open(
            os.path.join(app.static_folder, "map.geojson"), "r", encoding="utf-8"
        ) as f:
            gj = json.load(f)

        surveys = get_survey_data_from_sheets() or {}

        areas = []

        def prop_get(props, *keys):
            for k in keys:
                if k in props:
                    return props[k]
            return ""

        for feat in gj.get("features", []):
            props = feat.get("properties", {})
            geom = feat.get("geometry") or {}
            name = prop_get(
                props, "ten_xa", "tenphuongxa", "TEN_XA", "Name", "name", "xaphuong"
            )
            province = prop_get(props, "ten_tinh", "TEN_TINH", "province", "tinh")
            if not name or not geom:
                continue

            gtype = geom.get("type")
            coords = geom.get("coordinates")

            def first_ring(poly_coords):
                if not poly_coords:
                    return []
                return (
                    poly_coords[0]
                    if isinstance(poly_coords[0][0], list)
                    else poly_coords
                )

            if gtype == "Polygon":
                ring = first_ring(coords)
                if ring:
                    areas.append(
                        {"name": name, "coordinates": ring, "province": province}
                    )
            elif gtype == "MultiPolygon":
                if coords and coords[0]:
                    ring = first_ring(coords[0])
                    if ring:
                        areas.append(
                            {"name": name, "coordinates": ring, "province": province}
                        )

        payload = {
            "success": True,
            "areas": areas,
            "surveys": surveys,
            "total_areas": len(areas),
            "surveyed_areas": sum(1 for v in surveys.values() if v is not None),
            "last_update": datetime.now(timezone.utc).isoformat(),
        }
        return jsonify(payload)
    except FileNotFoundError:
        return jsonify({"success": False, "message": "map.geojson not found"}), 404
    except Exception as e:
        print(f"[API] map-data error: {e}")
        return jsonify({"success": False, "message": f"Lỗi server: {e}"}), 500


@app.route("/api/survey-details/<area_name>")
def get_survey_details(area_name):
    try:
        surveys = get_survey_data_from_sheets()
        # Try exact, then normalized
        survey = surveys.get(area_name) or surveys.get(normalize_area_name(area_name))
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

        total = 12
        completed = sum(1 for i in range(1, 13) if survey.get(f"dich_vu_{i}") == "Có")
        rate = (completed / total) * 100

        names = {
            1: "Biên lai điện tử",
            2: "Kiosk AI",
            3: "Kiosk bắt số",
            4: "Hội nghị trực tuyến",
            5: "Hệ thống WiFi",
            6: "Camera Hành chính công",
            7: "Camera xã phường",
            8: "Kênh truyền số liệu chuyên dụng",
            9: "AI cho Công chức viên chức",
            10: "Smart IR",
            11: "Firewall S-Gate",
            12: "VNPT-Money",
        }
        services = []
        details_raw = survey.get('service_details', {}) or {}
        for i in range(1, 13):
            key = f'dich_vu_{i}'
            status_norm = survey.get(key, 'Chưa khảo sát')              
            status_raw  = details_raw.get(key, status_norm)             
            services.append({
                'id': i,
                'name': names.get(i, key),
                'status': status_raw,                                   
                'available': (status_norm == 'Có'),                     
            })


        return jsonify(
            {
                "success": True,
                "area_name": area_name,
                "survey_data": survey,
                "statistics": {
                    "total_services": total,
                    "completed_services": completed,
                    "completion_rate": rate,
                },
                "services": services,
            }
        )
    except Exception as e:
        print(f"[API] survey-details error: {e}")
        return jsonify({"success": False, "message": f"Lỗi server: {e}"}), 500


@app.route('/submit', methods=['POST'])
def submit_form():
    try:
        data = request.get_json()
        if not data:
            return (
                jsonify({"success": False, "message": "Không có dữ liệu được gửi"}),
                400,
            )
        ok, msg = submit_to_google_sheet(data)
        if ok:
            return jsonify({"success": True, "message": msg})
        return jsonify({"success": False, "message": msg}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {e}"}), 500


@app.route("/api/xaphuong")
def get_xaphuong_data():
    try:
        with open("xaphuong.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify({"success": True, "data": data, "count": len(data)})
    except Exception as e:
        return (
            jsonify(
                {"success": False, "message": f"Lỗi khi đọc dữ liệu xã phường: {e}"}
            ),
            500,
        )


@app.route('/api/sync', methods=['POST'])
def sync_offline_data():
    try:
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({"success": False, "message": "Dữ liệu không hợp lệ"}), 400
        successful_syncs = 0
        failed_syncs = 0
        for submission in data:
            try:
                clean = {
                    k: v
                    for k, v in submission.items()
                    if k not in ["id", "timestamp", "synced", "syncedAt"]
                }
                ok, msg = submit_to_google_sheet(clean)
                successful_syncs += 1 if ok else 0
                failed_syncs += 0 if ok else 1
                if not ok:
                    print(f"[Sync] submission failed: {msg}")
            except Exception as ex:
                failed_syncs += 1
                print(f"[Sync] exception: {ex}")
        return jsonify(
            {
                "success": True,
                "message": f"Đã đồng bộ {successful_syncs} khảo sát thành công",
                "successful": successful_syncs,
                "failed": failed_syncs,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {e}"}), 500


@app.route('/health')
def health_check():
    return jsonify(
        {
            "status": "healthy",
            "message": "Server đang hoạt động bình thường",
            "offline_support": True,
        }
    )


# =========================
# Entrypoint
# =========================
if __name__ == '__main__':
    print("Khởi động server khảo sát...")
    print("Truy cập: http://localhost:5000  (map: /map)")
    app.run(debug=False, host="0.0.0.0", port=5000)
