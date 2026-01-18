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
      } else {
        setError('Ошибка входа: ' + (err.response?.data?.detail || err.message));
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
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <div style={{
        background: 'white',
        padding: '40px',
        borderRadius: '10px',
        boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
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
              background: loading ? '#999' : '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '5px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background 0.3s'
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.background = '#5568d3';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.background = '#667eea';
              }
            }}
          >
            {loading ? 'Вход...' : 'Войти'}
          </button>
        </form>

        <div style={{
          marginTop: '30px',
          padding: '15px',
          background: '#f9f9f9',
          borderRadius: '5px',
          fontSize: '12px',
          color: '#666'
        }}>
          <p style={{ margin: '0 0 10px 0', fontWeight: 'bold' }}>Тестовые пользователи:</p>
          <p style={{ margin: '5px 0' }}>
            <strong>director</strong> / director123 (Директор)
          </p>
          <p style={{ margin: '5px 0' }}>
            <strong>head_dept1</strong> / head123 (Начальник отдела)
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
