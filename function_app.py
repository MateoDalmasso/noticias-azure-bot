import azure.functions as func
import logging
import platform
import os # Necesario para leer la variable segura

app = func.FunctionApp()

@app.schedule(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=True, use_monitor=False) 
def NoticiasTimer(myTimer: func.TimerRequest) -> None:
    import pyodbc
    import requests
    from datetime import datetime

    # --- 1. RECUPERAR SECRETOS ---
    # Esto lee directo de la configuración de Azure.
    # Si falla aquí, es que la variable "SQL_PASSWORD" no está creada o tiene un espacio extra.
    try:
        password = os.environ["SQL_PASSWORD"]
    except KeyError:
        logging.error("❌ ERROR CRÍTICO: No se encontró la variable SQL_PASSWORD en Azure.")
        return

    # --- 2. CONFIGURACIÓN ---
    API_KEY = 'ca8e97d988914a44ab070688009916f4' 
    server = 'sql-server-noticias-mateo-v2.database.windows.net'
    database = 'db_noticias'
    
    # ⚠️ VERIFICA ESTO EN EL PORTAL DE AZURE -> SQL SERVER ⚠️
    # Asegúrate de que tu usuario administrador sea EXACTAMENTE este:
    username = 'adminusuario' 
    
    driver = '{ODBC Driver 18 for SQL Server}'
    
    # --- 3. CONEXIÓN ---
    # Agregamos impresiones de seguridad (ocultando la contraseña real)
    logging.info(f"Intentando conectar a {server} con usuario {username}...")

    conn_str = (
        f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};'
        f'UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;'
    )
    
    try:
        with pyodbc.connect(conn_str) as conn:
            logging.info("✅ ¡CONEXIÓN EXITOSA A LA BASE DE DATOS!")
            
            # Si llegamos aquí, la contraseña funcionó. Ahora la API.
            url = f'https://newsapi.org/v2/everything?q=bitcoin&language=es&apiKey={API_KEY}'
            response = requests.get(url)
            articulos = response.json().get('articles', [])[:5]

            with conn.cursor() as cursor:
                cursor.execute('''
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='noticias' AND xtype='U')
                    CREATE TABLE noticias (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        titulo NVARCHAR(MAX),
                        fuente NVARCHAR(255),
                        fecha_publicacion NVARCHAR(100),
                        fecha_carga DATETIME DEFAULT GETDATE()
                    )
                ''')

                contador = 0
                for art in articulos:
                    cursor.execute('''
                        INSERT INTO noticias (titulo, fuente, fecha_publicacion)
                        VALUES (?, ?, ?)
                    ''', art['title'], art['source']['name'], art['publishedAt'])
                    contador += 1
                
                conn.commit()
        
        logging.info(f"✅ ¡VICTORIA! Se guardaron {contador} noticias.")
    
    except Exception as e:
        logging.error(f"❌ Error de conexión: {e}")






