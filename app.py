from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
import pytz
import pusher
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuración de la zona horaria
lima_tz = pytz.timezone('America/Lima')

# Configuración de Pusher
pusher_client = None
pusher_enabled = False

# Verificar si las credenciales de Pusher están configuradas
pusher_app_id = os.environ.get('PUSHER_APP_ID')
pusher_key = os.environ.get('PUSHER_KEY')
pusher_secret = os.environ.get('PUSHER_SECRET')
pusher_cluster = os.environ.get('PUSHER_CLUSTER', 'us2')

if pusher_app_id and pusher_key and pusher_secret and pusher_app_id != 'your_app_id':
    try:
        pusher_client = pusher.Pusher(
            app_id=pusher_app_id,
            key=pusher_key,
            secret=pusher_secret,
            cluster=pusher_cluster,
            ssl=True
        )
        pusher_enabled = True
        print("✅ Pusher configurado correctamente")
    except Exception as e:
        print(f"❌ Error al configurar Pusher: {e}")
        pusher_enabled = False
else:
    print("⚠️  Pusher no configurado - usando modo polling. Configura las variables de entorno PUSHER_APP_ID, PUSHER_KEY y PUSHER_SECRET")

def get_db_connection():
    """Función para conectar a la base de datos MySQL"""
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'mysql-sistemasic.alwaysdata.net'),
            database=os.environ.get('DB_NAME', 'sistemasic_chat-python'),
            user=os.environ.get('DB_USER', '436286'),
            password=os.environ.get('DB_PASS', 'brayan933783039'),
            port=int(os.environ.get('DB_PORT', '3306')),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        if connection.is_connected():
            # Configurar zona horaria
            cursor = connection.cursor()
            cursor.execute("SET time_zone = '-05:00'")
            cursor.close()
            return connection
            
    except Error as e:
        print(f"Error de conexión a la base de datos: {e}")
        return None

@app.route('/api/send', methods=['POST'])
def send_message():
    """Endpoint para enviar mensajes"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No se recibieron datos'}), 400
            
        usuario = data.get('usuario', '').strip()
        mensaje = data.get('mensaje', '').strip()
        
        if not usuario or not mensaje:
            return jsonify({'error': 'Usuario y mensaje son requeridos'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cursor = connection.cursor()
        query = "INSERT INTO mensajes (usuario, mensaje) VALUES (%s, %s)"
        cursor.execute(query, (usuario, mensaje))
        connection.commit()
        
        message_id = cursor.lastrowid
        
        # Obtener el timestamp del mensaje recién insertado
        cursor.execute("SELECT timestamp FROM mensajes WHERE id = %s", (message_id,))
        timestamp_result = cursor.fetchone()
        
        cursor.close()
        connection.close()
        
        # Formatear timestamp para envío
        if timestamp_result:
            utc_time = timestamp_result[0].replace(tzinfo=pytz.UTC)
            lima_time = utc_time.astimezone(lima_tz)
            formatted_timestamp = lima_time.strftime('%Y-%m-%d %H:%M:%S')
        else:
            formatted_timestamp = datetime.now(lima_tz).strftime('%Y-%m-%d %H:%M:%S')
        
        # Enviar mensaje a través de Pusher si está habilitado
        message_data = {
            'id': message_id,
            'usuario': usuario,
            'mensaje': mensaje,
            'timestamp': formatted_timestamp
        }
        
        if pusher_enabled and pusher_client:
            try:
                pusher_client.trigger('chat', 'new-message', message_data)
            except Exception as e:
                print(f"Error al enviar evento Pusher: {e}")
        
        return jsonify({'success': True, 'id': message_id}), 200
        
    except Error as e:
        return jsonify({'error': f'Error de base de datos: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/api/messages', methods=['GET'])
def get_messages():
    """Endpoint para obtener mensajes"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cursor = connection.cursor(dictionary=True)
        query = "SELECT usuario, mensaje, timestamp FROM mensajes ORDER BY timestamp DESC LIMIT 50"
        cursor.execute(query)
        mensajes = cursor.fetchall()
        
        # Convertir timestamps a string para JSON
        for mensaje in mensajes:
            if mensaje['timestamp']:
                # Convertir a zona horaria de Lima
                utc_time = mensaje['timestamp'].replace(tzinfo=pytz.UTC)
                lima_time = utc_time.astimezone(lima_tz)
                mensaje['timestamp'] = lima_time.strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.close()
        connection.close()
        
        # Invertir el orden para mostrar los más antiguos primero
        mensajes_ordenados = list(reversed(mensajes))
        
        return jsonify({'messages': mensajes_ordenados}), 200
        
    except Error as e:
        return jsonify({'error': f'Error de base de datos: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/api/pusher/config', methods=['GET'])
def pusher_config():
    """Endpoint para obtener la configuración de Pusher"""
    if pusher_enabled:
        return jsonify({
            'enabled': True,
            'key': pusher_key,
            'cluster': pusher_cluster
        })
    else:
        return jsonify({'enabled': False})

@app.route('/api/pusher/auth', methods=['POST'])
def pusher_authentication():
    """Endpoint para autenticación de Pusher (si se necesita para canales privados)"""
    try:
        if not pusher_enabled or not pusher_client:
            return jsonify({'error': 'Pusher no está habilitado'}), 503
            
        socket_id = request.form['socket_id']
        channel_name = request.form['channel_name']
        
        # Para canales públicos, simplemente retornamos la autenticación
        auth = pusher_client.authenticate(channel=channel_name, socket_id=socket_id)
        return jsonify(auth)
        
    except Exception as e:
        return jsonify({'error': f'Error de autenticación: {str(e)}'}), 500

@app.route('/api/clear-messages', methods=['POST'])
def clear_messages():
    """Endpoint para limpiar todos los mensajes"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'error': 'Error de conexión a la base de datos'}), 500
        
        cursor = connection.cursor()
        cursor.execute("DELETE FROM mensajes")
        connection.commit()
        
        deleted_count = cursor.rowcount
        cursor.close()
        connection.close()
        
        return jsonify({'success': True, 'deleted_count': deleted_count}), 200
        
    except Error as e:
        return jsonify({'error': f'Error al eliminar mensajes: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': f'Error interno: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint para verificar el estado del servidor"""
    return jsonify({'status': 'OK', 'message': 'Servidor funcionando correctamente'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)