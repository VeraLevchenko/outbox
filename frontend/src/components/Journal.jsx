import React, { useState, useEffect } from 'react';
import { journalApi } from '../services/api';

const PAGE_SIZE = 100;

const Journal = () => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [yearFilter, setYearFilter] = useState(new Date().getFullYear());
  const [monthFilter, setMonthFilter] = useState(null);
  const [editingEntry, setEditingEntry] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [formData, setFormData] = useState({});
  const [currentPage, setCurrentPage] = useState(0);
  const [totalEntries, setTotalEntries] = useState(0);

  useEffect(() => {
    setCurrentPage(0);
    loadEntries(0);
  }, [yearFilter, monthFilter]);

  useEffect(() => {
    loadEntries(currentPage);
  }, [currentPage]);

  const loadEntries = async (page) => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        year: yearFilter,
        skip: (page ?? currentPage) * PAGE_SIZE,
        limit: PAGE_SIZE
      };
      if (monthFilter) {
        params.month = monthFilter;
      }

      const response = await journalApi.getEntries(params);
      setEntries(response.data.entries || []);
      setTotalEntries(response.data.total || 0);
    } catch (err) {
      setError('Ошибка загрузки журнала: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    try {
      const params = { year: yearFilter };
      if (monthFilter) {
        params.month = monthFilter;
      }

      const response = await journalApi.exportToXlsx(params);

      // Создаем ссылку для скачивания
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;

      let filename = `journal_${yearFilter}`;
      if (monthFilter) {
        filename += `_${monthFilter.toString().padStart(2, '0')}`;
      }
      filename += '.xlsx';

      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert('Ошибка экспорта: ' + err.message);
      console.error(err);
    }
  };

  const handleEdit = (entry) => {
    setEditingEntry(entry);
    setFormData({
      outgoing_no: entry.outgoing_no,
      formatted_number: entry.formatted_number,
      outgoing_date: entry.outgoing_date,
      to_whom: entry.to_whom || '',
      executor: entry.executor || '',
      folder_path: entry.folder_path || ''
    });
  };

  const handleCreate = () => {
    const today = new Date().toISOString().split('T')[0];
    setShowCreateForm(true);
    setFormData({
      outgoing_no: '',
      formatted_number: '',
      outgoing_date: today,
      to_whom: '',
      executor: '',
      folder_path: ''
    });
  };

  const handleSaveCreate = async () => {
    try {
      // Проверка обязательных полей
      if (!formData.outgoing_no || !formData.formatted_number || !formData.outgoing_date) {
        alert('Заполните обязательные поля: числовая часть номера, форматированный номер и дата');
        return;
      }

      await journalApi.createEntry(formData);
      setShowCreateForm(false);
      loadEntries();
      alert('Запись успешно создана!');
    } catch (err) {
      alert('Ошибка создания записи: ' + (err.response?.data?.detail || err.message));
      console.error(err);
    }
  };

  const handleSaveEdit = async () => {
    try {
      // Проверка обязательных полей
      if (!formData.formatted_number) {
        alert('Заполните обязательное поле: форматированный номер');
        return;
      }

      await journalApi.updateEntry(editingEntry.id, formData);
      setEditingEntry(null);
      loadEntries();
      alert('Запись успешно обновлена!');
    } catch (err) {
      alert('Ошибка обновления записи: ' + (err.response?.data?.detail || err.message));
      console.error(err);
    }
  };

  const handleDelete = async (entry) => {
    if (!window.confirm(`Удалить запись №${entry.formatted_number}? Папка с файлами также будет удалена.`)) {
      return;
    }

    try {
      await journalApi.deleteEntry(entry.id);
      loadEntries();
    } catch (err) {
      alert('Ошибка удаления записи: ' + err.message);
      console.error(err);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU');
  };

  const months = [
    { value: null, label: 'Все месяцы' },
    { value: 1, label: 'Январь' },
    { value: 2, label: 'Февраль' },
    { value: 3, label: 'Март' },
    { value: 4, label: 'Апрель' },
    { value: 5, label: 'Май' },
    { value: 6, label: 'Июнь' },
    { value: 7, label: 'Июль' },
    { value: 8, label: 'Август' },
    { value: 9, label: 'Сентябрь' },
    { value: 10, label: 'Октябрь' },
    { value: 11, label: 'Ноябрь' },
    { value: 12, label: 'Декабрь' }
  ];

  const currentYear = new Date().getFullYear();
  const years = Array.from({length: 5}, (_, i) => currentYear - i);

  return (
    <div style={{ padding: '20px' }}>
      {/* Заголовок и фильтры */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '15px'
      }}>
        <h2 style={{ margin: 0 }}>Журнал исходящей корреспонденции</h2>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Год */}
          <select
            value={yearFilter}
            onChange={(e) => setYearFilter(Number(e.target.value))}
            style={{
              padding: '8px 12px',
              borderRadius: '4px',
              border: '1px solid #ddd'
            }}
          >
            {years.map(year => (
              <option key={year} value={year}>{year}</option>
            ))}
          </select>

          {/* Месяц */}
          <select
            value={monthFilter || ''}
            onChange={(e) => setMonthFilter(e.target.value ? Number(e.target.value) : null)}
            style={{
              padding: '8px 12px',
              borderRadius: '4px',
              border: '1px solid #ddd'
            }}
          >
            {months.map(month => (
              <option key={month.value || 'all'} value={month.value || ''}>
                {month.label}
              </option>
            ))}
          </select>

          {/* Кнопка создания записи */}
          <button
            onClick={handleCreate}
            style={{
              padding: '8px 16px',
              background: '#16a34a',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            + Создать запись
          </button>

          {/* Кнопка экспорта */}
          <button
            onClick={handleExport}
            disabled={loading || entries.length === 0}
            style={{
              padding: '8px 16px',
              background: entries.length > 0 ? '#4b5563' : '#d1d5db',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: entries.length > 0 ? 'pointer' : 'not-allowed',
              fontWeight: '500'
            }}
          >
            Экспорт в Excel
          </button>
        </div>
      </div>

      {/* Таблица */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          Загрузка...
        </div>
      ) : error ? (
        <div style={{ color: 'red', padding: '20px' }}>{error}</div>
      ) : entries.length === 0 ? (
        <div style={{
          textAlign: 'center',
          padding: '40px',
          color: '#666',
          background: '#f9f9f9',
          borderRadius: '8px'
        }}>
          Нет записей за выбранный период
        </div>
      ) : (
        <div style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: 'calc(100vh - 220px)' }}>
          <table style={{
            width: '100%',
            borderCollapse: 'collapse',
            background: 'white',
            border: '1px solid #e5e7eb'
          }}>
            <thead>
              <tr style={{ background: '#f5f5f5', position: 'sticky', top: 0, zIndex: 1 }}>
                <th style={headerStyle}>№ п/п</th>
                <th style={headerStyle}>Исх. номер</th>
                <th style={headerStyle}>Дата</th>
                <th style={headerStyle}>Кому</th>
                <th style={headerStyle}>Исполнитель</th>
                <th style={headerStyle}>Путь к файлам</th>
                <th style={headerStyle}>Действия</th>
              </tr>
            </thead>
            <tbody>
              {entries.map((entry, index) => (
                <tr
                  key={entry.id}
                  style={{
                    borderBottom: '1px solid #eee',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#f9f9f9'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
                >
                  <td style={cellStyle}>{entry.outgoing_no}</td>
                  <td style={{...cellStyle, fontWeight: '500'}}>{entry.formatted_number}</td>
                  <td style={cellStyle}>{formatDate(entry.outgoing_date)}</td>
                  <td style={cellStyle}>{entry.to_whom || '-'}</td>
                  <td style={cellStyle}>{entry.executor || '-'}</td>
                  <td style={{...cellStyle, fontSize: '12px', color: '#666'}}>
                    {entry.folder_path || '-'}
                  </td>
                  <td style={{...cellStyle, whiteSpace: 'nowrap'}}>
                    <button
                      onClick={() => handleEdit(entry)}
                      style={{
                        padding: '6px 12px',
                        marginRight: '8px',
                        background: '#4b5563',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '13px'
                      }}
                    >
                      Редактировать
                    </button>
                    <button
                      onClick={() => handleDelete(entry)}
                      style={{
                        padding: '6px 12px',
                        background: '#dc2626',
                        color: 'white',
                        border: 'none',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        fontSize: '13px'
                      }}
                    >
                      Удалить
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Пагинация */}
          {(() => {
            const totalPages = Math.ceil(totalEntries / PAGE_SIZE);
            return (
              <div style={{
                marginTop: '15px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                color: '#666',
                fontSize: '14px'
              }}>
                <span>
                  Показано {currentPage * PAGE_SIZE + 1}–{Math.min((currentPage + 1) * PAGE_SIZE, totalEntries)} из {totalEntries}
                </span>
                {totalPages > 1 && (
                  <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
                    <button
                      onClick={() => setCurrentPage(0)}
                      disabled={currentPage === 0}
                      style={paginationBtnStyle(currentPage === 0)}
                    >
                      &laquo;
                    </button>
                    <button
                      onClick={() => setCurrentPage(p => p - 1)}
                      disabled={currentPage === 0}
                      style={paginationBtnStyle(currentPage === 0)}
                    >
                      &lsaquo;
                    </button>
                    <span style={{ padding: '0 8px' }}>
                      Стр. {currentPage + 1} из {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage(p => p + 1)}
                      disabled={currentPage >= totalPages - 1}
                      style={paginationBtnStyle(currentPage >= totalPages - 1)}
                    >
                      &rsaquo;
                    </button>
                    <button
                      onClick={() => setCurrentPage(totalPages - 1)}
                      disabled={currentPage >= totalPages - 1}
                      style={paginationBtnStyle(currentPage >= totalPages - 1)}
                    >
                      &raquo;
                    </button>
                  </div>
                )}
              </div>
            );
          })()}
        </div>
      )}

      {/* Модальное окно редактирования */}
      {editingEntry && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '4px',
            width: '500px',
            maxWidth: '90%',
            border: '1px solid #e5e7eb'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '20px' }}>Редактирование записи №{editingEntry.outgoing_no}</h3>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500', fontSize: '14px' }}>
                Форматированный номер:
              </label>
              <input
                type="text"
                value={formData.formatted_number || ''}
                onChange={(e) => setFormData({...formData, formatted_number: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
                placeholder="Например: 4-01"
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500', fontSize: '14px' }}>
                Дата:
              </label>
              <input
                type="date"
                value={formData.outgoing_date || ''}
                onChange={(e) => setFormData({...formData, outgoing_date: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500', fontSize: '14px' }}>
                Кому:
              </label>
              <input
                type="text"
                value={formData.to_whom || ''}
                onChange={(e) => setFormData({...formData, to_whom: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500', fontSize: '14px' }}>
                Исполнитель:
              </label>
              <input
                type="text"
                value={formData.executor || ''}
                onChange={(e) => setFormData({...formData, executor: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>

            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500', fontSize: '14px' }}>
                Путь к файлам:
              </label>
              <input
                type="text"
                value={formData.folder_path || ''}
                onChange={(e) => setFormData({...formData, folder_path: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setEditingEntry(null)}
                style={{
                  padding: '8px 16px',
                  background: '#9ca3af',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Отмена
              </button>
              <button
                onClick={handleSaveEdit}
                style={{
                  padding: '8px 16px',
                  background: '#4b5563',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Модальное окно создания записи */}
      {showCreateForm && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000
        }}>
          <div style={{
            background: 'white',
            padding: '30px',
            borderRadius: '4px',
            width: '500px',
            maxWidth: '90%',
            border: '1px solid #e5e7eb'
          }}>
            <h3 style={{ marginTop: 0, marginBottom: '20px' }}>Создание новой записи</h3>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500', fontSize: '14px' }}>
                Числовая часть номера: <span style={{ color: 'red' }}>*</span>
              </label>
              <input
                type="number"
                value={formData.outgoing_no || ''}
                onChange={(e) => setFormData({...formData, outgoing_no: Number(e.target.value)})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
                placeholder="Например: 4"
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500', fontSize: '14px' }}>
                Форматированный номер: <span style={{ color: 'red' }}>*</span>
              </label>
              <input
                type="text"
                value={formData.formatted_number || ''}
                onChange={(e) => setFormData({...formData, formatted_number: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
                placeholder="Например: 4-01"
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500', fontSize: '14px' }}>
                Дата: <span style={{ color: 'red' }}>*</span>
              </label>
              <input
                type="date"
                value={formData.outgoing_date || ''}
                onChange={(e) => setFormData({...formData, outgoing_date: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500', fontSize: '14px' }}>
                Кому:
              </label>
              <input
                type="text"
                value={formData.to_whom || ''}
                onChange={(e) => setFormData({...formData, to_whom: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500', fontSize: '14px' }}>
                Исполнитель:
              </label>
              <input
                type="text"
                value={formData.executor || ''}
                onChange={(e) => setFormData({...formData, executor: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>

            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: '500', fontSize: '14px' }}>
                Путь к файлам:
              </label>
              <input
                type="text"
                value={formData.folder_path || ''}
                onChange={(e) => setFormData({...formData, folder_path: e.target.value})}
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
                placeholder="Например: /mnt/doc/Исходящие/4-01"
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowCreateForm(false)}
                style={{
                  padding: '8px 16px',
                  background: '#9ca3af',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Отмена
              </button>
              <button
                onClick={handleSaveCreate}
                style={{
                  padding: '8px 16px',
                  background: '#16a34a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px'
                }}
              >
                Создать
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const headerStyle = {
  padding: '12px',
  textAlign: 'left',
  borderBottom: '2px solid #ddd',
  fontWeight: '600',
  color: '#333'
};

const cellStyle = {
  padding: '12px',
  textAlign: 'left'
};

const paginationBtnStyle = (disabled) => ({
  padding: '6px 10px',
  background: disabled ? '#e5e7eb' : '#4b5563',
  color: disabled ? '#9ca3af' : 'white',
  border: 'none',
  borderRadius: '4px',
  cursor: disabled ? 'not-allowed' : 'pointer',
  fontSize: '14px',
  fontWeight: '600'
});

export default Journal;
