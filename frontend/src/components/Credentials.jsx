import React, { useEffect, useState } from 'react';
import { adminApi } from '../services/api';

const roleLabel = (role) => {
  const labels = { acting_chairman: 'И.о. председателя', deputy_chairman: 'Заместитель председателя', director: 'Председатель', head: 'Начальник/заместитель' };
  return role.split(',').map(item => labels[item] || item).join(', ');
};

const Credentials = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    adminApi.getCredentials()
      .then(response => setUsers(response.data.users || []))
      .catch(err => setError(err.response?.data?.detail || err.message))
      .finally(() => setLoading(false));
  }, []);

  const downloadFile = async () => {
    try {
      const response = await adminApi.downloadCredentials();
      const url = URL.createObjectURL(new Blob([response.data], { type: 'application/json' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = 'uchetnye_zapisi_outbox.json';
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  if (loading) return <div style={{ padding: '32px' }}>Загрузка учётных записей...</div>;
  if (error) return <div style={{ padding: '32px', color: '#dc2626' }}>{error}</div>;

  return (
    <div style={{ padding: '24px', overflowY: 'auto', height: '100%', boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px' }}>
        <div>
          <h2 style={{ margin: 0 }}>Учётные записи сотрудников</h2>
          <div style={{ marginTop: '6px', color: '#6b7280', fontSize: '13px' }}>Раздел доступен только администратору.</div>
        </div>
        <button onClick={downloadFile} style={{ padding: '10px 16px', border: 'none', borderRadius: '6px', background: '#4b5563', color: 'white', cursor: 'pointer', fontWeight: '600' }}>
          Скачать файл
        </button>
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white' }}>
        <thead>
          <tr style={{ background: '#f3f4f6', textAlign: 'left' }}>
            {['Сотрудник', 'Логин', 'Пароль', 'Роль'].map(title => <th key={title} style={{ padding: '12px', border: '1px solid #e5e7eb' }}>{title}</th>)}
          </tr>
        </thead>
        <tbody>
          {users.map(user => (
            <tr key={user.username}>
              <td style={{ padding: '12px', border: '1px solid #e5e7eb' }}>{user.full_name}</td>
              <td style={{ padding: '12px', border: '1px solid #e5e7eb', fontFamily: 'monospace' }}>{user.username}</td>
              <td style={{ padding: '12px', border: '1px solid #e5e7eb', fontFamily: 'monospace' }}>{user.password}</td>
              <td style={{ padding: '12px', border: '1px solid #e5e7eb' }}>{roleLabel(user.role)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default Credentials;
