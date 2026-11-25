import React, { useState, useEffect } from 'react';
import { filesApi } from '../services/api';

const FileViewer = ({ fileUrl, fileName, cardId }) => {
  const [retryKey, setRetryKey] = useState(0);
  const [preview, setPreview] = useState({ key: null, url: null, error: null });

  useEffect(() => {
    setRetryKey(0);
  }, [fileUrl]);

  const fileExtension = fileName ? fileName.split('.').pop().toLowerCase() : '';
  const isOutgoingPreview = cardId && fileUrl && ['docx', 'pdf'].includes(fileExtension);
  const previewKey = `${cardId}:${fileName}:${fileUrl}:${retryKey}`;

  useEffect(() => {
    if (!isOutgoingPreview) return undefined;
    let cancelled = false;
    let objectUrl = null;
    setPreview({ key: previewKey, url: null, error: null });
    filesApi.previewOutgoingFile(cardId, fileName)
      .then(({ data }) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(data);
        setPreview({ key: previewKey, url: objectUrl, error: null });
      })
      .catch(() => {
        if (!cancelled) setPreview({ key: previewKey, url: null, error: 'Не удалось загрузить документ для просмотра' });
      });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [cardId, fileName, fileUrl, retryKey, isOutgoingPreview]);

  if (!fileUrl) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        Выберите файл для просмотра
      </div>
    );
  }

  const isPublicUrl = fileUrl.startsWith('http://') || fileUrl.startsWith('https://');

  if (isOutgoingPreview) {
    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '10px', background: '#f5f5f5', fontWeight: 'bold', display: 'flex', justifyContent: 'space-between' }}>
          <span>{fileName}</span>
          <button onClick={() => setRetryKey(key => key + 1)}>↺ Обновить</button>
        </div>
        {preview.key === previewKey && preview.url ? (
          <iframe src={preview.url} type="application/pdf" title={fileName} style={{ width: '100%', flex: 1, border: 'none' }} />
        ) : (
          <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
            {(preview.key === previewKey && preview.error) || 'Загрузка документа...'}
          </div>
        )}
      </div>
    );
  }

  if (isPublicUrl) {
    const viewerUrl = `https://docs.google.com/viewer?url=${encodeURIComponent(fileUrl)}&embedded=true&r=${retryKey}`;

    return (
      <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
        {fileName && (
          <div style={{
            padding: '10px',
            background: '#f5f5f5',
            borderBottom: '1px solid #ddd',
            fontWeight: 'bold',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <span>{fileName}</span>
            <button
              onClick={() => setRetryKey(k => k + 1)}
              title="Перезагрузить документ"
              style={{
                padding: '4px 10px',
                background: '#e5e7eb',
                border: '1px solid #d1d5db',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '13px',
                color: '#374151',
                fontWeight: '500',
                flexShrink: 0
              }}
            >
              ↺ Обновить
            </button>
          </div>
        )}
        <iframe
          key={retryKey}
          src={viewerUrl}
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            flex: 1
          }}
          title={fileName || 'Document Viewer'}
        />
      </div>
    );
  }

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const downloadUrl = `${API_BASE_URL}/api/files/download?file_path=${encodeURIComponent(fileUrl)}`;

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {fileName && (
        <div style={{
          padding: '10px',
          background: '#f5f5f5',
          borderBottom: '1px solid #ddd',
          fontWeight: 'bold'
        }}>
          {fileName}
        </div>
      )}

      {fileExtension === 'pdf' ? (
        <iframe
          src={downloadUrl}
          type="application/pdf"
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            flex: 1
          }}
          title={fileName || 'PDF Viewer'}
        />
      ) : (
        <div style={{
          padding: '40px',
          textAlign: 'center',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '20px'
        }}>
          <div style={{ fontSize: '16px', color: '#666' }}>
            Предварительный просмотр недоступен для файлов типа .{fileExtension}
          </div>
          <a
            href={downloadUrl}
            download={fileName}
            style={{
              padding: '12px 24px',
              background: '#4b5563',
              color: 'white',
              textDecoration: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600'
            }}
          >
            Скачать файл
          </a>
        </div>
      )}
    </div>
  );
};

export default FileViewer;
