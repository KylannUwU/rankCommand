from flask import Flask, request, jsonify
from pymongo import MongoClient
import os

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client['rangosDB']
collection = db['rangos']

SECRET_TOKEN = os.getenv("KEYTW")

@app.route("/")
def home():
    return "API Rangos con MongoDB activa."

@app.route("/rango")
def obtener_rango():
    juego_actual = request.args.get("game", "").strip()
    if not juego_actual:
        return "Falta el parámetro ?game=NombreDelJuego"

    rango_doc = collection.find_one({"juego": {"$regex": f"^{juego_actual}$", "$options": "i"}})
    if rango_doc:
        return f"El rango actual de Nephu en {rango_doc['juego']} ➜ {rango_doc['rango']}"

    # Si no está, mostrar todos
    todos = list(collection.find({}))
    respuesta = [f"{d['juego']} ➜ {d['rango']}" for d in todos]
    return " | ".join(respuesta)

@app.route("/setrango", methods=["GET", "POST"])
def set_rango():
    token = request.args.get("token")
    juego = request.args.get("game")
    nuevo_rango = request.args.get("rango")

    if token != SECRET_TOKEN:
        return "No autorizado."

    if not juego or not nuevo_rango:
        return "Faltan parámetros: game y rango"

    # Upsert: inserta si no existe, actualiza si existe
    collection.update_one(
        {"juego": {"$regex": f"^{juego}$", "$options": "i"}},
        {"$set": {"juego": juego, "rango": nuevo_rango}},
        upsert=True
    )
    return f"✅ Rango de {juego} actualizado a: {nuevo_rango}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
