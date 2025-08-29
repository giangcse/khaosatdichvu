import os
from flask import Blueprint, redirect, current_app, send_from_directory, jsonify, render_template


public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def home():
    # Render từ templates nếu có, fallback redirect /map
    tpl_path = os.path.join(current_app.template_folder or "", "index.html")
    if tpl_path and os.path.exists(tpl_path):
        return render_template("index.html")
    return redirect("/map")


@public_bp.get("/sw.js")
def service_worker():
    path = os.path.join(current_app.static_folder, "sw.js")
    if os.path.exists(path):
        resp = current_app.response_class(open(path, "r", encoding="utf-8").read(), mimetype="application/javascript")
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        resp.headers["Pragma"] = "no-cache"
        resp.headers["Expires"] = "0"
        return resp
    return ("Service Worker not found", 404)


@public_bp.get("/offline-manager.js")
def offline_manager():
    return send_from_directory(current_app.static_folder, "offline-manager.js")


@public_bp.get("/manifest.json")
def manifest():
    return send_from_directory(current_app.static_folder, "manifest.json")


@public_bp.get("/map")
def page_map():
    tpl_path = os.path.join(current_app.template_folder or "", "map.html")
    if tpl_path and os.path.exists(tpl_path):
        return render_template("map.html")
    return send_from_directory(current_app.static_folder, "map.html")


@public_bp.get("/dashboard")
def page_dashboard():
    tpl_path = os.path.join(current_app.template_folder or "", "dashboard.html")
    if tpl_path and os.path.exists(tpl_path):
        return render_template("dashboard.html")
    return ("Dashboard template not found", 404)


@public_bp.get("/map.geojson")
def serve_geojson():
    # map.geojson đã được chuyển vào app/static
    return send_from_directory(current_app.static_folder, "map.geojson")


# Backward-compatible non-prefixed submit route for index.html and SW
@public_bp.post("/submit")
def submit_compat():
    # Chuyển tiếp nội bộ tới /api/submit để dùng cùng handler
    from .api import submit_form  # import tại chỗ để tránh vòng lặp
    return submit_form()
