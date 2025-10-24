from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
import os
from datetime import datetime
import pytz
import pusher
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

peru_tz = pytz.timezone('America/Lima')

# Configuración de Pusher para tiempo real
pusher_client = None
pusher_enabled = False

pusher_app_id = os.environ.get('PUSHER_APP_ID')
pusher_key = os.environ.get('PUSHER_KEY')
pusher_secret = os.environ.get('PUSHER_SECRET')
pusher_cluster = os.environ.get('PUSHER_CLUSTER', 'us2')

if pusher_app_id and pusher_key and pusher_secret and pusher_app_id != 'your_app_id':
    pusher_client = pusher.Pusher(
        app_id=pusher_app_id,
        key=pusher_key,
        secret=pusher_secret,
        cluster=pusher_cluster,
        ssl=True
    )
    pusher_enabled = True

def get_db_connection():
    connection = mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'mysql-sistemasic.alwaysdata.net'),
        database=os.environ.get('DB_NAME', 'sistemasic_chat-python'),
        user=os.environ.get('DB_USER', '436286'),
        password=os.environ.get('DB_PASS', 'brayan933783039'),
        port=int(os.environ.get('DB_PORT', '3306')),
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )
    
    cursor = connection.cursor()
    cursor.execute("SET time_zone = '-05:00'")
    cursor.close()
    return connection

@app.route('/api/send', methods=['POST'])
def send_message():
    data = request.get_json()
    usuario = data.get('usuario', '').strip()
    mensaje = data.get('mensaje', '').strip()
    
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "INSERT INTO mensajes (usuario, mensaje) VALUES (%s, %s)"
    cursor.execute(query, (usuario, mensaje))
    connection.commit()
    
    message_id = cursor.lastrowid
    
    cursor.execute("SELECT timestamp FROM mensajes WHERE id = %s", (message_id,))
    timestamp_result = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    utc_time = timestamp_result[0].replace(tzinfo=pytz.UTC)
    peru_time = utc_time.astimezone(peru_tz)
    formatted_timestamp = peru_time.strftime('%Y-%m-%d %H:%M:%S')
    
    # Envío en tiempo real con Pusher
    message_data = {
        'id': message_id,
        'usuario': usuario,
        'mensaje': mensaje,
        'timestamp': formatted_timestamp
    }
    
    if pusher_enabled and pusher_client:
        pusher_client.trigger('chat', 'new-message', message_data)
    
    return jsonify({'success': True, 'id': message_id}), 200

@app.route('/api/messages', methods=['GET'])
def get_messages():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = "SELECT usuario, mensaje, timestamp FROM mensajes ORDER BY timestamp ASC LIMIT 30"
    cursor.execute(query)
    mensajes = cursor.fetchall()
    
    for mensaje in mensajes:
        if mensaje['timestamp']:
            utc_time = mensaje['timestamp'].replace(tzinfo=pytz.UTC)
            peru_time = utc_time.astimezone(peru_tz)
            mensaje['timestamp'] = peru_time.strftime('%I:%M %p')
    
    cursor.close()
    connection.close()
    
    return jsonify({'messages': mensajes}), 200

@app.route('/api/pusher/config', methods=['GET'])
def pusher_config():
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
    socket_id = request.form['socket_id']
    channel_name = request.form['channel_name']
    
    auth = pusher_client.authenticate(channel=channel_name, socket_id=socket_id)
    return jsonify(auth)

# Endpoint para limpiar todos los mensajes
@app.route('/api/clear-messages', methods=['POST'])
def clear_messages():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM mensajes")
    connection.commit()
    
    deleted_count = cursor.rowcount
    cursor.close()
    connection.close()
    
    return jsonify({
        'success': True, 
        'message': f'Deleted {deleted_count} messages',
        'deleted_count': deleted_count
    }), 200

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'OK', 'message': 'Server running'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
