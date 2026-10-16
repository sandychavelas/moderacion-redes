import { useState, useEffect, useRef } from 'react';
import {
  Bell,
  MapPin,
  Camera,
  CheckCircle2,
  AlertOctagon,
  Clock,
  Send,
  Key,
  Smartphone,
  RefreshCw,
  Info,
  ExternalLink,
  Trash2,
  Video,
  VideoOff,
} from 'lucide-react';
import {
  getNotificationPermission,
  requestAndSubscribePush,
  getSavedPushSubscription,
  unsubscribePush,
  sendPushNotification,
  queryGeolocationPermission,
  queryCameraPermission,
  requestDeviceLocation,
} from '../services/pwaFeatures';
import type {
  PermissionStatusType,
  PushSubscriptionDetails,
  ModeratorLocation,
  PermissionLogEntry,
} from '../services/pwaFeatures';

interface DeviceFeaturesPanelProps {
  moderatorLocation: ModeratorLocation | null;
  onLocationUpdate: (loc: ModeratorLocation | null) => void;
  pendingCount: number;
}

export function DeviceFeaturesPanel({
  moderatorLocation,
  onLocationUpdate,
  pendingCount,
}: DeviceFeaturesPanelProps) {
  // Estados de permisos
  const [notifPermission, setNotifPermission] = useState<PermissionStatusType>(() =>
    getNotificationPermission()
  );
  const [geoPermission, setGeoPermission] = useState<PermissionStatusType>('prompt');
  const [camPermission, setCamPermission] = useState<PermissionStatusType>('prompt');

  // Estado de suscripción Push
  const [subscription, setSubscription] = useState<PushSubscriptionDetails | null>(() =>
    getSavedPushSubscription()
  );
  const [subscribing, setSubscribing] = useState(false);

  // Configuración de notificación de prueba
  const [customTitle, setCustomTitle] = useState('🛡️ Alerta de Moderación IA');
  const [customBody, setCustomBody] = useState(
    `Tienes ${pendingCount || 4} publicaciones pendientes de revisión en la bandeja.`
  );
  const [sendingPush, setSendingPush] = useState(false);

  // Estado de Geolocalización
  const [loadingGeo, setLoadingGeo] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);

  // Estado de Cámara
  const [cameraActive, setCameraActive] = useState(false);
  const [loadingCam, setLoadingCam] = useState(false);
  const [camError, setCamError] = useState<string | null>(null);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // Bitácora de verificación de permisos (Punto 4 de la práctica)
  const [logs, setLogs] = useState<PermissionLogEntry[]>([
    {
      id: 'init-1',
      timestamp: new Date().toLocaleTimeString(),
      feature: 'ServiceWorker',
      status: 'info',
      title: 'Panel de Práctica 2.1 Inicializado',
      detail: `Estado inicial de Notificaciones: "${getNotificationPermission()}". Listo para verificar permisos concedidos o denegados.`,
    },
  ]);

  const addLog = (
    feature: PermissionLogEntry['feature'],
    status: PermissionLogEntry['status'],
    title: string,
    detail: string
  ) => {
    setLogs((prev) => [
      {
        id: `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`,
        timestamp: new Date().toLocaleTimeString(),
        feature,
        status,
        title,
        detail,
      },
      ...prev.slice(0, 24),
    ]);
  };

  // Sincronizar estado de permisos nativos y escuchar mensajes del Service Worker
  useEffect(() => {
    const syncPermissions = async () => {
      setNotifPermission(getNotificationPermission());
      const gPerm = await queryGeolocationPermission();
      setGeoPermission(gPerm);
      const cPerm = await queryCameraPermission();
      setCamPermission(cPerm);
    };
    void syncPermissions();

    const handleSWMessage = (event: MessageEvent) => {
      if (event.data && event.data.type === 'NOTIFICATION_CLICKED') {
        addLog(
          'Push',
          'success',
          'Clic en Notificación Push detectado',
          `El usuario interactuó con la notificación "${event.data.payload?.title}" (acción: ${event.data.payload?.action}).`
        );
      }
    };

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.addEventListener('message', handleSWMessage);
    }

    return () => {
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.removeEventListener('message', handleSWMessage);
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }
    };
  }, []);

  // --- MANEJADORES DE NOTIFICACIONES PUSH ---
  const handleRequestPushPermission = async () => {
    setSubscribing(true);
    addLog(
      'Push',
      'info',
      'Solicitando permiso de Notificaciones Push...',
      'Invocando Notification.requestPermission() y registrando PushManager.'
    );
    try {
      const result = await requestAndSubscribePush();
      setNotifPermission(result.permission);
      setSubscription(result.subscription);

      if (result.permission === 'granted') {
        addLog('Push', 'success', 'Permiso Push Concedido (granted)', result.message);
      } else if (result.permission === 'denied') {
        addLog('Push', 'error', 'Permiso Push Denegado (denied)', result.message);
      } else {
        addLog('Push', 'warning', `Estado de Permiso: ${result.permission}`, result.message);
      }
    } finally {
      setSubscribing(false);
    }
  };

  const handleUnsubscribePush = async () => {
    await unsubscribePush();
    setSubscription(null);
    addLog(
      'Push',
      'warning',
      'Suscripción Push Cancelada',
      'Se eliminó la suscripción activa del PushManager local.'
    );
  };

  const handleSendTestPush = async (overrideTitle?: string, overrideBody?: string) => {
    setSendingPush(true);
    const titleToUse = overrideTitle || customTitle;
    const bodyToUse = overrideBody || customBody;

    try {
      const res = await sendPushNotification({
        title: titleToUse,
        body: bodyToUse,
      });

      if (res.sent) {
        addLog(
          'Push',
          'success',
          `Notificación enviada (${res.method})`,
          `Título: "${titleToUse}" — Cuerpo: "${bodyToUse}"`
        );
      } else {
        addLog(
          'Push',
          'error',
          'Envío de Notificación Bloqueado',
          res.reason || 'No se pudo mostrar la notificación por falta de permisos.'
        );
      }
    } finally {
      setSendingPush(false);
    }
  };

  // --- MANEJADORES DE GEOLOCALIZACIÓN ---
  const handleGetLocation = async () => {
    setLoadingGeo(true);
    setGeoError(null);
    addLog(
      'Geolocalización',
      'info',
      'Solicitando coordenadas del dispositivo...',
      'Invocando navigator.geolocation.getCurrentPosition()'
    );

    const res = await requestDeviceLocation();
    const updatedPerm = await queryGeolocationPermission();
    setGeoPermission(res.permissionState === 'denied' ? 'denied' : updatedPerm);
    setLoadingGeo(false);

    if (res.success && res.location) {
      onLocationUpdate(res.location);
      addLog(
        'Geolocalización',
        'success',
        'Ubicación obtenida exitosamente (granted)',
        `${res.location.zoneLabel} | Precisión: ±${res.location.accuracy}m`
      );
    } else {
      setGeoError(res.errorMessage || 'Error al obtener ubicación.');
      addLog(
        'Geolocalización',
        res.permissionState === 'denied' ? 'error' : 'warning',
        res.permissionState === 'denied'
          ? 'Permiso de Ubicación Denegado (denied)'
          : 'Aviso al consultar Geolocalización',
        res.errorMessage || 'No fue posible obtener la ubicación.'
      );
    }
  };

  // --- MANEJADORES DE CÁMARA ---
  const handleStartCamera = async () => {
    setLoadingCam(true);
    setCamError(null);
    addLog(
      'Cámara',
      'info',
      'Solicitando acceso a cámara de video...',
      'Invocando navigator.mediaDevices.getUserMedia({ video: true })'
    );

    if (!('mediaDevices' in navigator) || !('getUserMedia' in navigator.mediaDevices)) {
      const msg = 'La API MediaDevices.getUserMedia no está disponible en este navegador.';
      setCamError(msg);
      setCamPermission('unsupported');
      setLoadingCam(false);
      addLog('Cámara', 'error', 'API de Cámara no soportada', msg);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 360 } },
        audio: false,
      });
      streamRef.current = stream;
      setCameraActive(true);
      setCamPermission('granted');

      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          void videoRef.current.play();
        }
      }, 50);

      addLog(
        'Cámara',
        'success',
        'Permiso de Cámara Concedido (granted)',
        `Stream activo: ${stream.getVideoTracks()[0]?.label || 'Cámara integrada'}`
      );
    } catch (err) {
      const errorObj = err as DOMException;
      if (errorObj.name === 'NotAllowedError' || errorObj.name === 'PermissionDeniedError') {
        const deniedMsg =
          'Permiso de Cámara DENEGADO por el usuario (NotAllowedError). La captura de evidencia visual se ha deshabilitado de forma segura.';
        setCamPermission('denied');
        setCamError(deniedMsg);
        addLog('Cámara', 'error', 'Permiso de Cámara Denegado (denied)', deniedMsg);
      } else if (errorObj.name === 'NotFoundError') {
        const notFoundMsg =
          'No se detectó ninguna cámara física conectada al dispositivo (NotFoundError).';
        setCamError(notFoundMsg);
        addLog('Cámara', 'warning', 'Dispositivo de cámara no encontrado', notFoundMsg);
      } else {
        const genericMsg = `No se pudo iniciar la cámara (${errorObj.name || 'Error'}): ${errorObj.message || ''}`;
        setCamError(genericMsg);
        addLog('Cámara', 'warning', 'Error al acceder a cámara', genericMsg);
      }
    } finally {
      setLoadingCam(false);
    }
  };

  const handleStopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setCameraActive(false);
    addLog('Cámara', 'info', 'Cámara detenida', 'Se liberaron los recursos de hardware de video.');
  };

  const handleCapturePhoto = () => {
    if (!videoRef.current) return;
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth || 640;
    canvas.height = videoRef.current.videoHeight || 360;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    // Estampar marca de agua de auditoría del moderador
    ctx.fillStyle = 'rgba(15, 23, 42, 0.78)';
    ctx.fillRect(0, canvas.height - 44, canvas.width, 44);
    ctx.fillStyle = '#34d399';
    ctx.font = 'bold 13px sans-serif';
    ctx.fillText(
      `✓ Evidencia Moderador PWA - ${new Date().toLocaleString()}`,
      12,
      canvas.height - 24
    );
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '11px sans-serif';
    ctx.fillText(
      moderatorLocation
        ? `Ubicación: ${moderatorLocation.zoneLabel} (±${moderatorLocation.accuracy}m)`
        : 'Ubicación: Sin sello GPS activo',
      12,
      canvas.height - 8
    );

    const dataUrl = canvas.toDataURL('image/png');
    setCapturedPhoto(dataUrl);
    addLog(
      'Cámara',
      'success',
      'Fotograma de evidencia capturado',
      'Imagen generada en Canvas local con marca de tiempo de auditoría.'
    );
  };

  // --- SIMULADOR DE ESCENARIOS DE PERMISOS (PUNTO 4) ---
  const handleSimulateDeniedBehavior = (feature: 'Push' | 'Geolocalización' | 'Cámara') => {
    if (feature === 'Push') {
      addLog(
        'Push',
        'error',
        '[Verificación Punto 4] Simulación: Permiso Push Denegado (denied)',
        'Cuando Notification.permission === "denied", el navegador bloquea PushManager.subscribe() y showNotification(). La PWA muestra un aviso no intrusivo en interfaz.'
      );
    } else if (feature === 'Geolocalización') {
      setGeoError(
        '[Simulación de Prueba] Permiso DENEGADO (Código 1: PERMISSION_DENIED). La PWA desactiva el sello GPS y permite seguir moderando normalmente sin bloquear la interfaz.'
      );
      addLog(
        'Geolocalización',
        'error',
        '[Verificación Punto 4] Simulación: Ubicación Denegada (PERMISSION_DENIED)',
        'El callback de error recibe GeolocationPositionError (code: 1) y la PWA degrada elegantemente la función.'
      );
    } else {
      setCamError(
        '[Simulación de Prueba] Permiso DENEGADO (DOMException: NotAllowedError). La PWA informa que se requiere permiso de cámara sin interrumpir la aplicación.'
      );
      addLog(
        'Cámara',
        'error',
        '[Verificación Punto 4] Simulación: Cámara Denegada (NotAllowedError)',
        'getUserMedia rechaza la promesa con NotAllowedError y la interfaz informa al usuario cómo habilitarlo.'
      );
    }
  };

  const renderPermissionBadge = (state: PermissionStatusType) => {
    if (state === 'granted') {
      return (
        <span className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 text-[11px] px-2.5 py-0.5 rounded-full font-bold flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3" />
          Concedido (granted)
        </span>
      );
    }
    if (state === 'denied') {
      return (
        <span className="bg-rose-500/15 text-rose-400 border border-rose-500/30 text-[11px] px-2.5 py-0.5 rounded-full font-bold flex items-center gap-1">
          <AlertOctagon className="w-3 h-3" />
          Denegado (denied)
        </span>
      );
    }
    if (state === 'unsupported') {
      return (
        <span className="bg-slate-700/40 text-slate-400 border border-slate-600/40 text-[11px] px-2.5 py-0.5 rounded-full font-bold">
          No Soportado
        </span>
      );
    }
    return (
      <span className="bg-amber-500/15 text-amber-300 border border-amber-500/30 text-[11px] px-2.5 py-0.5 rounded-full font-bold flex items-center gap-1">
        <Clock className="w-3 h-3" />
        Por solicitar ({state})
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* CABECERA Y EXPLICACIÓN DEL FLUJO DE SUSCRIPCIÓN (PUNTO 1 DE LA PRÁCTICA) */}
      <div className="glass-panel rounded-2xl p-6 border border-indigo-500/30 shadow-lg space-y-5">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 text-xs font-bold mb-2">
              <Smartphone className="w-3.5 h-3.5" />
              Práctica 2.1: Notificaciones Push y Características Nativas
            </div>
            <h2 className="text-xl font-extrabold text-slate-100">
              Centro de Permisos, Notificaciones Push y Hardware del Dispositivo
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Gestiona la suscripción Push del Service Worker y el acceso con permisos a Geolocalización y Cámara para auditoría de moderación.
            </p>
          </div>

          <div className="flex flex-wrap gap-2">
            <div className="bg-slate-950/80 border border-slate-800 px-3 py-2 rounded-xl text-xs">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Push API</span>
              {renderPermissionBadge(notifPermission)}
            </div>
            <div className="bg-slate-950/80 border border-slate-800 px-3 py-2 rounded-xl text-xs">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Ubicación</span>
              {renderPermissionBadge(geoPermission)}
            </div>
            <div className="bg-slate-950/80 border border-slate-800 px-3 py-2 rounded-xl text-xs">
              <span className="text-slate-400 block text-[10px] uppercase font-bold">Cámara</span>
              {renderPermissionBadge(camPermission)}
            </div>
          </div>
        </div>

        {/* Diagrama interactivo del Flujo de Suscripción Push (Punto 1) */}
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-4 space-y-3">
          <h3 className="text-xs font-extrabold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
            <Info className="w-4 h-4 text-indigo-400" />
            1. Flujo de Suscripción y Funcionamiento de Notificaciones Push en una PWA
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div
              className={`p-3 rounded-xl border transition-all ${
                notifPermission === 'granted'
                  ? 'bg-emerald-950/20 border-emerald-500/40'
                  : 'bg-slate-900/60 border-slate-800'
              }`}
            >
              <div className="font-bold text-slate-200 mb-1 flex items-center justify-between">
                <span>Paso 1: Permiso</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300">
                  Notification API
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                La PWA invoca <code className="text-indigo-300">Notification.requestPermission()</code>. El usuario decide entre conceder (<code className="text-emerald-400">granted</code>) o bloquear (<code className="text-rose-400">denied</code>).
              </p>
            </div>

            <div
              className={`p-3 rounded-xl border transition-all ${
                subscription
                  ? 'bg-emerald-950/20 border-emerald-500/40'
                  : 'bg-slate-900/60 border-slate-800'
              }`}
            >
              <div className="font-bold text-slate-200 mb-1 flex items-center justify-between">
                <span>Paso 2: Suscripción</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300">
                  PushManager
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                El Service Worker activo llama a <code className="text-indigo-300">pushManager.subscribe()</code> con una clave pública <strong>VAPID</strong> y obtiene un <code className="text-cyan-300">endpoint</code> y llaves de cifrado.
              </p>
            </div>

            <div className="p-3 rounded-xl border bg-slate-900/60 border-slate-800">
              <div className="font-bold text-slate-200 mb-1 flex items-center justify-between">
                <span>Paso 3: Disparo Push</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300">
                  Web Push / SW
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                El servidor o la PWA envía la carga útil (payload JSON) al Service Worker, despertándolo incluso si la pestaña está en segundo plano.
              </p>
            </div>

            <div className="p-3 rounded-xl border bg-slate-900/60 border-slate-800">
              <div className="font-bold text-slate-200 mb-1 flex items-center justify-between">
                <span>Paso 4: Visualización</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-indigo-300">
                  push-sw.js
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                El evento <code className="text-indigo-300">push</code> ejecuta <code className="text-emerald-300">registration.showNotification()</code> y <code className="text-indigo-300">notificationclick</code> enfoca la ventana al hacer clic.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* GRID PRINCIPAL: PUSH NOTIFICATIONS + CARACTERÍSTICAS NATIVAS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* COLUMNA IZQUIERDA: PASO 2 - NOTIFICACIONES PUSH */}
        <div className="glass-panel rounded-2xl p-6 space-y-5 shadow-md flex flex-col justify-between">
          <div className="space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2.5 rounded-xl bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
                  <Bell className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-100 text-base">
                    2. Notificaciones Push y Suscripción
                  </h3>
                  <p className="text-xs text-slate-400">
                    Solicitud de permiso al usuario y envío de alertas mediante Service Worker
                  </p>
                </div>
              </div>
              {renderPermissionBadge(notifPermission)}
            </div>

            {/* Botones de Permiso y Suscripción */}
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={handleRequestPushPermission}
                  disabled={subscribing}
                  className="flex-1 py-2.5 px-4 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 transition-all shadow-md glow-indigo disabled:opacity-50"
                >
                  <Key className={`w-4 h-4 ${subscribing ? 'animate-spin' : ''}`} />
                  {notifPermission === 'granted' && subscription
                    ? 'Actualizar Suscripción Push'
                    : 'Solicitar Permiso y Suscribir Push'}
                </button>

                {subscription && (
                  <button
                    onClick={handleUnsubscribePush}
                    className="py-2.5 px-3 bg-slate-900 hover:bg-rose-950/60 text-slate-300 hover:text-rose-300 border border-slate-800 hover:border-rose-500/40 text-xs font-bold rounded-xl flex items-center gap-1.5 transition-all"
                    title="Cancelar suscripción actual"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    Desuscribir
                  </button>
                )}
              </div>

              {/* Aviso cuando el permiso está denegado */}
              {notifPermission === 'denied' && (
                <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-200 space-y-1">
                  <div className="font-bold flex items-center gap-1.5 text-rose-400">
                    <AlertOctagon className="w-4 h-4" />
                    Permiso de Notificaciones Denegado (denied)
                  </div>
                  <p className="text-[11px] text-rose-200/90 leading-relaxed">
                    El usuario bloqueó las notificaciones. El navegador impide mostrar nuevos cuadros de diálogo automáticamente. Para volver a concederlo, haz clic en el icono de configuración/candado junto a la URL del navegador y cambia <strong>Notificaciones</strong> a <em>Permitir</em> o <em>Preguntar</em>.
                  </p>
                </div>
              )}

              {/* Datos de la suscripción generada */}
              {subscription && (
                <div className="p-3.5 rounded-xl bg-slate-950/80 border border-emerald-500/30 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[11px] font-bold text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Suscripción Push Activa ({subscription.mode === 'real-vapid' ? 'VAPID PushManager' : 'Service Worker Local'})
                    </span>
                    <span className="text-[10px] text-slate-500">
                      {new Date(subscription.createdAt).toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-slate-400 bg-slate-900/90 p-2.5 rounded-lg border border-slate-800 overflow-x-auto space-y-1">
                    <div>
                      <span className="text-indigo-400 font-bold">endpoint:</span>{' '}
                      {subscription.endpoint}
                    </div>
                    <div>
                      <span className="text-cyan-400 font-bold">keys.p256dh:</span>{' '}
                      {subscription.keys.p256dh.slice(0, 38)}...
                    </div>
                    <div>
                      <span className="text-emerald-400 font-bold">keys.auth:</span>{' '}
                      {subscription.keys.auth}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Formulario para enviar notificación push de prueba */}
            <div className="space-y-3 pt-3 border-t border-slate-800/80">
              <span className="text-xs font-bold text-slate-300 block">
                Enviar Notificación Push de Prueba (vía Service Worker)
              </span>

              <div className="space-y-2">
                <input
                  type="text"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  placeholder="Título de la notificación..."
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
                <textarea
                  rows={2}
                  value={customBody}
                  onChange={(e) => setCustomBody(e.target.value)}
                  placeholder="Mensaje de la notificación..."
                  className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              {/* Plantillas rápidas */}
              <div className="flex flex-wrap gap-1.5">
                <button
                  type="button"
                  onClick={() => {
                    const t = '🚨 Alerta de Spam Detectado';
                    const b = 'El motor de IA bloqueó 3 publicaciones con enlaces maliciosos en Reddit.';
                    setCustomTitle(t);
                    setCustomBody(b);
                    void handleSendTestPush(t, b);
                  }}
                  className="text-[10px] px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold transition-colors"
                >
                  🚨 Probar Alerta Spam
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const t = '✨ Síntesis de Tendencias Lista';
                    const b = 'Se han generado 3 nuevas oportunidades comerciales listas para marketing.';
                    setCustomTitle(t);
                    setCustomBody(b);
                    void handleSendTestPush(t, b);
                  }}
                  className="text-[10px] px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 font-semibold transition-colors"
                >
                  ✨ Probar Alerta Tendencias
                </button>
              </div>

              <button
                onClick={() => void handleSendTestPush()}
                disabled={sendingPush}
                className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 transition-all shadow-md glow-emerald disabled:opacity-50"
              >
                <Send className="w-3.5 h-3.5" />
                Enviar Notificación Push de Prueba Ahora
              </button>
            </div>
          </div>
        </div>

        {/* COLUMNA DERECHA: PASO 3 - ACCESO A CARACTERÍSTICAS NATIVAS DEL DISPOSITIVO */}
        <div className="space-y-6">
          {/* CARACTERÍSTICA NATIVA 1: GEOLOCALIZACIÓN */}
          <div className="glass-panel rounded-2xl p-6 space-y-4 shadow-md">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2.5 rounded-xl bg-cyan-600/20 text-cyan-400 border border-cyan-500/30">
                  <MapPin className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-100 text-base">
                    3A. Geolocalización del Moderador (GPS / Red)
                  </h3>
                  <p className="text-xs text-slate-400">
                    Registra la ubicación desde donde se auditan y aprueban las publicaciones
                  </p>
                </div>
              </div>
              {renderPermissionBadge(geoPermission)}
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => void handleGetLocation()}
                disabled={loadingGeo}
                className="flex-1 py-2.5 px-4 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 transition-all shadow-md disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingGeo ? 'animate-spin' : ''}`} />
                {loadingGeo ? 'Obteniendo coordenadas...' : 'Obtener Ubicación del Dispositivo'}
              </button>

              {moderatorLocation && (
                <button
                  onClick={() => {
                    onLocationUpdate(null);
                    addLog(
                      'Geolocalización',
                      'info',
                      'Ubicación limpiada',
                      'Se borraron las coordenadas almacenadas en la sesión actual.'
                    );
                  }}
                  className="py-2.5 px-3 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 text-xs font-bold rounded-xl"
                >
                  Limpiar
                </button>
              )}
            </div>

            {geoError && (
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-200 flex items-start gap-2">
                <AlertOctagon className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-rose-400 block">
                    Acceso a Ubicación no disponible o denegado:
                  </span>
                  <span>{geoError}</span>
                </div>
              </div>
            )}

            {moderatorLocation && (
              <div className="p-4 rounded-xl bg-slate-950/80 border border-cyan-500/30 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-cyan-400">
                    {moderatorLocation.zoneLabel}
                  </span>
                  <span className="text-[10px] text-slate-400">
                    Hora: {moderatorLocation.timestamp}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="bg-slate-900/90 p-2 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-500 block uppercase font-bold">
                      Latitud
                    </span>
                    <span className="text-xs font-mono font-bold text-slate-200">
                      {moderatorLocation.latitude.toFixed(5)}
                    </span>
                  </div>
                  <div className="bg-slate-900/90 p-2 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-500 block uppercase font-bold">
                      Longitud
                    </span>
                    <span className="text-xs font-mono font-bold text-slate-200">
                      {moderatorLocation.longitude.toFixed(5)}
                    </span>
                  </div>
                  <div className="bg-slate-900/90 p-2 rounded-lg border border-slate-800">
                    <span className="text-[10px] text-slate-500 block uppercase font-bold">
                      Precisión
                    </span>
                    <span className="text-xs font-mono font-bold text-emerald-400">
                      ±{moderatorLocation.accuracy} m
                    </span>
                  </div>
                </div>

                <div className="flex justify-between items-center pt-1">
                  <span className="text-[11px] text-slate-400">
                    ✓ Activo como sello de auditoría en Moderación Manual
                  </span>
                  <a
                    href={`https://www.openstreetmap.org/?mlat=${moderatorLocation.latitude}&mlon=${moderatorLocation.longitude}#map=15/${moderatorLocation.latitude}/${moderatorLocation.longitude}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-[11px] text-cyan-400 hover:text-cyan-300 font-bold flex items-center gap-1"
                  >
                    Ver en Mapa
                    <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            )}
          </div>

          {/* CARACTERÍSTICA NATIVA 2: CÁMARA DEL DISPOSITIVO */}
          <div className="glass-panel rounded-2xl p-6 space-y-4 shadow-md">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2.5 rounded-xl bg-emerald-600/20 text-emerald-400 border border-emerald-500/30">
                  <Camera className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-extrabold text-slate-100 text-base">
                    3B. Cámara del Dispositivo (MediaDevices API)
                  </h3>
                  <p className="text-xs text-slate-400">
                    Captura de evidencia visual o verificación de turno del moderador
                  </p>
                </div>
              </div>
              {renderPermissionBadge(camPermission)}
            </div>

            <div className="flex flex-wrap gap-2">
              {!cameraActive ? (
                <button
                  onClick={() => void handleStartCamera()}
                  disabled={loadingCam}
                  className="flex-1 py-2.5 px-4 bg-slate-900 hover:bg-slate-800 border border-emerald-500/40 text-emerald-300 text-xs font-bold rounded-xl flex items-center justify-center gap-2 transition-all"
                >
                  <Video className="w-4 h-4" />
                  {loadingCam ? 'Solicitando permiso de cámara...' : 'Activar Cámara con Permiso'}
                </button>
              ) : (
                <>
                  <button
                    onClick={handleCapturePhoto}
                    className="flex-1 py-2.5 px-4 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 transition-all"
                  >
                    <Camera className="w-4 h-4" />
                    Capturar Fotograma de Evidencia
                  </button>
                  <button
                    onClick={handleStopCamera}
                    className="py-2.5 px-4 bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30 text-xs font-bold rounded-xl flex items-center gap-1.5 transition-all"
                  >
                    <VideoOff className="w-4 h-4" />
                    Detener
                  </button>
                </>
              )}
            </div>

            {camError && (
              <div className="p-3 rounded-xl bg-rose-950/40 border border-rose-500/40 text-xs text-rose-200 flex items-start gap-2">
                <AlertOctagon className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-rose-400 block">Estado de Cámara:</span>
                  <span>{camError}</span>
                </div>
              </div>
            )}

            {cameraActive && (
              <div className="rounded-xl overflow-hidden border border-emerald-500/40 bg-black relative">
                <video
                  ref={videoRef}
                  playsInline
                  muted
                  className="w-full h-48 object-cover"
                />
                <div className="absolute top-2 left-2 bg-slate-950/80 border border-emerald-500/40 px-2 py-0.5 rounded text-[10px] text-emerald-400 font-bold flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                  CÁMARA EN VIVO
                </div>
              </div>
            )}

            {capturedPhoto && (
              <div className="space-y-2 bg-slate-950/70 p-3 rounded-xl border border-slate-800">
                <div className="flex justify-between items-center">
                  <span className="text-xs font-bold text-emerald-400">
                    Evidencia Capturada con Sello de Auditoría
                  </span>
                  <button
                    onClick={() => setCapturedPhoto(null)}
                    className="text-[10px] text-slate-400 hover:text-rose-400 font-bold"
                  >
                    Descartar captura
                  </button>
                </div>
                <img
                  src={capturedPhoto}
                  alt="Captura de evidencia"
                  className="w-full h-44 object-cover rounded-lg border border-slate-700"
                />
              </div>
            )}
          </div>
        </div>
      </div>

      {/* SECCIÓN 4: VERIFICACIÓN DE COMPORTAMIENTO (CONCEDIDO VS DENEGADO) Y BITÁCORA */}
      <div className="glass-panel rounded-2xl p-6 space-y-5 shadow-md">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-800/80 pb-3">
          <div>
            <h3 className="font-extrabold text-slate-100 text-base">
              4. Verificación del Comportamiento ante Permisos Concedidos o Denegados
            </h3>
            <p className="text-xs text-slate-400">
              Bitácora en tiempo real y simulador de respuesta de la PWA frente a las decisiones del usuario
            </p>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => handleSimulateDeniedBehavior('Push')}
              className="text-[11px] px-2.5 py-1.5 rounded-lg bg-rose-950/50 hover:bg-rose-900/60 border border-rose-500/30 text-rose-300 font-bold transition-all"
            >
              Simular Push Denegado
            </button>
            <button
              onClick={() => handleSimulateDeniedBehavior('Geolocalización')}
              className="text-[11px] px-2.5 py-1.5 rounded-lg bg-rose-950/50 hover:bg-rose-900/60 border border-rose-500/30 text-rose-300 font-bold transition-all"
            >
              Simular GPS Denegado
            </button>
            <button
              onClick={() => handleSimulateDeniedBehavior('Cámara')}
              className="text-[11px] px-2.5 py-1.5 rounded-lg bg-rose-950/50 hover:bg-rose-900/60 border border-rose-500/30 text-rose-300 font-bold transition-all"
            >
              Simular Cámara Denegada
            </button>
          </div>
        </div>

        {/* Tabla comparativa de comportamiento */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-4 rounded-xl bg-emerald-950/15 border border-emerald-500/30 space-y-2">
            <div className="font-bold text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              Cuando el usuario CONCEDE el permiso (granted)
            </div>
            <ul className="space-y-1.5 text-slate-300 text-[11px] list-disc list-inside leading-relaxed">
              <li>
                <strong>Notificaciones Push:</strong> Se registra la suscripción en{' '}
                <code className="text-emerald-300">PushManager</code> y el Service Worker muestra notificaciones nativas del sistema operativo (incluso al extraer o moderar lotes).
              </li>
              <li>
                <strong>Geolocalización:</strong> Se obtienen coordenadas exactas (latitud, longitud y precisión en metros) y se adjuntan como sello de auditoría al moderar publicaciones.
              </li>
              <li>
                <strong>Cámara:</strong> Se inicializa el <code className="text-emerald-300">MediaStream</code> en vivo y permite capturar evidencia con marca de agua.
              </li>
            </ul>
          </div>

          <div className="p-4 rounded-xl bg-rose-950/15 border border-rose-500/30 space-y-2">
            <div className="font-bold text-rose-400 flex items-center gap-1.5">
              <AlertOctagon className="w-4 h-4" />
              Cuando el usuario NIEGA el permiso (denied)
            </div>
            <ul className="space-y-1.5 text-slate-300 text-[11px] list-disc list-inside leading-relaxed">
              <li>
                <strong>Degradación elegante (Graceful Degradation):</strong> La PWA nunca se bloquea ni lanza errores no controlados; el resto del sistema de moderación sigue 100% operativo.
              </li>
              <li>
                <strong>No intrusividad:</strong> Se evita volver a spamear el prompt nativo bloqueado y se muestra una alerta informativa explicando cómo restablecer el permiso en el navegador.
              </li>
              <li>
                <strong>Captura de códigos de error estándar:</strong> Se manejan explícitamente <code className="text-rose-300">PERMISSION_DENIED (1)</code> en Geolocalización y <code className="text-rose-300">NotAllowedError</code> en Cámara.
              </li>
            </ul>
          </div>
        </div>

        {/* Bitácora en vivo */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Bitácora de Eventos de Permisos en Tiempo Real ({logs.length})
            </span>
            <button
              onClick={() => setLogs([])}
              className="text-[11px] text-slate-500 hover:text-slate-300 font-semibold"
            >
              Limpiar bitácora
            </button>
          </div>

          <div className="bg-slate-950/90 border border-slate-800 rounded-xl p-3 max-h-56 overflow-y-auto space-y-2">
            {logs.map((entry) => (
              <div
                key={entry.id}
                className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800/80 flex items-start justify-between gap-3 text-xs"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${
                        entry.status === 'success'
                          ? 'bg-emerald-500/20 text-emerald-400'
                          : entry.status === 'error'
                            ? 'bg-rose-500/20 text-rose-400'
                            : entry.status === 'warning'
                              ? 'bg-amber-500/20 text-amber-300'
                              : 'bg-indigo-500/20 text-indigo-300'
                      }`}
                    >
                      {entry.feature}
                    </span>
                    <span className="font-bold text-slate-200">{entry.title}</span>
                  </div>
                  <p className="text-[11px] text-slate-400">{entry.detail}</p>
                </div>
                <span className="text-[10px] font-mono text-slate-500 flex-shrink-0">
                  {entry.timestamp}
                </span>
              </div>
            ))}
            {logs.length === 0 && (
              <p className="text-xs text-slate-500 text-center py-4">
                Interactúa con los botones de arriba para registrar eventos de permisos y notificaciones.
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
