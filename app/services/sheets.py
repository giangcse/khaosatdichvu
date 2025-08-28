from datetime import datetime
from .surveys import get_google_sheets_client, SPREADSHEET_ID, WORKSHEET_NAME


def submit_to_google_sheet(data):
    try:
        client = get_google_sheets_client()
        if not client:
            return False, "Không thể kết nối với Google Sheets"

        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        def format_service_value(service_value, quantity=None, additional_info=None, reason=None):
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
            format_service_value(data.get("dich_vu_1", ""), data.get("so_luong_1", ""), None, data.get("ly_do_1", "")),
            format_service_value(data.get("dich_vu_2", ""), data.get("so_luong_2", ""), None, data.get("ly_do_2", "")),
            format_service_value(data.get("dich_vu_3", ""), data.get("so_luong_3", ""), None, data.get("ly_do_3", "")),
            format_service_value(data.get("dich_vu_4", ""), None, None, data.get("ly_do_4", "")),
            format_service_value(data.get("dich_vu_5", ""), data.get("so_luong_5", ""), None, data.get("ly_do_5", "")),
            format_service_value(data.get("dich_vu_6", ""), data.get("so_luong_6", ""), None, data.get("ly_do_6", "")),
            format_camera_value(data.get("dich_vu_7", ""), data.get("lich_hen_7", ""), data.get("ly_do_7", "")),
            format_service_value(data.get("dich_vu_8", ""), None, (_format_channel_speeds(data) if data.get("dich_vu_8") not in ["Không", ""] else None), data.get("ly_do_8", "")),
            format_service_value(data.get("dich_vu_9", ""), data.get("so_luong_9", ""), None, data.get("ly_do_9", "")),
            format_service_value(data.get("dich_vu_10", ""), data.get("so_luong_10", ""), None, data.get("ly_do_10", "")),
            format_service_value(data.get("dich_vu_11", ""), data.get("so_luong_11", ""), None, data.get("ly_do_11", "")),
            format_service_value(data.get("dich_vu_12", ""), None, None, data.get("ly_do_12", "")),
        ]

        worksheet.append_row(row_data)
        return True, "Dữ liệu đã được gửi thành công!"
    except Exception as e:
        return False, f"Lỗi khi gửi dữ liệu: {e}"


