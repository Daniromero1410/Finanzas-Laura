import os
import json
from flask import Flask, request, jsonify, render_template
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from functools import wraps
import time

# Inicialización de la aplicación Flask
app = Flask(__name__)

# Configuración de las credenciales y alcance para Google Sheets API
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Obtener credenciales desde variables de entorno
try:
    creds_dict = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(creds)
except Exception as e:
    print(f"Error al configurar credenciales: {str(e)}")
    raise

# ID de la hoja de cálculo desde variables de entorno
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID', "12QkCMOhlTXr6-3upKgXoQ3mISWpG42YTzAhUIVVpHpQ")

def retry_on_exception(retries=3, delay=1):
    """
    Decorador para reintentar funciones que pueden fallar debido a problemas de red
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for i in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if i == retries - 1:
                        print(f"Error después de {retries} intentos: {str(e)}")
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

@retry_on_exception(retries=3)
def agregar_registro(mes, categoria, descripcion, precio):
    """
    Función para agregar un nuevo registro de gasto a la hoja de cálculo.
    
    Args:
        mes (str): Nombre del mes (se convertirá a mayúsculas)
        categoria (str): Categoría del gasto (comida, transporte, otros)
        descripcion (str): Descripción del gasto
        precio (int): Valor del gasto en miles de pesos colombianos
    
    Returns:
        str: Mensaje indicando el resultado de la operación
    """
    try:
        # Abrir la hoja de cálculo
        spreadsheet = client.open_by_key(SPREADSHEET_ID)
        
        # Convertir el mes a mayúsculas y obtener la hoja
        mes_upper = mes.upper()
        sheet = spreadsheet.worksheet(mes_upper)
        
        # Obtener fecha actual
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        
        # Estructura de columnas por categoría
        columnas = {
            "comida": {
                "fecha": "A",
                "descripcion": "B",
                "precio": "C"
            },
            "otros": {
                "fecha": "D",
                "descripcion": "E",
                "precio": "F"
            },
            "transporte": {
                "fecha": "G",
                "descripcion": "H",
                "precio": "I"
            }
        }
        
        # Validar y procesar categoría
        categoria = categoria.lower()
        if categoria not in columnas:
            return "Categoría inválida"
        
        # Obtener columnas para la categoría
        cols = columnas[categoria]
        
        # Encontrar primera fila vacía
        fecha_col = cols["fecha"]
        fila_vacia = len(sheet.col_values(ord(fecha_col) - ord('A') + 1)) + 1
        
        # Actualizar celdas
        actualizaciones = [
            {
                'range': f"{cols['fecha']}{fila_vacia}",
                'values': [[fecha_actual]]
            },
            {
                'range': f"{cols['descripcion']}{fila_vacia}",
                'values': [[descripcion]]
            },
            {
                'range': f"{cols['precio']}{fila_vacia}",
                'values': [[precio]]
            }
        ]
        
        # Realizar todas las actualizaciones en batch
        sheet.batch_update(actualizaciones)
        
        return "Registro agregado exitosamente"
        
    except gspread.exceptions.WorksheetNotFound:
        return f"Hoja del mes {mes_upper} no encontrada"
    except Exception as e:
        return f"Error al agregar el registro: {str(e)}"

@app.route("/")
def index():
    """Ruta principal que muestra la página de inicio."""
    return render_template("index.html")

@app.route("/agregar", methods=["POST"])
def agregar():
    """Ruta para procesar la adición de un nuevo gasto."""
    try:
        # Validar el tipo de contenido
        if not request.is_json:
            return jsonify({"error": "El contenido debe ser JSON"}), 400

        # Obtener y validar datos
        data = request.json
        requeridos = ["mes", "categoria", "descripcion", "precio"]
        for campo in requeridos:
            if campo not in data:
                return jsonify({"error": f"Falta el campo requerido: {campo}"}), 400
        
        # Validar tipos de datos
        if not isinstance(data["precio"], (int, float)):
            return jsonify({"error": "El precio debe ser un número"}), 400
        
        # Intentar agregar el registro
        resultado = agregar_registro(
            data["mes"],
            data["categoria"],
            data["descripcion"],
            data["precio"]
        )
        
        return jsonify({"mensaje": resultado})
        
    except Exception as e:
        return jsonify({"error": f"Error interno del servidor: {str(e)}"}), 500

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Recurso no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Error interno del servidor"}), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)