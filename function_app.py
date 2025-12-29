import azure.functions as func
import logging
import platform

app = func.FunctionApp()

@app.schedule(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=True, use_monitor=False) 
def NoticiasTimer(myTimer: func.TimerRequest) -> None:
    import pyodbc
    import requests
    from datetime import datetime
    import os

    if myTimer.past_due:
        logging.info('El timer está retrasado.')

    # --- 1. CONFIGURACIÓN ---
    # API Key (Tu clave real)
    API_KEY = 'ca8e97d988914a44ab070688009916f4' 
    
    server = 'sql-server-noticias-mateo-v2.database.windows.net'
    database = 'db_noticias'
    username = 'adminusuario'
    
    # ⚠️ RECUERDA PONER TU CONTRASEÑA AQUÍ O USAR os.environ SI YA LA CONFIGURASTE ⚠️
    password = 'TU_CONTRASEÑA_NUEVA_AQUI' 
    
    # --- 2. SELECCIÓN DE DRIVER (CAMBIO IMPORTANTE) ---
    sistema = platform.system()
    
    # En Azure (Linux) y Windows moderno, usaremos el Driver 18
    # El Driver 17 a veces no está presente en las imágenes nuevas de Azure
    driver = '{ODBC Driver 18 for SQL Server}'
    
    logging.info(f"Sistema detectado: {sistema}. Intentando conexión con {driver}")

    # --- 3. LÓGICA ---
    url = f'https://newsapi.org/v2/everything?q=bitcoin&language=es&apiKey={API_KEY}'
    
    try:
        response = requests.get(url)
        articulos = response.json().get('articles', [])[:5]

        if not articulos:
            logging.warning("No se encontraron noticias.")
            return

        # --- CONEXIÓN (ACTUALIZADA PARA DRIVER 18) ---
        # Driver 18 requiere 'TrustServerCertificate=yes' para conexiones Azure rápidas
        conn_str = (
            f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};'
            f'UID={username};PWD={password};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=30;'
        )
        
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                # Crear tabla
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

                # Insertar
                contador = 0
                for art in articulos:
                    cursor.execute('''
                        INSERT INTO noticias (titulo, fuente, fecha_publicacion)
                        VALUES (?, ?, ?)
                    ''', art['title'], art['source']['name'], art['publishedAt'])
                    contador += 1
                
                conn.commit()
        
        logging.info(f"✅ ¡VICTORIA! Se insertaron {contador} noticias en la base de datos.")
    
    except Exception as e:
        # Este log nos dirá exactamente qué pasa si falla de nuevo
        logging.error(f"❌ Error detallado: {e}")





