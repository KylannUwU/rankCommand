from flask import Flask, request
from github import Github
import json
import os

app = Flask(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
SECRET_TOKEN = os.getenv("KEYTW")

REPO_NAME = "KylannUwU/rankCommand"
BRANCH = "main"
FILE_PATH = "rangos.json"

g = Github(GITHUB_TOKEN)
repo = g.get_repo(REPO_NAME)

def leer_rangos_github():
    try:
        contenido = repo.get_contents(FILE_PATH, ref=BRANCH)
        datos = json.loads(contenido.decoded_content.decode())
        return datos, contenido.sha
    except Exception as e:
        print(f"Error leyendo rangos desde GitHub: {e}")
        return {}, None

def guardar_rangos_github(datos, sha, mensaje="Actualización de rangos"):
    contenido_nuevo = json.dumps(datos, ensure_ascii=False, indent=2)
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

    datos, _ = leer_rangos_github()
    rangos = datos.get("rangos", {})
    emotes = datos.get("emotes", {})

    def agregar_emote(juego, rango):
        emote = emotes.get(juego.lower(), "")
        return f"{rango} {emote}" if emote else rango

    for juego, rango in rangos.items():
        if juego.lower() == juego_actual.lower():
            rango_emotivo = agregar_emote(juego, rango)
            return f"El rango actual de Nephu en {juego} ➜ {rango_emotivo}"

    # Si no está, mostrar todos con emotes
    respuesta = [
        f"{j} ➜ {agregar_emote(j, r)}"
        for j, r in rangos.items()
    ]
    return " | ".join(respuesta)

@app.route("/setrango", methods=["GET", "POST"])
def set_rango():
    token = request.args.get("token")
    data = request.args.get("data", "")

    if token != SECRET_TOKEN:
        return "No autorizado."

    if "," not in data:
        return "❌ Formato incorrecto. Usa: juego, rango"

    juego_input, nuevo_rango = [x.strip() for x in data.split(",", 1)]

    if not juego_input or not nuevo_rango:
        return "❌ Faltan datos. Asegúrate de escribir: juego, rango"

    datos, sha = leer_rangos_github()
    rangos = datos.get("rangos", {})

    # Buscar juego en rangos ignorando mayúsculas/minúsculas
    juego_clave = None
    for clave in rangos.keys():
        if clave.lower() == juego_input.lower():
            juego_clave = clave
            break

    if juego_clave:
        # Actualizar rango en la clave encontrada
        datos["rangos"][juego_clave] = nuevo_rango
    else:
        # Si no existe, agregar con el nombre tal cual lo escribió el usuario
        if "rangos" not in datos:
            datos["rangos"] = {}
        datos["rangos"][juego_input] = nuevo_rango

    exito = guardar_rangos_github(datos, sha, mensaje=f"Actualización rango {juego_input}")

    if exito:
        return f"✅ Rango de {juego_input} actualizado a: {nuevo_rango}"
    else:
        return "Error actualizando rangos en GitHub."


@app.route("/addrango", methods=["GET", "POST"])
def add_rango():
    token = request.args.get("token")
    data = request.args.get("data", "")

    if token != SECRET_TOKEN:
        return "No autorizado."

    partes = [x.strip() for x in data.split(",", 2)]
    if len(partes) != 3:
        return "❌ Formato incorrecto. Usa: juego, rango, emote"

    juego, nuevo_rango, nuevo_emote = partes

    if not juego or not nuevo_rango or not nuevo_emote:
        return "❌ Faltan datos. Asegúrate de escribir: juego, rango, emote"

    datos, sha = leer_rangos_github()
    if "rangos" not in datos:
        datos["rangos"] = {}
    if "emotes" not in datos:
        datos["emotes"] = {}

    # Añade juego + rango
    datos["rangos"][juego] = nuevo_rango
    # Añade o actualiza emote
    datos["emotes"][juego.lower()] = nuevo_emote

    exito = guardar_rangos_github(datos, sha, mensaje=f"Agregado rango y emote para {juego}")

    if exito:
        return f"✅ Juego {juego} añadido con rango y emote."
    else:
        return "Error guardando juego y emote en GitHub."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
