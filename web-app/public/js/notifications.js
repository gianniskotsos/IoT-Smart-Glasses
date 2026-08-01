

function acceptNotification(id) {
  const { historyKey, unreadKey } = window.getStorageKeys();
  let history = JSON.parse(localStorage.getItem(historyKey) || '[]');
  history = history.filter(item => item.id !== id);
  localStorage.setItem(historyKey, JSON.stringify(history));

  let unread = parseInt(localStorage.getItem(unreadKey) || '0', 10) || 0;
  if (unread > 0) {
    unread = Math.max(0, unread - 1);
    localStorage.setItem(unreadKey, String(unread));
  }

  // Remove DOM element if present
  const el = document.getElementById(`notification-${id}`);
  if (el) el.remove();

  if (typeof window.updateBadge === 'function') {
        window.updateBadge();
    }
}




window.updateNotificationsUI = function () {
  const { historyKey } = window.getStorageKeys();
  const container = document.getElementById('notifications-list');
  if (!container) return;
  const history = JSON.parse(localStorage.getItem(historyKey) || '[]').slice().reverse();
  container.innerHTML = '';

  history.forEach((n, idx) => {
    const wrapper = document.createElement('div');
    wrapper.className = 'notification-item';
    wrapper.id = `notification-${n.id}`;

    const time = new Date(n.ts).toLocaleString('el-GR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });

    wrapper.innerHTML = `
      <div class="notification-top">
        <i class="fa-solid fa-bell"></i>
        <div class="notification-info">
          <h4>${n.title}</h4>
          <span class="tag medium">${n.kind || ''}</span>
        </div>
        <span class="time">${time}</span>
      </div>
      <p class="description">${n.description}</p>
      <div class="notification-actions">
        <button class="secondary" onclick="acceptNotification('${n.id}')">Acknowledge</button>
      </div>
    `;

    container.appendChild(wrapper);
  });
  if (history.length === 0) {
        container.innerHTML = `
            <div class="notification-empty" style="text-align: center; padding: 40px; color: #a0aec0;">
                <i class="fa-solid fa-circle-check" style="font-size: 48px; margin-bottom: 16px; display: block; color: #cbd5e0;"></i>
                <p style="font-size: 18px; font-weight: 600;">No active alerts</p>
                <p style="font-size: 14px;">Everything looks good. You'll see new alerts here.</p>
            </div>
        `;
        if (typeof window.updateBadge === 'function') {
            window.updateBadge();
        }
        return;
    }
  if (typeof window.updateBadge === 'function') {
    window.updateBadge();
  }
};

document.addEventListener('DOMContentLoaded', () => {
               
    window.updateNotificationsUI(); 

    if (typeof window.updateBadge === 'function') {
        window.updateBadge();     
    }
});