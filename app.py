import os
import requests
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

# Cargar variables de entorno (Render las toma de su configuración)
load_dotenv()

app = Flask(__name__)

# --- Configuración de Conexiones ---
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# URL de tu flujo de Power Automate que ya responde con código 202
TEAMS_WEBHOOK_URL = "https://default51d73d7c33864091abf09f53c878c6.d5.environment.api.powerplatform.com:443/powerautomate/automations/direct/workflows/6e4e76f7ce9b43a3b931c0576160376f/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=Yfz5As0okOdm6xtVlTSQ5DqGJ1CYKlIOMQqKPS56_kc"

def enviar_alerta_teams(datos):
    """Envía los datos puros para que Power Automate llene la Tarjeta Adaptable"""
    try:
        # Enviamos el diccionario de datos directamente
        response = requests.post(TEAMS_WEBHOOK_URL, json=datos)
        print(f"Respuesta de Teams: {response.status_code}") # Debe ser 202
    except Exception as e:
        print(f"Error enviando a Teams: {e}")

# --- RUTA 1: Página principal (Carga de fechas disponibles) ---
@app.route('/')
def inicio():
    try:
        # Consultamos fechas con estado 'Disponible' para que el cliente elija
        respuesta = supabase.table("dias_disponibles").select("*").eq("estado", "Disponible").order("fecha").execute()
        fechas = respuesta.data
        return render_template('index.html', fechas=fechas)
    except Exception as e:
        return f"Error en la base de datos: {str(e)}"

# --- RUTA 2: Proceso de Reserva (Agendar y Notificar) ---
@app.route('/reservar', methods=['POST'])
def reservar():
    datos = request.json
    try:
        # 1. PASO: Guardar la reserva en la tabla de clientes
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
        
        # 2. PASO: Bloquear la fecha para que nadie más la tome
        # Esto 'agenda' el espacio oficialmente
        supabase.table("dias_disponibles").update({"estado": "Ocupado"}).eq("fecha", datos["fecha"]).execute()
        
        # 3. PASO: Disparar la notificación elegante a tu Teams
        enviar_alerta_teams(datos)
        
        return jsonify({"status": "success", "mensaje": "Reserva confirmada y agendada"})
    
    except Exception as e:
        print(f"Error en el proceso de reserva: {e}")
        return jsonify({"status": "error", "mensaje": str(e)})

if __name__ == '__main__':
    # Render asigna el puerto automáticamente
    app.run(debug=True)
