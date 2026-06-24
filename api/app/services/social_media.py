import logging
import httpx
from datetime import datetime

logger = logging.getLogger("app")

MOCK_POSTS = [
    {
        "id_externo": "mock_reddit_1",
        "texto": "He estado probando el nuevo modelo de DeepSeek en mis proyectos de FastAPI y la velocidad de respuesta es impresionante. Definitivamente es una gran alternativa para tareas de procesamiento de lenguaje natural.",
        "autor": "dev_juan",
        "fecha_creacion": "2026-06-09T18:00:00Z",
        "red_social": "Reddit"
    },
    {
        "id_externo": "mock_reddit_2",
        "texto": "OFERTA INCREÍBLE!!! Compra seguidores reales para Instagram y TikTok en nuestra web www.seguidoresfacil.com por solo $5 dólares! No pierdas esta oportunidad única de crecer en redes sociales rápido!",
        "autor": "spam_bot99",
        "fecha_creacion": "2026-06-09T18:15:00Z",
        "red_social": "Reddit"
    },
    {
        "id_externo": "mock_reddit_3",
        "texto": "Creo que el trabajo híbrido está aquí para quedarse. La productividad aumenta cuando tienes la flexibilidad de trabajar desde casa algunos días de la semana y colaborar en equipo.",
        "autor": "work_forward",
        "fecha_creacion": "2026-06-09T18:30:00Z",
        "red_social": "Reddit"
    },
    {
        "id_externo": "mock_reddit_4",
        "texto": "Eres un completo idiota si piensas que los lenguajes dinámicos son mejores que los tipados. Deberías retirarte de la programación, inútil de m...",
        "autor": "hater_programmer",
        "fecha_creacion": "2026-06-09T18:45:00Z",
        "red_social": "Reddit"
    },
    {
        "id_externo": "mock_reddit_5",
        "texto": "La ciberseguridad es el reto más grande de esta década. Los ataques de ransomware a infraestructura crítica demuestran que las empresas deben invertir mucho más en proteger sus datos.",
        "autor": "sec_analyst",
        "fecha_creacion": "2026-06-09T19:00:00Z",
        "red_social": "Reddit"
    }
]


class SocialMediaConnector:
    """
    Conector para extraer posts de redes sociales.
    Implementa conexión real a la API pública de Reddit (subreddits de tendencias)
    y fallback robusto a datos simulados realistas en caso de fallas de red.
    """

    def __init__(self, user_agent: str = "ModeracionApp/1.0 (by /u/dev_team)"):
        self.headers = {"User-Agent": user_agent}

    async def obtener_posts_tendencia(self, limit: int = 5) -> list[dict]:
        """
        Extrae los posts en tendencia de Reddit de forma asíncrona.
        En caso de error o límite de tasa de la API, recurre a datos mockeados realistas.
        """
        url = "https://www.reddit.com/r/technology/hot.json"
        params = {"limit": limit}

        try:
            logger.info(f"Intentando conectar con la API de Reddit: {url}")
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, headers=self.headers, params=params)

                if response.status_code == 200:
                    datos = response.json()
                    posts_procesados = []

                    children = datos.get("data", {}).get("children", [])
                    for child in children:
                        post_data = child.get("data", {})
                        # Combinar título y contenido del post
                        titulo = post_data.get("title", "")
                        contenido = post_data.get("selftext", "")
                        texto_completo = f"{titulo}. {contenido}".strip()

                        # Convertir timestamp UTC a ISO formato string
                        created_utc = post_data.get("created_utc")
                        fecha = datetime.fromtimestamp(created_utc).isoformat() + "Z" if created_utc else datetime.now().isoformat() + "Z"

                        posts_procesados.append({
                            "id_externo": f"reddit_{post_data.get('id')}",
                            "texto": texto_completo,
                            "autor": post_data.get("author", "desconocido"),
                            "fecha_creacion": fecha,
                            "red_social": "Reddit"
                        })
                    logger.info(f"Se extrajeron {len(posts_procesados)} posts reales con éxito de Reddit.")
                    return posts_procesados[:limit]
                else:
                    logger.warning(
                        f"La API de Reddit respondió con código {response.status_code}. Intentando Dev.to..."
                    )
        except Exception as e:
            logger.error(f"Error al conectar con la API de Reddit: {str(e)}. Intentando Dev.to...")

        # Fallback 1: Intentar Dev.to (Artículos tech frescos y muy descriptivos)
        try:
            logger.info("Intentando conectar con la API de Dev.to para artículos tech frescos...")
            async with httpx.AsyncClient(timeout=5.0) as client:
                dev_res = await client.get("https://dev.to/api/articles", params={"per_page": limit})
                if dev_res.status_code == 200:
                    articulos = dev_res.json()
                    posts_procesados = []
                    for art in articulos:
                        title = art.get("title", "")
                        description = art.get("description", "")
                        texto_completo = f"{title}. {description}".strip()
                        
                        published_at = art.get("published_at")
                        fecha = published_at if published_at else datetime.now().isoformat() + "Z"
                        
                        posts_procesados.append({
                            "id_externo": f"devto_{art.get('id')}",
                            "texto": texto_completo,
                            "autor": art.get("user", {}).get("username", "desconocido"),
                            "fecha_creacion": fecha,
                            "red_social": "Dev.to"
                        })
                    if posts_procesados:
                        logger.info(f"Se extrajeron {len(posts_procesados)} posts reales de Dev.to.")
                        return posts_procesados[:limit]
                else:
                    logger.warning(
                        f"La API de Dev.to respondió con código {dev_res.status_code}. Intentando Hacker News..."
                    )
        except Exception as dev_err:
            logger.error(f"Error al conectar con la API de Dev.to: {str(dev_err)}. Intentando Hacker News...")

        # Fallback 2: Intentar Hacker News (API 100% pública que no bloquea ni requiere API Key)
        try:
            logger.info("Intentando conectar con la API de Hacker News como alternativa real...")
            async with httpx.AsyncClient(timeout=5.0) as client:
                hn_res = await client.get("https://hacker-news.firebaseio.com/v0/topstories.json")
                if hn_res.status_code == 200:
                    story_ids = hn_res.json()[:limit]
                    posts_procesados = []
                    for s_id in story_ids:
                        item_res = await client.get(f"https://hacker-news.firebaseio.com/v0/item/{s_id}.json")
                        if item_res.status_code == 200:
                            item = item_res.json()
                            titulo = item.get("title", "")
                            texto = item.get("text", "")
                            texto_completo = f"{titulo}. {texto}" if texto else titulo
                            
                            created_time = item.get("time")
                            fecha = datetime.fromtimestamp(created_time).isoformat() + "Z" if created_time else datetime.now().isoformat() + "Z"
                            
                            posts_procesados.append({
                                "id_externo": f"hn_{item.get('id')}",
                                "texto": texto_completo.strip(),
                                "autor": item.get("by", "desconocido"),
                                "fecha_creacion": fecha,
                                "red_social": "HackerNews"
                            })
                    if posts_procesados:
                        logger.info(f"Se extrajeron {len(posts_procesados)} posts reales de Hacker News.")
                        return posts_procesados
        except Exception as hn_err:
            logger.error(f"Error al conectar con la API de Hacker News: {str(hn_err)}. Usando mock fallback.")

        # Fallback 2: Cargar datos locales simulados (en caso de que falle todo lo anterior o no haya internet)
        logger.info(f"Cargando {min(limit, len(MOCK_POSTS))} posts del simulador de tendencias.")
        return MOCK_POSTS[:limit]
