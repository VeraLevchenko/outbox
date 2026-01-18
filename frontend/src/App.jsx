import React, { useState } from 'react';
import IncomingFiles from './components/IncomingFiles';
import OutgoingFiles from './components/OutgoingFiles';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('incoming');
  const [cardId, setCardId] = useState(1001);

  return (
    <div className="app">
      {/* Заголовок */}
      <header className="app-header">
        <h1>Outbox - Просмотр файлов</h1>
        <div className="card-selector">
          <label>Карточка: </label>
          <select
            value={cardId}
            onChange={(e) => setCardId(Number(e.target.value))}
          >
            <option value={1001}>1001 - Письмо в Минфин</option>
            <option value={1002}>1002 - Договор на поставку</option>
            <option value={2001}>2001 - Отчет о работе</option>
          </select>
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
