// Client API para conectarse al backend de FastAPI y proveer datos en Modo Demo

const BASE_URL = 'http://localhost:8000/api/v1';

let demoMode = true; // Por defecto inicia en Modo Demo para asegurar visualización inicial vistosa

export function isDemoMode(): boolean {
  return demoMode;
}

export function setDemoMode(enabled: boolean): void {
  demoMode = enabled;
  console.log(`[API] Modo Demo: ${demoMode ? 'ACTIVADO' : 'DESACTIVADO'}`);
}

// --- BASE DE DATOS MOCK LOCAL PARA EL MODO DEMO ---
let mockPosts = [
  {
    id: 1,
    id_externo: "mock_reddit_1",
    texto: "DeepSeek ha cambiado el juego por completo. Ofrece rendimiento similar a GPT-4 a una fracción de su costo. He migrado todas mis herramientas internas a su API y la latencia es increíble.",
    autor: "tech_pioneer",
    fecha_creacion: "2026-06-23T18:00:00Z",
    red_social: "Reddit",
    estado_moderacion: "Aprobado",
    categoria_tendencia: "Inteligencia Artificial",
    justificacion_moderacion: "Aprobado automáticamente. Post de alto valor informativo sobre costos de IA.",
    fecha_extraccion: "2026-06-23T18:05:00Z"
  },
  {
    id: 2,
    id_externo: "mock_reddit_2",
    texto: "La ciberseguridad es el reto más grande de esta década. Los ataques de ransomware a infraestructura crítica demuestran que las empresas deben invertir mucho más en proteger sus datos.",
    autor: "sec_analyst",
    fecha_creacion: "2026-06-23T17:45:00Z",
    red_social: "Reddit",
    estado_moderacion: "Aprobado",
    categoria_tendencia: "Ciberseguridad",
    justificacion_moderacion: "Aprobado. Tema respetuoso sobre concientización de seguridad informática.",
    fecha_extraccion: "2026-06-23T18:05:00Z"
  },
  {
    id: 3,
    id_externo: "mock_hn_1",
    texto: "Show HN: Tailwind CSS v4.0 lanzado oficialmente. Ahora cuenta con un compilador completamente nuevo escrito en Rust. La velocidad de compilación es hasta 10 veces más rápida en proyectos grandes.",
    autor: "adamwathan",
    fecha_creacion: "2026-06-23T16:20:00Z",
    red_social: "Hacker News",
    estado_moderacion: "Aprobado",
    categoria_tendencia: "Desarrollo Frontend",
    justificacion_moderacion: "Aprobado. Lanzamiento de framework tecnológico relevante para desarrolladores.",
    fecha_extraccion: "2026-06-23T18:05:00Z"
  },
  {
    id: 4,
    id_externo: "mock_reddit_3",
    texto: "Eres un completo idiota si piensas que los lenguajes dinámicos son mejores que los tipados. Deberías retirarte de la programación, inútil de m...",
    autor: "hater_programmer",
    fecha_creacion: "2026-06-23T15:30:00Z",
    red_social: "Reddit",
    estado_moderacion: "Malo",
    categoria_tendencia: "General",
    justificacion_moderacion: "Clasificación automática por fallback local (Filtro de ofensas). El post contiene palabras vulgares o insultos agresivos.",
    fecha_extraccion: "2026-06-23T18:05:00Z"
  },
  {
    id: 5,
    id_externo: "mock_reddit_4",
    texto: "!!! GANA DINERO RÁPIDO !!! 500 USD al día sin hacer nada. Solo entra a www.millonariofacil.com y descarga nuestra app 100% real no fake!!",
    autor: "spammer_master",
    fecha_creacion: "2026-06-23T14:15:00Z",
    red_social: "Reddit",
    estado_moderacion: "Malo",
    categoria_tendencia: "Marketing Digital",
    justificacion_moderacion: "Rechazado por IA. Contenido clasificado como Spam comercial abusivo y enlaces sospechosos.",
    fecha_extraccion: "2026-06-23T18:05:00Z"
  },
  {
    id: 6,
    id_externo: "mock_reddit_5",
    texto: "El trabajo híbrido no es solo una moda, es el futuro. Permite a las personas balancear su vida y reduce la huella de carbono al evitar el tráfico diario. Las oficinas deben convertirse en centros de colaboración, no cárceles.",
    autor: "hr_innovator",
    fecha_creacion: "2026-06-23T13:00:00Z",
    red_social: "Reddit",
    estado_moderacion: "Aprobado",
    categoria_tendencia: "Trabajo Remoto",
    justificacion_moderacion: "Aprobado. Post analítico sobre recursos humanos y bienestar.",
    fecha_extraccion: "2026-06-23T18:05:00Z"
  },
  {
    id: 7,
    id_externo: "mock_reddit_6",
    texto: "Estamos buscando programador frontend con conocimientos en React, TypeScript y Tailwind v4. Ofrecemos trabajo 100% remoto, excelentes beneficios y un equipo genial. Interesados enviar DM.",
    autor: "startup_founder",
    fecha_creacion: "2026-06-23T12:30:00Z",
    red_social: "Reddit",
    estado_moderacion: "Aprobado",
    categoria_tendencia: "Empleo / Tech",
    justificacion_moderacion: "Aprobado. Oferta de empleo respetuosa y valiosa.",
    fecha_extraccion: "2026-06-23T18:05:00Z"
  },
  {
    id: 8,
    id_externo: "mock_reddit_7",
    texto: "Aprende a programar en 3 semanas y consigue trabajo de 5000 USD al mes garantizado en nuestro bootcamp premium de programación acelerada por IA. Cupos limitados, regístrate ya.",
    autor: "bootcamp_seller",
    fecha_creacion: "2026-06-23T11:45:00Z",
    red_social: "Reddit",
    estado_moderacion: "Malo",
    categoria_tendencia: "Marketing Digital",
    justificacion_moderacion: "Rechazado por IA. Contiene publicidad engañosa y promesas financieras dudosas.",
    fecha_extraccion: "2026-06-23T18:05:00Z"
  }
];

