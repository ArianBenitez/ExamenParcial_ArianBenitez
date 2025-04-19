# ver_resultados.py
import sqlite3
from pprint import pprint

def mostrar_tabla(cur, nombre):
    cur.execute(f"PRAGMA table_info({nombre});")
    cols = [row[1] for row in cur.fetchall()]
    cur.execute(f"SELECT * FROM {nombre};")
    filas = cur.fetchall()
    print(f"\n=== {nombre} ===")
    print(cols)
    pprint(filas)

def main():
    db = sqlite3.connect("resultados.db")
    cur = db.cursor()
    for tabla in ("nreinas", "knight_tour", "hanoi"):
        mostrar_tabla(cur, tabla)
    db.close()

if __name__ == "__main__":
    main()
