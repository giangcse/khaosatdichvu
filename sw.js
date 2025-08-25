// Service Worker cho tính năng offline-first
const CACHE_NAME = 'khaosat-offline-v1';
const urlsToCache = [
    '/',
    '/static/css/main.css',
    'https://cdn.tailwindcss.com',
    'https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js',
    'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css',
    'https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js',
    'https://cdn.jsdelivr.net/npm/sweetalert2@11',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap'
];

// Cài đặt Service Worker
self.addEventListener('install', event => {
    console.log('📦 Service Worker: Đang cài đặt...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('📦 Service Worker: Đang cache các tài nguyên');
                return cache.addAll(urlsToCache);
            })
            .catch(err => {
                console.error('❌ Lỗi khi cache tài nguyên:', err);
                // Không để lỗi cache ngăn cản việc cài đặt SW
                return Promise.resolve();
            })
    );
});

// Kích hoạt Service Worker
self.addEventListener('activate', event => {
    console.log('🚀 Service Worker: Đã kích hoạt');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('🗑️ Service Worker: Xóa cache cũ:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Xử lý fetch requests
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Xử lý requests đến API submit
    if (url.pathname === '/submit' && request.method === 'POST') {
        event.respondWith(handleOfflineSubmit(request));
        return;
    }

    // Xử lý requests đến API xã phường
    if (url.pathname === '/api/xaphuong') {
        event.respondWith(handleXaPhuongRequest(request));
        return;
    }

    // Xử lý các requests khác với cache-first strategy
    event.respondWith(
        caches.match(request)
            .then(response => {
                // Trả về từ cache nếu có
                if (response) {
                    return response;
                }

                // Nếu không có trong cache, fetch từ network
                return fetch(request)
                    .then(response => {
                        // Kiểm tra response hợp lệ
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone response để cache
                        const responseToCache = response.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(request, responseToCache);
                            });

                        return response;
                    })
                    .catch(() => {
                        // Nếu offline, trả về trang fallback cho HTML requests
                        if (request.destination === 'document') {
                            return caches.match('/');
                        }
                    });
            })
    );
});

// Xử lý submit form khi offline
async function handleOfflineSubmit(request) {
    try {
        // Thử gửi online trước
        const response = await fetch(request);
        return response;
    } catch (error) {
        // Nếu offline, lưu vào IndexedDB
        console.log('📱 Offline: Lưu dữ liệu form để đồng bộ sau');
        
        const formData = await request.json();
        await saveOfflineData(formData);
        
        // Trả về response giả lập
        return new Response(JSON.stringify({
            success: true,
            message: 'Dữ liệu đã được lưu offline. Sẽ đồng bộ khi có mạng.',
            offline: true
        }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Xử lý request xã phường với cache
async function handleXaPhuongRequest(request) {
    try {
        // Thử fetch từ network trước
        const response = await fetch(request);
        
        // Cache response nếu thành công
        if (response.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }
        
        return response;
    } catch (error) {
        // Nếu offline, trả về từ cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Fallback với dữ liệu mặc định
        return new Response(JSON.stringify({
            success: true,
            data: [
                { diaban: "Vĩnh Long", xaphuong: "Xã Cái Nhum" },
                { diaban: "Vĩnh Long", xaphuong: "Xã Tân Long Hội" },
                { diaban: "Vĩnh Long", xaphuong: "Xã Nhơn Phú" }
            ],
            count: 3,
            offline: true
        }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Lưu dữ liệu offline vào IndexedDB
async function saveOfflineData(data) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('KhaoSatOfflineDB', 1);
        
        request.onerror = () => reject(request.error);
        
        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction(['offlineSubmissions'], 'readwrite');
            const store = transaction.objectStore('offlineSubmissions');
            
            const submissionData = {
                ...data,
                timestamp: Date.now(),
                synced: false
            };
            
            store.add(submissionData);
            
            transaction.oncomplete = () => resolve();
            transaction.onerror = () => reject(transaction.error);
        };
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            const store = db.createObjectStore('offlineSubmissions', { keyPath: 'id', autoIncrement: true });
            store.createIndex('timestamp', 'timestamp', { unique: false });
            store.createIndex('synced', 'synced', { unique: false });
        };
    });
}

// Background sync để đồng bộ dữ liệu khi online
self.addEventListener('sync', event => {
    if (event.tag === 'sync-offline-data') {
        console.log('🔄 Background sync: Đồng bộ dữ liệu offline');
        event.waitUntil(syncOfflineData());
    }
});

// Đồng bộ dữ liệu offline
async function syncOfflineData() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('KhaoSatOfflineDB', 1);
        
        request.onsuccess = async () => {
            const db = request.result;
            const transaction = db.transaction(['offlineSubmissions'], 'readwrite');
            const store = transaction.objectStore('offlineSubmissions');
            const index = store.index('synced');
            
            const unsynced = await index.getAll(false);
            
            for (const submission of unsynced) {
                try {
                    const response = await fetch('/submit', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(submission)
                    });
                    
                    if (response.ok) {
                        // Đánh dấu đã đồng bộ
                        submission.synced = true;
                        submission.syncedAt = Date.now();
                        store.put(submission);
                        
                        console.log('✅ Đã đồng bộ submission:', submission.id);
                    }
                } catch (error) {
                    console.error('❌ Lỗi đồng bộ submission:', submission.id, error);
                }
            }
            
            resolve();
        };
        
        request.onerror = () => reject(request.error);
    });
}

// Thông báo khi có update
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
