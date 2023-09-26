from connection_manager import ws_manager
import asyncio
mensajes = []
def printt(message):
    print(message)
    mensajes.append(message)
    
def send():
    for message in mensajes:
        message = str(message)
        message=message.replace("<", " ")
        loop = asyncio.get_running_loop()  # This line is adjusted
        asyncio.run_coroutine_threadsafe(ws_manager.send_log_message(str(message)), loop)
    mensajes.clear()