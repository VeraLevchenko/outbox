import React from 'react';

const FileViewer = ({ fileUrl, fileName }) => {
  if (!fileUrl) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        Выберите файл для просмотра
      </div>
    );
  }

  // Определяем тип файла: URL из Kaiten (публичный) или путь на сервере (локальный)
  const isPublicUrl = fileUrl.startsWith('http://') || fileUrl.startsWith('https://');

  // Определяем расширение файла
  const fileExtension = fileName ? fileName.split('.').pop().toLowerCase() : '';

  // Для файлов из Kaiten (публичные URL) - используем Google Viewer
  if (isPublicUrl) {
    const viewerUrl = `https://docs.google.com/viewer?url=${encodeURIComponent(fileUrl)}&embedded=true`;

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
        <iframe
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

  // Для файлов с сервера (локальные пути) - используем endpoint для скачивания
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

      {/* Просмотр PDF встроенным просмотрщиком браузера */}
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
        /* Для других форматов - предложение скачать */
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