let mockPendientes = [
  {
    id: 101,
    id_externo: "mock_pending_1",
    texto: "La automatización con scripts de Python permite a nuestro equipo de contabilidad ahorrar 15 horas semanales de reportes manuales. Es una inversión de tiempo mínima para un retorno gigante.",
    autor: "python_enthusiast",
    fecha_creacion: "2026-06-23T20:10:00Z",
    red_social: "Reddit",
    estado_moderacion: "Pendiente"
  },
  {
    id: 102,
    id_externo: "mock_pending_2",
    texto: "COMPRA SEGUIDORES DE TIKTOK AHORA MISMO!!! Visita seguidoresrapidos.biz y obtén 10k seguidores al instante por solo $10. Oferta por tiempo limitado.",
    autor: "tiktok_grower",
    fecha_creacion: "2026-06-23T19:50:00Z",
    red_social: "Reddit",
    estado_moderacion: "Pendiente"
  },
  {
    id: 103,
    id_externo: "mock_pending_3",
    texto: "Un estudio sobre micro-animaciones revela que agregar sutiles rebotes y retrasos en los hover de botones incrementa la tasa de clics en formularios un 18%. Los detalles de UX importan.",
    autor: "ux_designer",
    fecha_creacion: "2026-06-23T19:30:00Z",
    red_social: "Reddit",
    estado_moderacion: "Pendiente"
  },
  {
    id: 104,
    id_externo: "mock_pending_4",
    texto: "Ustedes son unos estúpidos ineptos si usan frameworks de CSS. CSS vanilla es el único camino real y todos los demás son mediocres impostores que no saben nada.",
    autor: "css_purist",
    fecha_creacion: "2026-06-23T19:00:00Z",
    red_social: "Reddit",
    estado_moderacion: "Pendiente"
  }
];

