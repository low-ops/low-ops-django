function bindPasswordToggles() {
  document.querySelectorAll('.password-toggle').forEach((button) => {
    button.addEventListener('click', () => {
      const input = button.parentElement.querySelector('input');
      const visible = input.type === 'text';
      input.type = visible ? 'password' : 'text';
      button.setAttribute('aria-label', visible ? 'Show password' : 'Hide password');
    });
  });
}

async function handleSignIn(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const errorEl = document.getElementById('sign-in-error');
  const submit = form.querySelector('[type="submit"]');
  errorEl.classList.add('hidden');

  submit.disabled = true;
  try {
    await apiFetch('/api/auth/sign-in/', {
      method: 'POST',
      body: JSON.stringify({
        email: form.email.value,
        password: form.password.value,
      }),
    });
    window.location.href = '/admin/users/';
  } catch (error) {
    errorEl.textContent = error.message;
    errorEl.classList.remove('hidden');
  } finally {
    submit.disabled = false;
  }
}

async function handleSignUp(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const errorEl = document.getElementById('sign-up-error');
  const submit = form.querySelector('[type="submit"]');
  errorEl.classList.add('hidden');

  submit.disabled = true;
  try {
    await apiFetch('/api/auth/sign-up/', {
      method: 'POST',
      body: JSON.stringify({
        name: form.name.value,
        email: form.email.value,
        password: form.password.value,
      }),
    });
    window.location.href = '/auth/sign-in/';
  } catch (error) {
    errorEl.textContent = error.message;
    errorEl.classList.remove('hidden');
  } finally {
    submit.disabled = false;
  }
}

bindPasswordToggles();

const signInForm = document.getElementById('sign-in-form');
if (signInForm) signInForm.addEventListener('submit', handleSignIn);

const signUpForm = document.getElementById('sign-up-form');
if (signUpForm) signUpForm.addEventListener('submit', handleSignUp);
