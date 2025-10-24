from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
import pytz

app = Flask(__name__)
CORS(app)

lima_tz = pytz.timezone('America/Lima')

# Aqui configuro la conexion a mi base de datos mysql
def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            database=os.environ.get('DB_NAME', 'chat_db'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', '')
        )
        return connection
    except Error:
        return None

@app.route('/api/messages', methods=['GET'])
def get_messages():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 50")
        messages = cursor.fetchall()
        
        # Convierto la hora UTC a hora de Peru para mostrar correctamente
        for message in messages:
            if message['timestamp']:
                utc_time = message['timestamp'].replace(tzinfo=pytz.UTC)
                lima_time = utc_time.astimezone(lima_tz)
                message['timestamp'] = lima_time.strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({'messages': list(reversed(messages))})
    except Error:
        return jsonify({'error': 'Database error'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/send', methods=['POST'])
def send_message():
    data = request.get_json()
    if not data or 'usuario' not in data or 'mensaje' not in data:
        return jsonify({'error': 'Missing data'}), 400
    
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        lima_time = datetime.now(lima_tz)
        
        # Inserto el nuevo mensaje con la hora actual de Peru
        cursor.execute(
            "INSERT INTO messages (usuario, mensaje, timestamp) VALUES (%s, %s, %s)",
            (data['usuario'], data['mensaje'], lima_time)
        )
        connection.commit()
        return jsonify({'success': True})
    except Error:
        return jsonify({'error': 'Database error'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

@app.route('/api/clear-messages', methods=['POST'])
def clear_messages():
    connection = get_db_connection()
    if not connection:
        return jsonify({'error': 'Database connection failed'}), 500
    
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM messages")
        connection.commit()
        return jsonify({'success': True})
    except Error:
        return jsonify({'error': 'Database error'}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)