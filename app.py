from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from datetime import datetime
import pytz
import os
import paho.mqtt.client as mqtt

app = Flask(__name__)
CORS(app)
app.debug = True
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'crowd_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'SECRET!'

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")  # habilita websockets


local_timezone = pytz.timezone('America/Mexico_City')  # Ajusta según tu zona horaria

class CrowdData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(local_timezone))
    cantidad = db.Column(db.String(80), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'cantidad': self.cantidad
        }
@socketio.on('connect')
def test_connect():
    print('client connected')
      
@socketio.on('disconnect')
def test_connect():
    print('client disonnected')

# Función para manejar mensajes MQTT
def on_message(client, userdata, msg):
    print("Mensaje recibido en MQTT:", msg.payload.decode())  # Mensaje de depuración
    cantidad = msg.payload.decode()
    
    with app.app_context():  # Asegurar el contexto de la app
        crowd_data = CrowdData(cantidad=cantidad)
        db.session.add(crowd_data)
        db.session.commit()
        socketio.emit('new_data', {'cantidad': cantidad})
        
        print(f"Datos almacenados y enviados por websocket: {cantidad}")


# Configurar el cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.subscribe("crowd_data/eventos")
#mqtt_client.loop_start()
mqtt_client.loop_forever()

@app.route("/data", methods=["GET"])
def get_all_data():
    data = CrowdData.query.all()
    return jsonify([item.to_dict() for item in data])

if __name__ == '__main__':
    # Crear el directorio 'instance' si no existe
    if not os.path.exists(os.path.join(basedir, 'instance')):
        os.makedirs(os.path.join(basedir, 'instance'))
    
    # Crear todas las tablas en la base de datos antes de iniciar la aplicación
    with app.app_context():
        db.create_all()
    
    # Iniciar el bucle MQTT en un hilo de fondo para no bloquear Flask
    mqtt_client.loop_start()
    
    # Iniciar el servidor Flask
    socketio.run(app, host="0.0.0.0", port=5000)