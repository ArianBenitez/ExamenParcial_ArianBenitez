# Máquina Arcade Distribuida

Este proyecto es una **Máquina Arcade Distribuida** implementada en Python con Pygame, que incluye tres juegos clásicos:

1. **N-Reinas** (N-Reinas)
2. **Knight’s Tour** (Caballo)
3. **Torres de Hanói** (Hanoi)

Cada cliente (frontend) corre con Pygame y se comunica con un servidor backend mediante sockets TCP y JSON. Además, cuenta con un sistema de "Ayuda IA" que combina:

* **Sugerencias algorítmicas** (solver) garantizadas para los puzzles.
* **Chat libre** alimentado por un modelo local de DialoGPT-medium (cargado con `transformers + torch`).

## Estructura del Proyecto

```
arcade_distribuida/
├── client/
│   ├── common/
│   │   ├── communication.py    # Socket+JSON
│   │   ├── threading_utils.py  # Decorador @run_async
│   │   └── ia_client.py        # Pipeline local de IA
│   ├── nreinas/
│   │   └── nreinas.py          # Cliente N-Reinas con chat y solver
│   ├── caballo/
│   │   └── caballo.py          # Cliente Knight’s Tour con heurística Warnsdorff
│   └── hanoi/
│       └── hanoi.py            # Cliente Torres de Hanói con secuencia óptima
├── server/
│   ├── db.py                   # SQLite + SQLAlchemy
│   ├── models.py               # ORM: Resultados
│   └── main.py                 # Servidor TCP multihilo
├── resultados.db               # Base de datos SQLite
├── requirements.txt            # Dependencias Python
└── README.md                   # Documentación (este archivo)
```

## Requisitos

* Python 3.8+
* Pygame
* Transformers
* Torch
* SQLAlchemy

Instalar con:

```bash
pip install -r requirements.txt
```

`requirements.txt` incluye al menos:

```
pygame
transformers
torch
sqlalchemy
```

## Uso

1. Iniciar el servidor (en la raíz del proyecto):

   ```bash
   python server/main.py
   ```
2. En otra terminal, lanzar el menú principal:

   ```bash
   python client/common/base_client.py
   ```
3. Navegar el menú con **↑ ↓** y **Enter**.
4. Elegir un juego:

   * **N-Reinas**: pide N en pantalla y permite colocar/quitar reinas.
   * **Knight’s Tour**: clicar para elegir inicio y mover caballo.
   * **Torres de Hanói**: clicar en pilar origen/destino.

### Controles del chat / "Ayuda IA"

* Pulsar **TAB** o clicar el botón **Ayuda IA** para abrir el chat.
* Escribir libremente en la caja inferior y pulsar **Enter** para enviar.
* Escribir palabras clave como **"siguiente"**, **"movimiento"** o **"posición"** para recibir la **sugerencia algorítmica** (siguiente jugada garantizada).
* Para cualquier otra consulta, el chat responde usando el modelo local de DialoGPT.
* Pulsar **ESC** para cerrar el chat y retomar el juego.

## Servidor y Base de Datos

* El servidor usa **SQLite** (`resultados.db`) y **SQLAlchemy**.
* Registra cada partida con juego, parámetros, éxito/fallo, movimientos/intentos y timestamp.
* Permite consultar el **Top 5** de mejores resultados por juego.

  * En el menú: elegir **Ver mejores tiempos**.

## IA Local

* Utiliza `transformers` con `microsoft/DialoGPT-medium` en local.
* No requiere clave de API ni llamadas externas; todo corre en tu máquina.
* El pipeline se inicializa bajo demanda y responde en un hilo separado para no bloquear la UI.

---

**¡Disfruta de tu Máquina Arcade Distribuida con IA integrada!**
