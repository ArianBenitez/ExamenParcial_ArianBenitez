import socket
import threading
import json
from server.db import init_db, Session
from server.models import ResultadoNReinas, ResultadoKnightTour, ResultadoHanoi
from datetime import datetime

HOST = "0.0.0.0"
PORT = 5000
BUFFER_SIZE = 4096
SEPARATOR = "\n"

def handle_client(conn, addr):
    print(f"[+] Conexión entrante de {addr}")
    buffer = ""
    while True:
        data = conn.recv(BUFFER_SIZE).decode("utf-8")
        if not data:
            break
        buffer += data
        while SEPARATOR in buffer:
            line, buffer = buffer.split(SEPARATOR, 1)
            try:
                msg = json.loads(line)
                print(f"[DEBUG] Mensaje recibido: {msg}")
                acción = msg.get("acción")
                
                if acción == "guardar_resultado":
                    salvar_resultado(msg)
                    resp = {
                        "acción": "confirmación",
                        "status": "ok",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "mensaje": "Resultado guardado"
                    }
                elif acción == "solicitar_mejores":
                    top = consultar_top(msg["juego"])
                    resp = {
                        "acción": "confirmación",
                        "status": "ok",
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "mejores": top
                    }
                else:
                    resp = {
                        "acción": "error",
                        "error": {"code":400, "mensaje":"Acción desconocida"},
                        "timestamp": datetime.utcnow().isoformat() + "Z"
                    }
            except Exception as e:
                resp = {
                    "acción": "error",
                    "error": {"code":500, "mensaje": str(e)},
                    "timestamp": datetime.utcnow().isoformat() + "Z"
                }
            conn.sendall((json.dumps(resp) + SEPARATOR).encode('utf-8'))
    conn.close()
    print(f"[-] Conexión cerrada {addr}")

def salvar_resultado(msg: dict):
    juego = msg["juego"]
    datos = msg["datosPartida"]
    sesión = Session()

    # Convertir timestamp ISO -> datetime
    ts = datetime.fromisoformat(msg["timestamp"].replace("Z", ""))

    if juego == "nreinas":
        r = ResultadoNReinas(
            N=datos["N"],
            resuelto=datos["resuelto"],
            intentos=datos["intentos"],
            timestamp=ts
        )
    elif juego == "caballo":
        r = ResultadoKnightTour(
            posicion_inicial=datos.get("posicion_inicial", ""),
            movimientos=datos["movimientos"],
            completado=datos["completado"],
            timestamp=ts
        )
    elif juego == "hanoi":
        r = ResultadoHanoi(
            discos=datos["discos"],
            movimientos=datos["movimientos"],
            completado=datos["completado"],
            timestamp=ts
        )
    else:
        sesión.close()
        raise ValueError("Juego no reconocido")

    print(f"[DEBUG] Guardando en DB: {r}")
    sesión.add(r)
    sesión.commit()
    sesión.close()

def consultar_top(juego: str, limit: int = 5):
    sesión = Session()
    if juego == "nreinas":
        q = sesión.query(ResultadoNReinas).filter_by(resuelto=True).order_by(ResultadoNReinas.intentos).limit(limit)
    elif juego == "caballo":
        q = sesión.query(ResultadoKnightTour).filter_by(completado=True).order_by(ResultadoKnightTour.movimientos).limit(limit)
    elif juego == "hanoi":
        q = sesión.query(ResultadoHanoi).filter_by(completado=True).order_by(ResultadoHanoi.movimientos).limit(limit)
    else:
        sesión.close()
        raise ValueError("Juego no reconocido")

    resultado = [
        {col.name: getattr(r, col.name) for col in r.__table__.columns}
        for r in q
    ]
    sesión.close()
    return resultado

def start_server():
    init_db()  # crea tablas si no existen
    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.bind((HOST, PORT))
    serv.listen()
    print(f"Servidor escuchando en {HOST}:{PORT}")
    while True:
        conn, addr = serv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
