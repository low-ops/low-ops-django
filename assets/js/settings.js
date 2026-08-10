const form = document.getElementById('settings-form');
const avatarInput = document.getElementById('avatar-input');
const avatarPicker = document.getElementById('avatar-picker');
const avatarPreview = document.getElementById('avatar-preview');
const errorEl = document.getElementById('settings-error');

let pendingAvatarFile = null;

if (avatarPicker && avatarInput) {
  avatarPicker.addEventListener('click', () => avatarInput.click());
  avatarInput.addEventListener('change', () => {
    const file = avatarInput.files?.[0];
    if (!file) return;
    if (!file.type.startsWith('image/')) {
      showToast('Please select an image file');
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      showToast('Image must be 5 MB or smaller');
      return;
    }
    pendingAvatarFile = file;
    if (avatarPreview.tagName === 'IMG') {
      avatarPreview.src = URL.createObjectURL(file);
    } else {
      const img = document.createElement('img');
      img.id = 'avatar-preview';
      img.className = 'avatar-image';
      img.src = URL.createObjectURL(file);
      avatarPicker.replaceChild(img, avatarPreview);
    }
  });
}

if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    errorEl.classList.add('hidden');
    const submit = form.querySelector('[type="submit"]');
    submit.disabled = true;

    try {
      let imageValue = window.settingsUser.image;

      if (pendingAvatarFile) {
        const body = new FormData();
        body.append('file', pendingAvatarFile);
        const uploaded = await apiFetch('/api/user/avatar/', { method: 'POST', body });
        imageValue = uploaded.key;
      }

      await apiFetch('/api/user/profile/', {
        method: 'PATCH',
        body: JSON.stringify({
          name: form.name.value,
          image: imageValue,
        }),
      });

      pendingAvatarFile = null;
      showToast('Profile updated successfully.');
    } catch (error) {
      errorEl.textContent = error.message;
      errorEl.classList.remove('hidden');
    } finally {
      submit.disabled = false;
    }
  });
}
