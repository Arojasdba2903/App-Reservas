import os
import requests
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)

# --- Configuración de Conexiones ---
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# URL de tu flujo de Power Automate (Asegúrate de que sea la del disparador HTTP)
TEAMS_WEBHOOK_URL = "https://default51d73d7c33864091abf09f53c878c6.d5.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/6e4e76f7ce9b43a3b931c0576160376f/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Yfz5As0okOdm6xtVlTSQ5DqGJ1CYKlIOMQqKPS56_kc"

def enviar_alerta_teams(datos):
    """
    Envía los datos puros a Power Automate para agendar en Outlook.
    IMPORTANTE: No enviamos código de tarjeta (JSON complejo) desde aquí 
    para evitar errores de tipo 'Null'.
    """
    try:
        # Enviamos el diccionario de datos tal cual lo recibimos
        response = requests.post(TEAMS_WEBHOOK_URL, json=datos)
        print(f"Estado envío Power Automate: {response.status_code}")
    except Exception as e:
        print(f"Error al notificar al flujo: {e}")

# --- RUTA 1: Página principal ---
@app.route('/')
def inicio():
    try:
        # Consultar fechas disponibles
        respuesta = supabase.table("dias_disponibles").select("*").eq("estado", "Disponible").order("fecha").execute()
        fechas = respuesta.data
        return render_template('index.html', fechas=fechas)
    except Exception as e:
        return f"Error de conexión: {str(e)}"

# --- RUTA 2: Proceso de Reserva ---
@app.route('/reservar', methods=['POST'])
def reservar():
    datos = request.json
    try:
        # 1. Guardar en la tabla de registros
        supabase.table("reservas_clientes").insert({
            "nombre": datos["nombre"],
            "correo": datos["correo"],
            "telefono": datos["telefono"],
            "modalidad": datos["modalidad"],
            "servicio": datos["servicio"],
            "cargo": datos.get("cargo", ""),
            "notas": datos.get("notas", ""),
            "fecha_reserva": datos["fecha"]
        }).execute()
        
        # 2. Bloquear la fecha en la tabla de disponibilidad
        supabase.table("dias_disponibles").update({"estado": "Ocupado"}).eq("fecha", datos["fecha"]).execute()
        
        # 3. Disparar el flujo de Power Automate (Datos puros)
        enviar_alerta_teams(datos)
        
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error en reserva: {e}")
        return jsonify({"status": "error", "mensaje": str(e)})

if __name__ == '__main__':
    app.run(debug=True)
