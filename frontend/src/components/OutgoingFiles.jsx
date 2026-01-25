import React, { useState, useEffect } from 'react';
import { filesApi, kaitenApi, outboxApi } from '../services/api';
import FileViewer from './FileViewer';
import SigningModal from './SigningModal';

const OutgoingFiles = ({ cardId }) => {
  const [mainDocx, setMainDocx] = useState(null);
  const [attachments, setAttachments] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [executor, setExecutor] = useState(null);
  const [executorLoading, setExecutorLoading] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [registrationResult, setRegistrationResult] = useState(null);
  const [showSigningModal, setShowSigningModal] = useState(false);
  const [cardTitle, setCardTitle] = useState('');

  useEffect(() => {
    if (cardId) {
      loadFiles();
      loadExecutor();
      loadCardTitle();
    }
  }, [cardId]);

  const loadFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('[OutgoingFiles] Loading files for card:', cardId);
      const response = await filesApi.getOutgoingFiles(cardId);
      console.log('[OutgoingFiles] Files loaded:', response.data);
      console.log('[OutgoingFiles] Main DOCX:', response.data.main_docx);
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
      console.log('[OutgoingFiles] Loading executor for card:', cardId);
      const response = await kaitenApi.getCardExecutor(cardId);
      console.log('[OutgoingFiles] Executor loaded:', response.data);
      setExecutor(response.data);
    } catch (err) {
      console.error('Ошибка загрузки исполнителя:', err);
      console.error('Error details:', err.response?.data);
      // Не показываем ошибку пользователю, так как это не критично
      setExecutor(null);
    } finally {
      setExecutorLoading(false);
    }
  };

  const loadCardTitle = async () => {
    try {
      console.log('[OutgoingFiles] Loading card title for card:', cardId);
      // Используем существующий метод из filesApi для получения файлов
      // В ответе обычно есть информация о карточке
      const response = await filesApi.getOutgoingFiles(cardId);
      // Если в ответе есть card_title, используем его
      if (response.data.card_title) {
        setCardTitle(response.data.card_title);
      }
    } catch (err) {
      console.error('Ошибка загрузки названия карточки:', err);
      setCardTitle('');
    }
  };

  const handleRegisterAndSign = async () => {
    if (!executor) {
      alert('Исполнитель не найден. Убедитесь, что в карточке Kaiten есть участник с типом 2.');
      return;
    }

    if (!selectedFile) {
      alert('Выберите файл для регистрации в просмотрщике.');
      return;
    }

    // Проверяем, что выбранный файл - DOCX
    if (!selectedFile.name.toLowerCase().endsWith('.docx')) {
      alert(`Файл "${selectedFile.name}" не является DOCX документом.\n\nРегистрировать можно только DOCX файлы с полями для заполнения ({{outgoing_no}}, {{outgoing_date}}, {{stamp}}).`);
      return;
    }

    try {
      setRegistering(true);
      setRegistrationResult(null);

      // Поле "Кому" берется из названия карточки (title)
      // Исполнитель используется только для генерации номера
      // Подписывается файл, который открыт в просмотрщике
      const response = await outboxApi.prepareRegistration(cardId, selectedFile.name);
      setRegistrationResult(response.data);

      // Открываем модальное окно для подписания
      setShowSigningModal(true);

    } catch (err) {
      console.error('Ошибка регистрации:', err);
      alert('Ошибка регистрации: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRegistering(false);
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

  // Отладочная информация
  console.log('[OutgoingFiles] Render state:', {
    mainDocx: !!mainDocx,
    executor: !!executor,
    executorLoading,
    registering,
    cardId
  });

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

        {/* Предупреждение, если исполнитель не найден */}
        {!executorLoading && !executor && (
          <div style={{
            padding: '12px 16px',
            background: '#fef3c7',
            borderBottom: '2px solid #e5e7eb',
            fontSize: '13px',
            color: '#92400e'
          }}>
            <div style={{ fontWeight: '600', marginBottom: '4px' }}>
              Исполнитель не найден
            </div>
            <div style={{ fontSize: '12px' }}>
              Убедитесь, что в карточке есть участник с типом 2
            </div>
          </div>
        )}

        {/* Кнопка "Зарегистрировать и подписать" */}
        {executor && (
          <div style={{
            padding: '16px',
            background: '#ffffff',
            borderBottom: '2px solid #e5e7eb'
          }}>
            <button
              onClick={handleRegisterAndSign}
              disabled={registering}
              style={{
                width: '100%',
                padding: '12px 16px',
                background: registering ? '#9ca3af' : '#4b5563',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: registering ? 'not-allowed' : 'pointer',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => {
                if (!registering) {
                  e.currentTarget.style.background = '#374151';
                }
              }}
              onMouseLeave={(e) => {
                if (!registering) {
                  e.currentTarget.style.background = '#4b5563';
                }
              }}
            >
              {registering ? 'Регистрация...' : 'Зарегистрировать и подписать'}
            </button>
          </div>
        )}

        {/* Результат регистрации */}
        {registrationResult && (
          <div style={{
            padding: '12px 16px',
            background: '#f0fdf4',
            borderBottom: '2px solid #e5e7eb',
            fontSize: '13px'
          }}>
            <div style={{
              color: '#166534',
              fontWeight: '600',
              marginBottom: '4px'
            }}>
              Документ зарегистрирован
            </div>
            <div style={{ color: '#15803d', fontSize: '12px' }}>
              № {registrationResult.formatted_number} от {registrationResult.outgoing_date}
            </div>
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

      {/* Модальное окно подписания */}
      {registrationResult && (
        <SigningModal
          isOpen={showSigningModal}
          onClose={() => setShowSigningModal(false)}
          fileId={registrationResult.file_id}
          pdfFile={registrationResult.file_id + '_' + registrationResult.formatted_number.replace(/[\/\-\\]/g, '_') + '_' + registrationResult.outgoing_date.replace(/\./g, '_') + '_' + selectedFile.name.replace(/\s/g, '_').replace(/[()[\]]/g, '').replace('.docx', '.pdf')}
          cardId={cardId}
          outgoingNo={registrationResult.outgoing_no}
          formattedNumber={registrationResult.formatted_number}
          outgoingDate={registrationResult.outgoing_date}
          toWhom={cardTitle}
          executor={registrationResult.executor}
          onSuccess={() => {
            setShowSigningModal(false);
            alert('✅ Документ успешно подписан и запись добавлена в журнал!');
          }}
        />
      )}
    </div>
  );
};

export default OutgoingFiles;
