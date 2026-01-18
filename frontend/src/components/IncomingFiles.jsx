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
    return <div style={{ padding: '20px' }}>Загрузка входящих файлов...</div>;
  }

  if (error) {
    return <div style={{ padding: '20px', color: 'red' }}>{error}</div>;
  }

  if (files.length === 0) {
    return <div style={{ padding: '20px' }}>Нет входящих файлов</div>;
  }

  return (
    <div style={{ display: 'flex', height: '100%' }}>
      {/* Список файлов слева */}
      <div style={{
        width: '250px',
        borderRight: '1px solid #ddd',
        background: '#f9f9f9',
        overflowY: 'auto'
      }}>
        <div style={{
          padding: '10px',
          background: '#4CAF50',
          color: 'white',
          fontWeight: 'bold'
        }}>
          Входящие файлы ({files.length})
        </div>
        {files.map((file, index) => (
          <div
            key={index}
            onClick={() => setSelectedFile(file)}
            style={{
              padding: '12px',
              cursor: 'pointer',
              borderBottom: '1px solid #eee',
              background: selectedFile === file ? '#e3f2fd' : 'white',
              transition: 'background 0.2s'
            }}
            onMouseEnter={(e) => {
              if (selectedFile !== file) {
                e.target.style.background = '#f5f5f5';
              }
            }}
            onMouseLeave={(e) => {
              if (selectedFile !== file) {
                e.target.style.background = 'white';
              }
            }}
          >
            <div style={{ fontWeight: selectedFile === file ? 'bold' : 'normal' }}>
              {file.name}
            </div>
            <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
              {(file.size / 1024).toFixed(1)} KB
            </div>
            {file.is_main && (
              <div style={{
                fontSize: '11px',
                color: '#4CAF50',
                marginTop: '4px',
                fontWeight: 'bold'
              }}>
                ● Основной документ
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
