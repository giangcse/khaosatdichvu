import json
import os
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, current_app

from ..services.sheets import submit_to_google_sheet
from ..services.surveys import (
    get_survey_data_from_sheets,
    normalize_area_name,
)


api_bp = Blueprint("api", __name__)


@api_bp.get("/map-data")
def api_map_data():
    try:
        static_file = os.path.join(current_app.static_folder, "map.geojson")

        # Thử lấy "areas" từ Redis cache, key theo mtime của file
        redis_client = (current_app.extensions or {}).get("redis")
        areas = None
        cache_ttl_seconds = 6 * 60 * 60  # 6 giờ
        cache_key = None
        try:
            mtime = int(os.path.getmtime(static_file))
            cache_key = f"cache:map_areas:{mtime}"
            if redis_client:
                cached = redis_client.get(cache_key)
                if cached:
                    areas = json.loads(cached)
        except Exception:
            pass

        if areas is None:
            with open(static_file, "r", encoding="utf-8") as f:
                gj = json.load(f)

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
                                {
                                    "name": name,
                                    "coordinates": ring,
                                    "province": province,
                                }
                            )

            # Lưu cache nếu có Redis
            try:
                if redis_client and cache_key and areas is not None:
                    redis_client.setex(
                        cache_key,
                        cache_ttl_seconds,
                        json.dumps(areas, ensure_ascii=False),
                    )
            except Exception:
                pass

        surveys = get_survey_data_from_sheets() or {}

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
        return jsonify({"success": False, "message": f"Lỗi server: {e}"}), 500


@api_bp.get("/survey-details/<area_name>")
def get_survey_details(area_name):
    try:
        surveys = get_survey_data_from_sheets()
        survey = surveys.get(area_name) or surveys.get(normalize_area_name(area_name))
        if not survey:
            return jsonify({"success": False, "message": "Không tìm thấy dữ liệu khảo sát cho khu vực này"}), 404

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
        details_raw = survey.get("service_details", {}) or {}
        for i in range(1, 13):
            key = f"dich_vu_{i}"
            status_norm = survey.get(key, "Chưa khảo sát")
            status_raw = details_raw.get(key, status_norm)
            services.append(
                {
                    "id": i,
                    "name": names.get(i, key),
                    "status": status_raw,
                    "available": (status_norm == "Có"),
                }
            )

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
        return jsonify({"success": False, "message": f"Lỗi server: {e}"}), 500


@api_bp.post("/submit")
def submit_form():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Không có dữ liệu được gửi"}), 400
        ok, msg = submit_to_google_sheet(data)
        if ok:
            return jsonify({"success": True, "message": msg})
        return jsonify({"success": False, "message": msg}), 500
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {e}"}), 500


@api_bp.get("/xaphuong")
def get_xaphuong_data():
    try:
        static_file = os.path.join(current_app.static_folder, "xaphuong.json")
        redis_client = (current_app.extensions or {}).get("redis")
        cache_ttl_seconds = 12 * 60 * 60  # 12 giờ vì dữ liệu ít thay đổi
        cache_key = None
        data = None
        try:
            mtime = int(os.path.getmtime(static_file))
            cache_key = f"cache:xaphuong:{mtime}"
            if redis_client:
                cached = redis_client.get(cache_key)
                if cached:
                    data = json.loads(cached)
        except Exception:
            pass

        if data is None:
            with open(static_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            try:
                if redis_client and cache_key and data is not None:
                    redis_client.setex(
                        cache_key,
                        cache_ttl_seconds,
                        json.dumps(data, ensure_ascii=False),
                    )
            except Exception:
                pass

        return jsonify({"success": True, "data": data, "count": len(data)})
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi khi đọc dữ liệu xã phường: {e}"}), 500


@api_bp.post("/sync")
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
                    k: v for k, v in submission.items() if k not in ["id", "timestamp", "synced", "syncedAt"]
                }
                ok, msg = submit_to_google_sheet(clean)
                successful_syncs += 1 if ok else 0
                failed_syncs += 0 if ok else 1
            except Exception:
                failed_syncs += 1
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


