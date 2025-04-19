# Máquina Arcade Distribuida

Una mini-plataforma cliente-servidor en Python que integra tres puzzles clásicos:
- **N‑Reinas**  
- **Knight’s Tour**  
- **Torres de Hanói**

## 🎯 Objetivo

Practicar:
- Arquitectura cliente‑servidor (sockets TCP + JSON)  
- Programación Orientada a Objetos  
- Concurrencia con hilos  
- Interfaces gráficas con Pygame  
- Persistencia con SQLite y SQLAlchemy  

---

## ⚙️ Requisitos

- Python ≥ 3.7  
- [Pygame](https://www.pygame.org/)  
- [SQLAlchemy](https://www.sqlalchemy.org/)  

Instala dependencias:

```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 📁 Estructura de carpetas

```
arcade_distribuida/
├── server/
│   ├── __init__.py
│   ├── main.py           # Servidor TCP + ORM + consultas top5
│   ├── models.py         # Modelos SQLAlchemy
│   └── db.py             # Init de SQLite
├── client/
│   ├── common/
│   │   ├── __init__.py
│   │   ├── communication.py   # send/recv JSON
│   │   ├── threading_utils.py # helpers de hilos
│   │   └── base_cliente.py    # Menú + “Mejores tiempos”
│   ├── nreinas/
│   │   ├── __init__.py
│   │   └── nreinas.py         # Juego N‑Reinas
│   ├── caballo/
│   │   ├── __init__.py
│   │   └── caballo.py         # Juego Knight’s Tour
│   └── hanoi/
│       ├── __init__.py
│       └── hanoi.py           # Juego Torres de Hanói
├── resultados.db         # Base de datos SQLite (se crea al arrancar)
├── requirements.txt
└── README.md
```

---

## 🚀 Ejecución

1. **Arranca el servidor**  
   ```bash
   cd arcade_distribuida
   python -m server.main
   ```  
   Verás en consola: `Servidor escuchando en 0.0.0.0:5000`.

2. **Lanza el menú de juegos**  
   En otra terminal (mismo venv):
   ```bash
   cd arcade_distribuida
   python -m client.common.base_cliente
   ```  
   - Usa ↑/↓ para navegar y Enter para seleccionar.  
   - Selecciona un puzzle, introduce parámetros (N o nº discos) en consola, y ¡a jugar!  
   - Tras completar o cerrar, el resultado se guarda en la BD.

3. **Ver mejores tiempos**  
   En el mismo menú:  
   - `Ver mejores tiempos` → elige el juego → verás el top 5 formateado.  
   - Pulsa cualquier tecla o clic para volver al menú.

---

## 🗃️ Inspeccionar la base de datos

Si quieres verlo por consola sin instalar sqlite3, usa:

```bash
python ver_resultados.py
```

(Primero crea ese script con el código que te pasé.)

---

## 📄 Licencia y créditos

Proyecto de práctica académica — ¡diviértete con tu propia Máquina Arcade Distribuida!  

---

**Fecha de entrega:** 2025‑05‑04  