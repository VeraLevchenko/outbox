import React, { useState, useEffect } from 'react';
import { kaitenApi } from '../services/api';

const CardsList = ({ userRole, onCardSelect, selectedCardId }) => {
  const [cards, setCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCards();
    // Обновляем список каждые 30 секунд
    const interval = setInterval(loadCards, 30000);
    return () => clearInterval(interval);
  }, [userRole]);

  const loadCards = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await kaitenApi.getCards(userRole);
      setCards(response.data.cards || []);

      // Если нет выбранной карточки, выбираем первую
      if (!selectedCardId && response.data.cards?.length > 0) {
        onCardSelect(response.data.cards[0].id);
      }
    } catch (err) {
      setError('Ошибка загрузки карточек: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && cards.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        Загрузка карточек...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '20px', color: 'red' }}>
        {error}
        <button
          onClick={loadCards}
          style={{
            marginLeft: '10px',
            padding: '5px 10px',
            cursor: 'pointer'
          }}
        >
          Повторить
        </button>
      </div>
    );
  }

  if (cards.length === 0) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        Нет карточек для обработки
      </div>
    );
  }

  return (
    <div style={{
      padding: '15px',
      background: '#f9f9f9',
      borderBottom: '2px solid #ddd'
    }}>
      <div style={{
        fontSize: '14px',
        fontWeight: 'bold',
        marginBottom: '10px',
        color: '#333'
      }}>
        Карточки на согласование ({cards.length})
      </div>

      <div style={{
        display: 'flex',
        gap: '10px',
        flexWrap: 'wrap'
      }}>
        {cards.map((card) => (
          <div
            key={card.id}
            onClick={() => onCardSelect(card.id)}
            style={{
              padding: '12px 16px',
              background: selectedCardId === card.id ? '#2196F3' : 'white',
              color: selectedCardId === card.id ? 'white' : '#333',
              border: selectedCardId === card.id ? '2px solid #1976D2' : '1px solid #ddd',
              borderRadius: '6px',
              cursor: 'pointer',
              transition: 'all 0.2s',
              minWidth: '200px',
              boxShadow: selectedCardId === card.id ? '0 2px 8px rgba(33, 150, 243, 0.3)' : 'none'
            }}
            onMouseEnter={(e) => {
              if (selectedCardId !== card.id) {
                e.currentTarget.style.background = '#f5f5f5';
                e.currentTarget.style.borderColor = '#bbb';
              }
            }}
            onMouseLeave={(e) => {
              if (selectedCardId !== card.id) {
                e.currentTarget.style.background = 'white';
                e.currentTarget.style.borderColor = '#ddd';
              }
            }}
          >
            <div style={{
              fontWeight: 'bold',
              marginBottom: '4px',
              fontSize: '15px'
            }}>
              #{card.id} {card.title}
            </div>
            <div style={{
              fontSize: '12px',
              opacity: 0.9
            }}>
              {card.column}
            </div>
            {card.incoming_no && (
              <div style={{
                fontSize: '12px',
                marginTop: '4px',
                opacity: 0.8
              }}>
                Вх. №: {card.incoming_no}
              </div>
            )}
          </div>
        ))}
      </div>

      {loading && (
        <div style={{
          marginTop: '10px',
          fontSize: '12px',
          color: '#666',
          textAlign: 'center'
        }}>
          Обновление...
        </div>
      )}
    </div>
  );
};

export default CardsList;
