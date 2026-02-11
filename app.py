import os
import requests
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# --- Configuración de Conexiones ---
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Tu URL de Teams (Webhook)
TEAMS_WEBHOOK_URL = "https://default51d73d7c33864091abf09f53c878c6.d5.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/6e4e76f7ce9b43a3b931c0576160376f/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Yfz5As0okOdm6xtVlTSQ5DqGJ1CYKlIOMQqKPS56_kc"

def enviar_alerta_teams(datos):
    """Envia notificación simplificada a Teams para máxima compatibilidad"""
    try:
        # Formato de texto enriquecido simple
        texto_alerta = (
            f"🔔 **¡Nueva Reserva Recibida!**\n\n"
            f"👤 **Cliente:** {datos['nombre']}\n"
            f"📅 **Fecha:** {datos['fecha']}\n"
            f"📧 **Correo:** {datos['correo']}\n"
            f"💼 **Servicio:** {datos['servicio']}\n"
            f"📍 **Modalidad:** {datos['modalidad']}\n"
            f"📝 **Notas:** {datos.get('notas', 'Sin notas')}"
        )
        
        mensaje = {
            "text": texto_alerta
        }
        
        response = requests.post(TEAMS_WEBHOOK_URL, json=mensaje)
        print(f"Respuesta de Teams: {response.status_code}")
    except Exception as e:
        print(f"Error enviando a Teams: {e}")

# --- RUTA 1: Mostrar la página ---
@app.route('/')
def inicio():
    try:
        respuesta = supabase.table("dias_disponibles").select("*").eq("estado", "Disponible").order("fecha").execute()
        fechas = respuesta.data
        return render_template('index.html', fechas=fechas)
    except Exception as e:
        return f"Error en la base de datos: {str(e)}"

# --- RUTA 2: Recibir y guardar la reserva ---
@app.route('/reservar', methods=['POST'])
def reservar():
    datos = request.json
    try:
        # 1. Guardar los datos del cliente en Supabase
        supabase.table("reservas_clientes").insert({
            "nombre": datos["nombre"],
            "correo": datos["correo"],
            "telefono": datos["telefono"],
            "modalidad": datos["modalidad"],
            "servicio": datos["servicio"],
            "cargo": datos["cargo"],
            "notas": datos["notas"],
            "fecha_reserva": datos["fecha"]
        }).execute()
        
        # 2. Bloquear la fecha
        supabase.table("dias_disponibles").update({"estado": "Ocupado"}).eq("fecha", datos["fecha"]).execute()
        
        # 3. ENVIAR ALERTA A TEAMS
        enviar_alerta_teams(datos)
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