let mockTrends = [
  {
    id: 1,
    titulo: "Evolución y Optimización de IA",
    resumen: "Conversación destacada sobre el rendimiento, costos y eficiencia al integrar APIs de inteligencia artificial eficientes como DeepSeek. Los desarrolladores evalúan la latencia y la reducción de costos operativos en sus integraciones.",
    enfoque_comercial: "Las startups de tecnología pueden crear contenidos de tipo tutorial explicando cómo redujeron costos de su API un 80% usando alternativas inteligentes. Esto genera autoridad y atrae leads de software.",
    palabras_clave: ["ia", "deepseek", "tecnologia"],
    fecha_registro: "2026-06-23T22:00:00Z"
  },
  {
    id: 2,
    titulo: "Velocidad de Desarrollo en CSS",
    resumen: "Gran expectación en Hacker News por el lanzamiento oficial de Tailwind CSS v4.0 y su nuevo compilador en Rust, reduciendo tiempos de build y mejorando la productividad del desarrollador frontend.",
    enfoque_comercial: "Empresas SaaS y agencias pueden crear artículos o videos comparativos de velocidad de desarrollo para convencer a clientes corporativos de migrar a arquitecturas web modernas.",
    palabras_clave: ["tailwind", "frontend", "desarrollo"],
    fecha_registro: "2026-06-23T22:00:00Z"
  },
  {
    id: 3,
    titulo: "Zero-Trust ante Ransomware",
    resumen: "Discusiones sobre seguridad informática resaltan la urgencia de fortalecer la protección de datos e infraestructura en la nube empresarial ante la sofisticación de ataques masivos de secuestro de datos.",
    enfoque_comercial: "Proveedores de ciberseguridad pueden ofrecer auditorías de brechas de seguridad gratuitas y checklists para pequeñas empresas.",
    palabras_clave: ["ciberseguridad", "ransomware", "seguridad"],
    fecha_registro: "2026-06-23T22:00:00Z"
  }
];

// --- FUNCIONES AXILIARES DE MOCK ---

function getMockAnalytics() {
  const aprobados = mockPosts.filter(p => p.estado_moderacion === 'Aprobado').length;
  const malos = mockPosts.filter(p => p.estado_moderacion === 'Malo').length;
  const total = aprobados + malos + mockPendientes.length;

  // Contar tendencias reales de mockPosts aprobados
  const countTendencias: Record<string, number> = {};
  mockPosts.forEach(p => {
    if (p.estado_moderacion === 'Aprobado' && p.categoria_tendencia) {
      countTendencias[p.categoria_tendencia] = (countTendencias[p.categoria_tendencia] || 0) + 1;
    }
  });

  const topTendencias = Object.entries(countTendencias)
    .map(([categoria, cantidad]) => ({ categoria, cantidad }))
    .sort((a, b) => b.cantidad - a.cantidad)
    .slice(0, 5);

  return {
    total_posts: total,
    por_estado: {
      Pendiente: mockPendientes.length,
      Aprobado: aprobados,
      Malo: malos
    },
    por_red_social: {
      Reddit: mockPosts.filter(p => p.red_social === 'Reddit').length + mockPendientes.filter(p => p.red_social === 'Reddit').length,
      "Hacker News": mockPosts.filter(p => p.red_social === 'Hacker News').length + mockPendientes.filter(p => p.red_social === 'Hacker News').length
    },
    top_tendencias: topTendencias.length > 0 ? topTendencias : [
      { categoria: "Inteligencia Artificial", cantidad: 3 },
      { categoria: "Ciberseguridad", cantidad: 2 }
    ]
  };
}

// --- CLIENTE API ---

export async function obtenerMetricas(): Promise<any> {
  if (demoMode) {
    return new Promise((resolve) => setTimeout(() => resolve(getMockAnalytics()), 300));
  }
  try {
    const res = await fetch(`${BASE_URL}/posts/analytics`);
    if (!res.ok) throw new Error("Error en respuesta de API");
    return await res.json();
  } catch (e) {
    console.warn("Backend desconectado. Activando fallback de Modo Demo automático.");
    setDemoMode(true);
    return getMockAnalytics();
  }
}

