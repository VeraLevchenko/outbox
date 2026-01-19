import React, { useState, useEffect } from 'react';
import IncomingFiles from './components/IncomingFiles';
import OutgoingFiles from './components/OutgoingFiles';
import { kaitenApi } from './services/api';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('incoming');
  const [cardId, setCardId] = useState(null);
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);

  // Загрузить карточки из Kaiten при монтировании
  useEffect(() => {
    loadCards();
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

  return (
    <div className="app">
      {/* Заголовок */}
      <header className="app-header">
        <h1>Outbox - Просмотр файлов</h1>
        <div className="card-selector">
          <label>Карточка: </label>
          {loading ? (
            <span>Загрузка...</span>
          ) : cards.length > 0 ? (
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
      </header>

      {/* Табы */}
      <div className="tabs">
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
      </div>

      {/* Контент */}
      <div className="content">
        {activeTab === 'incoming' && <IncomingFiles cardId={cardId} />}
        {activeTab === 'outgoing' && <OutgoingFiles cardId={cardId} />}
      </div>
    </div>
  );
}

export default App;