@api_bp.get("/dashboard-stats")
def dashboard_stats():
    """API endpoint để cung cấp thống kê cho dashboard"""
    try:
        surveys = get_survey_data_from_sheets() or {}

        # Thống kê tổng quan - tính dựa trên tổng số xã/phường thực tế từ xaphuong.json
        # Đọc tổng số xã/phường từ xaphuong.json
        try:
            import json
            import os

            static_file = os.path.join(
                os.path.dirname(__file__), "..", "static", "xaphuong.json"
            )
            with open(static_file, "r", encoding="utf-8") as f:
                xaphuong_data = json.load(f)
            total_areas_from_json = len(xaphuong_data)  # 131 xã/phường
        except Exception:
            # Fallback nếu không đọc được file
            total_areas_from_json = 131  # 35 + 40 + 56

        total_areas = total_areas_from_json  # Tổng số xã/phường thực tế
        surveyed_areas = len(surveys)  # Số xã/phường đã được khảo sát

        # Danh sách dịch vụ
        service_names = {
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

        # Thống kê theo dịch vụ
        service_stats = {}
        for i in range(1, 13):
            service_key = f"dich_vu_{i}"

            # Đếm các trạng thái khác nhau
            co_count = 0
            khong_co_nhu_cau_count = 0
            hop_dong_vnpt_count = 0
            hop_dong_khac_count = 0

            for survey in surveys.values():
                status = survey.get(service_key, "")
                raw_detail = survey.get("service_details", {}).get(service_key, status)

                # Xử lý trạng thái đặc biệt cho dịch vụ 8 (Kênh TSL CD)
                if i == 8:
                    # Kiểm tra giá trị thực tế từ raw_detail (dropdown value)
                    if status == "Có" or "kênh" in str(raw_detail).lower():
                        co_count += 1
                    elif status == "Không":
                        # Phân tích lý do từ raw_detail nếu có
                        raw_lower = str(raw_detail).lower()
                        if (
                            "ký hợp đồng với vnpt" in raw_lower
                            or "đã ký hợp đồng với vnpt" in raw_lower
                        ):
                            hop_dong_vnpt_count += 1
                        elif (
                            "ký hợp đồng với nhà cung cấp khác" in raw_lower
                            or "ký hợp đồng với đơn vị khác" in raw_lower
                        ):
                            hop_dong_khac_count += 1
                        elif (
                            "không có nhu cầu" in raw_lower
                            or "chưa có nhu cầu" in raw_lower
                        ):
                            khong_co_nhu_cau_count += 1
                        else:
                            khong_co_nhu_cau_count += 1
                    continue

                # Xử lý trạng thái đặc biệt cho dịch vụ 7 (Camera xã phường)
                if i == 7:
                    if status == "Có":
                        # Camera xã phường với "Có" có thể có hẹn lịch khảo sát
                        co_count += 1
                    elif status == "Không":
                        # Phân tích lý do từ raw_detail
                        raw_lower = str(raw_detail).lower()
                        if (
                            "ký hợp đồng với vnpt" in raw_lower
                            or "đã ký hợp đồng với vnpt" in raw_lower
                        ):
                            hop_dong_vnpt_count += 1
                        elif (
                            "ký hợp đồng với nhà cung cấp khác" in raw_lower
                            or "ký hợp đồng với đơn vị khác" in raw_lower
                        ):
                            hop_dong_khac_count += 1
                        elif (
                            "không có nhu cầu" in raw_lower
                            or "chưa có nhu cầu" in raw_lower
                        ):
                            khong_co_nhu_cau_count += 1
                        else:
                            khong_co_nhu_cau_count += 1
                    continue

                # Xử lý các trạng thái thông thường
                if status == "Có":
                    co_count += 1
                elif status == "Không":
                    # Phân tích lý do từ raw_detail
                    raw_lower = str(raw_detail).lower()
                    if (
                        "không có nhu cầu" in raw_lower
                        or "chưa có nhu cầu" in raw_lower
                        or raw_detail == "Không"
                        or raw_detail == ""
                    ):
                        khong_co_nhu_cau_count += 1
                    elif (
                        "ký hợp đồng với vnpt" in raw_lower
                        or "đã ký hợp đồng với vnpt" in raw_lower
                    ):
                        hop_dong_vnpt_count += 1
                    elif (
                        "ký hợp đồng với nhà cung cấp khác" in raw_lower
                        or "ký hợp đồng với đơn vị khác" in raw_lower
                        or "đã ký hợp đồng với nhà cung cấp khác" in raw_lower
                    ):
                        hop_dong_khac_count += 1
                    else:
                        khong_co_nhu_cau_count += 1
                else:
                    # Trường hợp không xác định, tính là chưa có nhu cầu
                    khong_co_nhu_cau_count += 1

            total_count = (
                co_count
                + khong_co_nhu_cau_count
                + hop_dong_vnpt_count
                + hop_dong_khac_count
            )

            service_stats[i] = {
                "name": service_names[i],
                "co": co_count,
                "khong_co_nhu_cau": khong_co_nhu_cau_count,
                "hop_dong_vnpt": hop_dong_vnpt_count,
                "hop_dong_khac": hop_dong_khac_count,
                "total": total_count,
                # Giữ lại các field cũ để tương thích
                "khong": khong_co_nhu_cau_count,
            }

            # Thống kê theo địa bàn - sử dụng lại dữ liệu đã đọc ở trên
        if "xaphuong_data" in locals():
            # Đếm tổng số xã/phường theo từng địa bàn
            total_areas_by_diaban = {}
            for item in xaphuong_data:
                diaban = item.get("diaban", "Không xác định")
                total_areas_by_diaban[diaban] = total_areas_by_diaban.get(diaban, 0) + 1
        else:
            # Fallback nếu không đọc được file
            total_areas_by_diaban = {
                "Vĩnh Long (cũ)": 35,
                "Trà Vinh (cũ)": 40,
                "Bến Tre (cũ)": 56,
            }

        diaban_stats = {}
        for survey in surveys.values():
            diaban = survey.get("diaban", "Không xác định")
            if diaban not in diaban_stats:
                diaban_stats[diaban] = {
                    "surveyed_areas": 0,  # Số xã/phường đã khảo sát
                    "total_areas": total_areas_by_diaban.get(
                        diaban, 0
                    ),  # Tổng số xã/phường trong địa bàn
                }

            diaban_stats[diaban]["surveyed_areas"] += 1

        # Danh sách chi tiết từng xã/phường
        area_details = []
        for area_key, survey in surveys.items():
            completed = sum(
                1 for i in range(1, 13) if survey.get(f"dich_vu_{i}") == "Có"
            )
            completion_rate = (completed / 12) * 100 if completed > 0 else 0

            area_details.append(
                {
                    "area_name": survey.get("xaphuong", area_key),
                    "area_normalized": area_key,
                    "diaban": survey.get("diaban", "Không xác định"),
                    "completed_services": completed,
                    "total_services": 12,
                    "completion_rate": round(completion_rate, 1),
                }
            )

        # Sắp xếp theo tỷ lệ hoàn thành giảm dần
        area_details.sort(key=lambda x: x["completion_rate"], reverse=True)

        payload = {
            "success": True,
            "overview": {
                "total_areas": total_areas,
                "surveyed_areas": surveyed_areas,
                "completion_rate": (
                    round((surveyed_areas / total_areas * 100), 1)
                    if total_areas > 0
                    else 0
                ),
            },
            "service_stats": service_stats,
            "diaban_stats": diaban_stats,
            "area_details": area_details,
            "last_update": datetime.now(timezone.utc).isoformat(),
        }

        return jsonify(payload)
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi server: {e}"}), 500


@api_bp.get("/health")
def health_check():
    return jsonify({"status": "healthy", "message": "Server đang hoạt động bình thường", "offline_support": True})
