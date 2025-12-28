import azure.functions as func
import logging
import platform # Para detectar si es Windows o Linux

app = func.FunctionApp()

@app.schedule(schedule="0 0 9 * * *", arg_name="myTimer", run_on_startup=True, use_monitor=False) 
def NoticiasTimer(myTimer: func.TimerRequest) -> None:
    # --- 1. IMPORTS DENTRO DE LA FUNCIÓN ---
    # Esto evita errores de arranque en Azure
    import pyodbc
    import requests
    from datetime import datetime

    if myTimer.past_due:
        logging.info('El timer está retrasado.')

    # --- 2. CONFIGURACIÓN ---
    # He puesto tu API Key real aquí:
    API_KEY = 'ca8e97d988914a44ab070688009916f4' 
    
    server = 'sql-server-noticias-mateo-v2.database.windows.net'
    database = 'db_noticias'
    username = 'adminusuario'
    
    # ⚠️ CAMBIA ESTO POR TU NUEVA CONTRASEÑA ⚠️
    password = 'MateoDal16!'
    
    # --- 3. SELECCIÓN INTELIGENTE DE DRIVER ---
    # Si detecta Windows (tu PC), usa el 18. Si es Linux (Azure), usa el 17.
    sistema = platform.system()
    if sistema == 'Windows':
        driver = '{ODBC Driver 18 for SQL Server}'
        logging.info("Sistema Windows detectado: Usando Driver 18")
    else:
        driver = '{ODBC Driver 17 for SQL Server}'
        logging.info("Sistema Linux/Azure detectado: Usando Driver 17")

    logging.info('Iniciando extracción de noticias...')

    # --- 4. LÓGICA DE EXTRACCIÓN Y CARGA ---
    url = f'https://newsapi.org/v2/everything?q=bitcoin&language=es&apiKey={API_KEY}'
    
    try:
        # Petición a la API
        response = requests.get(url)
        articulos = response.json().get('articles', [])[:5] # Tomamos 5 noticias

        if not articulos:
            logging.warning("No se encontraron noticias en la API.")
            return

        # Cadena de conexión
        conn_str = f'DRIVER={driver};SERVER={server};PORT=1433;DATABASE={database};UID={username};PWD={password}'
        
        # Conexión a la Base de Datos
        with pyodbc.connect(conn_str) as conn:
            with conn.cursor() as cursor:
                # Crear tabla si no existe
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

                # Insertar datos
                contador = 0
                for art in articulos:
                    cursor.execute('''
                        INSERT INTO noticias (titulo, fuente, fecha_publicacion)
                        VALUES (?, ?, ?)
                    ''', art['title'], art['source']['name'], art['publishedAt'])
                    contador += 1
                
                conn.commit()
        
        logging.info(f"✅ ¡ÉXITO TOTAL! Se insertaron {contador} noticias usando el driver: {driver}")
    
    except Exception as e:
        logging.error(f"❌ Error en la función: {e}")




