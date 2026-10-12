import React, { useState, useEffect } from 'react';
import IncomingFiles from './components/IncomingFiles';
import OutgoingFiles from './components/OutgoingFiles';
import ServerProjects from './components/ServerProjects';
import Journal from './components/Journal';
import Credentials from './components/Credentials';
import Login from './components/Login';
import { kaitenApi, authApi, serverProjectsApi } from './services/api';
import { preloadCryptoPro } from './services/cryptoPro';
import './App.css';

const formatDue = (iso) => {
  const d = new Date(iso);
  return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: 'numeric' });
};

const formatDueLabel = (iso) => {
  if (!iso) return '';

  const due = new Date(iso);
  const today = new Date();
  due.setHours(0, 0, 0, 0);
  today.setHours(0, 0, 0, 0);

  const marker = due < today ? '❗ ' : due.getTime() === today.getTime() ? '⚠ ' : '';
  return `${marker}${formatDue(iso)} · `;
};

function App() {
  const [mainTab, setMainTab] = useState('cards'); // 'cards' или 'journal'
  const [subTab, setSubTab] = useState('outgoing'); // 'incoming' или 'outgoing' - по умолчанию 'outgoing'
  const [cardId, setCardId] = useState(null);
  const [cards, setCards] = useState([]);
  const [user, setUser] = useState(null);
  const [sourceMode, setSourceMode] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [loading, setLoading] = useState(true);
  const isDirector = user?.role === 'director' || user?.role === 'acting_chairman';

  useEffect(() => {
    if (user) preloadCryptoPro().catch(error => console.warn('CryptoPro preload failed:', error));
  }, [user]);

  useEffect(() => {
    if (sourceMode !== 'kaiten' || !cardId || cards.length < 2) return undefined;
    const currentIndex = cards.findIndex(card => card.id === cardId);
    const nextCard = cards[currentIndex + 1];
    const nextDocument = nextCard?.files?.find(file =>
      !file.deleted && file.name?.toLowerCase().endsWith('.docx') && (file.url || file.path)
    );
    if (!nextDocument) return undefined;
    const sourceUrl = nextDocument.url || nextDocument.path;
    if (!/^https?:\/\//.test(sourceUrl)) return undefined;
    const prefetch = document.createElement('link');
    prefetch.rel = 'prefetch';
    prefetch.href = 'https://docs.google.com/viewer?url=' + encodeURIComponent(sourceUrl) + '&embedded=true';
    prefetch.as = 'document';
    document.head.appendChild(prefetch);
    return () => prefetch.remove();
  }, [cards, cardId, sourceMode]);

  // Проверяем наличие сохраненного пользователя при монтировании
  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    const token = localStorage.getItem('token');

    if (savedUser && token) {
      try {
        const userData = JSON.parse(savedUser);
        setUser(userData);
        const savedMode = sessionStorage.getItem('sourceMode');
        if (savedMode === 'kaiten' || savedMode === 'server') {
          setSourceMode(savedMode);
          loadCards(savedMode);
        } else {
          setLoading(false);
        }
      } catch (e) {
        console.error('Error parsing saved user:', e);
        authApi.logout();
        setLoading(false);
      }
    } else {
      setLoading(false);
    }
  }, []);

  const loadCards = async (mode = sourceMode) => {
    try {
      setLoading(true);
      setLoadError(null);
      const response = mode === 'server' ? await serverProjectsApi.getProjects() : await kaitenApi.getCards();
      const fetchedCards = response.data || [];
      setCards(fetchedCards);

      // Автоматически выбрать первую карточку
      if (fetchedCards.length > 0) {
        setCardId(mode === 'server' ? fetchedCards[0].name : fetchedCards[0].id);
      } else {
        setCardId(null);
      }
    } catch (error) {
      console.error('Ошибка загрузки карточек:', error);
      setCards([]);
      setCardId(null);
      setLoadError(error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = (userData, mode) => {
    setUser(userData);
    setSourceMode(mode);
    loadCards(mode);
  };

  const chooseSource = (mode) => {
    sessionStorage.setItem('sourceMode', mode);
    setSourceMode(mode);
    setCardId(null);
    setCards([]);
    setMainTab('cards');
    setSubTab('outgoing');
    loadCards(mode);
  };

  const handleLogout = () => {
    authApi.logout();
    sessionStorage.removeItem('sourceMode');
    setUser(null);
    setSourceMode(null);
    setLoadError(null);
    setCardId(null);
    setCards([]);
    setMainTab('cards');
    setSubTab('outgoing');
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

  if (!sourceMode) {
    return (
      <div style={{ padding: '48px', textAlign: 'center' }}>
        <h2>Выберите источник писем</h2>
        <button onClick={() => chooseSource('kaiten')} style={{ margin: '8px', padding: '12px 20px' }}>С КАЙТЕН</button>
        <button onClick={() => chooseSource('server')} style={{ margin: '8px', padding: '12px 20px' }}>С сервера</button>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Заголовок */}
      <header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <h1>Outbox</h1>
          <div className="card-selector">
            <label>{sourceMode === 'server' ? 'Проект: ' : 'Карточка: '}</label>
            {cards.length > 0 ? (
              <select
                value={cardId || ''}
                onChange={(e) => setCardId(sourceMode === 'server' ? e.target.value : Number(e.target.value))}
              >
                {cards.map((card) => (
                  <option key={sourceMode === 'server' ? card.name : card.id} value={sourceMode === 'server' ? card.name : card.id}>
                    {sourceMode === 'server' ? card.name : <>{formatDueLabel(card.due_date)}{card.properties?.id_228499 || card.id} — {card.title}</>}
                  </option>
                ))}
              </select>
            ) : (
              <span>{loadError || (sourceMode === 'server' ? 'Нет проектов на подпись' : 'Нет карточек')}</span>
            )}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <label style={{ fontSize: '13px' }}>
            Источник писем{' '}
            <select value={sourceMode} onChange={(e) => chooseSource(e.target.value)} style={{ padding: '7px', borderRadius: '4px' }}>
              <option value="kaiten">С КАЙТЕН</option>
              <option value="server">С сервера</option>
            </select>
          </label>
          {sourceMode === 'server' && <button onClick={() => loadCards('server')} style={{ padding: '8px 12px', border: '1px solid white', borderRadius: '4px', background: 'transparent', color: 'white', cursor: 'pointer' }}>Обновить проекты</button>}
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontWeight: '600', fontSize: '14px' }}>{user.full_name || user.username}</div>
            <div style={{ fontSize: '12px', opacity: '0.9' }}>
              {user.role === 'acting_chairman' ? 'И.о. председателя' : user.role === 'deputy_chairman' ? 'Заместитель председателя' : isDirector ? 'Директор' : 'Начальник отдела'}
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
          {sourceMode === 'server' ? 'Проекты' : 'Карточки'}
        </button>
        {isDirector && (
        <button
          className={`tab ${mainTab === 'journal' ? 'active' : ''}`}
          onClick={() => setMainTab('journal')}
        >
          Журнал
        </button>
        )}
        {user.username === 'levchenko' && (
          <button className={`tab ${mainTab === 'credentials' ? 'active' : ''}`} onClick={() => setMainTab('credentials')}>
            Учётные записи
          </button>
        )}
      </div>

      {/* Подтабы для карточек */}
      {mainTab === 'cards' && sourceMode === 'kaiten' && (
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
        {mainTab === 'cards' && sourceMode === 'kaiten' && subTab === 'incoming' && <IncomingFiles cardId={cardId} />}
        {mainTab === 'cards' && sourceMode === 'kaiten' && subTab === 'outgoing' && <OutgoingFiles cardId={cardId} card={cards.find(card => card.id === cardId)} onCardsUpdate={() => loadCards('kaiten')} userRole={user?.role} />}
        {mainTab === 'cards' && sourceMode === 'server' && <ServerProjects folder={cardId} project={cards.find(card => card.name === cardId)} onProjectsUpdate={() => loadCards('server')} userRole={user?.role} />}
        {user.username === 'levchenko' && mainTab === 'credentials' && <Credentials />}
        {isDirector && mainTab === 'journal' && <Journal />}
      </div>
    </div>
  );
}

export default App;
