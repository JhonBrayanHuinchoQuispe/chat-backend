# Chat en Tiempo Real - Backend


###  Base de Datos



CREATE TABLE  mensajes (
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

-- Crear índices
CREATE INDEX idx_timestamp ON mensajes(timestamp DESC);
CREATE INDEX idx_usuario ON mensajes(usuario);
```


## 📝 Notas

- El chat funciona con o sin Pusher
- Si Pusher no está disponible, usa polling cada 3 segundos
- La zona horaria está configurada para Lima, Perú
- Los mensajes se almacenan en MySQL con charset utf8mb4
