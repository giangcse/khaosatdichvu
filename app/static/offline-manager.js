(function () {
  const STORAGE_KEY = 'pendingSubmissions';

  function readQueue() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function writeQueue(queue) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(queue));
    } catch (e) {
      // ignore
    }
  }

  async function saveOfflineSubmission(data) {
    const queue = readQueue();
    queue.push({ data, ts: Date.now() });
    writeQueue(queue);
    updatePendingCounter();
  }

  async function manualSync() {
    const queue = readQueue();
    if (!queue.length) {
      toast('Không có dữ liệu chờ đồng bộ', 'info');
      return;
    }
    try {
      const payload = queue.map((i) => i.data);
      const res = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const result = await res.json();
      if (res.ok && result && result.success) {
        writeQueue([]);
        updatePendingCounter();
        toast(`Đã đồng bộ ${result.successful || payload.length} khảo sát`, 'success');
      } else {
        toast(result && result.message ? result.message : 'Đồng bộ thất bại', 'error');
      }
    } catch (e) {
      toast('Không thể đồng bộ. Kiểm tra kết nối mạng.', 'error');
    }
  }

  function updatePendingCounter() {
    const el = document.getElementById('pendingSubmissions');
    if (!el) return;
    const count = readQueue().length;
    if (count > 0) {
      el.classList.remove('hidden');
      const textEl = el.querySelector('div');
      if (textEl) textEl.innerHTML = textEl.innerHTML.replace(/^[0-9]+\s+chờ\s+đồng\s+bộ|.*$/i, `${count} chờ đồng bộ`);
      el.querySelector('div') && (el.querySelector('div').childNodes[1].nodeValue = ` ${count} chờ đồng bộ`);
    } else {
      el.classList.add('hidden');
    }
  }

  function toast(message, type) {
    if (window.Swal) {
      window.Swal.fire({
        icon: type === 'success' ? 'success' : type === 'error' ? 'error' : 'info',
        title: type === 'success' ? 'Thành công' : type === 'error' ? 'Lỗi' : 'Thông báo',
        text: message,
        confirmButtonText: 'Đóng',
      });
    } else {
      console.log(`[${type}]`, message);
    }
  }

  function updateNetworkStatus() {
    const el = document.getElementById('networkStatus');
    if (!el) return;
    const dot = el.querySelector('.w-2.h-2');
    const textNode = el.querySelector('.flex.items-center.text-gray-600.text-sm');
    const online = navigator.onLine;
    if (dot) dot.className = `w-2 h-2 rounded-full mr-2 ${online ? 'bg-green-500' : 'bg-gray-400'}`;
    if (textNode) textNode.lastChild.nodeValue = online ? ' Đang trực tuyến' : ' Ngoại tuyến';
  }

  window.addEventListener('online', () => {
    updateNetworkStatus();
  });
  window.addEventListener('offline', () => {
    updateNetworkStatus();
  });

  document.addEventListener('DOMContentLoaded', () => {
    updateNetworkStatus();
    updatePendingCounter();
  });

  window.offlineManager = {
    saveOfflineSubmission,
    manualSync,
    updatePendingCounter,
  };
})();
