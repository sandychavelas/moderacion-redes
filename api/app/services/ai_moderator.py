import logging
import httpx
import json
from app.core.settings import settings

logger = logging.getLogger("app")


class AIModeratorService:
    """
    Servicio de moderación de contenido e identificación de tendencias utilizando la IA DeepSeek.
    Incluye un clasificador inteligente por reglas de fallback para cuando no hay conexión
    o no se ha configurado la API Key.
    """

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_base = settings.DEEPSEEK_API_BASE
        # Usamos el modelo chat de DeepSeek por defecto
        self.model = "deepseek-chat"

    async def moderar_post(self, texto: str) -> dict:
        """
        Envía un post a DeepSeek para clasificarlo como 'Aprobado' o 'Malo'
        y extraer tendencias relevantes en formato JSON.
        """
        if not texto or not texto.strip():
            return {
                "clasificacion": "Malo",
                "categoria_tendencia": "Ninguna",
                "palabras_clave": [],
                "justificacion": "El post está vacío."
            }

        # Si no hay API Key configurada, ir directamente a fallback local para ahorrar tiempo y evitar errores
        if not self.api_key:
            logger.info("DeepSeek API Key no encontrada. Usando analizador de respaldo local.")
            return self._analisis_local_fallback(texto, "API Key ausente")

        url = f"{self.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        # Prompt del sistema para forzar la estructura de salida y criterios de decisión
        system_prompt = (
            "Eres un moderador experto de redes sociales y analista de tendencias para negocios.\n"
            "Tu tarea es analizar el texto de un post y determinar si es apto para inspirar ideas comerciales.\n"
            "Modéralo y clasifícalo en una de estas categorías:\n"
            "- 'Aprobado': Apto para el público, no contiene insultos, spam, profanidades ni desprecio.\n"
            "- 'Malo': Contiene spam, ofertas dudosas, insultos, contenido inapropiado o irrelevante.\n\n"
            "Además, extrae la categoría/tendencia general del post (ej. Tecnología, Estilo de vida, Empleo, "
            "Finanzas, Ciberseguridad, etc.) y un máximo de 3 palabras clave en minúsculas.\n\n"
            "Debes responder estrictamente con un JSON que tenga esta estructura:\n"
            "{\n"
            "  \"clasificacion\": \"Aprobado\" o \"Malo\",\n"
            "  \"categoria_tendencia\": \"Categoría\",\n"
            "  \"palabras_clave\": [\"palabra1\", \"palabra2\", \"palabra3\"],\n"
            "  \"justificacion\": \"Una justificación breve en español\"\n"
            "}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analiza este post:\n\"\"\"\n{texto}\n\"\"\""}
            ],
            "temperature": 0.1,
            # Asegura que responda en formato JSON
            "response_format": {"type": "json_object"}
        }

        try:
            logger.info("Enviando petición a la API de DeepSeek...")
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=headers, json=payload)

                if response.status_code == 200:
                    resultado = response.json()
                    contenido_json = resultado["choices"][0]["message"]["content"]
                    logger.info("Respuesta de DeepSeek recibida correctamente.")
                    return json.loads(contenido_json)
                else:
                    logger.warning(
                        f"La API de DeepSeek devolvió código {response.status_code}. Detalle: {response.text}. "
                        f"Usando fallback local."
                    )
        except Exception as e:
            logger.error(f"Error al conectar con la API de DeepSeek: {str(e)}. Usando fallback local.")

        return self._analisis_local_fallback(texto, "Error en llamada API")

    def _analisis_local_fallback(self, texto: str, motivo: str) -> dict:
        """
        Algoritmo heurístico de respaldo (fallback) que analiza localmente palabras clave
        para clasificar el post sin necesidad de realizar solicitudes externas.
        """
        texto_lc = texto.lower()

        # Palabras comunes de spam o insultos
        palabras_malo = [
            "compra seguidores", "seguidoresfacil", "idiota", "estúpido", "imbécil",
            "inútil", "inutil", "spam", "grosería", "vulgar", "oferta única",
            "gana dinero rápido", "hazte rico"
        ]

        es_malo = any(palabra in texto_lc for palabra in palabras_malo)

        # Inferir categoría básica de tendencia basándonos en palabras clave del texto
        categoria = "General"
        palabras_clave = []

        if "deepseek" in texto_lc or "ia" in texto_lc or "ai" in texto_lc or "inteligencia artificial" in texto_lc:
            categoria = "Tecnología / IA"
            palabras_clave.append("ia")
            if "deepseek" in texto_lc:
                palabras_clave.append("deepseek")
        elif "ciberseguridad" in texto_lc or "ransomware" in texto_lc or "seguridad" in texto_lc:
            categoria = "Ciberseguridad"
            palabras_clave.append("seguridad")
            if "ransomware" in texto_lc:
                palabras_clave.append("ransomware")
        elif "híbrido" in texto_lc or "trabajo" in texto_lc or "flexibilidad" in texto_lc:
            categoria = "Entorno Laboral"
            palabras_clave.append("trabajo")
            if "híbrido" in texto_lc:
                palabras_clave.append("hibrido")
        elif "seguidores" in texto_lc or "instagram" in texto_lc or "tiktok" in texto_lc:
            categoria = "Marketing Digital"
            palabras_clave.append("spam")
            palabras_clave.append("seguidores")

        # Rellenar palabras clave si quedaron vacías
        if not palabras_clave:
            palabras_clave = [palabra[:15] for palabra in texto_lc.split()[:2] if len(palabra) > 3]

        clasificacion = "Malo" if es_malo else "Aprobado"
        justificacion = (
            f"Clasificación automática por fallback local ({motivo}). "
            f"El post {'contiene palabras inapropiadas o publicitarias' if es_malo else 'es respetuoso y apto para negocios'}."
        )

        return {
            "clasificacion": clasificacion,
            "categoria_tendencia": categoria,
            "palabras_clave": palabras_clave[:3],
            "justificacion": justificacion
        }

    async def sintetizar_tendencias_del_dia(self, posts_textos: list[str]) -> list[dict]:
        """
        Analiza un lote de textos de posts aprobados y genera las 3 tendencias principales
        del día con enfoque comercial en formato JSON.
        """
        if not posts_textos:
            return []

        if not self.api_key:
            logger.info("DeepSeek API Key no encontrada para análisis de tendencias. Usando fallback local.")
            return self._sintetizar_local_fallback(posts_textos, "API Key ausente")

        url = f"{self.api_base}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        system_prompt = (
            "Eres un experto analista de marketing digital y tendencias comerciales.\n"
            "Recibirás una lista de posts aprobados de redes sociales.\n"
            "Tu tarea es analizar y agrupar estos posts para identificar las 3 tendencias del día más importantes.\n"
            "Para cada tendencia, proporciona:\n"
            "- \"titulo\": Un título representativo corto (ej. 'Revolución de la IA', 'Ciberseguridad en Pymes').\n"
            "- \"resumen\": Una descripción de de qué trata la tendencia según los posts.\n"
            "- \"enfoque_comercial\": Explicación de por qué una marca o negocio debe publicar sobre esto "
            "y qué ideas de contenido pueden generar (ángulos de marketing).\n"
            "- \"palabras_clave\": 3 palabras clave o hashtags en minúsculas.\n\n"
            "Debes responder estrictamente con un JSON que tenga esta estructura:\n"
            "{\n"
            "  \"trends\": [\n"
            "    {\n"
            "      \"titulo\": \"Título de la tendencia\",\n"
            "      \"resumen\": \"Resumen...\",\n"
            "      \"enfoque_comercial\": \"Enfoque comercial...\",\n"
            "      \"palabras_clave\": [\"tag1\", \"tag2\", \"tag3\"]\n"
            "    }\n"
            "  ]\n"
            "}"
        )

        posts_combina = "\n---\n".join([f"- {texto}" for texto in posts_textos])
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Aquí están los posts aprobados del día:\n\n{posts_combina}"}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }

        try:
            logger.info("Enviando lote de posts a DeepSeek para sintetizar tendencias...")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    resultado = response.json()
                    contenido_json = resultado["choices"][0]["message"]["content"]
                    logger.info("Tendencias sintetizadas por DeepSeek recibidas correctamente.")
                    datos = json.loads(contenido_json)
                    return datos.get("trends", [])
                else:
                    logger.warning(
                        f"La API de DeepSeek devolvió código {response.status_code} al generar tendencias. "
                        f"Usando fallback local."
                    )
        except Exception as e:
            logger.error(f"Error al conectar con DeepSeek para tendencias: {str(e)}. Usando fallback local.")

        return self._sintetizar_local_fallback(posts_textos, "Error en llamada API")

    def _sintetizar_local_fallback(self, posts_textos: list[str], motivo: str) -> list[dict]:
        """
        Genera tendencias simuladas coherentes basadas en el contenido real de los posts provistos.
        """
        texto_unido = " ".join(posts_textos).lower()
        trends = []

        # Tendencia 1: Inteligencia Artificial (si se mencionan temas de IA)
        if any(w in texto_unido for w in ["ia", "ai", "deepseek", "inteligencia", "nlp"]):
            trends.append({
                "titulo": "Adopción de Modelos de IA",
                "resumen": f"Creciente interés de los desarrolladores y empresas por integrar modelos de IA eficientes como DeepSeek en entornos de desarrollo asíncronos (FastAPI/Python) para optimizar costos y tiempos de respuesta. ({motivo})",
                "enfoque_comercial": "Las marcas tecnológicas pueden publicar tutoriales de optimización con IA y compartir casos de uso de automatización para posicionarse como líderes de innovación.",
                "palabras_clave": ["ia", "deepseek", "desarrollo"]
            })

        # Tendencia 2: Ciberseguridad (si se menciona ransomware, seguridad, ataques)
        if any(w in texto_unido for w in ["seguridad", "ciberseguridad", "ransomware", "ataque"]):
            trends.append({
                "titulo": "Ciberseguridad de Infraestructura",
                "resumen": f"El ransomware y los ataques a infraestructuras críticas obligan a las empresas a replantear sus presupuestos e inversiones en protección de datos y políticas de seguridad digital. ({motivo})",
                "enfoque_comercial": "Empresas de TI o consultorías pueden crear guías de prevención de ransomware y listas de verificación rápidas de seguridad para atraer prospectos B2B.",
                "palabras_clave": ["ciberseguridad", "ransomware", "prevencion"]
            })

        # Tendencia 3: Trabajo Híbrido (si se menciona trabajo, híbrido, remoto, flexibilidad)
        if any(w in texto_unido for w in ["trabajo", "híbrido", "hibrido", "remoto", "flexibilidad"]):
            trends.append({
                "titulo": "Evolución del Trabajo Híbrido",
                "resumen": f"Estudios y debates en redes demuestran que el esquema híbrido y la flexibilidad laboral aumentan la productividad individual al tiempo que exigen nuevas herramientas de colaboración. ({motivo})",
                "enfoque_comercial": "Marcas de muebles de oficina, software SaaS o recursos humanos pueden publicar posts sobre balance vida-trabajo y tips de ergonomía en casa.",
                "palabras_clave": ["trabajo", "productividad", "flexibilidad"]
            })

        # Tendencia por defecto si no coincide con las anteriores
        if not trends:
            trends.append({
                "titulo": "Marketing de Contenidos Digital",
                "resumen": f"Análisis general de la conversación diaria en redes sociales enfocado en el valor del contenido útil y no invasivo para construir comunidades sólidas. ({motivo})",
                "enfoque_comercial": "Crear hilos informativos desmintiendo mitos de tu industria para ganar confianza e interacciones orgánicas.",
                "palabras_clave": ["marketing", "redessociales", "contenido"]
            })

        return trends[:3]
