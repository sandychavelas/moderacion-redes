# Documento de Diseño: Mockups de la Interfaz Web (MDREC-9)

Este documento describe la propuesta de diseño y experiencia de usuario (UX/UI) para el frontend en React del **Sistema de Moderación de Redes Sociales**.

---

## 🎨 1. Estilo Visual y Paleta de Colores

Para lograr una apariencia premium y moderna, utilizaremos un diseño basado en **Glassmorphism** y un esquema de colores en **Modo Oscuro** con acentos neón:

*   **Fondo de la App:** Azul Grisáceo Oscuro Profundo (`#0F172A`).
*   **Paneles (Tarjetas):** Fondos traslúcidos con bordes semi-transparentes y un ligero desenfoque de fondo (*backdrop-filter: blur*).
*   **Acento de Aprobación:** Verde esmeralda brillante (`#10B981`) para elementos de éxito y posts aprobados.
*   **Acento de Bloqueo/Peligro:** Rojo carmesí brillante (`#EF4444`) para posts rechazados o palabras ofensivas.
*   **Tipografía:** *Outfit* o *Inter* de Google Fonts para garantizar máxima legibilidad y limpieza estética.

---

## 📐 2. Estructura del Layout (Dashboard de 3 Columnas)

La interfaz se compone de un diseño responsivo organizado en tres columnas principales:

### Columna Izquierda: Panel de Tendencias y Categorías
*   Muestra un resumen de los hashtags y temas más extraídos y clasificados por la IA en las últimas 24 horas (ej. `#Tecnología`, `#Ciberseguridad`, `#IA`).
*   Permite filtrar el feed central al hacer clic en cualquiera de las tendencias.
*   Incluye un buscador dinámico para buscar palabras clave comercial (MDREC-7) en tiempo real.

### Columna Central: Feed de "Posts Aprobados"
*   Es la zona principal de lectura. Muestra tarjetas con posts que han obtenido la clasificación **"Aprobado"** por DeepSeek.
*   Cada post incluye:
    *   Autor de la publicación y logo de la red social (ej. Reddit).
    *   Cuerpo del post destacado.
    *   Una etiqueta de la categoría asignada.
    *   Un botón de **"Copiar Idea"** para que los creadores de contenido del negocio puedan usarlo como inspiración rápida.

### Columna Derecha: Panel de Control y "Bandeja de Posts Bloqueados"
*   Muestra de forma compacta (y colapsable para proteger la sensibilidad visual) los posts que fueron clasificados como **"Malo"** (spam, insultos, publicidad agresiva).
*   Cada elemento incluye el motivo de rechazo determinado por DeepSeek (ej. *"Contiene spam publicitario"* o *"Mensaje ofensivo"*).
*   Incluye estadísticas globales en la parte superior:
    *   *Total de Posts Extraídos*.
    *   *Porcentaje de Aprobación*.
    *   *Volumen de Spam bloqueado*.

---

## 🖼️ 3. Boceto / Mockup Visual de la Interfaz

A continuación se muestra el boceto visual premium generado para la interfaz de usuario del dashboard:

![Boceto UI del Dashboard de Moderación de Redes](file:///C:/Users/emili/.gemini/antigravity/brain/a9af49df-faa9-47c3-b73d-2623c92bfbf5/moderation_dashboard_mockup_1781062818084.png)

---

## ⚡ 4. Interacciones y Micro-animaciones clave

1.  **Transición de Moderación:** Al presionar "Moderar" en un post pendiente, se muestra una animación de carga de neón girando y luego la tarjeta se desplaza suavemente al feed central (si es aprobado) o al panel lateral derecho (si es bloqueado).
2.  **Efectos de Cursor (Hover):** Las tarjetas de posts tienen un ligero aumento de tamaño (+2%) y un resplandor en los bordes cuando el cursor pasa sobre ellas.
3.  **Filtro Inmediato:** Al escribir palabras en el buscador de la columna izquierda, el feed central se filtra asíncronamente con un efecto de transición de desvanecimiento suave (*fade-out / fade-in*).
