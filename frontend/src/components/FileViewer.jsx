import React from 'react';

const FileViewer = ({ fileUrl, fileName }) => {
  if (!fileUrl) {
    return (
      <div style={{ padding: '20px', textAlign: 'center', color: '#666' }}>
        Выберите файл для просмотра
      </div>
    );
  }

  // Генерируем URL для Google Viewer
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
};

export default FileViewer;
