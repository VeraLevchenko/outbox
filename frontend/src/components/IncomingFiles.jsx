import React, { useState, useEffect } from 'react';
import { filesApi } from '../services/api';
import FileViewer from './FileViewer';

const IncomingFiles = ({ cardId }) => {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (cardId) {
      loadFiles();
    }
  }, [cardId]);

  const loadFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await filesApi.getIncomingFiles(cardId);
      setFiles(response.data.files || []);
      // Автоматически выбираем первый файл
      if (response.data.files && response.data.files.length > 0) {
        setSelectedFile(response.data.files[0]);
      }
    } catch (err) {
      setError('Ошибка загрузки входящих файлов: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ padding: '32px', textAlign: 'center', color: '#6b7280', fontSize: '15px' }}>
      Загрузка входящих файлов...
    </div>;
  }

  if (error) {
    return <div style={{ padding: '32px', color: '#ef4444', background: '#fef2f2', borderRadius: '8px', margin: '16px', fontSize: '14px' }}>
      {error}
    </div>;
  }

  if (files.length === 0) {
    return <div style={{ padding: '32px', textAlign: 'center', color: '#9ca3af', fontSize: '15px' }}>
      Нет входящих файлов
    </div>;
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      {/* Список файлов слева */}
      <div style={{
        width: '280px',
        borderRight: '1px solid #e5e7eb',
        background: '#f9fafb',
        overflowY: 'auto',
        boxShadow: '2px 0 8px rgba(0,0,0,0.04)'
      }}>
        <div style={{
          padding: '16px 20px',
          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
          color: 'white',
          fontWeight: '700',
          fontSize: '15px',
          letterSpacing: '0.3px'
        }}>
          📥 Входящие файлы ({files.length})
        </div>
        {files.map((file, index) => (
          <div
            key={index}
            onClick={() => setSelectedFile(file)}
            style={{
              padding: '16px',
              cursor: 'pointer',
              borderBottom: '1px solid #f3f4f6',
              background: selectedFile === file ? '#dcfce7' : 'white',
              transition: 'all 0.2s ease',
              borderLeft: selectedFile === file ? '3px solid #10b981' : '3px solid transparent'
            }}
            onMouseEnter={(e) => {
              if (selectedFile !== file) {
                e.currentTarget.style.background = '#fafafa';
                e.currentTarget.style.borderLeft = '3px solid #e5e7eb';
              }
            }}
            onMouseLeave={(e) => {
              if (selectedFile !== file) {
                e.currentTarget.style.background = 'white';
                e.currentTarget.style.borderLeft = '3px solid transparent';
              }
            }}
          >
            <div style={{ fontWeight: selectedFile === file ? '700' : '500', fontSize: '14px', color: '#111827', marginBottom: '6px' }}>
              {file.name}
            </div>
            <div style={{ fontSize: '12px', color: '#9ca3af' }}>
              {(file.size / 1024).toFixed(1)} KB
            </div>
            {file.is_main && (
              <div style={{
                fontSize: '11px',
                color: '#10b981',
                marginTop: '6px',
                fontWeight: '700',
                letterSpacing: '0.3px'
              }}>
                ⭐ Основной документ
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Просмотр файла справа */}
      <div style={{ flex: 1 }}>
        <FileViewer
          fileUrl={selectedFile?.path}
          fileName={selectedFile?.name}
        />
      </div>
    </div>
  );
};

export default IncomingFiles;
