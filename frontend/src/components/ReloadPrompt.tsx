import { useRegisterSW } from 'virtual:pwa-register/react'

export function ReloadPrompt() {
  const {
    offlineReady: [offlineReady, setOfflineReady],
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW({
    onRegistered(r) {
      console.log('PWA Service Worker registrado correctamente:', r)
    },
    onRegisterError(error) {
      console.error('Error al registrar PWA Service Worker:', error)
    },
  })

  const close = () => {
    setOfflineReady(false)
    setNeedRefresh(false)
  }

  if (!offlineReady && !needRefresh) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 p-4 bg-slate-900 text-white rounded-xl shadow-2xl border border-slate-700 max-w-sm transition-all duration-300">
      <div className="flex items-start gap-3">
        <div className="flex-1 text-sm">
          {offlineReady ? (
            <p className="font-medium text-emerald-400">
              ✓ Aplicación lista para usarse sin conexión.
            </p>
          ) : (
            <p className="font-medium text-slate-200">
              Nueva versión disponible. ¿Deseas actualizar ahora?
            </p>
          )}
        </div>
      </div>
      <div className="flex justify-end gap-2 mt-3">
        {needRefresh && (
          <button
            type="button"
            className="px-3 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 active:scale-95 rounded-lg text-white transition-colors"
            onClick={() => {
              void updateServiceWorker(true)
            }}
          >
            Actualizar
          </button>
        )}
        <button
          type="button"
          className="px-3 py-1.5 text-xs font-medium border border-slate-600 hover:bg-slate-800 rounded-lg text-slate-300 transition-colors"
          onClick={close}
        >
          Cerrar
        </button>
      </div>
    </div>
  )
}
