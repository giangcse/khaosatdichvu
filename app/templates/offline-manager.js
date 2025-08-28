// Offline Manager - Quản lý tính năng offline-first
class OfflineManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.pendingSubmissions = [];
        this.syncInProgress = false;
        this.init();
    }

    async init() {
        // Đăng ký Service Worker
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('✅ Service Worker đã đăng ký thành công:', registration.scope);
                
                // Lắng nghe cập nhật Service Worker
                registration.addEventListener('updatefound', () => {
                    console.log('🔄 Service Worker có cập nhật mới');
                    this.showUpdateNotification();
                });
            } catch (error) {
                console.error('❌ Lỗi đăng ký Service Worker:', error);
            }
        }

        // Khởi tạo IndexedDB
        await this.initDB();

        // Lắng nghe sự kiện online/offline
        this.setupNetworkListeners();

        // Đồng bộ dữ liệu nếu online
        if (this.isOnline) {
            this.syncPendingData();
        }

        // Hiển thị trạng thái mạng
        this.updateNetworkStatus();
    }

    // Khởi tạo IndexedDB
    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('KhaoSatOfflineDB', 1);
            
            request.onerror = () => reject(request.error);
            
            request.onsuccess = () => {
                this.db = request.result;
                console.log('✅ IndexedDB đã được khởi tạo');
                resolve();
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Tạo object store cho submissions offline
                if (!db.objectStoreNames.contains('offlineSubmissions')) {
                    const store = db.createObjectStore('offlineSubmissions', { 
                        keyPath: 'id', 
                        autoIncrement: true 
                    });
                    store.createIndex('timestamp', 'timestamp', { unique: false });
                    store.createIndex('synced', 'synced', { unique: false });
                }
                
                console.log('🗄️ IndexedDB schema đã được tạo');
            };
        });
    }

    // Thiết lập lắng nghe sự kiện mạng
    setupNetworkListeners() {
        window.addEventListener('online', () => {
            console.log('🌐 Đã kết nối mạng');
            this.isOnline = true;
            this.updateNetworkStatus();
            this.syncPendingData();
        });

        window.addEventListener('offline', () => {
            console.log('📱 Mất kết nối mạng');
            this.isOnline = false;
            this.updateNetworkStatus();
        });
    }

    // Cập nhật hiển thị trạng thái mạng
    updateNetworkStatus() {
        const statusIndicator = document.getElementById('networkStatus');
        if (!statusIndicator) return;

        if (this.isOnline) {
            statusIndicator.innerHTML = `
                <div class="flex items-center text-green-600 text-sm">
                    <div class="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                    Online
                </div>
            `;
        } else {
            statusIndicator.innerHTML = `
                <div class="flex items-center text-orange-600 text-sm">
                    <div class="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
                    Offline
                </div>
            `;
        }

        // Cập nhật counter pending submissions
        this.updatePendingCounter();
    }

    // Cập nhật counter các submission chưa đồng bộ
    async updatePendingCounter() {
        const pendingCount = await this.getPendingSubmissionsCount();
        const pendingIndicator = document.getElementById('pendingSubmissions');
        
        if (!pendingIndicator) return;

        if (pendingCount > 0) {
            pendingIndicator.innerHTML = `
                <div class="flex items-center text-blue-600 text-sm">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    ${pendingCount} chờ đồng bộ
                </div>
            `;
            pendingIndicator.classList.remove('hidden');
        } else {
            pendingIndicator.classList.add('hidden');
        }
    }

    // Lấy số lượng submissions chưa đồng bộ
    async getPendingSubmissionsCount() {
        return new Promise((resolve) => {
            const transaction = this.db.transaction(['offlineSubmissions'], 'readonly');
            const store = transaction.objectStore('offlineSubmissions');
            const index = store.index('synced');
            const request = index.count(false);
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => resolve(0);
        });
    }

    // Lưu submission offline
    async saveOfflineSubmission(data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['offlineSubmissions'], 'readwrite');
            const store = transaction.objectStore('offlineSubmissions');
            
            const submissionData = {
                ...data,
                timestamp: Date.now(),
                synced: false
            };
            
            const request = store.add(submissionData);
            
            request.onsuccess = () => {
                console.log('💾 Đã lưu submission offline:', request.result);
                this.updatePendingCounter();
                resolve(request.result);
            };
            
            request.onerror = () => reject(request.error);
        });
    }

    // Đồng bộ dữ liệu chờ xử lý
    async syncPendingData() {
        if (this.syncInProgress || !this.isOnline) return;

        this.syncInProgress = true;
        console.log('🔄 Bắt đầu đồng bộ dữ liệu offline...');

        try {
            const pendingSubmissions = await this.getPendingSubmissions();
            
            for (const submission of pendingSubmissions) {
                try {
                    const response = await fetch('/submit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(submission)
                    });

                    if (response.ok) {
                        await this.markAsSynced(submission.id);
                        console.log('✅ Đã đồng bộ submission:', submission.id);
                        
                        // Hiển thị thông báo
                        this.showSyncNotification('success', 'Đã đồng bộ 1 khảo sát thành công');
                    } else {
                        console.error('❌ Lỗi đồng bộ submission:', submission.id);
                    }
                } catch (error) {
                    console.error('❌ Lỗi đồng bộ submission:', submission.id, error);
                    break; // Dừng nếu có lỗi network
                }
            }

            this.updatePendingCounter();
        } catch (error) {
            console.error('❌ Lỗi trong quá trình đồng bộ:', error);
        } finally {
            this.syncInProgress = false;
        }
    }

    // Lấy danh sách submissions chưa đồng bộ
    async getPendingSubmissions() {
        return new Promise((resolve) => {
            const transaction = this.db.transaction(['offlineSubmissions'], 'readonly');
            const store = transaction.objectStore('offlineSubmissions');
            const index = store.index('synced');
            const request = index.getAll(false);
            
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => resolve([]);
        });
    }

    // Đánh dấu submission đã đồng bộ
    async markAsSynced(id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['offlineSubmissions'], 'readwrite');
            const store = transaction.objectStore('offlineSubmissions');
            const request = store.get(id);
            
            request.onsuccess = () => {
                const submission = request.result;
                if (submission) {
                    submission.synced = true;
                    submission.syncedAt = Date.now();
                    
                    const updateRequest = store.put(submission);
                    updateRequest.onsuccess = () => resolve();
                    updateRequest.onerror = () => reject(updateRequest.error);
                } else {
                    resolve();
                }
            };
            
            request.onerror = () => reject(request.error);
        });
    }

    // Hiển thị thông báo đồng bộ
    showSyncNotification(type, message) {
        const notification = document.createElement('div');
        notification.className = `fixed top-20 right-4 p-3 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-green-500 text-white' : 'bg-blue-500 text-white'
        } transform translate-x-full transition-transform duration-300`;
        notification.textContent = message;

        document.body.appendChild(notification);

        // Hiển thị notification
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        // Ẩn sau 3 giây
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Hiển thị thông báo cập nhật Service Worker
    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 left-4 p-4 bg-blue-600 text-white rounded-lg shadow-lg z-50';
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>Có phiên bản mới! Tải lại để cập nhật.</span>
                <button onclick="window.location.reload()" class="ml-4 px-3 py-1 bg-white text-blue-600 rounded text-sm">
                    Tải lại
                </button>
            </div>
        `;

        document.body.appendChild(notification);
    }

    // Đồng bộ thủ công
    async manualSync() {
        if (!this.isOnline) {
            this.showSyncNotification('error', 'Không có kết nối mạng để đồng bộ');
            return;
        }

        this.showSyncNotification('info', 'Đang đồng bộ dữ liệu...');
        await this.syncPendingData();
    }
}

// Khởi tạo Offline Manager
window.offlineManager = new OfflineManager();