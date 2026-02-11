import os
from flask import Flask, render_template, request, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# --- RUTA 1: Mostrar la página ---
@app.route('/')
def inicio():
    try:
        # Buscar fechas disponibles
        respuesta = supabase.table("dias_disponibles").select("*").eq("estado", "Disponible").order("fecha").execute()
        fechas = respuesta.data
        # ¡Aquí conectamos con tu diseño HTML!
        return render_template('index.html', fechas=fechas)
    except Exception as e:
        return f"Error en la base de datos: {str(e)}"

# --- RUTA 2: Recibir y guardar la reserva ---
@app.route('/reservar', methods=['POST'])
def reservar():
    datos = request.json
    try:
        # 1. Guardar los datos del cliente
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
        
        # 2. Bloquear la fecha (cambiar a Ocupado)
        supabase.table("dias_disponibles").update({"estado": "Ocupado"}).eq("fecha", datos["fecha"]).execute()
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)})

if __name__ == '__main__':
    app.run(debug=True)