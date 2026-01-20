import React, { useState, useEffect } from 'react';
import { filesApi, kaitenApi } from '../services/api';
import FileViewer from './FileViewer';

const OutgoingFiles = ({ cardId }) => {
  const [mainDocx, setMainDocx] = useState(null);
  const [attachments, setAttachments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [executor, setExecutor] = useState(null);
  const [executorLoading, setExecutorLoading] = useState(false);

  useEffect(() => {
    if (cardId) {
      loadFiles();
      loadExecutor();
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

  const loadExecutor = async () => {
    try {
      setExecutorLoading(true);
      const response = await kaitenApi.getCardExecutor(cardId);
      setExecutor(response.data);
    } catch (err) {
      console.error('Ошибка загрузки исполнителя:', err);
      // Не показываем ошибку пользователю, так как это не критично
      setExecutor(null);
    } finally {
      setExecutorLoading(false);
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
          background: '#6b7280',
          color: 'white',
          fontWeight: '600',
          fontSize: '15px',
          borderBottom: '1px solid #e5e7eb'
        }}>
          Исходящие файлы ({allFiles.length})
        </div>

        {/* Информация об исполнителе */}
        {executor && (
          <div style={{
            padding: '12px 16px',
            background: '#ffffff',
            borderBottom: '2px solid #e5e7eb',
            fontSize: '14px'
          }}>
            <div style={{
              color: '#6b7280',
              fontSize: '12px',
              fontWeight: '600',
              marginBottom: '4px',
              textTransform: 'uppercase'
            }}>
              Исполнитель
            </div>
            <div style={{
              color: '#111827',
              fontWeight: '500'
            }}>
              {executor.full_name}
            </div>
          </div>
        )}
        {executorLoading && (
          <div style={{
            padding: '12px 16px',
            background: '#ffffff',
            borderBottom: '2px solid #e5e7eb',
            fontSize: '13px',
            color: '#9ca3af'
          }}>
            Загрузка исполнителя...
          </div>
        )}

        {/* Главный DOCX */}
        {mainDocx && (
          <>
            <div style={{
              padding: '10px 16px',
              background: '#f3f4f6',
              fontSize: '12px',
              fontWeight: '600',
              color: '#4b5563',
              borderBottom: '1px solid #e5e7eb'
            }}>
              Главный документ
            </div>
            <div
              onClick={() => setSelectedFile(mainDocx)}
              style={{
                padding: '16px',
                cursor: 'pointer',
                borderBottom: '1px solid #f3f4f6',
                background: selectedFile === mainDocx ? '#f3f4f6' : 'white',
                borderLeft: selectedFile === mainDocx ? '3px solid #4b5563' : '3px solid transparent'
              }}
              onMouseEnter={(e) => {
                if (selectedFile !== mainDocx) {
                  e.currentTarget.style.background = '#fafafa';
                  e.currentTarget.style.borderLeft = '3px solid #d1d5db';
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
              background: '#f3f4f6',
              fontSize: '12px',
              fontWeight: '600',
              color: '#4b5563',
              borderBottom: '1px solid #e5e7eb',
              marginTop: '8px'
            }}>
              Приложения ({attachments.length})
            </div>
            {attachments.map((file, index) => (
              <div
                key={index}
                onClick={() => setSelectedFile(file)}
                style={{
                  padding: '16px',
                  cursor: 'pointer',
                  borderBottom: '1px solid #f3f4f6',
                  background: selectedFile === file ? '#f3f4f6' : 'white',
                  borderLeft: selectedFile === file ? '3px solid #4b5563' : '3px solid transparent'
                }}
                onMouseEnter={(e) => {
                  if (selectedFile !== file) {
                    e.currentTarget.style.background = '#fafafa';
                    e.currentTarget.style.borderLeft = '3px solid #d1d5db';
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
