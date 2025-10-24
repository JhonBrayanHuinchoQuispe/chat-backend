# Chat en Tiempo Real - Backend

## 🚀 Deployment en Render

### 1. Variables de Entorno Requeridas

Configura estas variables en Render:

```
PUSHER_APP_ID=1893095
PUSHER_KEY=b8e9c9c8a8e8c8e8c8e8
PUSHER_SECRET=a1b2c3d4e5f6g7h8i9j0
PUSHER_CLUSTER=us2
DB_HOST=mysql-sistemasic.alwaysdata.net
DB_NAME=sistemasic_chat-python
DB_USER=436286
DB_PASS=brayan933783039
DB_PORT=3306
PORT=5000
```

### 2. Configuración de la Base de Datos

Ejecuta el script SQL en phpMyAdmin:

```sql
-- Usar la base de datos
USE sistemasic_chat_python;

-- Crear tabla de mensajes
CREATE TABLE IF NOT EXISTS mensajes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario VARCHAR(100) NOT NULL,
    mensaje TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- Crear vista de mensajes recientes
CREATE OR REPLACE VIEW mensajes_recientes AS
SELECT 
    id,
    usuario,
    mensaje,
    timestamp,
    DATE_FORMAT(timestamp, '%H:%i:%s') as hora
FROM mensajes 
ORDER BY timestamp DESC 
LIMIT 50;

-- Insertar mensajes de ejemplo
INSERT INTO mensajes (usuario, mensaje) VALUES 
('Sistema', 'Bienvenido al chat de SistemasSIC'),
('Admin', 'Chat iniciado correctamente');

-- Crear índices
CREATE INDEX idx_timestamp ON mensajes(timestamp DESC);
CREATE INDEX idx_usuario ON mensajes(usuario);
```

### 3. Endpoints de la API

- `POST /api/send` - Enviar mensaje
- `GET /api/messages` - Obtener mensajes
- `GET /api/pusher/config` - Configuración de Pusher
- `GET /health` - Health check

### 4. Frontend

El frontend debe apuntar a: `https://chat-backend-python-sistemasic.onrender.com`

### 5. Verificación

1. ✅ Variables de entorno configuradas en Render
2. ✅ Base de datos creada con tabla `mensajes`
3. ✅ Frontend apuntando a la URL correcta del backend
4. ✅ Pusher configurado (opcional, funciona con polling si no está disponible)

## 🔧 Desarrollo Local

1. Copia `.env.example` a `.env`
2. Instala dependencias: `pip install -r requirements.txt`
3. Ejecuta: `python app.py`

## 📝 Notas

- El chat funciona con o sin Pusher
- Si Pusher no está disponible, usa polling cada 3 segundos
- La zona horaria está configurada para Lima, Perú
- Los mensajes se almacenan en MySQL con charset utf8mb4