export async function listarPosts(keyword?: string, estado?: string, limit: number = 20, offset: number = 0): Promise<any[]> {
  if (demoMode) {
    return new Promise((resolve) => {
      setTimeout(() => {
        let filtrados = [...mockPosts];
        if (estado) {
          filtrados = filtrados.filter(p => p.estado_moderacion === estado);
        }
        if (keyword && keyword.trim()) {
          const kw = keyword.toLowerCase().trim();
          filtrados = filtrados.filter(p => p.texto.toLowerCase().includes(kw));
        }
        resolve(filtrados.slice(offset, offset + limit));
      }, 300);
    });
  }
  try {
    const params = new URLSearchParams();
    if (keyword) params.append('keyword', keyword);
    if (estado) params.append('estado', estado);
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());

    const res = await fetch(`${BASE_URL}/posts?${params}`);
    if (!res.ok) throw new Error("Error en respuesta de API");
    return await res.json();
  } catch (e) {
    console.warn("Backend desconectado. Activando fallback de Modo Demo automático.");
    setDemoMode(true);
    return listarPosts(keyword, estado, limit, offset);
  }
}

export async function moderarPostUnico(postId: number): Promise<any> {
  if (demoMode) {
    return new Promise((resolve, reject) => {
      setTimeout(() => {
        const postIndex = mockPendientes.findIndex(p => p.id === postId);
        if (postIndex === -1) {
          reject(new Error("Post no encontrado en pendientes"));
          return;
        }

        const post = mockPendientes[postIndex];
        mockPendientes.splice(postIndex, 1); // Remover de pendientes

        // Analizar texto localmente
        const esMalo = post.texto.toLowerCase().includes("compra seguidores") || 
                       post.texto.toLowerCase().includes("estúpidos") ||
                       post.texto.toLowerCase().includes("estúpido") ||
                       post.texto.toLowerCase().includes("ineptos");

        let categoria = "General";
        if (post.texto.toLowerCase().includes("python") || post.texto.toLowerCase().includes("automatización")) {
          categoria = "Automatización / IA";
        } else if (post.texto.toLowerCase().includes("animaciones") || post.texto.toLowerCase().includes("ux")) {
          categoria = "Desarrollo Frontend / UX";
        } else if (post.texto.toLowerCase().includes("seguidores")) {
          categoria = "Marketing Digital";
        }

        const veredicto = {
          id: post.id,
          id_externo: post.id_externo,
          texto: post.texto,
          autor: post.autor,
          fecha_creacion: post.fecha_creacion,
          red_social: post.red_social,
          estado_moderacion: esMalo ? "Malo" : "Aprobado",
          categoria_tendencia: categoria,
          justificacion_moderacion: esMalo 
            ? "Rechazado localmente. Mensaje detectado como insulto o spam publicitario."
            : "Aprobado localmente. Contenido constructivo y apto para marketing.",
          fecha_extraccion: new Date().toISOString()
        };

        mockPosts.unshift(veredicto); // Agregar a la base de moderados
        resolve({
          post_id: postId,
          estado_moderacion: veredicto.estado_moderacion,
          categoria_tendencia: veredicto.categoria_tendencia,
          justificacion: veredicto.justificacion_moderacion,
          historial_id: Math.floor(Math.random() * 1000)
        });
      }, 500);
    });
  }
  try {
    const res = await fetch(`${BASE_URL}/posts/${postId}/moderate`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error("Error en moderación de API");
    return await res.json();
  } catch (e) {
    console.warn("Backend desconectado. Activando fallback de Modo Demo automático.");
    setDemoMode(true);
    return moderarPostUnico(postId);
  }
}

export async function moderarLotePendiente(limit: number = 10): Promise<any> {
  if (demoMode) {
    return new Promise((resolve) => {
      setTimeout(async () => {
        const lote = mockPendientes.slice(0, limit);
        const resultados = [];
        
        for (const p of lote) {
          const res = await moderarPostUnico(p.id);
          resultados.push(res);
        }

        resolve({
          status: "success",
          procesados: lote.length,
          moderados: resultados
        });
      }, 1000);
    });
  }
  try {
    const res = await fetch(`${BASE_URL}/posts/moderate-pending?limit=${limit}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error("Error en moderación en lote de API");
    return await res.json();
  } catch (e) {
    console.warn("Backend desconectado. Activando fallback de Modo Demo automático.");
    setDemoMode(true);
    return moderarLotePendiente(limit);
  }
}

export async function sintetizarTendencias(limit: number = 30): Promise<any[]> {
  if (demoMode) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(mockTrends);
      }, 1200);
    });
  }
  try {
    const res = await fetch(`${BASE_URL}/posts/generate-trends?limit=${limit}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error("Error en síntesis de API");
    return await res.json();
  } catch (e) {
    console.warn("Backend desconectado. Activando fallback de Modo Demo automático.");
    setDemoMode(true);
    return sintetizarTendencias(limit);
  }
}

export async function listarTendencias(limit: number = 10): Promise<any[]> {
  if (demoMode) {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(mockTrends.slice(0, limit));
      }, 300);
    });
  }
  try {
    const res = await fetch(`${BASE_URL}/posts/trends?limit=${limit}`);
    if (!res.ok) throw new Error("Error en respuesta de API");
    return await res.json();
  } catch (e) {
    console.warn("Backend desconectado. Activando fallback de Modo Demo automático.");
    setDemoMode(true);
    return listarTendencias(limit);
  }
}

