const PREFERRED_CERTIFICATE_KEY = 'outbox_preferred_certificate';

let certificatesPromise = null;

const PLUGIN_OPERATION_TIMEOUT_MS = 15000;

const withTimeout = (promise, operation) => Promise.race([
  promise,
  new Promise((_, reject) => {
    setTimeout(
      () => reject(new Error(`КриптоПро не ответил: ${operation}`)),
      PLUGIN_OPERATION_TIMEOUT_MS
    );
  })
]);

const waitForPlugin = async () => {
  for (let attempt = 1; attempt <= 30; attempt += 1) {
    try {
      if (typeof cadesplugin === 'undefined') throw new Error('Плагин КриптоПро не найден');
      await withTimeout(
        cadesplugin.CreateObjectAsync('CAdESCOM.About'),
        'проверка плагина'
      );
      return;
    } catch (error) {
      if (attempt === 30) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
};

const loadCertificates = async () => {
  await waitForPlugin();
  const store = await withTimeout(
    cadesplugin.CreateObjectAsync('CAdESCOM.Store'),
    'создание хранилища сертификатов'
  );
  await withTimeout(
    store.Open(
      cadesplugin.CAPICOM_CURRENT_USER_STORE,
      cadesplugin.CAPICOM_MY_STORE,
      cadesplugin.CAPICOM_STORE_OPEN_MAXIMUM_ALLOWED
    ),
    'открытие хранилища сертификатов'
  );
  try {
    const certs = await store.Certificates;
    const count = await certs.Count;
    const result = [];
    for (let index = 1; index <= count; index += 1) {
      try {
        const cert = await certs.Item(index);
        const subjectName = await cert.SubjectName;
        const validTo = await cert.ValidToDate;
        const thumbprint = await cert.Thumbprint;
        const hasPrivateKey = await cert.HasPrivateKey();
        const validity = await cert.IsValid();
        if (hasPrivateKey && await validity.Result) {
          const cnMatch = subjectName.match(/CN=([^,]+)/);
          result.push({
            index,
            thumbprint,
            cn: cnMatch ? cnMatch[1] : subjectName.substring(0, 50),
            subjectName,
            validTo: new Date(validTo)
          });
        }
      } catch (error) {
        console.error(`Ошибка при обработке сертифика ${index}:`, error);
      }
    }
    if (!result.length) throw new Error('Нет действительных сертификатов с закрытыми ключами');
    return result;
  } finally {
    await store.Close();
  }
};

export const preloadCryptoPro = () => {
  if (!certificatesPromise) {
    certificatesPromise = withTimeout(
      loadCertificates(),
      'загрузка списка сертификатов'
    ).catch(error => {
      certificatesPromise = null;
      throw error;
    });
  }
  return certificatesPromise;
};

export const resetCryptoProCache = () => {
  certificatesPromise = null;
};

export const getPreferredCertificate = () => sessionStorage.getItem(PREFERRED_CERTIFICATE_KEY);

export const setPreferredCertificate = (thumbprint) => {
  if (thumbprint) sessionStorage.setItem(PREFERRED_CERTIFICATE_KEY, thumbprint);
  else sessionStorage.removeItem(PREFERRED_CERTIFICATE_KEY);
};
