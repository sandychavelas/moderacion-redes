import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import os
import sys
import json

# Asegurar que el directorio api está en el sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mockear la base de datos y validaciones globales para evitar conexiones reales en lifespan
mock_pool = MagicMock()
patch("app.dependencies.database.crear_pool_conexiones", new_callable=AsyncMock, return_value=mock_pool).start()
patch("app.dependencies.database.cerrar_pool_conexiones", new_callable=AsyncMock).start()
patch("app.core.validaciones.validar_configuracion_servidor", return_value=None).start()

from fastapi.testclient import TestClient
from app.main import app
from app.services.ai_moderator import AIModeratorService


class TestAIModeratorService(unittest.IsolatedAsyncioTestCase):

    async def test_moderar_post_vacio(self):
        """Prueba que un texto vacío sea rechazado de inmediato."""
        service = AIModeratorService()
        res = await service.moderar_post("")
        self.assertEqual(res["clasificacion"], "Malo")
        self.assertEqual(res["categoria_tendencia"], "Ninguna")

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_moderar_post_exito_deepseek(self, mock_post):
        """Prueba que el servicio procese la respuesta exitosa de la API de DeepSeek."""
        mock_response_json = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "clasificacion": "Aprobado",
                            "categoria_tendencia": "Tecnología / Programación",
                            "palabras_clave": ["deepseek", "fastapi", "ia"],
                            "justificacion": "El post habla sobre desarrollo técnico de forma constructiva."
                        })
                    }
                }
            ]
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_json
        mock_post.return_value = mock_response

        # Configurar clave ficticia de API para obligar a llamar a la API
        service = AIModeratorService()
        service.api_key = "sk-fake-key"

        res = await service.moderar_post("Probando DeepSeek con FastAPI y Python")

        mock_post.assert_called_once()
        self.assertEqual(res["clasificacion"], "Aprobado")
        self.assertEqual(res["categoria_tendencia"], "Tecnología / Programación")
        self.assertEqual(res["palabras_clave"], ["deepseek", "fastapi", "ia"])
        self.assertIn("desarrollo técnico", res["justificacion"])

    async def test_moderar_post_sin_api_key_fallback(self):
        """Prueba que si no hay API key, se ejecute la clasificación local por palabras clave."""
        service = AIModeratorService()
        service.api_key = ""  # Forzar ausencia de clave

        # Post que debería ser marcado como malo localmente por spam de seguidores
        res_malo = await service.moderar_post("Compra seguidores de instagram en www.seguidoresfacil.com ya!")
        self.assertEqual(res_malo["clasificacion"], "Malo")
        self.assertEqual(res_malo["categoria_tendencia"], "Marketing Digital")
        self.assertIn("seguidores", res_malo["palabras_clave"])

        # Post que debería ser marcado como aprobado localmente
        res_bueno = await service.moderar_post("Estamos diseñando una nueva arquitectura en la nube con Kubernetes.")
        self.assertEqual(res_bueno["clasificacion"], "Aprobado")

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    async def test_moderar_post_error_api_fallback(self, mock_post):
        """Prueba que si la API responde con un error (ej. 503 Service Unavailable), el servicio caiga al fallback."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"
        mock_post.return_value = mock_response

        service = AIModeratorService()
        service.api_key = "sk-fake-key"

        # Post que contiene la palabra insulto local 'imbécil'
        res = await service.moderar_post("Eres un imbécil si crees que esto fallará.")

        mock_post.assert_called_once()
        # El fallback local debe clasificarlo como malo
        self.assertEqual(res["clasificacion"], "Malo")
        self.assertIn("fallback", res["justificacion"])


class TestModerationEndpoint(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    @patch("app.services.ai_moderator.AIModeratorService.moderar_post", new_callable=AsyncMock)
    def test_classify_endpoint_exito(self, mock_moderar):
        """Prueba que el endpoint /api/v1/moderation/classify devuelva los datos clasificados por el servicio."""
        mock_res_data = {
            "clasificacion": "Aprobado",
            "categoria_tendencia": "Salud",
            "palabras_clave": ["ejercicio", "salud"],
            "justificacion": "Post constructivo sobre salud."
        }
        mock_moderar.return_value = mock_res_data

        response = self.client.post(
            "/api/v1/moderation/classify",
            json={"texto": "El ejercicio diario ayuda a mantener un cuerpo sano."}
        )

        self.assertEqual(response.status_code, 200)
        datos = response.json()
        self.assertEqual(datos["clasificacion"], "Aprobado")
        self.assertEqual(datos["categoria_tendencia"], "Salud")
        self.assertEqual(datos["palabras_clave"], ["ejercicio", "salud"])
        mock_moderar.assert_called_once_with(texto="El ejercicio diario ayuda a mantener un cuerpo sano.")

    def test_classify_endpoint_datos_invalidos(self):
        """Prueba que el endpoint rechace textos vacíos o payloads incorrectos."""
        # Payload vacío (falta el campo texto)
        response_vacio = self.client.post("/api/v1/moderation/classify", json={})
        self.assertEqual(response_vacio.status_code, 422)

        # Texto vacío
        response_texto_vacio = self.client.post("/api/v1/moderation/classify", json={"texto": ""})
        self.assertEqual(response_texto_vacio.status_code, 422)


if __name__ == "__main__":
    unittest.main()
