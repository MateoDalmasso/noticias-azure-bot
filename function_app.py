import azure.functions as func
import logging

app = func.FunctionApp()

@app.schedule(schedule="0 */5 * * * *", arg_name="myTimer", run_on_startup=True, use_monitor=False) 
def NoticiasTimer(myTimer: func.TimerRequest) -> None:
    logging.info('¡Prueba de vida exitosa! La función se ha cargado correctamente.')


