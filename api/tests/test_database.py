import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import os
import sys
from datetime import datetime

# Asegurar que el directorio api está en el sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mockear la base de datos y validaciones globales para evitar conexiones reales en lifespan
mock_pool = MagicMock()
patch("app.dependencies.database.crear_pool_conexiones", new_callable=AsyncMock, return_value=mock_pool).start()
patch("app.dependencies.database.cerrar_pool_conexiones", new_callable=AsyncMock).start()
patch("app.core.validaciones.validar_configuracion_servidor", return_value=None).start()

from fastapi.testclient import TestClient
from app.main import app
from app.dependencies.database import obtener_conexion_bd
from app.repository import posts_repo as repo


class TestPostsRepository(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        # Crear una conexión mockeada y cursor mockeado
        self.mock_conn = MagicMock()
        self.mock_cursor = AsyncMock()
        self.mock_conn.cursor.return_value.__aenter__.return_value = self.mock_cursor

    async def test_guardar_posts_vacio(self):
        """Prueba que guardar una lista vacía de posts retorne 0 de inmediato."""
        res = await repo.guardar_posts(self.mock_conn, [])
        self.assertEqual(res, 0)
        self.mock_conn.cursor.assert_not_called()

    async def test_guardar_posts_exito(self):
        """Prueba que se ejecute la inserción masiva en lote con executemany."""
        posts = [
            {
                "id_externo": "reddit_p1",
                "texto": "Texto de prueba 1",
                "autor": "autor1",
                "fecha_creacion": "2026-06-09T18:00:00Z"
            },
            {
                "id_externo": "reddit_p2",
                "texto": "Texto de prueba 2",
                "autor": "autor2",
                "fecha_creacion": datetime.now()
            }
        ]

        self.mock_cursor.rowcount = 2

        res = await repo.guardar_posts(self.mock_conn, posts)

        self.assertEqual(res, 2)
        self.mock_cursor.executemany.assert_called_once()

    async def test_obtener_posts_sin_filtros(self):
        """Prueba que la consulta de posts retorne la lista correcta."""
        mock_posts = [
            {
                "id": 1,
                "id_externo": "reddit_p1",
                "texto": "Texto de prueba 1",
                "autor": "autor1",
                "fecha_creacion": datetime(2026, 6, 9, 18, 0, 0),
                "red_social": "Reddit",
                "estado_moderacion": "Pendiente",
                "categoria_tendencia": None,
                "justificacion_moderacion": None,
                "fecha_extraccion": datetime(2026, 6, 9, 19, 0, 0)
            }
        ]

        # Configurar DictCursor mockeado
        mock_dict_cursor = AsyncMock()
        mock_dict_cursor.fetchall.return_value = mock_posts
        self.mock_conn.cursor.return_value.__aenter__.return_value = mock_dict_cursor

        res = await repo.obtener_posts(self.mock_conn)

        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["id"], 1)
        # La fecha debe estar formateada a string ISO en la salida del repositorio
        self.assertEqual(res[0]["fecha_creacion"], "2026-06-09T18:00:00Z")
        self.assertEqual(res[0]["fecha_extraccion"], "2026-06-09T19:00:00Z")

    async def test_obtener_posts_con_filtro_palabras_clave(self):
        """Prueba que el filtro por palabras clave (MDREC-7) se aplique en la consulta SQL."""
        mock_dict_cursor = AsyncMock()
        mock_dict_cursor.fetchall.return_value = []
        self.mock_conn.cursor.return_value.__aenter__.return_value = mock_dict_cursor

        # Buscar palabra clave 'oferta'
        await repo.obtener_posts(self.mock_conn, keyword="oferta")

        # Verificar que el query contenga LIKE
        call_args = mock_dict_cursor.execute.call_args[0]
        query = call_args[0]
        params = call_args[1]

        self.assertIn("texto LIKE %s", query)
        self.assertIn("%oferta%", params)

    async def test_obtener_metricas_analisis(self):
        """Prueba que obtener_metricas_analisis retorne el formato esperado."""
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.side_effect = [
            (10,), # count total
        ]
        mock_cursor.fetchall.side_effect = [
            [("Aprobado", 6), ("Malo", 4)], # por_estado
            [("Reddit", 8), ("Hacker News", 2)], # por_red_social
            [("Tecnología", 5), ("Finanzas", 3)] # top_tendencias
        ]
        self.mock_conn.cursor.return_value.__aenter__.return_value = mock_cursor

        res = await repo.obtener_metricas_analisis(self.mock_conn)
        self.assertEqual(res["total_posts"], 10)
        self.assertEqual(res["por_estado"]["Aprobado"], 6)
        self.assertEqual(res["por_red_social"]["Reddit"], 8)
        self.assertEqual(res["top_tendencias"][0]["categoria"], "Tecnología")
        self.assertEqual(res["top_tendencias"][0]["cantidad"], 5)

    async def test_obtener_posts_pendientes(self):
        """Prueba que obtener_posts_pendientes retorne la lista de posts en estado Pendiente."""
        mock_posts = [
            {
                "id": 1,
                "id_externo": "reddit_p1",
                "texto": "Texto pendiente 1",
                "autor": "autor1",
                "fecha_creacion": datetime(2026, 6, 9, 18, 0, 0),
                "red_social": "Reddit",
                "estado_moderacion": "Pendiente"
            }
        ]
        mock_dict_cursor = AsyncMock()
        mock_dict_cursor.fetchall.return_value = mock_posts
        self.mock_conn.cursor.return_value.__aenter__.return_value = mock_dict_cursor

        res = await repo.obtener_posts_pendientes(self.mock_conn, limit=5)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["estado_moderacion"], "Pendiente")
        self.assertEqual(res[0]["fecha_creacion"], "2026-06-09T18:00:00Z")

    async def test_guardar_tendencia_dia(self):
        """Prueba que guardar_tendencia_dia ejecute la inserción y devuelva el ID."""
        self.mock_cursor.lastrowid = 12
        res = await repo.guardar_tendencia_dia(
            self.mock_conn,
            titulo="IA en Pymes",
            resumen="Resumen de IA",
            enfoque_comercial="Vender IA",
            palabras_clave=["ia", "pymes"]
        )
        self.assertEqual(res, 12)
        self.mock_cursor.execute.assert_called_once()

    async def test_obtener_tendencias_dia(self):
        """Prueba que obtener_tendencias_dia retorne tendencias guardadas y parsee las palabras clave."""
        mock_trends = [
            {
                "id": 1,
                "titulo": "IA en Pymes",
                "resumen": "Resumen de IA",
                "enfoque_comercial": "Vender IA",
                "palabras_clave": "ia,pymes,automatizacion",
                "fecha_registro": datetime(2026, 6, 9, 18, 0, 0)
            }
        ]
        mock_dict_cursor = AsyncMock()
        mock_dict_cursor.fetchall.return_value = mock_trends
        self.mock_conn.cursor.return_value.__aenter__.return_value = mock_dict_cursor

        res = await repo.obtener_tendencias_dia(self.mock_conn, limit=5)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["palabras_clave"], ["ia", "pymes", "automatizacion"])
        self.assertEqual(res[0]["fecha_registro"], "2026-06-09T18:00:00Z")


class TestDatabaseEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        # Mockear la conexión del endpoint
        self.mock_db = MagicMock()
        async def mock_get_db():
            yield self.mock_db
        app.dependency_overrides[obtener_conexion_bd] = mock_get_db

    def tearDown(self):
        app.dependency_overrides.clear()

    @patch("app.repository.posts_repo.obtener_posts", new_callable=AsyncMock)
    def test_list_posts_endpoint(self, mock_obtener):
        """Prueba que el endpoint GET /api/v1/posts devuelva posts de la BD y admita filtros."""
        mock_posts = [
            {
                "id": 10,
                "id_externo": "reddit_x",
                "texto": "Gran oferta en laptops",
                "autor": "tienda_online",
                "fecha_creacion": "2026-06-09T18:00:00Z",
                "red_social": "Reddit",
                "estado_moderacion": "Pendiente",
                "categoria_tendencia": None,
                "justificacion_moderacion": None,
                "fecha_extraccion": "2026-06-09T19:00:00Z"
            }
        ]
        mock_obtener.return_value = mock_posts

        # Consultar filtrando por 'oferta' (MDREC-7)
        response = self.client.get("/api/v1/posts?keyword=oferta")
        self.assertEqual(response.status_code, 200)
        datos = response.json()
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["id"], 10)
        self.assertEqual(datos[0]["texto"], "Gran oferta en laptops")
        mock_obtener.assert_called_once_with(
            conexion=self.mock_db,
            keyword="oferta",
            estado=None,
            limit=20,
            offset=0
        )

    @patch("app.repository.posts_repo.guardar_posts", new_callable=AsyncMock)
    @patch("app.services.social_media.SocialMediaConnector.obtener_posts_tendencia", new_callable=AsyncMock)
    def test_fetch_and_store_endpoint(self, mock_obtener_red, mock_guardar_bd):
        """Prueba que el endpoint /fetch-and-store extraiga y guarde posts en la BD."""
        mock_posts_red = [
            {"id_externo": "reddit_1", "texto": "Post 1", "autor": "user1", "fecha_creacion": "2026-06-09T18:00:00Z"}
        ]
        mock_obtener_red.return_value = mock_posts_red
        mock_guardar_bd.return_value = 1

        response = self.client.post("/api/v1/posts/fetch-and-store?limit=5")
        self.assertEqual(response.status_code, 201)
        datos = response.json()
        self.assertEqual(datos["status"], "success")
        self.assertEqual(datos["extraidos"], 1)
        self.assertEqual(datos["nuevos_guardados"], 1)

        mock_obtener_red.assert_called_once_with(limit=5)
        mock_guardar_bd.assert_called_once_with(self.mock_db, mock_posts_red)

    @patch("app.repository.posts_repo.guardar_historial_moderacion", new_callable=AsyncMock)
    @patch("app.repository.posts_repo.actualizar_moderacion", new_callable=AsyncMock)
    @patch("app.services.ai_moderator.AIModeratorService.moderar_post", new_callable=AsyncMock)
    @patch("app.repository.posts_repo.obtener_post_por_id", new_callable=AsyncMock)
    def test_moderate_stored_post_endpoint(self, mock_obtener_id, mock_moderar, mock_actualizar, mock_historial):
        """Prueba que el endpoint /{post_id}/moderate llame a la IA y guarde los veredictos."""
        post_original = {
            "id": 5,
            "id_externo": "reddit_x",
            "texto": "Post comercial de zapatillas",
            "autor": "run_store",
            "fecha_creacion": "2026-06-09T18:00:00Z",
            "red_social": "Reddit",
            "estado_moderacion": "Pendiente",
            "categoria_tendencia": None,
            "justificacion_moderacion": None,
            "fecha_extraccion": "2026-06-09T19:00:00Z"
        }
        mock_obtener_id.return_value = post_original

        mock_moderar.return_value = {
            "clasificacion": "Aprobado",
            "categoria_tendencia": "Deportes / Moda",
            "palabras_clave": ["zapatillas", "run"],
            "justificacion": "Aprobado por ser contenido publicitario limpio."
        }

        mock_actualizar.return_value = True
        mock_historial.return_value = 42

        response = self.client.post("/api/v1/posts/5/moderate")
        self.assertEqual(response.status_code, 200)
        datos = response.json()
        self.assertEqual(datos["post_id"], 5)
        self.assertEqual(datos["estado_moderacion"], "Aprobado")
        self.assertEqual(datos["categoria_tendencia"], "Deportes / Moda")
        self.assertEqual(datos["historial_id"], 42)

        mock_obtener_id.assert_called_once_with(self.mock_db, 5)
        mock_moderar.assert_called_once_with(texto="Post comercial de zapatillas")
        mock_actualizar.assert_called_once_with(
            conexion=self.mock_db,
            post_id=5,
            estado="Aprobado",
            categoria="Deportes / Moda",
            justificacion="Aprobado por ser contenido publicitario limpio."
        )
        mock_historial.assert_called_once_with(
            conexion=self.mock_db,
            post_id=5,
            clasificacion="Aprobado",
            categoria_tendencia="Deportes / Moda",
            justificacion="Aprobado por ser contenido publicitario limpio."
        )

    @patch("app.repository.posts_repo.obtener_metricas_analisis", new_callable=AsyncMock)
    def test_get_analytics_endpoint(self, mock_metricas):
        """Prueba que el endpoint GET /api/v1/posts/analytics devuelva las métricas correctas."""
        mock_data = {
            "total_posts": 100,
            "por_estado": {"Pendiente": 10, "Aprobado": 60, "Malo": 30},
            "por_red_social": {"Reddit": 80, "Hacker News": 20},
            "top_tendencias": [{"categoria": "Tecnología", "cantidad": 45}]
        }
        mock_metricas.return_value = mock_data

        response = self.client.get("/api/v1/posts/analytics")
        self.assertEqual(response.status_code, 200)
        datos = response.json()
        self.assertEqual(datos["total_posts"], 100)
        self.assertEqual(datos["por_estado"]["Aprobado"], 60)
        self.assertEqual(datos["top_tendencias"][0]["categoria"], "Tecnología")
        mock_metricas.assert_called_once_with(self.mock_db)

    @patch("app.repository.posts_repo.guardar_historial_moderacion", new_callable=AsyncMock)
    @patch("app.repository.posts_repo.actualizar_moderacion", new_callable=AsyncMock)
    @patch("app.services.ai_moderator.AIModeratorService.moderar_post", new_callable=AsyncMock)
    @patch("app.repository.posts_repo.obtener_posts_pendientes", new_callable=AsyncMock)
    def test_moderate_pending_posts_endpoint(self, mock_pendientes, mock_moderar, mock_actualizar, mock_historial):
        """Prueba que el endpoint POST /api/v1/posts/moderate-pending modere posts pendientes."""
        mock_pendientes.return_value = [
            {
                "id": 1,
                "id_externo": "reddit_p1",
                "texto": "Post pendiente 1",
                "autor": "autor1",
                "red_social": "Reddit",
                "estado_moderacion": "Pendiente",
                "fecha_creacion": "2026-06-09T18:00:00Z"
            }
        ]
        mock_moderar.return_value = {
            "clasificacion": "Aprobado",
            "categoria_tendencia": "Tecnología",
            "justificacion": "Lote aprobado"
        }
        mock_actualizar.return_value = True
        mock_historial.return_value = 101

        response = self.client.post("/api/v1/posts/moderate-pending?limit=5")
        self.assertEqual(response.status_code, 200)
        datos = response.json()
        self.assertEqual(datos["status"], "success")
        self.assertEqual(datos["procesados"], 1)
        self.assertEqual(len(datos["moderados"]), 1)
        self.assertEqual(datos["moderados"][0]["post_id"], 1)
        self.assertEqual(datos["moderados"][0]["estado_moderacion"], "Aprobado")
        self.assertEqual(datos["moderados"][0]["historial_id"], 101)

        mock_pendientes.assert_called_once_with(self.mock_db, limit=5)
        mock_moderar.assert_called_once_with("Post pendiente 1")
        mock_actualizar.assert_called_once_with(
            conexion=self.mock_db,
            post_id=1,
            estado="Aprobado",
            categoria="Tecnología",
            justificacion="Lote aprobado"
        )
        mock_historial.assert_called_once_with(
            conexion=self.mock_db,
            post_id=1,
            clasificacion="Aprobado",
            categoria_tendencia="Tecnología",
            justificacion="Lote aprobado"
        )

    @patch("app.repository.posts_repo.guardar_tendencia_dia", new_callable=AsyncMock)
    @patch("app.services.ai_moderator.AIModeratorService.sintetizar_tendencias_del_dia", new_callable=AsyncMock)
    @patch("app.repository.posts_repo.obtener_posts", new_callable=AsyncMock)
    def test_generate_daily_trends_endpoint(self, mock_obtener, mock_sintetizar, mock_guardar_tendencia):
        """Prueba que POST /api/v1/posts/generate-trends agrupe posts aprobados y sintetice tendencias."""
        mock_obtener.return_value = [
            {"id": 1, "texto": "Texto aprobado 1", "estado_moderacion": "Aprobado"}
        ]
        mock_sintetizar.return_value = [
            {
                "titulo": "Adopción de IA",
                "resumen": "Resumen de IA",
                "enfoque_comercial": "Enfoque IA",
                "palabras_clave": ["ia", "tecnologia"]
            }
        ]
        mock_guardar_tendencia.return_value = 88

        response = self.client.post("/api/v1/posts/generate-trends?limit=30")
        self.assertEqual(response.status_code, 201)
        datos = response.json()
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["id"], 88)
        self.assertEqual(datos[0]["titulo"], "Adopción de IA")
        self.assertEqual(datos[0]["palabras_clave"], ["ia", "tecnologia"])

        mock_obtener.assert_called_once_with(self.mock_db, estado="Aprobado", limit=30)
        mock_sintetizar.assert_called_once_with(["Texto aprobado 1"])
        mock_guardar_tendencia.assert_called_once_with(
            conexion=self.mock_db,
            titulo="Adopción de IA",
            resumen="Resumen de IA",
            enfoque_comercial="Enfoque IA",
            palabras_clave=["ia", "tecnologia"]
        )

    @patch("app.repository.posts_repo.obtener_tendencias_dia", new_callable=AsyncMock)
    def test_list_trends_endpoint(self, mock_obtener_trends):
        """Prueba que GET /api/v1/posts/trends devuelva las tendencias guardadas."""
        mock_trends = [
            {
                "id": 1,
                "titulo": "Adopción de IA",
                "resumen": "Resumen de IA",
                "enfoque_comercial": "Enfoque IA",
                "palabras_clave": ["ia", "tecnologia"],
                "fecha_registro": "2026-06-09T18:00:00Z"
            }
        ]
        mock_obtener_trends.return_value = mock_trends

        response = self.client.get("/api/v1/posts/trends?limit=10")
        self.assertEqual(response.status_code, 200)
        datos = response.json()
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["id"], 1)
        self.assertEqual(datos[0]["titulo"], "Adopción de IA")
        mock_obtener_trends.assert_called_once_with(self.mock_db, limit=10)


if __name__ == "__main__":
    unittest.main()
