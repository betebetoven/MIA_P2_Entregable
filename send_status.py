from connection_manager_status import ws_manager_status
import asyncio
mensajes_status = []
def printt_status(message):
    print(message)
    mensajes_status.append(message)
    
def send_status():
    for message in mensajes_status:
        message = str(message)
        message=message.replace("<", " ")
        loop = asyncio.get_running_loop()  # This line is adjusted
        asyncio.run_coroutine_threadsafe(ws_manager_status.send_log_message(str(message)), loop)
    mensajes_status.clear()