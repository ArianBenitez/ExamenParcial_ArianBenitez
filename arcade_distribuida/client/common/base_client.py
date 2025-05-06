# client/common/base_client.py

import pygame
import sys
import time
from datetime import datetime
from client.nreinas.nreinas import main as nreinas_main
from client.caballo.caballo import main as caballo_main
from client.hanoi.hanoi import main as hanoi_main
from client.common.communication import send_and_receive

# Configuración de ventana
WINDOW_WIDTH, WINDOW_HEIGHT = 600, 400
FPS = 60

MAIN_OPTIONS = [
    "NReinas",
    "Knight’s Tour",
    "Torres de Hanói",
    "Ver mejores tiempos",
    "Salir"
]

GAMES = {
    "NReinas": "nreinas",
    "Knight’s Tour": "caballo",
    "Torres de Hanói": "hanoi"
}

def show_menu(options, title="Menú", prompt=None):
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(title)
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    selected = 0
    message = prompt or ""

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif evt.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif evt.key == pygame.K_RETURN:
                    choice = options[selected]
                    pygame.quit()
                    return choice

        screen.fill((30, 30, 30))
        if message:
            msg_surf = font.render(message, True, (200,200,200))
            screen.blit(msg_surf, msg_surf.get_rect(center=(WINDOW_WIDTH//2,50)))
        for i,opt in enumerate(options):
            color = (255,255,0) if i==selected else (255,255,255)
            txt = font.render(opt, True, color)
            screen.blit(txt, txt.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + i*50 - 50)))
        pygame.display.flip()
        clock.tick(FPS)

def display_top_times(game_key):
    msg = {
        "juego": GAMES[game_key],
        "acción": "solicitar_mejores",
        "timestamp": datetime.utcnow().isoformat()+"Z"
    }
    try:
        resp = send_and_receive(msg)
        mejores = resp.get("mejores", [])
    except Exception as e:
        mejores = []
        error_text = f"Error de red: {e}"

    header, rows = [], []
    if mejores:
        if game_key=="NReinas":
            header = ["#"," N ","Intentos"," Fecha"]
            for i,ent in enumerate(mejores,1):
                rows.append(f"{i:>2}   {ent['N']:<3}     {ent['intentos']:<8} {ent['timestamp']}")
        else:
            header = ["#","Movs"," Fecha"]
            for i,ent in enumerate(mejores,1):
                movs = ent.get("movimientos", ent.get("intentos","?"))
                rows.append(f"{i:>2}   {movs:<5}  {ent['timestamp']}")
    else:
        header = ["No hay datos de mejores tiempos."]
        if 'error_text' in locals():
            rows = [error_text]

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
    pygame.display.set_caption(f"Top 5 – {game_key}")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier",24)

    while True:
        for evt in pygame.event.get():
            if evt.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                pygame.quit()
                return
        screen.fill((30,30,30))
        y=20
        if rows:
            hdr = "  ".join(header)
            screen.blit(font.render(hdr,True,(255,215,0)), (20,y))
            y+=40
        for line in rows:
            screen.blit(font.render(line,True,(255,255,255)), (20,y))
            y+=30
        tip = "Pulsa cualquier tecla para volver"
        screen.blit(font.render(tip,True,(200,200,200)), (20,WINDOW_HEIGHT-40))
        pygame.display.flip()
        clock.tick(FPS)

def run_menu():
    while True:
        choice = show_menu(MAIN_OPTIONS, title="Máquina Arcade Distribuida")
        if choice=="NReinas":
            try:
                nreinas_main()
            except Exception as e:
                print("Error en N-Reinas:", e, file=sys.stderr)
                time.sleep(2)
        elif choice=="Knight’s Tour":
            try:
                caballo_main()
            except Exception as e:
                print("Error en Knight’s Tour:", e, file=sys.stderr)
                time.sleep(2)
        elif choice=="Torres de Hanói":
            try:
                hanoi_main()
            except Exception as e:
                print("Error en Torres de Hanói:", e, file=sys.stderr)
                time.sleep(2)
        elif choice=="Ver mejores tiempos":
            sel = show_menu(
                ["NReinas","Knight’s Tour","Torres de Hanói","Volver"],
                title="Selecciona juego", prompt="Consultar top 5"
            )
            if sel in GAMES:
                display_top_times(sel)
        else:
            sys.exit()

if __name__=="__main__":
    run_menu()
