function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) {
    return parts.pop().split(';').shift();
  }
  return '';
}

async function onTelegramAuth(user) {
  const statusNode = document.getElementById('auth-status');
  const nextUrl = window.NEXT_URL || '/workspace/';

  try {
    statusNode.textContent = 'Проверяем Telegram-подпись...';

    const response = await fetch('/auth/telegram/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken')
      },
      body: JSON.stringify(user)
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail || 'Ошибка авторизации');
    }

    statusNode.textContent = 'Вход выполнен. Перенаправляем...';
    window.location.href = nextUrl;
  } catch (error) {
    statusNode.textContent = `Не удалось войти: ${error.message}`;
  }
}
