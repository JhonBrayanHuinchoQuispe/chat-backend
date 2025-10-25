# Chat en Tiempo Real - Backend


###  Base de Datos
```sql
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

-- Crear índices
CREATE INDEX idx_timestamp ON mensajes(timestamp DESC);
CREATE INDEX idx_usuario ON mensajes(usuario);
```
