import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import os
import sys

# Asegurar que el directorio api está en el sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mockear la base de datos y validaciones globales para evitar conexiones reales en lifespan
mock_pool = MagicMock()
patch("app.dependencies.database.crear_pool_conexiones", new_callable=AsyncMock, return_value=mock_pool).start()
patch("app.dependencies.database.cerrar_pool_conexiones", new_callable=AsyncMock).start()
patch("app.core.validaciones.validar_configuracion_servidor", return_value=None).start()

from fastapi.testclient import TestClient
from app.main import app
from app.services.social_media import SocialMediaConnector, MOCK_POSTS


class TestSocialMediaConnector(unittest.IsolatedAsyncioTestCase):

    async def test_obtener_posts_tendencia_exito_real(self):
        """Prueba que el conector procese correctamente una respuesta exitosa (200 OK) de Reddit."""
        mock_response_data = {
            "data": {
                "children": [
                    {
                        "data": {
                            "id": "abc123_test",
                            "title": "Nuevo avance en IA",
                            "selftext": "DeepSeek está ganando popularidad.",
                            "author": "tech_user",
                            "created_utc": 1718020800
                        }
                    }
                ]
            }
        }

        # Mockear httpx.AsyncClient.get para retornar una respuesta exitosa con los datos simulados
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response) as mock_get:
            connector = SocialMediaConnector()
            posts = await connector.obtener_posts_tendencia(limit=1)

            mock_get.assert_called_once()
            self.assertEqual(len(posts), 1)
            self.assertEqual(posts[0]["id_externo"], "reddit_abc123_test")
            self.assertIn("Nuevo avance en IA", posts[0]["texto"])
            self.assertEqual(posts[0]["autor"], "tech_user")
            self.assertEqual(posts[0]["red_social"], "Reddit")

    async def test_obtener_posts_tendencia_error_api_fallback(self):
        """Prueba que el conector use los datos mockeados si la API responde con un código de error (ej. 500)."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response) as mock_get:
            connector = SocialMediaConnector()
            posts = await connector.obtener_posts_tendencia(limit=3)

            mock_get.assert_called_once()
            # Debe caer al fallback y retornar la cantidad solicitada
            self.assertEqual(len(posts), 3)
            self.assertEqual(posts[0]["id_externo"], MOCK_POSTS[0]["id_externo"])

    async def test_obtener_posts_tendencia_excepcion_fallback(self):
        """Prueba que el conector use los datos mockeados si ocurre una excepción de conexión."""
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=Exception("Falla de red")) as mock_get:
            connector = SocialMediaConnector()
            posts = await connector.obtener_posts_tendencia(limit=2)

            mock_get.assert_called_once()
            self.assertEqual(len(posts), 2)
            self.assertEqual(posts[0]["id_externo"], MOCK_POSTS[0]["id_externo"])


class TestPostsEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch("app.services.social_media.SocialMediaConnector.obtener_posts_tendencia", new_callable=AsyncMock)
    def test_fetch_posts_endpoint_exito(self, mock_obtener_posts):
        """Prueba que el endpoint /api/v1/posts/fetch devuelva los posts del servicio."""
        mock_posts_data = [
            {
                "id_externo": "reddit_t1",
                "texto": "Post de prueba",
                "autor": "test_author",
                "fecha_creacion": "2026-06-09T18:00:00Z",
                "red_social": "Reddit"
            }
        ]
        mock_obtener_posts.return_value = mock_posts_data

        response = self.client.get("/api/v1/posts/fetch?limit=1")
        self.assertEqual(response.status_code, 200)
        datos = response.json()
        self.assertEqual(len(datos), 1)
        self.assertEqual(datos[0]["id_externo"], "reddit_t1")
        self.assertEqual(datos[0]["texto"], "Post de prueba")
        mock_obtener_posts.assert_called_once_with(limit=1)

    def test_fetch_posts_endpoint_limites_invalidos(self):
        """Prueba que el endpoint valide correctamente los límites (debe ser >= 1 y <= 20)."""
        # Límite demasiado bajo (0)
        response_bajo = self.client.get("/api/v1/posts/fetch?limit=0")
        self.assertEqual(response_bajo.status_code, 422)  # ValidationError

        # Límite demasiado alto (21)
        response_alto = self.client.get("/api/v1/posts/fetch?limit=21")
        self.assertEqual(response_alto.status_code, 422)  # ValidationError


if __name__ == "__main__":
    unittest.main()
