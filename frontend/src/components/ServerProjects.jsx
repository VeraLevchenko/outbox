import React, { useEffect, useState } from 'react';
import { serverProjectsApi } from '../services/api';
import SigningModal from './SigningModal';

const errorText = (error) => error.response?.data?.detail || error.message;

const ServerProjects = ({ folder, project, onProjectsUpdate, userRole }) => {
  const [files, setFiles] = useState([]);
  const [selected, setSelected] = useState(null);
  const [toWhom, setToWhom] = useState('');
  const [executor, setExecutor] = useState('');
  const [content, setContent] = useState('');
  const [approvalStatus, setApprovalStatus] = useState('');
  const [loading, setLoading] = useState(false);
  const [preparing, setPreparing] = useState(false);
  const [error, setError] = useState('');
  const [registration, setRegistration] = useState(null);
  const [showSigning, setShowSigning] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [viewingSigned, setViewingSigned] = useState(false);

  useEffect(() => {
    setFiles([]);
    setSelected(null);
    setRegistration(null);
    setShowSigning(false);
    setViewingSigned(false);
    setToWhom('');
    setExecutor('');
    setContent('');
    setError('');
    if (!folder || project?.error || !['director', 'acting_chairman'].includes(userRole)) return;
    let cancelled = false;
    setLoading(true);
    serverProjectsApi.getFiles(folder)
      .then((response) => {
        if (cancelled) return;
        setFiles(response.data);
        setSelected(response.data.find((file) => file.is_docx) || response.data[0] || null);
      })
      .catch((err) => { if (!cancelled) setError(errorText(err)); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [folder, project?.error, userRole]);

  useEffect(() => {
    const extension = selected?.name.toLowerCase().split('.').pop();
    if (!folder || !selected || !['pdf', 'docx'].includes(extension)) {
      setPreviewUrl(null);
      return undefined;
    }
    let cancelled = false;
    let url = null;
    setPreviewUrl(null);
    const request = viewingSigned
      ? extension === 'docx'
        ? serverProjectsApi.previewSignedDocx(folder, selected.name)
        : serverProjectsApi.downloadSignedFile(folder, selected.name)
      : extension === 'docx'
        ? serverProjectsApi.previewDocx(folder, selected.name)
        : serverProjectsApi.downloadFile(folder, selected.name);
    request
      .then((response) => {
        if (cancelled) return;
        url = URL.createObjectURL(response.data);
        setPreviewUrl(url);
      })
      .catch((err) => { if (!cancelled) setError(errorText(err)); });
    return () => { cancelled = true; if (url) URL.revokeObjectURL(url); };
  }, [folder, selected, viewingSigned]);

  useEffect(() => {
    if (!folder || viewingSigned || !selected?.is_docx) {
      setApprovalStatus('');
      return undefined;
    }
    let cancelled = false;
    setApprovalStatus('checking');
    const checkApproval = async () => {
      try {
        const statusResponse = await serverProjectsApi.getApprovalStatus(folder, selected.name);
        if (!statusResponse.data.signed) {
          if (!cancelled) setApprovalStatus(statusResponse.data.stale ? 'stale' : 'missing');
          return;
        }
        if (typeof cadesplugin === 'undefined') throw new Error('КриптоПро недоступен');
        const [documentResponse, signatureResponse] = await Promise.all([
          serverProjectsApi.downloadFile(folder, selected.name),
          serverProjectsApi.downloadFile(folder, statusResponse.data.signature_name)
        ]);
        const documentBytes = await documentResponse.data.arrayBuffer();
        const signatureBytes = await signatureResponse.data.arrayBuffer();
        const toBase64 = (buffer) => {
          let binary = '';
          for (const byte of new Uint8Array(buffer)) binary += String.fromCharCode(byte);
          return btoa(binary);
        };
        const signedData = await cadesplugin.CreateObjectAsync('CAdESCOM.CadesSignedData');
        await signedData.propset_ContentEncoding(cadesplugin.CADESCOM_BASE64_TO_BINARY);
        await signedData.propset_Content(toBase64(documentBytes));
        await signedData.VerifyCades(toBase64(signatureBytes), cadesplugin.CADESCOM_CADES_BES, true);
        if (!cancelled) setApprovalStatus('valid');
      } catch (err) {
        if (!cancelled) setApprovalStatus('invalid');
      }
    };
    checkApproval();
    return () => { cancelled = true; };
  }, [folder, selected, viewingSigned]);

  const downloadSelected = async () => {
    if (!selected) return;
    try {
      const response = viewingSigned
        ? await serverProjectsApi.downloadSignedFile(folder, selected.name)
        : await serverProjectsApi.downloadFile(folder, selected.name);
      const url = URL.createObjectURL(response.data);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = selected.name;
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      setError(errorText(err));
    }
  };

  const showSignedFiles = async () => {
    setViewingSigned(true);
    setFiles([]);
    setSelected(null);
    setError('');
    setLoading(true);
    try {
      const response = await serverProjectsApi.getSignedFiles(folder);
      const signedFiles = response.data;
      const generatedPrefix = `${folder.replace(/-/g, '_')}_`;
      setFiles(signedFiles);
      setSelected(
        signedFiles.find((file) => file.name.startsWith(generatedPrefix) && file.name.toLowerCase().endsWith('.pdf'))
        || signedFiles.find((file) => file.name.toLowerCase().endsWith('.pdf'))
        || signedFiles[0]
        || null
      );
      return true;
    } catch (err) {
      setError(`Документ подписан, но не удалось открыть папку «Исходящие»: ${errorText(err)}`);
      return false;
    } finally {
      setLoading(false);
    }
  };

  const prepare = async () => {
    if (!selected?.is_docx) {
      setError('Выберите Word документ DOCX для подписи');
      return;
    }
    if (!toWhom.trim() || !executor.trim()) {
      setError('Укажите адресата и исполнителя');
      return;
    }
    if (approvalStatus === 'checking') {
      setError('Дождитесь проверки согласования');
      return;
    }
    const skipApproval = approvalStatus !== 'valid';
    if (skipApproval && !window.confirm('Согласующая подпись DOCX отсутствует или не прошла проверку. Продолжить без неё?')) return;
    setError('');
    setPreparing(true);
    try {
      const response = await serverProjectsApi.prepare({
        folder, selected_file_name: selected.name, to_whom: toWhom, executor,
        content, skip_head_approval: skipApproval
      });
      setRegistration(response.data);
      setShowSigning(true);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setPreparing(false);
    }
  };

  if (!['director', 'acting_chairman'].includes(userRole)) {
    return <div style={{ padding: '24px' }}>Подписание исходящих писем доступно руководителю.</div>;
  }
  if (!folder) return <div style={{ padding: '24px' }}>Нет проектов на подпись.</div>;
  if (project?.error) return <div style={{ padding: '24px', color: '#b91c1c' }}>{project.error}: {folder}</div>;

  return (
    <div style={{ display: 'flex', gap: '24px', padding: '24px', height: '100%', boxSizing: 'border-box' }}>
      <div style={{ width: '340px', flexShrink: 0, overflowY: 'auto' }}>
        <h2 style={{ marginTop: 0 }}>{viewingSigned ? 'Подписано' : 'Проект'} № {folder}</h2>
        <p style={{ fontSize: '13px', color: '#4b5563' }}>
          {viewingSigned ? `Исходящие\\${folder}` : `Проекты_исходящие\\${folder}`}
        </p>
        {viewingSigned && <button onClick={onProjectsUpdate} style={{ padding: '9px 12px', marginBottom: '16px' }}>К следующему проекту</button>}
        {loading && <p>Загрузка файлов...</p>}
        {error && <p role="alert" style={{ color: '#b91c1c' }}>{error}</p>}
        {!loading && files.length === 0 && !error && <p>В папке нет файлов.</p>}
        {!viewingSigned && !loading && files.length > 0 && !files.some((file) => file.is_docx) && <p role="alert">В папке нет Word документа DOCX для подписи.</p>}
        {files.map((file) => (
          <button key={file.name} onClick={() => setSelected(file)} style={{ display: 'block', width: '100%', textAlign: 'left', padding: '10px', marginBottom: '6px', border: '1px solid #d1d5db', borderRadius: '4px', background: selected?.name === file.name ? '#e5e7eb' : 'white', cursor: 'pointer' }}>
            {file.name} <small>({(file.size / 1024).toFixed(1)} КБ)</small>
          </button>
        ))}
        {!viewingSigned && <><label style={{ display: 'block', marginTop: '16px' }}>Кому
          <input value={toWhom} onChange={(event) => setToWhom(event.target.value)} style={{ display: 'block', width: '100%', padding: '9px', boxSizing: 'border-box' }} />
        </label>
        <label style={{ display: 'block', marginTop: '12px' }}>Исполнитель
          <input value={executor} onChange={(event) => setExecutor(event.target.value)} style={{ display: 'block', width: '100%', padding: '9px', boxSizing: 'border-box' }} />
        </label>
        <label style={{ display: 'block', marginTop: '12px' }}>Краткое содержание (необязательно)
          <textarea value={content} onChange={(event) => setContent(event.target.value)} style={{ display: 'block', width: '100%', padding: '9px', boxSizing: 'border-box' }} />
        </label>
        {selected?.is_docx && <p style={{ fontSize: '13px', color: approvalStatus === 'valid' ? '#166534' : '#92400e' }}>
          {approvalStatus === 'checking' ? 'Проверка согласования...' : approvalStatus === 'valid' ? 'DOCX согласован, подпись действительна' : approvalStatus === 'stale' ? 'Согласование относится к другой версии DOCX' : approvalStatus === 'invalid' ? 'Подпись согласования не прошла проверку' : 'Подпись согласования не найдена'}
        </p>}
        <button onClick={prepare} disabled={preparing || !selected?.is_docx} style={{ marginTop: '18px', padding: '12px', width: '100%', background: '#4b5563', color: 'white', border: 0, borderRadius: '4px', cursor: 'pointer' }}>
          {preparing ? 'Подготовка...' : 'Зарегистрировать и подписать'}
        </button>
        </>}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        {selected && <div style={{ padding: '10px', background: '#f3f4f6' }}>{selected.name}</div>}
        {previewUrl ? (
          <iframe src={previewUrl} title={selected.name} style={{ width: '100%', height: '80%', border: 0 }} />
        ) : selected ? (
          <p>Предпросмотр этого файла недоступен. Скачайте его для просмотра.</p>
        ) : null}
        {selected && <button onClick={downloadSelected} style={{ padding: '10px 16px' }}>Скачать файл</button>}
      </div>
      {registration && (
        <SigningModal
          isOpen={showSigning}
          onClose={() => setShowSigning(false)}
          serverMode
          fileId={registration.file_id}
          pdfFile={registration.docx_preview_url.split('/').pop()}
          formattedNumber={registration.formatted_number}
          outgoingDate={registration.outgoing_date}
          onSuccess={async (result) => {
            setShowSigning(false);
            setRegistration(null);
            const shown = await showSignedFiles();
            if (result?.warning) alert(result.warning);
            else if (!shown) alert(`Документ № ${folder} подписан, но открыть подписанные файлы не удалось.`);
          }}
        />
      )}
    </div>
  );
};

export default ServerProjects;