export async function extraerPostsRedes(limit: number = 10): Promise<any> {
  if (demoMode) {
    return new Promise((resolve) => {
      setTimeout(() => {
        // Generar algunos posts pendientes mock nuevos
        const nuevos = [
          {
            id: mockPendientes.length + 101,
            id_externo: `mock_pending_${Date.now()}`,
            texto: `Post extraído en vivo sobre innovación tecnológica número ${mockPendientes.length + 1}. Es un excelente día para aprender algo nuevo.`,
            autor: "live_surfer",
            fecha_creacion: new Date().toISOString(),
            red_social: Math.random() > 0.5 ? "Reddit" : "Hacker News",
            estado_moderacion: "Pendiente"
          }
        ];
        mockPendientes.push(...nuevos);
        resolve({
          status: "success",
          extraidos: limit,
          nuevos_guardados: nuevos.length
        });
      }, 800);
    });
  }
  try {
    const res = await fetch(`${BASE_URL}/posts/fetch-and-store?limit=${limit}`, {
      method: 'POST'
    });
    if (!res.ok) throw new Error("Error en extracción de API");
    return await res.json();
  } catch (e) {
    console.warn("Backend desconectado. Activando fallback de Modo Demo automático.");
    setDemoMode(true);
    return extraerPostsRedes(limit);
  }
}

// Función auxiliar para simular la carga inicial si queremos rellenar o listar los pendientes en modo demo
export function obtenerPendientesDemo() {
  return [...mockPendientes];
}

export function moderarPostDemoManual(postId: number, estado: 'Aprobado' | 'Malo') {
  const postIndex = mockPendientes.findIndex(p => p.id === postId);
  if (postIndex === -1) return null;
  const post = mockPendientes[postIndex];
  mockPendientes.splice(postIndex, 1);

  const veredicto = {
    id: post.id,
    id_externo: post.id_externo,
    texto: post.texto,
    autor: post.autor,
    fecha_creacion: post.fecha_creacion,
    red_social: post.red_social,
    estado_moderacion: estado,
    categoria_tendencia: estado === 'Aprobado' ? "General" : "Rechazo Manual",
    justificacion_moderacion: estado === 'Aprobado'
      ? "Aprobado manualmente por el moderador."
      : "Rechazado manualmente por el moderador.",
    fecha_extraccion: new Date().toISOString()
  };

  mockPosts.unshift(veredicto);
  return veredicto;
}
