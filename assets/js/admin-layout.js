const logoutBtn = document.getElementById('logout-btn');
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');

if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => sidebar.classList.toggle('open'));
}

if (logoutBtn) {
  logoutBtn.addEventListener('click', async () => {
    try {
      await apiFetch('/api/auth/sign-out/', { method: 'POST', body: '{}' });
    } catch (_) {
      // Still redirect on failure.
    }
    window.location.href = '/auth/sign-in/';
  });
}

document.querySelectorAll('[data-close-dialog]').forEach((button) => {
  button.addEventListener('click', () => button.closest('dialog')?.close());
});
