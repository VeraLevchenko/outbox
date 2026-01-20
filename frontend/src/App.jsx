import React, { useState, useEffect } from 'react';
import IncomingFiles from './components/IncomingFiles';
import OutgoingFiles from './components/OutgoingFiles';
import Journal from './components/Journal';
import Login from './components/Login';
import { kaitenApi, authApi } from './services/api';
import './App.css';

function App() {
  const [mainTab, setMainTab] = useState('cards'); // 'cards' или 'journal'
  const [subTab, setSubTab] = useState('incoming'); // 'incoming' или 'outgoing'
  const [cardId, setCardId] = useState(null);
  const [cards, setCards] = useState([]);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Проверяем наличие сохраненного пользователя при монтировании
  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');

    if (savedUser && token) {
      try {
        const userData = JSON.parse(savedUser);
        setUser(userData);
        loadCards();
      } catch (e) {
        console.error('Error parsing saved user:', e);
        authApi.logout();
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  const loadCards = async () => {
    try {
      setLoading(true);
      const response = await kaitenApi.getCards('director');
      const fetchedCards = response.data || [];
      setCards(fetchedCards);

      // Автоматически выбрать первую карточку
      if (fetchedCards.length > 0) {
        setCardId(fetchedCards[0].id);
      }
    } catch (error) {
      console.error('Ошибка загрузки карточек:', error);
      setCards([]);
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = (userData) => {
    setUser(userData);
    loadCards();
  };

  const handleLogout = () => {
    authApi.logout();
    setUser(null);
    setCardId(null);
    setCards([]);
    setMainTab('cards');
    setSubTab('incoming');
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
          <div className="card-selector">
            <label>Карточка: </label>
            {cards.length > 0 ? (
              <select
                value={cardId || ''}
                onChange={(e) => setCardId(Number(e.target.value))}
              >
                {cards.map((card) => (
                  <option key={card.id} value={card.id}>
                    {card.properties?.id_228499 || card.id} - {card.title}
                  </option>
                ))}
              </select>
            ) : (
              <span>Нет карточек</span>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontWeight: '600', fontSize: '14px' }}>{user.full_name || user.username}</div>
            <div style={{ fontSize: '12px', opacity: '0.9' }}>
              {user.role === 'director' ? 'Директор' : 'Начальник отдела'}
            </div>
          </div>
          <button
            onClick={handleLogout}
            style={{
              padding: '8px 16px',
              background: 'rgba(255, 255, 255, 0.2)',
              color: 'white',
              border: '1px solid rgba(255, 255, 255, 0.3)',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => {
              e.target.style.background = 'rgba(255, 255, 255, 0.3)';
            }}
            onMouseLeave={(e) => {
              e.target.style.background = 'rgba(255, 255, 255, 0.2)';
            }}
          >
            Выйти
          </button>
        </div>
      </header>

      {/* Главные табы */}
      <div className="tabs">
        <button
          className={`tab ${mainTab === 'cards' ? 'active' : ''}`}
          onClick={() => setMainTab('cards')}
        >
          Карточки
        </button>
        <button
          className={`tab ${mainTab === 'journal' ? 'active' : ''}`}
          onClick={() => setMainTab('journal')}
        >
          Журнал
        </button>
      </div>

      {/* Подтабы для карточек */}
      {mainTab === 'cards' && (
        <div className="tabs" style={{ background: '#f9fafb', borderTop: '1px solid #e5e7eb' }}>
          <button
            className={`tab ${subTab === 'incoming' ? 'active' : ''}`}
            onClick={() => setSubTab('incoming')}
          >
            Входящие
          </button>
          <button
            className={`tab ${subTab === 'outgoing' ? 'active' : ''}`}
            onClick={() => setSubTab('outgoing')}
          >
            Исходящие
          </button>
        </div>
      )}

      {/* Контент */}
      <div className="content">
        {mainTab === 'cards' && subTab === 'incoming' && <IncomingFiles cardId={cardId} />}
        {mainTab === 'cards' && subTab === 'outgoing' && <OutgoingFiles cardId={cardId} />}
        {mainTab === 'journal' && <Journal />}
      </div>
    </div>
  );
}

export default App;
