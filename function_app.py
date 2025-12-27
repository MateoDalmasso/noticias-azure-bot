import azure.functions as func
import logging
import pyodbc
import requests
from datetime import datetime

app = func.FunctionApp()

# Este "Timer" hará que se ejecute solo
@app.schedule(schedule="0 0 9 * * *", arg_name="myTimer", run_on_startup=True, use_monitor=False) 
def NoticiasTimer(myTimer: func.TimerRequest) -> None:
    if myTimer.past_due:
        logging.info('El timer está retrasado.')

    # --- CONFIGURACIÓN (Usa tus datos) ---
    API_KEY = 'ca8e97d988914a44ab070688009916f4'
    server = 'sql-server-noticias-mateo-v2.database.windows.net'
    database = 'db_noticias'
    username = 'adminusuario'
    password = 'MateoDal13!' 
    # IMPORTANTE: En Azure Linux el driver se llama así:
    driver = '{ODBC Driver 18 for SQL Server}' 

    logging.info('Iniciando extracción de noticias...')

    # 1. Obtener Datos
    url = f'https://newsapi.org/v2/everything?q=bitcoin&language=es&apiKey={API_KEY}'
    try:
        response = requests.get(url)
        articulos = response.json().get('articles', [])[:5]

        # 2. Conexión e Inserción
        conn_str = f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}'
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                for art in articulos:
                    cursor.execute('''
                        INSERT INTO noticias (titulo, fuente, fecha_publicacion)
                        VALUES (?, ?, ?)
                    ''', art['title'], art['source']['name'], art['publishedAt'])
                conn.commit()
        
        logging.info(f"✅ Se insertaron {len(articulos)} noticias exitosamente.")
    
    except Exception as e:
        logging.error(f"❌ Error en la función: {e}")