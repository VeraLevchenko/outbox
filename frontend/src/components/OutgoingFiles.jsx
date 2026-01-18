import React, { useState, useEffect } from 'react';
import { filesApi } from '../services/api';
import FileViewer from './FileViewer';

const OutgoingFiles = ({ cardId }) => {
  const [mainDocx, setMainDocx] = useState(null);
  const [attachments, setAttachments] = useState([]);
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
      const response = await filesApi.getOutgoingFiles(cardId);
      setMainDocx(response.data.main_docx);
      setAttachments(response.data.attachments || []);

      // Автоматически выбираем главный DOCX
      if (response.data.main_docx) {
        setSelectedFile(response.data.main_docx);
      } else if (response.data.attachments && response.data.attachments.length > 0) {
        setSelectedFile(response.data.attachments[0]);
      }
    } catch (err) {
      setError('Ошибка загрузки исходящих файлов: ' + err.message);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ padding: '20px' }}>Загрузка исходящих файлов...</div>;
  }

  if (error) {
    return <div style={{ padding: '20px', color: 'red' }}>{error}</div>;
  }

  const allFiles = mainDocx ? [mainDocx, ...attachments] : attachments;

  if (allFiles.length === 0) {
    return <div style={{ padding: '20px' }}>Нет исходящих файлов</div>;
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
          background: '#2196F3',
          color: 'white',
          fontWeight: 'bold'
        }}>
          Исходящие файлы ({allFiles.length})
        </div>

        {/* Главный DOCX */}
        {mainDocx && (
          <>
            <div style={{
              padding: '8px 12px',
              background: '#fff3cd',
              fontSize: '12px',
              fontWeight: 'bold',
              color: '#856404'
            }}>
              Главный документ
            </div>
            <div
              onClick={() => setSelectedFile(mainDocx)}
              style={{
                padding: '12px',
                cursor: 'pointer',
                borderBottom: '1px solid #eee',
                background: selectedFile === mainDocx ? '#e3f2fd' : 'white',
                transition: 'background 0.2s'
              }}
              onMouseEnter={(e) => {
                if (selectedFile !== mainDocx) {
                  e.target.style.background = '#f5f5f5';
                }
              }}
              onMouseLeave={(e) => {
                if (selectedFile !== mainDocx) {
                  e.target.style.background = 'white';
                }
              }}
            >
              <div style={{ fontWeight: selectedFile === mainDocx ? 'bold' : 'normal' }}>
                {mainDocx.name}
              </div>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                {(mainDocx.size / 1024).toFixed(1)} KB
              </div>
            </div>
          </>
        )}

        {/* Приложения */}
        {attachments.length > 0 && (
          <>
            <div style={{
              padding: '8px 12px',
              background: '#e8f5e9',
              fontSize: '12px',
              fontWeight: 'bold',
              color: '#2e7d32'
            }}>
              Приложения ({attachments.length})
            </div>
            {attachments.map((file, index) => (
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
              </div>
            ))}
          </>
        )}
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

export default OutgoingFiles;
