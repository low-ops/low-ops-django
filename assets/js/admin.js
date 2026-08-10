let currentPage = 1;
let currentRole = 'all';
let currentEmail = '';
let debounceTimer = null;

const tableBody = document.getElementById('users-table-body');
const countEl = document.getElementById('users-count');
const paginationEl = document.getElementById('users-pagination');
const searchInput = document.getElementById('users-search');
const roleFilter = document.getElementById('users-role-filter');
const addUserBtn = document.getElementById('add-user-btn');
const addUserDialog = document.getElementById('add-user-dialog');
const addUserForm = document.getElementById('add-user-form');
const banDialog = document.getElementById('ban-user-dialog');
const banForm = document.getElementById('ban-user-form');
const roleDialog = document.getElementById('role-user-dialog');
const roleForm = document.getElementById('role-user-form');
const deleteDialog = document.getElementById('delete-user-dialog');
const deleteForm = document.getElementById('delete-user-form');
const deleteMessageEl = document.getElementById('delete-user-message');

function formatDate(value) {
  if (!value) return 'Never';
  return new Date(value).toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function badge(label, kind, icon = '') {
  const iconMarkup = icon ? `<span class="badge-icon" aria-hidden="true">${icon}</span>` : '';
  return `<span class="badge badge-${kind} badge-with-icon">${iconMarkup}${label}</span>`;
}

const ICONS = {
  verified: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>',
  unverified: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 8v4"/><path d="M12 16h.01"/></svg>',
  admin: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10"/></svg>',
  user: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
};

function verificationBadge(verified) {
  return verified
    ? badge('Verified', 'success', ICONS.verified)
    : badge('Unverified', 'muted', ICONS.unverified);
}

function roleBadge(role) {
  const isAdmin = role === 'admin';
  return badge(
    isAdmin ? 'Admin' : 'User',
    isAdmin ? 'admin' : 'user',
    isAdmin ? ICONS.admin : ICONS.user,
  );
}

function setRolePicker(form, role) {
  const value = role === 'admin' ? 'admin' : 'user';
  form.querySelectorAll('input[name="role"]').forEach((input) => {
    input.checked = input.value === value;
  });
}

function renderUsers(data) {
  if (!data.users.length) {
    tableBody.innerHTML = '<tr><td colspan="8" class="loading-cell">No users found.</td></tr>';
  } else {
    tableBody.innerHTML = data.users.map((user) => `
      <tr>
        <td>
          <div class="user-cell">
            ${user.avatarUrl
              ? `<img src="${user.avatarUrl}" alt="" class="avatar">`
              : `<span class="avatar-fallback">${user.name.slice(0, 2).toUpperCase()}</span>`}
            <div>
              <strong>${user.name}</strong>
              <span>${user.email}</span>
            </div>
          </div>
        </td>
        <td>${verificationBadge(user.verified)}</td>
        <td>${(user.accounts || []).join(', ') || 'credential'}</td>
        <td>${roleBadge(user.role || 'user')}</td>
        <td>${user.banned ? badge('Banned', 'danger') : badge('Active', 'success')}</td>
        <td>${formatDate(user.lastSignIn)}</td>
        <td>${formatDate(user.createdAt)}</td>
        <td>
          <div class="actions-menu">
            <button type="button" class="icon-btn" data-menu-toggle aria-label="Open menu">⋯</button>
            <div class="menu-panel hidden" data-menu-panel>
              <button type="button" data-action="role" data-user-id="${user.id}" data-user-role="${user.role || 'user'}">Update role</button>
              ${user.banned
                ? `<button type="button" data-action="unban" data-user-id="${user.id}">Unban user</button>`
                : `<button type="button" data-action="ban" data-user-id="${user.id}">Ban user</button>`}
              <button type="button" data-action="revoke" data-user-id="${user.id}">Revoke sessions</button>
              <button type="button" data-action="delete" data-user-id="${user.id}" data-user-name="${user.name}" data-user-email="${user.email}">Delete user</button>
            </div>
          </div>
        </td>
      </tr>
    `).join('');
  }

  countEl.textContent = `Showing ${data.users.length} of ${data.total} users`;
  renderPagination(data.page, data.totalPages);
  bindMenus();
}

function renderPagination(page, totalPages) {
  if (totalPages <= 1) {
    paginationEl.innerHTML = '';
    return;
  }

  const buttons = [];
  for (let i = 1; i <= totalPages; i += 1) {
    buttons.push(`<button type="button" data-page="${i}" class="${i === page ? 'active' : ''}">${i}</button>`);
  }
  paginationEl.innerHTML = buttons.join('');
  paginationEl.querySelectorAll('[data-page]').forEach((button) => {
    button.addEventListener('click', () => {
      currentPage = Number(button.dataset.page);
      loadUsers();
    });
  });
}

async function loadUsers() {
  tableBody.innerHTML = '<tr><td colspan="8" class="loading-cell">Loading users...</td></tr>';
  const params = new URLSearchParams({
    page: String(currentPage),
    limit: '10',
  });
  if (currentRole !== 'all') params.set('role', currentRole);
  if (currentEmail) params.set('email', currentEmail);

  try {
    const data = await apiFetch(`/api/admin/users/?${params.toString()}`);
    renderUsers(data);
  } catch (error) {
    tableBody.innerHTML = `<tr><td colspan="8" class="loading-cell">${error.message}</td></tr>`;
  }
}

function bindMenus() {
  document.querySelectorAll('[data-menu-toggle]').forEach((button) => {
    button.addEventListener('click', (event) => {
      event.stopPropagation();
      document.querySelectorAll('[data-menu-panel]').forEach((panel) => panel.classList.add('hidden'));
      button.nextElementSibling?.classList.toggle('hidden');
    });
  });

  document.querySelectorAll('[data-action]').forEach((button) => {
    button.addEventListener('click', async () => {
      const userId = button.dataset.userId;
      const action = button.dataset.action;
      document.querySelectorAll('[data-menu-panel]').forEach((panel) => panel.classList.add('hidden'));

      if (action === 'ban') {
        banForm.userId.value = userId;
        banDialog.showModal();
        return;
      }
      if (action === 'role') {
        roleForm.userId.value = userId;
        setRolePicker(roleForm, button.dataset.userRole || 'user');
        roleDialog.showModal();
        return;
      }
      if (action === 'delete') {
        deleteForm.userId.value = userId;
        if (deleteMessageEl) {
          const name = button.dataset.userName || 'this user';
          const email = button.dataset.userEmail || '';
          deleteMessageEl.textContent = email
            ? `Delete ${name} (${email})? Their account and sessions will be permanently removed.`
            : `Delete ${name}? Their account and sessions will be permanently removed.`;
        }
        deleteDialog.showModal();
        return;
      }

      try {
        if (action === 'unban') {
          await apiFetch(`/api/admin/users/${userId}/unban/`, { method: 'POST', body: '{}' });
          showToast('User unbanned.');
        } else if (action === 'revoke') {
          await apiFetch(`/api/admin/users/${userId}/revoke-sessions/`, { method: 'POST', body: '{}' });
          showToast('Sessions revoked.');
        }
        loadUsers();
      } catch (error) {
        showToast(error.message);
      }
    });
  });
}

document.addEventListener('click', () => {
  document.querySelectorAll('[data-menu-panel]').forEach((panel) => panel.classList.add('hidden'));
});

if (searchInput) {
  searchInput.addEventListener('input', () => {
    window.clearTimeout(debounceTimer);
    debounceTimer = window.setTimeout(() => {
      currentEmail = searchInput.value.trim();
      currentPage = 1;
      loadUsers();
    }, 300);
  });
}

if (roleFilter) {
  roleFilter.addEventListener('change', () => {
    currentRole = roleFilter.value;
    currentPage = 1;
    loadUsers();
  });
}

if (addUserBtn && addUserDialog) {
  addUserBtn.addEventListener('click', () => {
    const errorEl = document.getElementById('add-user-error');
    if (errorEl) {
      errorEl.textContent = '';
      errorEl.classList.add('hidden');
    }
    setRolePicker(addUserForm, 'user');
    addUserDialog.showModal();
  });
}

if (addUserForm) {
  addUserForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(addUserForm);
    const errorEl = document.getElementById('add-user-error');
    if (errorEl) {
      errorEl.textContent = '';
      errorEl.classList.add('hidden');
    }
    try {
      await apiFetch('/api/admin/users/create/', {
        method: 'POST',
        body: JSON.stringify({
          name: formData.get('name'),
          email: formData.get('email'),
          password: formData.get('password'),
          role: formData.get('role') || 'user',
          autoVerify: formData.get('autoVerify') === 'on',
        }),
      });
      addUserDialog.close();
      addUserForm.reset();
      setRolePicker(addUserForm, 'user');
      showToast('User created.');
      loadUsers();
    } catch (error) {
      if (errorEl) {
        errorEl.textContent = error.message;
        errorEl.classList.remove('hidden');
      } else {
        showToast(error.message);
      }
    }
  });
}

