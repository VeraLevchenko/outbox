import React, { useState } from 'react';
import { authApi } from '../services/api';

const Login = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!username || !password) {
      setError('Введите имя пользователя и пароль');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await authApi.login(username, password);
      const { access_token, user } = response.data;

      // Сохраняем токен и данные пользователя
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      // Уведомляем родительский компонент
      if (onLoginSuccess) {
        onLoginSuccess(user);
      }
    } catch (err) {
      console.error('Login error:', err);
      if (err.response?.status === 401) {
        setError('Неверное имя пользователя или пароль');
      } else if (err.response?.status === 422) {
        setError('Неверный формат данных. Проверьте логин и пароль');
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        setError('Ошибка подключения к серверу. Убедитесь, что backend запущен на порту 8000');
      } else {
        const detail = err.response?.data?.detail;
        const message = typeof detail === 'string' ? detail : err.message;
        setError('Ошибка входа: ' + message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      background: '#f3f4f6'
    }}>
      <div style={{
        background: 'white',
        padding: '40px',
        borderRadius: '4px',
        border: '1px solid #e5e7eb',
        width: '400px',
        maxWidth: '90%'
      }}>
        <h1 style={{
          textAlign: 'center',
          marginBottom: '10px',
          color: '#333'
        }}>
          Outbox
        </h1>
        <p style={{
          textAlign: 'center',
          color: '#666',
          marginBottom: '30px',
          fontSize: '14px'
        }}>
          Система управления исходящей корреспонденцией
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '5px',
              color: '#333',
              fontWeight: '500'
            }}>
              Имя пользователя
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={loading}
              placeholder="Введите имя пользователя"
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '5px',
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
              autoFocus
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={{
              display: 'block',
              marginBottom: '5px',
              color: '#333',
              fontWeight: '500'
            }}>
              Пароль
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              placeholder="Введите пароль"
              style={{
                width: '100%',
                padding: '12px',
                border: '1px solid #ddd',
                borderRadius: '5px',
                fontSize: '14px',
                boxSizing: 'border-box'
              }}
            />
          </div>

          {error && (
            <div style={{
              background: '#fee',
              color: '#c33',
              padding: '12px',
              borderRadius: '5px',
              marginBottom: '20px',
              fontSize: '14px',
              border: '1px solid #fcc'
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              background: loading ? '#9ca3af' : '#4b5563',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.background = '#374151';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.background = '#4b5563';
              }
            }}
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;
