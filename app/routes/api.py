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


@api_bp.get("/health")
def health_check():
    return jsonify({"status": "healthy", "message": "Server đang hoạt động bình thường", "offline_support": True})
