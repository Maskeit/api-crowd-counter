from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
import os
import paho.mqtt.client as mqtt

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'crowd_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

# Función para manejar mensajes MQTT
def on_message(client, userdata, msg):
    cantidad = msg.payload.decode()
    
    with app.app_context():  # Asegurar el contexto de la app
        crowd_data = CrowdData(cantidad=cantidad)
        db.session.add(crowd_data)
        db.session.commit()
        print(f"Datos almacenados: {cantidad}")

# Configurar el cliente MQTT
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect("localhost", 1883, 60)  # Cambia 'localhost' si el broker está en otro servidor
mqtt_client.subscribe("crowd_data/eventos")
mqtt_client.loop_start()

@app.route("/data", methods=["GET"])
def get_all_data():
    data = CrowdData.query.all()
    return jsonify([item.to_dict() for item in data])

if __name__ == '__main__':
    if not os.path.exists(os.path.join(basedir, 'instance')):
        os.makedirs(os.path.join(basedir, 'instance'))
    with app.app_context():
        db.create_all()  # Crear todas las tablas
    app.run(debug=True)
