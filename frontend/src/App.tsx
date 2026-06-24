import { useState, useEffect } from 'react';
import { 
  Shield, 
  TrendingUp, 
  BarChart3, 
  CheckCircle2, 
  AlertOctagon, 
  Clock, 
  Search, 
  Copy, 
  Check, 
  Sparkles, 
  Zap, 
  Share2, 
  RefreshCw, 
  PlusCircle, 
  Layers,
  Flame,
  ThumbsUp,
  MessageSquare,
  BookOpen
} from 'lucide-react';
import * as api from './services/api';
import logo from './assets/logo.png';

interface Post {
  id: number;
  id_externo: string;
  texto: string;
  autor: string;
  fecha_creacion: string;
  red_social: string;
  estado_moderacion: string;
  categoria_tendencia?: string;
  justificacion_moderacion?: string;
  fecha_extraccion?: string;
}

interface Trend {
  id: number;
  titulo: string;
  resumen: string;
  enfoque_comercial: string;
  palabras_clave: string[];
  fecha_registro?: string;
}

interface Analytics {
  total_posts: number;
  por_estado: {
    Pendiente: number;
    Aprobado: number;
    Malo: number;
  };
  por_red_social: Record<string, number>;
  top_tendencias: Array<{ categoria: string; cantidad: number }>;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'moderation' | 'analytics' | 'trends'>('dashboard');
  const [demoMode, setDemoModeState] = useState<boolean>(api.isDemoMode());
  
  // Data States
  const [posts, setPosts] = useState<Post[]>([]);
  const [pendingPosts, setPendingPosts] = useState<any[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);

