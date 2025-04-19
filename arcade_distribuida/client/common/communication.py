import socket
import json
import threading
import time

BUFFER_SIZE = 4096
SEPARATOR = "\n"

def connect(host="localhost", port=5000, retries=3, delay=2):
    """
    Intenta conectar al servidor con reintentos.
    Devuelve el socket conectado o lanza excepción si falla.
    """
    for attempt in range(retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            return sock
        except socket.error as e:
            if attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e

def send_message(message: dict, sock: socket.socket):
    """
    Serializa y envía un mensaje JSON terminado en '\n'.
    """
    payload = json.dumps(message) + SEPARATOR
    sock.sendall(payload.encode("utf-8"))

def receive_message(sock: socket.socket) -> dict:
    """
    Lee del socket hasta encontrar '\n', luego parsea el JSON y lo devuelve.
    """
    buffer = ""
    while SEPARATOR not in buffer:
        data = sock.recv(BUFFER_SIZE).decode("utf-8")
        if not data:
            raise ConnectionError("Conexión cerrada por el servidor")
        buffer += data
    line, _ = buffer.split(SEPARATOR, 1)
    return json.loads(line)

def send_and_receive(message: dict, host="localhost", port=5000) -> dict:
    """
    Función de conveniencia: conecta, envía y recibe respuesta.
    """
    sock = connect(host, port)
    try:
        send_message(message, sock)
        return receive_message(sock)
    finally:
        sock.close()
