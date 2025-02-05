from flask import Flask, request, jsonify, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Inicialización de la aplicación Flask
app = Flask(__name__)

# Configuración de las credenciales y alcance para Google Sheets API
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Cargar las credenciales desde el archivo JSON y autorizar el cliente
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
client = gspread.authorize(creds)

# ID de tu hoja de cálculo de Google Sheets
SPREADSHEET_ID = "12QkCMOhlTXr6-3upKgXoQ3mISWpG42YTzAhUIVVpHpQ"

def agregar_registro(mes, categoria, descripcion, precio):
    """
    Función para agregar un nuevo registro de gasto a la hoja de cálculo.
    
    Args:
        mes (str): Nombre del mes (se convertirá a mayúsculas para coincidir con la hoja)
        categoria (str): Categoría del gasto (comida, transporte, otros)
        descripcion (str): Descripción del gasto
        precio (int): Valor del gasto en miles de pesos colombianos
    
    Returns:
        str: Mensaje indicando el resultado de la operación
    """
    # Abrir la hoja de cálculo por su ID
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    
    try:
        # Convertir el nombre del mes completamente a mayúsculas
        mes_upper = mes.upper()
        # Intentar abrir la hoja correspondiente al mes
        sheet = spreadsheet.worksheet(mes_upper)
    except gspread.exceptions.WorksheetNotFound:
        return f"Hoja del mes {mes_upper} no encontrada"
    
    # Obtener la fecha actual en formato YYYY-MM-DD
    fecha_actual = datetime.now().strftime("%Y-%m-%d")
    
    # Definir la estructura de columnas para cada categoría
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
    
    # Convertir la categoría a minúsculas para evitar errores de capitalización
    categoria = categoria.lower()
    
    # Verificar si la categoría es válida
    if categoria not in columnas:
        return "Categoría inválida"
    
    # Obtener las columnas correspondientes a la categoría
    cols = columnas[categoria]
    
    # Encontrar la primera fila vacía en la columna de fecha de la categoría
    fecha_col = cols["fecha"]
    fila_vacia = len(sheet.col_values(ord(fecha_col) - ord('A') + 1)) + 1
    
    try:
        # Actualizar las celdas con la información del gasto
        sheet.update_acell(f"{cols['fecha']}{fila_vacia}", fecha_actual)
        sheet.update_acell(f"{cols['descripcion']}{fila_vacia}", descripcion)
        sheet.update_acell(f"{cols['precio']}{fila_vacia}", precio)
        
        return "Registro agregado exitosamente"
    except Exception as e:
        return f"Error al agregar el registro: {str(e)}"

@app.route("/")
def index():
    """
    Ruta principal que muestra la página de inicio.
    """
    return render_template("index.html")

@app.route("/agregar", methods=["POST"])
def agregar():
    """
    Ruta para procesar la adición de un nuevo gasto.
    """
    # Obtener los datos enviados en la solicitud
    data = request.json
    
    # Extraer los campos necesarios
    mes = data.get("mes")
    categoria = data.get("categoria")
    descripcion = data.get("descripcion")
    precio = data.get("precio")
    
    # Verificar que todos los campos requeridos estén presentes
    if not all([mes, categoria, descripcion, precio]):
        return jsonify({"error": "Faltan datos requeridos"}), 400
    
    # Intentar agregar el registro
    resultado = agregar_registro(mes, categoria, descripcion, precio)
    
    # Devolver el resultado como JSON
    return jsonify({"mensaje": resultado})

if __name__ == "__main__":
    app.run(debug=True)