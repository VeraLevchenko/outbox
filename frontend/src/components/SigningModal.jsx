import React, { useState, useEffect } from 'react';
import { outboxApi } from '../services/api';

const SigningModal = ({ isOpen, onClose, fileId, pdfFile, cardId, outgoingNo, outgoingDate, toWhom, executor, onSuccess }) => {
  const [certificates, setCertificates] = useState([]);
  const [selectedCert, setSelectedCert] = useState(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      initPlugin();
    }
  }, [isOpen]);

  const initPlugin = async () => {
    setStatus('Инициализация плагина КриптоПро...');
    setLoading(true);

    try {
      if (typeof cadesplugin === 'undefined') {
        throw new Error('Плагин КриптоПро не найден. Установите с https://www.cryptopro.ru/products/cades/plugin');
      }

      // Ожидание инициализации плагина
      let pluginReady = false;
      let attempts = 0;
      const maxAttempts = 30;

      while (!pluginReady && attempts < maxAttempts) {
        try {
          attempts++;
          const testAbout = await cadesplugin.CreateObjectAsync("CAdESCOM.About");
          pluginReady = true;

          setStatus('Плагин активен. Загрузка сертификатов...');
          await loadCertificates();

        } catch (err) {
          if (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 1000));
          } else {
            throw err;
          }
        }
      }

      if (!pluginReady) {
        throw new Error('Не удалось инициализировать плагин за 30 секунд');
      }

    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const loadCertificates = async () => {
    try {
      const store = await cadesplugin.CreateObjectAsync("CAdESCOM.Store");
      await store.Open(
        cadesplugin.CAPICOM_CURRENT_USER_STORE,
        cadesplugin.CAPICOM_MY_STORE,
        cadesplugin.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED
      );

      const certs = await store.Certificates;
      const count = await certs.Count;

      if (count === 0) {
        setError('Сертификаты КЭП не найдены в хранилище');
        setLoading(false);
        return;
      }

      const certList = [];

      for (let i = 1; i <= count; i++) {
        try {
          const cert = await certs.Item(i);
          const subjectName = await cert.SubjectName;
          const validTo = await cert.ValidToDate;
          const thumbprint = await cert.Thumbprint;
          const hasPrivateKey = await cert.HasPrivateKey();
          const isValid = await cert.IsValid();
          const isValidResult = await isValid.Result;

          const cnMatch = subjectName.match(/CN=([^,]+)/);
          const cn = cnMatch ? cnMatch[1] : subjectName.substring(0, 50);

          if (hasPrivateKey && isValidResult) {
            certList.push({
              index: i,
              thumbprint: thumbprint,
              cn: cn,
              subjectName: subjectName,
              validTo: new Date(validTo),
              hasPrivateKey: hasPrivateKey,
              isValid: isValidResult
            });
          }
        } catch (certErr) {
          console.error(`Ошибка при обработке сертификата ${i}:`, certErr);
        }
      }

      await store.Close();

      if (certList.length === 0) {
        setError('Нет действительных сертификатов с закрытыми ключами');
        setLoading(false);
        return;
      }

      setCertificates(certList);
      setStatus('Выберите сертификат для подписания');
      setLoading(false);

    } catch (err) {
      setError('Ошибка загрузки сертификатов: ' + err.message);
      setLoading(false);
    }
  };

  const handleSign = async () => {
    if (!selectedCert) {
      setError('Выберите сертификат');
      return;
    }

    setLoading(true);
    setStatus('Загрузка PDF...');

    try {
      // 1. Получаем PDF
      const token = localStorage.getItem('token');
      const pdfResponse = await fetch(`http://localhost:8000/api/outbox/download/${pdfFile}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!pdfResponse.ok) {
        throw new Error(`Ошибка загрузки PDF: ${pdfResponse.status}`);
      }

      const pdfBlob = await pdfResponse.blob();
      const pdfArrayBuffer = await pdfBlob.arrayBuffer();
      setStatus(`PDF загружен (${pdfArrayBuffer.byteLength} байт)`);

      // 2. Конвертируем в Base64
      setStatus('Подготовка данных...');
      const pdfBase64 = arrayBufferToBase64(pdfArrayBuffer);

      // 3. Получаем сертификат
      setStatus('Получение сертификата...');
      const store = await cadesplugin.CreateObjectAsync("CAdESCOM.Store");
      await store.Open(
        cadesplugin.CAPICOM_CURRENT_USER_STORE,
        cadesplugin.CAPICOM_MY_STORE,
        cadesplugin.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED
      );

      const certs = await store.Certificates;
      const foundCerts = await certs.Find(
        cadesplugin.CAPICOM_CERTIFICATE_FIND_SHA1_HASH,
        selectedCert.thumbprint
      );

      const foundCount = await foundCerts.Count;
      if (foundCount === 0) {
        throw new Error('Сертификат не найден по отпечатку');
      }

      const cert = await foundCerts.Item(1);
      await store.Close();

      // 4. Создаём подпись
      setStatus('Создание подписи (может появиться окно PIN)...');

      const signer = await cadesplugin.CreateObjectAsync("CAdESCOM.CPSigner");
      await signer.propset_Certificate(cert);
      await signer.propset_CheckCertificate(true);

      const signedData = await cadesplugin.CreateObjectAsync("CAdESCOM.CadesSignedData");
      await signedData.propset_ContentEncoding(cadesplugin.CADESCOM_BASE64_TO_BINARY);
      await signedData.propset_Content(pdfBase64);

      const signature = await signedData.SignCades(
        signer,
        cadesplugin.CADESCOM_CADES_BES,
        true  // detached = true
      );

      setStatus('Отправка подписи на сервер...');

      // 5. Отправляем на сервер с данными для журнала
      await outboxApi.uploadClientSignature({
        file_id: fileId,
        signature: signature,
        thumbprint: selectedCert.thumbprint,
        cn: selectedCert.cn,
        // Данные для записи в журнал
        card_id: cardId,
        outgoing_no: outgoingNo,
        outgoing_date: outgoingDate,
        to_whom: toWhom,
        executor: executor
      });

      setStatus('✅ Подпись успешно создана!');
      setLoading(false);

      // Уведомляем родительский компонент
      if (onSuccess) {
        setTimeout(() => {
          onSuccess();
        }, 1500);
      }

    } catch (err) {
      console.error('Ошибка подписания:', err);
      setError('Ошибка подписания: ' + err.message);
      setLoading(false);
    }
  };

  const arrayBufferToBase64 = (buffer) => {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  };

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: 'white',
        borderRadius: '8px',
        padding: '24px',
        maxWidth: '500px',
        width: '90%',
        maxHeight: '80vh',
        overflow: 'auto',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
      }}>
        <h2 style={{ marginBottom: '16px', fontSize: '20px', fontWeight: '600' }}>
          🔐 Подписание документа
        </h2>

        {/* Статус */}
        {status && (
          <div style={{
            padding: '12px',
            background: '#f0fdf4',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '14px',
            color: '#166534'
          }}>
            {status}
          </div>
        )}

        {/* Ошибка */}
        {error && (
          <div style={{
            padding: '12px',
            background: '#fef2f2',
            borderRadius: '6px',
            marginBottom: '16px',
            fontSize: '14px',
            color: '#dc2626'
          }}>
            {error}
          </div>
        )}

        {/* Список сертификатов */}
        {certificates.length > 0 && !loading && (
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontWeight: '500', fontSize: '14px' }}>
              Выберите сертификат КЭП:
            </label>
            <select
              value={selectedCert?.thumbprint || ''}
              onChange={(e) => {
                const cert = certificates.find(c => c.thumbprint === e.target.value);
                setSelectedCert(cert);
              }}
              style={{
                width: '100%',
                padding: '12px',
                fontSize: '14px',
                border: '2px solid #e5e7eb',
                borderRadius: '6px',
                marginBottom: '16px'
              }}
            >
              <option value="">-- Выберите сертификат --</option>
              {certificates.map((cert, index) => (
                <option key={index} value={cert.thumbprint}>
                  {cert.cn} (до {cert.validTo.toLocaleDateString()})
                </option>
              ))}
            </select>
          </div>
        )}

        {/* Кнопки */}
        <div style={{ display: 'flex', gap: '12px', marginTop: '20px' }}>
          <button
            onClick={handleSign}
            disabled={!selectedCert || loading}
            style={{
              flex: 1,
              padding: '12px 24px',
              background: (!selectedCert || loading) ? '#9ca3af' : '#4b5563',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: (!selectedCert || loading) ? 'not-allowed' : 'pointer'
            }}
          >
            {loading ? 'Подписание...' : '🔏 Подписать'}
          </button>
          <button
            onClick={onClose}
            disabled={loading}
            style={{
              padding: '12px 24px',
              background: 'white',
              color: '#6b7280',
              border: '2px solid #e5e7eb',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: loading ? 'not-allowed' : 'pointer'
            }}
          >
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
};

export default SigningModal;
