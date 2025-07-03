from flask import Flask, request
from github import Github
import json
import os

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("La variable de entorno GITHUB_TOKEN no está definida")

SECRET_TOKEN = os.getenv("KEYTW")
if not SECRET_TOKEN:
    raise ValueError("La variable de entorno KEYTW no está definida")

# Fijos acá:
REPO_NAME = "KylannUwU/rankCommand"
BRANCH = "main"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

FILE_PATH = "rangos.json"

def leer_rangos_github():
    try:
        contenido = repo.get_contents(FILE_PATH, ref=BRANCH)
        datos = json.loads(contenido.decoded_content.decode())
        return datos, contenido.sha
    except Exception as e:
        print(f"Error leyendo rangos desde GitHub: {e}")
        return {}, None

def guardar_rangos_github(rangos_dict, sha, mensaje="Actualización de rangos"):
    contenido_nuevo = json.dumps(rangos_dict, ensure_ascii=False, indent=2)
    try:
        if sha:
            repo.update_file(FILE_PATH, mensaje, contenido_nuevo, sha, branch=BRANCH)
        else:
            repo.create_file(FILE_PATH, mensaje, contenido_nuevo, branch=BRANCH)
        return True
    except Exception as e:
        print(f"Error guardando rangos en GitHub: {e}")
        return False

@app.route("/")
def home():
    return "API Rangos con commits a GitHub activa."

@app.route("/rango")
def obtener_rango():
    juego_actual = request.args.get("game", "").strip()
    if not juego_actual:
        return "Falta el parámetro ?game=NombreDelJuego"

    rangos, _ = leer_rangos_github()
    for juego, rango in rangos.items():
        if juego.lower() == juego_actual.lower():
            return f"El rango actual de Nephu en {juego} ➜ {rango}"

    respuesta = [f"{j} ➜ {r}" for j, r in rangos.items()]
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

    rangos, sha = leer_rangos_github()
    rangos[juego] = nuevo_rango

    exito = guardar_rangos_github(rangos, sha, mensaje=f"Actualización rango {juego}")

    if exito:
        return f"✅ Rango de {juego} actualizado a: {nuevo_rango}"
    else:
        return "Error actualizando rangos en GitHub."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
