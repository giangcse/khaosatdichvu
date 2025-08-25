# Hướng dẫn sử dụng tính năng Offline-First

## Tổng quan

Ứng dụng khảo sát dịch vụ VNPT hiện đã được nâng cấp với tính năng **offline-first**, cho phép:

- ✅ Ghi nhận khảo sát khi không có mạng
- ✅ Tự động đồng bộ dữ liệu khi có kết nối
- ✅ Lưu trữ dữ liệu an toàn trên thiết bị
- ✅ Hoạt động như Progressive Web App (PWA)

## Tính năng chính

### 🌐 Service Worker
- Cache tự động các tài nguyên cần thiết
- Xử lý requests offline thông minh
- Cập nhật background khi có phiên bản mới

### 💾 Lưu trữ Offline
- Sử dụng IndexedDB để lưu trữ dữ liệu
- Tự động backup khảo sát chưa gửi được
- Bảo toàn dữ liệu ngay cả khi đóng ứng dụng

### 🔄 Đồng bộ thông minh
- Tự động đồng bộ khi có kết nối
- Background sync khi ứng dụng không mở
- Đồng bộ thủ công khi cần thiết

### 📱 Progressive Web App
- Có thể cài đặt trên điện thoại/máy tính
- Hoạt động offline hoàn toàn
- Trải nghiệm như ứng dụng native

## Cách sử dụng

### 1. Trạng thái kết nối

Ở góc trên bên trái, bạn sẽ thấy:

- 🟢 **Online**: Có kết nối mạng
- 🟠 **Offline**: Không có kết nối mạng
- 🔵 **X chờ đồng bộ**: Số lượng khảo sát chưa được gửi

### 2. Ghi nhận khảo sát offline

1. Điền form khảo sát bình thường
2. Nhấn nút "Gửi"
3. Nếu offline:
   - Dữ liệu được lưu tự động
   - Hiển thị thông báo "Đã lưu offline"
   - Counter "chờ đồng bộ" tăng lên

### 3. Đồng bộ dữ liệu

#### Tự động:
- Khi có kết nối mạng trở lại
- Khi mở lại ứng dụng (nếu có mạng)
- Background sync (trình duyệt hỗ trợ)

#### Thủ công:
- Nhấn nút đồng bộ (biểu tượng refresh) ở góc trên trái
- Chỉ hiển thị khi có dữ liệu chờ đồng bộ

### 4. Cài đặt PWA

#### Trên điện thoại (Android):
1. Mở ứng dụng trong Chrome
2. Nhấn menu (3 chấm dọc)
3. Chọn "Thêm vào màn hình chính"
4. Xác nhận cài đặt

#### Trên máy tính:
1. Mở ứng dụng trong Chrome/Edge
2. Nhấn biểu tượng cài đặt ở thanh địa chỉ
3. Hoặc menu → "Cài đặt ứng dụng"

## Lợi ích

### Cho nhân viên khảo sát:
- ✅ Không lo mất dữ liệu khi mất mạng
- ✅ Tiếp tục làm việc ở vùng sóng yếu
- ✅ Tự động backup an toàn
- ✅ Trải nghiệm mượt mà

### Cho quản lý:
- ✅ Dữ liệu được bảo toàn 100%
- ✅ Không cần lo về kết nối mạng
- ✅ Tự động đồng bộ khi có điều kiện
- ✅ Theo dõi trạng thái sync realtime

## Khắc phục sự cố

### Nếu không đồng bộ được:
1. Kiểm tra kết nối mạng
2. Thử đồng bộ thủ công
3. Tải lại trang nếu cần
4. Kiểm tra server có hoạt động không

### Nếu mất dữ liệu offline:
1. Không xóa dữ liệu trình duyệt
2. Không xóa cache/cookies
3. Dữ liệu lưu trong IndexedDB, an toàn với việc đóng tab

### Nếu Service Worker lỗi:
1. Tải lại trang (Ctrl+F5)
2. Xóa cache trình duyệt nếu cần
3. Kiểm tra console để debug

## Hỗ trợ trình duyệt

### Đầy đủ tính năng:
- ✅ Chrome 67+
- ✅ Firefox 60+
- ✅ Safari 11.1+
- ✅ Edge 79+

### Hạn chế:
- ❌ Internet Explorer (không hỗ trợ)
- ⚠️ Safari iOS < 11.3 (hạn chế PWA)

## API Endpoints mới

### `/api/sync` (POST)
Đồng bộ dữ liệu offline lên server

### `/sw.js` (GET)
Service Worker file

### `/offline-manager.js` (GET)
Offline Manager script

### `/manifest.json` (GET)
PWA Manifest file

## Cấu trúc dữ liệu offline

```javascript
{
  id: auto_increment,
  timestamp: 1234567890,
  synced: false,
  // ... dữ liệu form gốc
}
```

## Bảo mật

- ✅ Dữ liệu chỉ lưu trên thiết bị của người dùng
- ✅ Không gửi về server bên thứ 3
- ✅ Tự động xóa sau khi đồng bộ thành công
- ✅ Mã hóa theo chuẩn trình duyệt

---

**Liên hệ hỗ trợ**: Nếu gặp vấn đề, vui lòng liên hệ team phát triển với thông tin chi tiết về lỗi và trình duyệt đang sử dụng.
