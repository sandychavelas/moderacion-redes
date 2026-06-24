-- =====================================================================
-- Esquema de Base de Datos para el Sistema de Moderación de Redes (moderacionbd)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS moderacionbd;
USE moderacionbd;

-- --- TABLA DE USUARIOS ---
CREATE TABLE IF NOT EXISTS usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    rol ENUM('Product Owner', 'Scrum Master', 'Developer') DEFAULT 'Developer',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --- TABLA DE PRODUCTOS / TEMAS DE INTERÉS ---
CREATE TABLE IF NOT EXISTS productos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    sector VARCHAR(50),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --- TABLA DE POSTS EXTRAÍDOS DE REDES SOCIALES ---
CREATE TABLE IF NOT EXISTS posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_externo VARCHAR(100) NOT NULL UNIQUE, -- Identificador único de origen (ej. 'reddit_abc123')
    texto TEXT NOT NULL,
    autor VARCHAR(100) NOT NULL,
    fecha_creacion DATETIME NOT NULL,
    red_social VARCHAR(50) NOT NULL,
    estado_moderacion ENUM('Pendiente', 'Aprobado', 'Malo') DEFAULT 'Pendiente',
    categoria_tendencia VARCHAR(100) DEFAULT NULL,
    justificacion_moderacion TEXT DEFAULT NULL,
    fecha_extraccion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --- TABLA DE HISTORIAL / AUDITORÍA DE MODERACIÓN DE IA Y USUARIOS ---
CREATE TABLE IF NOT EXISTS historial_moderacion (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    usuario_id INT DEFAULT NULL, -- NULL indica moderación automática realizada por la IA
    clasificacion ENUM('Aprobado', 'Malo') NOT NULL,
    categoria_tendencia VARCHAR(100) NOT NULL,
    justificacion TEXT NOT NULL,
    fecha_moderacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historial_post FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    CONSTRAINT fk_historial_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --- TABLA DE TENDENCIAS GENERALES DEL DÍA (AGRUPADAS POR IA) ---
CREATE TABLE IF NOT EXISTS tendencias_dia (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(150) NOT NULL,
    resumen TEXT NOT NULL,
    enfoque_comercial TEXT NOT NULL,
    palabras_clave VARCHAR(255) NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --- INSERTAR ALGUNOS DATOS DE PRUEBA INICIALES (MOCK) ---
INSERT INTO usuarios (nombre, email, rol) VALUES
('Emilio PO', 'emilio.po@empresa.com', 'Product Owner'),
('Sandy SM', 'sandy.sm@empresa.com', 'Scrum Master'),
('Developer Team', 'dev@empresa.com', 'Developer')
ON DUPLICATE KEY UPDATE nombre=nombre;

INSERT INTO productos (nombre, descripcion, sector) VALUES
('Análisis de Tendencias', 'Seguimiento de temas populares y moderación de contenido para ideas de publicaciones', 'Tecnología/Marketing')
ON DUPLICATE KEY UPDATE nombre=nombre;
