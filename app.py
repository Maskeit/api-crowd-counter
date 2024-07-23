from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'crowd_data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class CrowdData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    cantidad = db.Column(db.String(80), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'cantidad': self.cantidad
        }

@app.route("/")
def root():
    return "Hola mundo"

@app.route("/data/<int:data_id>")
def get_data(data_id):
    data = CrowdData.query.get(data_id)
    if data is None:
        return jsonify({'error': 'Data not found'}), 404
    return jsonify(data.to_dict()), 200
@app.route("/data", methods=["GET"])
def get_all_data():
    data = CrowdData.query.all()
    return jsonify([item.to_dict() for item in data])

@app.route("/data", methods=["POST"])
def create_data():
    data = request.get_json()
    cantidad = data.get('cantidad')
    if cantidad is None:
        return jsonify({'error': 'Missing cantidad field'}), 400

    crowd_data = CrowdData(cantidad=cantidad)
    db.session.add(crowd_data)
    db.session.commit()

    return jsonify(crowd_data.to_dict()), 201

if __name__ == '__main__':
    if not os.path.exists(os.path.join(basedir, 'instance')):
        os.makedirs(os.path.join(basedir, 'instance'))
    with app.app_context():
        db.create_all()  # Crear todas las tablas
    app.run(debug=True)
