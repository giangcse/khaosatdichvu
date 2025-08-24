# Hệ thống Khảo sát Dịch vụ

Hệ thống khảo sát dịch vụ với khả năng gửi dữ liệu trực tiếp lên Google Sheet.

## Tính năng

- Form khảo sát với giao diện đẹp và thân thiện
- Tự động gửi dữ liệu lên Google Sheet
- Hỗ trợ nhiều loại dịch vụ khác nhau
- Giao diện responsive, tương thích mobile
- Xác nhận dữ liệu trước khi gửi

## Cài đặt

### 1. Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình Google Sheets API

#### Bước 1: Tạo Google Cloud Project
1. Truy cập [Google Cloud Console](https://console.cloud.google.com/)
2. Tạo project mới hoặc chọn project có sẵn
3. Bật Google Sheets API và Google Drive API

#### Bước 2: Tạo Service Account
1. Vào "IAM & Admin" > "Service Accounts"
2. Tạo service account mới
3. Tạo key (JSON format) và tải về
4. Đổi tên file thành `credentials.json` và đặt trong thư mục dự án

#### Bước 3: Tạo Google Sheet
1. Tạo Google Sheet mới
2. Chia sẻ sheet với email của service account (có trong file credentials.json)
3. Copy Spreadsheet ID từ URL (phần giữa /d/ và /edit)

#### Bước 4: Cấu hình trong code
Mở file `main.py` và cập nhật các thông tin sau:

```python
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID'  # Thay bằng ID của Google Sheet
WORKSHEET_NAME = 'Sheet1'  # Tên sheet trong Google Sheet
```

### 3. Cấu trúc Google Sheet

Google Sheet cần có các cột sau (theo thứ tự):

| Cột | Mô tả |
|-----|-------|
| A | Thời gian gửi |
| B | Địa bàn |
| C | Phường/Xã |
| D | Biên lai điện tử |
| E | Số lượng biên lai điện tử |
| F | Kiosk AI |
| G | Số lượng Kiosk AI |
| H | Kiosk bắt số |
| I | Số lượng Kiosk bắt số |
| J | Hội nghị trực tuyến |
| K | Hệ thống WiFi |
| L | Camera Hành chính công |
| M | Camera xã phường |
| N | Lịch hẹn camera xã phường |
| O | Kênh truyền số liệu chuyên dụng |
| P | Tốc độ kênh 1 |
| Q | Tốc độ kênh 2 |
| R | Tốc độ kênh 3 |
| S | Tốc độ kênh 4 |
| T | Tốc độ kênh 5 |
| U | AI cho Công chức viên chức |
| V | Smart IR |
| W | Firewall S-Gate |
| X | VNPT-Money |

## Chạy ứng dụng

```bash
python main.py
```

Sau đó truy cập: http://localhost:5000

## Cấu trúc dự án

```
Khaosat/
├── main.py              # Backend Flask server
├── index.html           # Frontend form khảo sát
├── xaphuong.json        # Dữ liệu xã phường
├── credentials.json     # Google API credentials (cần tạo)
├── requirements.txt     # Python dependencies
└── README.md           # Hướng dẫn này
```

## API Endpoints

- `GET /` - Trang chủ với form khảo sát
- `POST /submit` - Gửi dữ liệu form lên Google Sheet
- `GET /health` - Kiểm tra trạng thái server

## Xử lý lỗi

### Lỗi kết nối Google Sheets
- Kiểm tra file `credentials.json` có tồn tại và đúng format
- Đảm bảo Google Sheets API đã được bật
- Kiểm tra quyền truy cập của service account

### Lỗi gửi dữ liệu
- Kiểm tra Spreadsheet ID có đúng không
- Đảm bảo sheet đã được chia sẻ với service account
- Kiểm tra tên worksheet có đúng không

## Bảo mật

- Không commit file `credentials.json` lên git
- Thêm `credentials.json` vào `.gitignore`
- Sử dụng HTTPS trong môi trường production
- Giới hạn quyền truy cập của service account

## Hỗ trợ

Nếu gặp vấn đề, vui lòng kiểm tra:
1. Console log của trình duyệt
2. Log của Flask server
3. Quyền truy cập Google Sheet
4. Cấu hình API credentials