if (banForm) {
  banForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(banForm);
    const duration = formData.get('banDuration');
    let banExpiresIn = null;
    if (duration !== 'permanent') {
      banExpiresIn = Number(duration) * 24 * 60 * 60;
    }
    try {
      await apiFetch(`/api/admin/users/${formData.get('userId')}/ban/`, {
        method: 'POST',
        body: JSON.stringify({
          banReason: formData.get('banReason') || 'Spamming',
          banExpiresIn,
        }),
      });
      banDialog.close();
      showToast('User banned.');
      loadUsers();
    } catch (error) {
      showToast(error.message);
    }
  });
}

if (roleForm) {
  roleForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(roleForm);
    try {
      await apiFetch(`/api/admin/users/${formData.get('userId')}/role/`, {
        method: 'POST',
        body: JSON.stringify({ role: formData.get('role') }),
      });
      roleDialog.close();
      showToast('Role updated.');
      loadUsers();
    } catch (error) {
      showToast(error.message);
    }
  });
}

if (deleteForm) {
  deleteForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const formData = new FormData(deleteForm);
    try {
      await apiFetch(`/api/admin/users/${formData.get('userId')}/`, { method: 'DELETE' });
      deleteDialog.close();
      showToast('User deleted.');
      loadUsers();
    } catch (error) {
      showToast(error.message);
    }
  });
}

loadUsers();
