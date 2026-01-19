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
    return <div style={{ padding: '32px', textAlign: 'center', color: '#6b7280', fontSize: '15px' }}>
      Загрузка исходящих файлов...
    </div>;
  }

  if (error) {
    return <div style={{ padding: '32px', color: '#ef4444', background: '#fef2f2', borderRadius: '8px', margin: '16px', fontSize: '14px' }}>
      {error}
    </div>;
  }

  const allFiles = mainDocx ? [mainDocx, ...attachments] : attachments;

  if (allFiles.length === 0) {
    return <div style={{ padding: '32px', textAlign: 'center', color: '#9ca3af', fontSize: '15px' }}>
      Нет исходящих файлов
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
          background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
          color: 'white',
          fontWeight: '700',
          fontSize: '15px',
          letterSpacing: '0.3px'
        }}>
          📤 Исходящие файлы ({allFiles.length})
        </div>

        {/* Главный DOCX */}
        {mainDocx && (
          <>
            <div style={{
              padding: '10px 16px',
              background: '#fef3c7',
              fontSize: '12px',
              fontWeight: '700',
              color: '#92400e',
              letterSpacing: '0.5px',
              textTransform: 'uppercase'
            }}>
              ⭐ Главный документ
            </div>
            <div
              onClick={() => setSelectedFile(mainDocx)}
              style={{
                padding: '16px',
                cursor: 'pointer',
                borderBottom: '1px solid #f3f4f6',
                background: selectedFile === mainDocx ? '#ede9fe' : 'white',
                transition: 'all 0.2s ease',
                borderLeft: selectedFile === mainDocx ? '3px solid #8b5cf6' : '3px solid transparent'
              }}
              onMouseEnter={(e) => {
                if (selectedFile !== mainDocx) {
                  e.currentTarget.style.background = '#fafafa';
                  e.currentTarget.style.borderLeft = '3px solid #e5e7eb';
                }
              }}
              onMouseLeave={(e) => {
                if (selectedFile !== mainDocx) {
                  e.currentTarget.style.background = 'white';
                  e.currentTarget.style.borderLeft = '3px solid transparent';
                }
              }}
            >
              <div style={{ fontWeight: selectedFile === mainDocx ? '700' : '500', fontSize: '14px', color: '#111827', marginBottom: '6px' }}>
                {mainDocx.name}
              </div>
              <div style={{ fontSize: '12px', color: '#9ca3af' }}>
                {(mainDocx.size / 1024).toFixed(1)} KB
              </div>
            </div>
          </>
        )}

        {/* Приложения */}
        {attachments.length > 0 && (
          <>
            <div style={{
              padding: '10px 16px',
              background: '#d1fae5',
              fontSize: '12px',
              fontWeight: '700',
              color: '#065f46',
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
              marginTop: '8px'
            }}>
              📎 Приложения ({attachments.length})
            </div>
            {attachments.map((file, index) => (
              <div
                key={index}
                onClick={() => setSelectedFile(file)}
                style={{
                  padding: '16px',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f3f4f6',
                  background: selectedFile === file ? '#ede9fe' : 'white',
                  transition: 'all 0.2s ease',
                  borderLeft: selectedFile === file ? '3px solid #8b5cf6' : '3px solid transparent'
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
