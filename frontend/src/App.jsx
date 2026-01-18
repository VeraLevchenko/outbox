import React, { useState, useEffect } from 'react';
import IncomingFiles from './components/IncomingFiles';
import OutgoingFiles from './components/OutgoingFiles';
import CardsList from './components/CardsList';
import Journal from './components/Journal';
import Login from './components/Login';
import { authApi } from './services/api';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('incoming');
  const [cardId, setCardId] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Проверяем наличие сохраненного пользователя
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');

    if (savedUser && token) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        console.error('Error parsing saved user:', e);
        authApi.logout();
      }
    }
    setLoading(false);
  }, []);

  const handleLoginSuccess = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    authApi.logout();
    setUser(null);
    setCardId(null);
    setActiveTab('incoming');
  };

  const handleCardSelect = (newCardId) => {
    setCardId(newCardId);
  };

  // Пока загружаемся
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh',
        fontSize: '18px',
        color: '#666'
      }}>
        Загрузка...
      </div>
    );
  }

  // Если не авторизован - показываем логин
  if (!user) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="app">
      {/* Заголовок */}
      <header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <h1>Outbox</h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ fontSize: '14px', color: '#666', textAlign: 'right' }}>
            <div style={{ fontWeight: 'bold' }}>{user.full_name || user.username}</div>
            <div style={{ fontSize: '12px' }}>
              {user.role === 'director' ? 'Директор' : 'Начальник отдела'}
            </div>
          </div>
          <button
            onClick={handleLogout}
            style={{
              padding: '8px 16px',
              background: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Выход
          </button>
        </div>
      </header>

      {/* Список карточек */}
      <CardsList
        userRole={user.role}
        onCardSelect={handleCardSelect}
        selectedCardId={cardId}
      />

      {/* Табы */}
      <div className="tabs">
        {cardId && (
          <>
            <button
              className={`tab ${activeTab === 'incoming' ? 'active' : ''}`}
              onClick={() => setActiveTab('incoming')}
            >
              📥 Входящие
            </button>
            <button
              className={`tab ${activeTab === 'outgoing' ? 'active' : ''}`}
              onClick={() => setActiveTab('outgoing')}
            >
              📤 Исходящие
            </button>
          </>
        )}
        <button
          className={`tab ${activeTab === 'journal' ? 'active' : ''}`}
          onClick={() => setActiveTab('journal')}
        >
          📋 Журнал
        </button>
      </div>

      {/* Контент */}
      <div className="content">
        {activeTab === 'journal' ? (
          <Journal />
        ) : cardId ? (
          <>
            {activeTab === 'incoming' && <IncomingFiles cardId={cardId} />}
            {activeTab === 'outgoing' && <OutgoingFiles cardId={cardId} />}
          </>
        ) : (
          <div style={{
            padding: '40px',
            textAlign: 'center',
            color: '#666',
            fontSize: '16px'
          }}>
            Выберите карточку для просмотра файлов
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
