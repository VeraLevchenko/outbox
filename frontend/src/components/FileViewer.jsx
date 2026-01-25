import React from 'react';

const FileViewer = ({ fileUrl, fileName }) => {
  if (!fileUrl) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        Выберите файл для просмотра
      </div>
    );
  }

  // Используем endpoint backend для скачивания файла
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const downloadUrl = `${API_BASE_URL}/api/files/download?file_path=${encodeURIComponent(fileUrl)}`;

  // Определяем расширение файла
  const fileExtension = fileName ? fileName.split('.').pop().toLowerCase() : '';

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
        <embed
          src={downloadUrl}
          type="application/pdf"
          style={{
            width: '100%',
            height: '100%',
            border: 'none',
            flex: 1
          }}
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