  // Derived state: true pending posts count from database (production) or local pendingPosts (demo)
  const pendingCount = api.isDemoMode()
    ? pendingPosts.length
    : (analytics?.por_estado?.Pendiente ?? pendingPosts.length);

  
  // Control States
  const [searchKeyword, setSearchKeyword] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedSocialNetwork, setSelectedSocialNetwork] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [moderating, setModerating] = useState(false);
  const [synthesizing, setSynthesizing] = useState(false);
  const [copiedPostId, setCopiedPostId] = useState<number | null>(null);

  // Carga inicial y recarga al cambiar modo demo
  const loadData = async () => {
    setLoading(true);
    try {
      const pData = await api.listarPosts();
      setPosts(pData);
      
      const aData = await api.obtenerMetricas();
      setAnalytics(aData);
      
      const tData = await api.listarTendencias();
      setTrends(tData);

      if (api.isDemoMode()) {
        setPendingPosts(api.obtenerPendientesDemo());
      } else {
        // En producción obtenemos posts con estado pendiente de la API de posts
        const res = await api.listarPosts(undefined, 'Pendiente', 50);
        setPendingPosts(res);
      }
    } catch (e) {
      console.error("Error al cargar datos de la API", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [demoMode]);

  // Cambiar modo demo
  const handleToggleDemoMode = (checked: boolean) => {
    api.setDemoMode(checked);
    setDemoModeState(checked);
  };

  // Copiar idea comercial al portapapeles
  const handleCopyText = (text: string, postId: number) => {
    navigator.clipboard.writeText(text);
    setCopiedPostId(postId);
    setTimeout(() => {
      setCopiedPostId(null);
    }, 2000);
  };

  // Extraer más posts de la red social
  const handleExtractPosts = async () => {
    setExtracting(true);
    try {
      await api.extraerPostsRedes(10);
      await loadData();
    } catch (e) {
      alert("Error al extraer posts");
    } finally {
      setExtracting(false);
    }
  };

  // Moderar lote pendiente
  const handleModerateBatch = async () => {
    setModerating(true);
    try {
      await api.moderarLotePendiente(10);
      await loadData();
    } catch (e) {
      alert("Error al moderar lote");
    } finally {
      setModerating(false);
    }
  };

  // Generar tendencias con IA
  const handleGenerateTrends = async () => {
    setSynthesizing(true);
    try {
      await api.sintetizarTendencias(30);
      await loadData();
    } catch (e) {
      alert("Error al generar tendencias. Asegúrate de tener posts 'Aprobados' en el sistema.");
    } finally {
      setSynthesizing(false);
    }
  };

  // Moderar un post de forma unitaria
  const handleModerateSingle = async (postId: number, approved: boolean = true) => {
    try {
      if (api.isDemoMode()) {
        api.moderarPostDemoManual(postId, approved ? 'Aprobado' : 'Malo');
      } else {
        await api.moderarPostUnico(postId);
      }
      await loadData();
    } catch (e) {
      alert("Error al moderar el post");
    }
  };

  // Filtrado de posts aprobados para el feed central
  const filteredApprovedPosts = posts.filter(post => {
    if (post.estado_moderacion !== 'Aprobado') return false;
    if (selectedCategory && post.categoria_tendencia !== selectedCategory) return false;
    if (selectedSocialNetwork && post.red_social !== selectedSocialNetwork) return false;
    if (searchKeyword.trim() !== '') {
      return post.texto.toLowerCase().includes(searchKeyword.toLowerCase());
    }
    return true;
  });

  // Filtrado de posts bloqueados para el feed derecho
  const filteredBlockedPosts = posts.filter(post => post.estado_moderacion === 'Malo');

  return (
    <div className="bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-slate-100 min-h-screen font-sans selection:bg-indigo-500 selection:text-white">
      
      {/* --- HEADER --- */}
      <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-xl border-b border-slate-800/80 px-6 py-3 flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-3">
          <img src={logo} alt="Logo" className="h-9 w-auto object-contain rounded-lg filter drop-shadow-[0_0_8px_rgba(99,102,241,0.5)]" />
          <div>
            <h1 className="font-extrabold text-lg bg-gradient-to-r from-indigo-400 via-cyan-400 to-emerald-400 bg-clip-text text-transparent tracking-tight">
              MODERACIÓN DE CONTENIDO	
            </h1>
            <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Inteligencia Artificial & Moderaión de Contenido</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1 bg-slate-900/50 p-1 border border-slate-800/60 rounded-xl">
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${activeTab === 'dashboard' ? 'bg-indigo-600/90 text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'}`}
          >
            <Layers className="w-4 h-4" />
            Dashboard
          </button>
          <button 
            onClick={() => setActiveTab('moderation')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${activeTab === 'moderation' ? 'bg-indigo-600/90 text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'}`}
          >
            <Shield className="w-4 h-4" />
            Moderación Manual
            {pendingCount > 0 && (
              <span className="bg-rose-500 text-white text-[10px] px-1.5 py-0.5 rounded-full font-bold ml-1 animate-pulse">
                {pendingCount}
              </span>
            )}
          </button>
          <button 
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${activeTab === 'analytics' ? 'bg-indigo-600/90 text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'}`}
          >
            <BarChart3 className="w-4 h-4" />
            Analíticas
          </button>
          <button 
            onClick={() => setActiveTab('trends')}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 ${activeTab === 'trends' ? 'bg-indigo-600/90 text-white shadow-md' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'}`}
          >
            <TrendingUp className="w-4 h-4" />
            Tendencias IA
          </button>
        </nav>

        {/* Demo Mode Toggle */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-slate-900/60 border border-slate-800/80 px-3.5 py-1.5 rounded-xl">
            <span className="text-xs font-semibold text-slate-300">Modo Demo</span>
            <label className="relative inline-flex items-center cursor-pointer">
              <input 
                type="checkbox" 
                checked={demoMode} 
                onChange={(e) => handleToggleDemoMode(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-9 h-5 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-emerald-500"></div>
            </label>
          </div>
          
          <button 
            onClick={loadData}
            disabled={loading}
            className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-slate-200 rounded-xl transition-all disabled:opacity-50"
            title="Recargar datos"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      {/* Mobile Tab Selector */}
      <div className="md:hidden flex bg-slate-950 border-b border-slate-800/60 p-2 overflow-x-auto gap-1">
        <button 
          onClick={() => setActiveTab('dashboard')}
          className={`flex-none px-4 py-1.5 rounded-lg text-xs font-bold ${activeTab === 'dashboard' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
        >
          Dashboard
        </button>
        <button 
          onClick={() => setActiveTab('moderation')}
          className={`flex-none px-4 py-1.5 rounded-lg text-xs font-bold ${activeTab === 'moderation' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
        >
          Moderación ({pendingCount})
        </button>
        <button 
          onClick={() => setActiveTab('analytics')}
          className={`flex-none px-4 py-1.5 rounded-lg text-xs font-bold ${activeTab === 'analytics' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
        >
          Analíticas
        </button>
        <button 
          onClick={() => setActiveTab('trends')}
          className={`flex-none px-4 py-1.5 rounded-lg text-xs font-bold ${activeTab === 'trends' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
        >
          Tendencias
        </button>
      </div>

      {/* --- MAIN BODY CONTAINER --- */}
      <main className="max-w-7xl mx-auto p-4 md:p-6">

        {/* --- MODO DEMO WARNING RIBBON --- */}
        {demoMode && (
          <div className="mb-4 bg-gradient-to-r from-amber-500/20 via-yellow-500/10 to-amber-500/20 border border-amber-500/40 rounded-xl p-3 flex items-center justify-between text-xs text-amber-300 font-medium backdrop-blur-md shadow-md animate-pulse">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-400" />
              <span><strong>Modo Demo Activo:</strong> Estás interactuando con datos de prueba locales. Cambia el selector en la cabecera para conectar a la API real.</span>
            </div>
            <button 
              onClick={() => handleToggleDemoMode(false)}
              className="px-2.5 py-1 bg-amber-500/30 hover:bg-amber-500/50 text-amber-100 rounded-lg border border-amber-400/30 transition-all font-bold"
            >
              Cambiar a Real
            </button>
          </div>
        )}

        {/* --- TAB CONTENT: DASHBOARD (3 COLUMNS) --- */}
        {activeTab === 'dashboard' && (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            
            {/* COLUMN 1: TRENDS & FILTERS */}
            <div className="lg:col-span-1 space-y-5">
              <div className="glass-panel rounded-2xl p-4 shadow-md space-y-4">
                <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <Search className="w-4 h-4 text-indigo-400" />
                  Filtrar Feed
                </h3>
                
                {/* Keyword Search */}
                <div className="relative">
                  <input 
                    type="text" 
                    placeholder="Buscador por palabra..." 
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    className="w-full bg-slate-950/80 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                  <Search className="absolute left-3 top-3 text-slate-500 w-4 h-4" />
                </div>

                {/* Social Network Selector */}
                <div className="space-y-2">
                  <span className="text-xs text-slate-400 font-semibold block">Red Social</span>
                  <div className="grid grid-cols-3 gap-1.5">
                    <button 
                      onClick={() => setSelectedSocialNetwork(null)}
                      className={`text-xs py-1.5 px-2 rounded-lg font-bold border transition-all ${!selectedSocialNetwork ? 'bg-indigo-600/30 border-indigo-500 text-white' : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200'}`}
                    >
                      Todos
                    </button>
                    <button 
                      onClick={() => setSelectedSocialNetwork('Reddit')}
                      className={`text-xs py-1.5 px-2 rounded-lg font-bold border transition-all ${selectedSocialNetwork === 'Reddit' ? 'bg-indigo-600/30 border-indigo-500 text-white' : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200'}`}
                    >
                      Reddit
                    </button>
                    <button 
                      onClick={() => setSelectedSocialNetwork('Hacker News')}
                      className={`text-xs py-1.5 px-2 rounded-lg font-bold border transition-all ${selectedSocialNetwork === 'Hacker News' ? 'bg-indigo-600/30 border-indigo-500 text-white' : 'bg-slate-950/40 border-slate-800 text-slate-400 hover:text-slate-200'}`}
                    >
                      HN
                    </button>
                  </div>
                </div>

                {/* Categories filter */}
                <div className="space-y-2">
                  <span className="text-xs text-slate-400 font-semibold block">Categoría de IA</span>
                  <div className="space-y-1">
                    <button 
                      onClick={() => setSelectedCategory(null)}
                      className={`w-full text-left text-xs px-3 py-2 rounded-xl transition-all font-semibold flex justify-between items-center ${!selectedCategory ? 'bg-indigo-600/20 text-indigo-300 border-l-2 border-indigo-500' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'}`}
                    >
                      <span>Mostrar todas</span>
                    </button>
                    {analytics?.top_tendencias.map((t, idx) => (
                      <button 
                        key={idx}
                        onClick={() => setSelectedCategory(t.categoria)}
                        className={`w-full text-left text-xs px-3 py-2 rounded-xl transition-all font-semibold flex justify-between items-center ${selectedCategory === t.categoria ? 'bg-indigo-600/20 text-indigo-300 border-l-2 border-indigo-500' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'}`}
                      >
                        <span className="truncate max-w-[120px]">{t.categoria}</span>
                        <span className="bg-slate-850 px-1.5 py-0.5 rounded text-[10px] text-slate-400 font-bold">{t.cantidad}</span>
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Trending Topics (AI Synthesized mini-panel) */}
              <div className="glass-panel rounded-2xl p-4 shadow-md space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
                    <Flame className="w-4 h-4 text-orange-500" />
                    Síntesis IA
                  </h3>
                  <button 
                    onClick={() => setActiveTab('trends')}
                    className="text-[10px] text-indigo-400 hover:text-indigo-300 font-bold flex items-center gap-0.5"
                  >
                    Ver más
                  </button>
                </div>
                
                <div className="space-y-3">
                  {trends.slice(0, 3).map((trend, idx) => (
                    <div key={idx} className="p-2.5 bg-slate-950/50 border border-slate-800/40 rounded-xl hover:border-slate-800 transition-colors">
                      <div className="flex items-center gap-1.5 mb-1">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
                        <span className="text-xs font-bold text-slate-200 truncate">{trend.titulo}</span>
                      </div>
                      <p className="text-[10px] text-slate-400 line-clamp-2 leading-relaxed">{trend.resumen}</p>
                    </div>
                  ))}
                  {trends.length === 0 && (
                    <p className="text-xs text-slate-500 text-center py-2">Sin tendencias generadas hoy.</p>
                  )}
                </div>
              </div>
            </div>

            {/* COLUMN 2 & 3: MAIN APP FEED */}
            <div className="lg:col-span-2 space-y-5">
              
              {/* Feed Header Controls */}
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 bg-slate-900/40 border border-slate-800/50 p-3 rounded-2xl">
                <div>
                  <h2 className="font-extrabold text-slate-200 text-base flex items-center gap-2">
                    Feed: Ideas Aprobadas
                    <span className="bg-emerald-500/10 text-emerald-400 text-xs px-2 py-0.5 rounded-full font-bold border border-emerald-500/20">
                      {filteredApprovedPosts.length}
                    </span>
                  </h2>
                  <p className="text-xs text-slate-400">Publicaciones seguras listas para inspiración comercial</p>
                </div>

                <div className="flex gap-2">
                  <button 
                    onClick={handleExtractPosts}
                    disabled={extracting}
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl border border-slate-700 flex items-center gap-1.5 transition-all disabled:opacity-50"
                  >
                    <PlusCircle className={`w-3.5 h-3.5 ${extracting ? 'animate-spin' : ''}`} />
                    Extraer
                  </button>
                  <button 
                    onClick={handleGenerateTrends}
                    disabled={synthesizing}
                    className="px-3 py-1.5 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-bold rounded-xl flex items-center gap-1.5 transition-all shadow-md glow-indigo disabled:opacity-50"
                  >
                    <Sparkles className={`w-3.5 h-3.5 ${synthesizing ? 'animate-spin' : ''}`} />
                    Sintetizar
                  </button>
                </div>
              </div>

              {/* Feed List */}
              <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
                {filteredApprovedPosts.map((post) => (
                  <div 
                    key={post.id} 
                    className="glass-panel border-l-4 border-l-emerald-500 rounded-2xl p-5 relative hover:scale-[1.01] hover:border-slate-700/80 transition-all duration-300 shadow-md hover:shadow-lg glow-emerald"
                  >
                    {/* Top Row info */}
                    <div className="flex justify-between items-center mb-3">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center font-bold text-indigo-400 text-sm border border-slate-700 uppercase">
                          {post.autor.substring(0, 2)}
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-200">@{post.autor}</div>
                          <div className="text-[10px] text-slate-400 flex items-center gap-1">
                            <span>{post.red_social}</span>
                            <span>•</span>
                            <Clock className="w-2.5 h-2.5" />
                            <span>{new Date(post.fecha_creacion).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>

                      {/* Tag Category */}
                      {post.categoria_tendencia && (
                        <span className="bg-indigo-500/10 text-indigo-300 text-[10px] px-2.5 py-1 rounded-full font-bold border border-indigo-500/20">
                          {post.categoria_tendencia}
                        </span>
                      )}
                    </div>

                    {/* Post Content */}
                    <p className="text-slate-300 text-sm leading-relaxed mb-4 whitespace-pre-line">
                      {post.texto}
                    </p>

                    {/* Footer Actions */}
                    <div className="border-t border-slate-800/60 pt-3 flex justify-between items-center">
                      <div className="flex gap-4 text-slate-500 text-[10px]">
                        <span className="flex items-center gap-1"><ThumbsUp className="w-3.5 h-3.5" /> Likes</span>
                        <span className="flex items-center gap-1"><MessageSquare className="w-3.5 h-3.5" /> Comentarios</span>
                      </div>

                      {/* Copy Action */}
                      <button 
                        onClick={() => handleCopyText(post.texto, post.id)}
                        className={`text-xs font-bold px-3 py-1.5 rounded-xl border flex items-center gap-1.5 transition-all relative ${copiedPostId === post.id ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-400' : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:text-white hover:border-slate-700'}`}
                      >
                        {copiedPostId === post.id ? (
                          <>
                            <Check className="w-3.5 h-3.5" />
                            Copiado
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            Copiar Idea
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                ))}

                {filteredApprovedPosts.length === 0 && (
                  <div className="glass-panel p-12 text-center rounded-2xl flex flex-col items-center justify-center">
                    <BookOpen className="w-12 h-12 text-slate-600 mb-3" />
                    <h3 className="font-bold text-slate-400 mb-1">Sin Posts Aprobados</h3>
                    <p className="text-xs text-slate-500 max-w-sm">No se encontraron publicaciones aprobadas que cumplan con los filtros de búsqueda establecidos en el panel izquierdo.</p>
                  </div>
                )}
              </div>
            </div>

            {/* COLUMN 4: CONTROL PANEL & REJECTED */}
            <div className="lg:col-span-1 space-y-5">
              
              {/* Stats KPI Panel */}
              <div className="glass-panel rounded-2xl p-4 shadow-md space-y-4">
                <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-indigo-400" />
                  Métricas de Moderación
                </h3>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-950/50 border border-slate-850 p-3 rounded-xl">
                    <span className="text-[10px] text-slate-500 font-bold block uppercase">Extraídos</span>
                    <span className="text-xl font-extrabold text-slate-200">{analytics?.total_posts || 0}</span>
                  </div>
                  <div className="bg-slate-950/50 border border-slate-850 p-3 rounded-xl">
                    <span className="text-[10px] text-slate-500 font-bold block uppercase">Aprobados</span>
                    <span className="text-xl font-extrabold text-emerald-400">{analytics?.por_estado.Aprobado || 0}</span>
                  </div>
                  <div className="bg-slate-950/50 border border-slate-850 p-3 rounded-xl">
                    <span className="text-[10px] text-slate-500 font-bold block uppercase">Spam Bloqueado</span>
                    <span className="text-xl font-extrabold text-rose-500">{analytics?.por_estado.Malo || 0}</span>
                  </div>
                  <div className="bg-slate-950/50 border border-slate-850 p-3 rounded-xl">
                    <span className="text-[10px] text-slate-500 font-bold block uppercase">Pendientes</span>
                    <span className="text-xl font-extrabold text-amber-500">{pendingCount}</span>
                  </div>
                </div>

                {/* Progress bar state */}
                {analytics && (
                  <div className="space-y-1.5 pt-2 border-t border-slate-800/40">
                    <div className="flex justify-between text-xs text-slate-400">
                      <span>Tasa de Aprobación</span>
                      <span className="font-bold text-slate-200">
                        {analytics.total_posts > 0 
                          ? Math.round((analytics.por_estado.Aprobado / (analytics.por_estado.Aprobado + analytics.por_estado.Malo || 1)) * 100) 
                          : 0}%
                      </span>
                    </div>
                    <div className="h-2 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-850">
                      <div 
                        className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500" 
                        style={{ width: `${analytics.total_posts > 0 ? (analytics.por_estado.Aprobado / (analytics.por_estado.Aprobado + analytics.por_estado.Malo || 1)) * 100 : 0}%` }}
                      ></div>
                    </div>
                  </div>
                )}
              </div>

              {/* Action Buttons Panel */}
              <div className="glass-panel rounded-2xl p-4 shadow-md space-y-3">
                <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <Zap className="w-4 h-4 text-indigo-400" />
                  Operaciones IA
                </h3>

                <button 
                  onClick={handleModerateBatch}
                  disabled={moderating || pendingCount === 0}
                  className="w-full py-2.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-2 transition-all shadow-md glow-indigo disabled:opacity-50"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${moderating ? 'animate-spin' : ''}`} />
                  Moderar Lote ({pendingCount})
                </button>
                <button 
                  onClick={handleExtractPosts}
                  disabled={extracting}
                  className="w-full py-2.5 bg-slate-950 hover:bg-slate-900 border border-slate-800 text-slate-200 text-xs font-bold rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-50"
                >
                  <PlusCircle className={`w-3.5 h-3.5 ${extracting ? 'animate-spin' : ''}`} />
                  Extraer Lote de Redes
                </button>
              </div>

              {/* Flagged / Blocked Posts column */}
              <div className="glass-panel rounded-2xl p-4 shadow-md space-y-4">
                <h3 className="font-bold text-sm text-rose-400 uppercase tracking-wider flex items-center gap-2">
                  <AlertOctagon className="w-4 h-4 text-rose-500" />
                  Bandeja de Bloqueados ({filteredBlockedPosts.length})
                </h3>

                <div className="space-y-3 max-h-[30vh] overflow-y-auto pr-1">
                  {filteredBlockedPosts.map((post) => (
                    <div key={post.id} className="p-3 bg-slate-950/60 border border-rose-950/30 rounded-xl glow-rose hover:border-rose-900/60 transition-colors">
                      <div className="flex justify-between items-center mb-1.5">
                        <span className="text-xs font-bold text-slate-300">@{post.autor}</span>
                        <span className="text-[9px] bg-rose-500/10 text-rose-400 border border-rose-500/20 px-1.5 py-0.5 rounded-full font-extrabold uppercase">
                          Spam / Malo
                        </span>
                      </div>
                      <p className="text-[10px] text-slate-400 line-clamp-2 leading-relaxed mb-2">"{post.texto}"</p>
                      <div className="bg-slate-900/60 border border-slate-850 p-2 rounded-lg text-[9px] text-rose-300/80 leading-relaxed font-semibold">
                        <strong>Motivo:</strong> {post.justificacion_moderacion}
                      </div>
                    </div>
                  ))}

                  {filteredBlockedPosts.length === 0 && (
                    <p className="text-xs text-slate-500 text-center py-4">Bandeja limpia de spam.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* --- TAB CONTENT: MANUAL MODERATION --- */}
        {activeTab === 'moderation' && (
          <div className="space-y-6">
            <div className="bg-slate-900/40 border border-slate-800/50 p-4 rounded-2xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div>
                <h2 className="font-extrabold text-slate-200 text-lg flex items-center gap-2">
                  Moderación Manual
                  <span className="bg-amber-500/10 text-amber-400 text-xs px-2.5 py-0.5 rounded-full font-bold border border-amber-500/20">
                    {pendingCount} pendientes
                  </span>
                </h2>
                <p className="text-xs text-slate-400">Analiza individualmente las publicaciones antes de que se aprueben para el feed general</p>
              </div>

              <button 
                onClick={handleModerateBatch}
                disabled={moderating || pendingCount === 0}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl flex items-center gap-2 transition-all shadow-md disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${moderating ? 'animate-spin' : ''}`} />
                Automoderar lote
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {pendingPosts.map((post) => (
                <div key={post.id} className="glass-panel p-5 rounded-2xl border border-slate-800 shadow-md space-y-4 flex flex-col justify-between hover:border-slate-700 transition-colors">
                  <div>
                    <div className="flex justify-between items-center mb-3">
                      <span className="text-xs font-bold text-slate-200">@{post.autor}</span>
                      <span className="text-[10px] bg-slate-950 px-2 py-1 rounded border border-slate-850 text-slate-400 font-bold">
                        {post.red_social}
                      </span>
                    </div>
                    <p className="text-slate-350 text-sm leading-relaxed">"{post.texto}"</p>
                  </div>

                  <div className="pt-4 border-t border-slate-800/60 flex flex-col sm:flex-row gap-2">
                    <button 
                      onClick={() => handleModerateSingle(post.id, true)}
                      className="flex-1 py-2 bg-emerald-600/20 hover:bg-emerald-600 text-emerald-300 hover:text-white border border-emerald-500/30 hover:border-emerald-500 text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 transition-all shadow-sm"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                      Aprobar
                    </button>
                    <button 
                      onClick={() => handleModerateSingle(post.id, false)}
                      className="flex-1 py-2 bg-rose-600/20 hover:bg-rose-600 text-rose-300 hover:text-white border border-rose-500/30 hover:border-rose-500 text-xs font-bold rounded-xl flex items-center justify-center gap-1.5 transition-all shadow-sm"
                    >
                      <AlertOctagon className="w-4 h-4" />
                      Rechazar
                    </button>
                  </div>
                </div>
              ))}

              {pendingPosts.length === 0 && (
                <div className="col-span-2 glass-panel p-16 text-center rounded-2xl flex flex-col items-center justify-center">
                  <CheckCircle2 className="w-12 h-12 text-emerald-500 mb-3" />
                  <h3 className="font-bold text-slate-300 mb-1">¡Todo Moderado!</h3>
                  <p className="text-xs text-slate-500 max-w-sm">No existen posts pendientes de moderar en la base de datos. Utiliza el botón de extraer posts en el Dashboard para obtener más contenido.</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* --- TAB CONTENT: DETAILED ANALYTICS --- */}
        {activeTab === 'analytics' && (
          <div className="space-y-6">
            <h2 className="font-extrabold text-slate-200 text-lg">Reportes Estadísticos Detallados</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* KPI Total Posts */}
              <div className="glass-panel p-5 rounded-2xl flex items-center justify-between shadow-md">
                <div>
                  <span className="text-xs text-slate-400 font-bold block uppercase tracking-wider">Posts Extraídos</span>
                  <span className="text-3xl font-extrabold text-slate-200 mt-1 block">{analytics?.total_posts || 0}</span>
                </div>
                <div className="p-3 bg-indigo-600/20 rounded-2xl text-indigo-400">
                  <Layers className="w-6 h-6" />
                </div>
              </div>

              {/* KPI Aprobados */}
              <div className="glass-panel p-5 rounded-2xl flex items-center justify-between shadow-md">
                <div>
                  <span className="text-xs text-slate-400 font-bold block uppercase tracking-wider">Posts Aprobados</span>
                  <span className="text-3xl font-extrabold text-emerald-400 mt-1 block">{analytics?.por_estado.Aprobado || 0}</span>
                </div>
                <div className="p-3 bg-emerald-600/20 rounded-2xl text-emerald-400">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
              </div>

              {/* KPI Rechazados */}
              <div className="glass-panel p-5 rounded-2xl flex items-center justify-between shadow-md">
                <div>
                  <span className="text-xs text-slate-400 font-bold block uppercase tracking-wider">Spam Bloqueado</span>
                  <span className="text-3xl font-extrabold text-rose-500 mt-1 block">{analytics?.por_estado.Malo || 0}</span>
                </div>
                <div className="p-3 bg-rose-600/20 rounded-2xl text-rose-400">
                  <AlertOctagon className="w-6 h-6" />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              {/* Distribution by Social Network */}
              <div className="glass-panel p-6 rounded-2xl shadow-md space-y-4">
                <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <Share2 className="w-4 h-4 text-indigo-400" />
                  Distribución por Red Social
                </h3>
                
                {analytics && (
                  <div className="space-y-4">
                    {Object.entries(analytics.por_red_social).map(([red, cant]) => {
                      const porc = analytics.total_posts > 0 ? Math.round((cant / analytics.total_posts) * 100) : 0;
                      return (
                        <div key={red} className="space-y-1.5">
                          <div className="flex justify-between text-xs font-semibold">
                            <span className="text-slate-200">{red}</span>
                            <span className="text-slate-400">{cant} posts ({porc}%)</span>
                          </div>
                          <div className="h-3 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-850">
                            <div 
                              className={`h-full rounded-full transition-all duration-500 ${red === 'Reddit' ? 'bg-orange-500' : 'bg-cyan-500'}`}
                              style={{ width: `${porc}%` }}
                            ></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Distribution by Status */}
              <div className="glass-panel p-6 rounded-2xl shadow-md space-y-4">
                <h3 className="font-bold text-sm text-slate-300 uppercase tracking-wider flex items-center gap-2">
                  <Shield className="w-4 h-4 text-indigo-400" />
                  Estados de Moderación
                </h3>
                
                {analytics && (
                  <div className="space-y-4">
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-emerald-400">Aprobados</span>
                        <span className="text-slate-400">{analytics.por_estado.Aprobado}</span>
                      </div>
                      <div className="h-3 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-850">
                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${analytics.total_posts > 0 ? (analytics.por_estado.Aprobado / analytics.total_posts) * 100 : 0}%` }}></div>
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-rose-500">Rechazados (Spam)</span>
                        <span className="text-slate-400">{analytics.por_estado.Malo}</span>
                      </div>
                      <div className="h-3 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-850">
                        <div className="h-full bg-rose-500 rounded-full" style={{ width: `${analytics.total_posts > 0 ? (analytics.por_estado.Malo / analytics.total_posts) * 100 : 0}%` }}></div>
                      </div>
                    </div>
                    <div className="space-y-1.5">
                      <div className="flex justify-between text-xs font-semibold">
                        <span className="text-amber-500">Pendientes</span>
                        <span className="text-slate-400">{pendingCount}</span>
                      </div>
                      <div className="h-3 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-850">
                        <div className="h-full bg-amber-500 rounded-full" style={{ width: `${analytics.total_posts > 0 ? (pendingCount / analytics.total_posts) * 100 : 0}%` }}></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* --- TAB CONTENT: AI TRENDS DETAIL --- */}
        {activeTab === 'trends' && (
          <div className="space-y-6">
            <div className="bg-slate-900/40 border border-slate-800/50 p-4 rounded-2xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
              <div>
                <h2 className="font-extrabold text-slate-200 text-lg flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  Síntesis de Tendencias de Mercado (IA)
                </h2>
                <p className="text-xs text-slate-400">Análisis semántico consolidado de la conversación diaria agrupado por temas de interés comercial</p>
              </div>

              <button 
                onClick={handleGenerateTrends}
                disabled={synthesizing}
                className="px-4 py-2 bg-gradient-to-r from-indigo-600 via-violet-600 to-indigo-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold rounded-xl flex items-center gap-2 transition-all shadow-md glow-indigo disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${synthesizing ? 'animate-spin' : ''}`} />
                Actualizar Síntesis
              </button>
            </div>

            <div className="space-y-6">
              {trends.map((trend) => (
                <div key={trend.id} className="glass-panel p-6 rounded-2xl border border-slate-800 shadow-md space-y-4 hover:border-slate-700 transition-colors">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-extrabold text-slate-100 text-base flex items-center gap-2">
                        <Flame className="w-5 h-5 text-orange-500" />
                        {trend.titulo}
                      </h3>
                      {trend.fecha_registro && (
                        <span className="text-[10px] text-slate-500">Registrado el {new Date(trend.fecha_registro).toLocaleString()}</span>
                      )}
                    </div>

                    <div className="flex gap-1">
                      {trend.palabras_clave.map((kw, idx) => (
                        <span key={idx} className="bg-slate-950 text-slate-400 text-[9px] px-2 py-0.5 rounded border border-slate-850 font-bold uppercase">
                          #{kw}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                    <div className="space-y-2">
                      <span className="text-xs text-slate-400 font-bold block uppercase tracking-wider">Resumen de la Conversación</span>
                      <p className="text-slate-300 text-sm leading-relaxed bg-slate-950/40 p-4 rounded-xl border border-slate-850/50">
                        {trend.resumen}
                      </p>
                    </div>

                    <div className="space-y-2">
                      <span className="text-xs text-indigo-400 font-bold block uppercase tracking-wider flex items-center gap-1">
                        <Zap className="w-3.5 h-3.5 text-indigo-400" />
                        Enfoque y Propuesta Comercial (Marketing)
                      </span>
                      <p className="text-slate-300 text-sm leading-relaxed bg-indigo-950/15 p-4 rounded-xl border border-indigo-900/25">
                        {trend.enfoque_comercial}
                      </p>
                    </div>
                  </div>
                </div>
              ))}

              {trends.length === 0 && (
                <div className="glass-panel p-16 text-center rounded-2xl flex flex-col items-center justify-center">
                  <Sparkles className="w-12 h-12 text-indigo-400 mb-3 animate-pulse" />
                  <h3 className="font-bold text-slate-300 mb-1">Sin Tendencias Generadas</h3>
                  <p className="text-xs text-slate-500 max-w-sm">Haz clic en "Actualizar Síntesis" en la esquina superior para analizar los posts aprobados e identificar las tendencias de marketing.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
