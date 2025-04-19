import pygame
import sys
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
    """
    Muestra un menú con las opciones dadas y devuelve la seleccionada.
    Cierra pygame justo antes de devolver.
    """
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
            elif evt.type == pygame.KEYDOWN:
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
            msg_surf = font.render(message, True, (200, 200, 200))
            msg_rect = msg_surf.get_rect(center=(WINDOW_WIDTH//2, 50))
            screen.blit(msg_surf, msg_rect)

        for idx, opt in enumerate(options):
            color = (255, 255, 0) if idx == selected else (255, 255, 255)
            txt = font.render(opt, True, color)
            rect = txt.get_rect(center=(WINDOW_WIDTH // 2,
                                        WINDOW_HEIGHT // 2 + idx * 50 - 50))
            screen.blit(txt, rect)

        pygame.display.flip()
        clock.tick(FPS)

def display_top_times(game_key):
    """
    Consulta al servidor los mejores tiempos para el juego indicado
    y los muestra en pantalla tipo tabla con fuente monoespaciada.
    """
    # Petición al servidor
    msg = {
        "juego": GAMES[game_key],
        "acción": "solicitar_mejores",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    try:
        resp = send_and_receive(msg)
        mejores = resp.get("mejores", [])
    except Exception as e:
        mejores = []
        error_text = f"Error de red: {e}"

    # Preparar líneas de la “tabla”
    header = []
    rows = []
    if mejores:
        if game_key == "NReinas":
            header = ["#"," N ","Intentos"," Fecha"]
            for i, entry in enumerate(mejores, start=1):
                rows.append(f"{i:>2}   {entry['N']:<3}     {entry['intentos']:<8} {entry['timestamp']}")
        else:
            header = ["#","Movs"," Fecha"]
            for i, entry in enumerate(mejores, start=1):
                movs = entry.get("movimientos", entry.get("intentos", "?"))
                rows.append(f"{i:>2}   {movs:<5}  {entry['timestamp']}")
    else:
        header = ["No hay datos de mejores tiempos."]
        if 'error_text' in locals():
            rows = [error_text]

    # Mostrar en Pygame
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"Top 5 – {game_key}")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Courier", 24)  # monoespaciada

    while True:
        for evt in pygame.event.get():
            if evt.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                pygame.quit()
                return

        screen.fill((30, 30, 30))
        y = 20

        # Render encabezado si hay filas
        if rows:
            hdr_surf = font.render("  ".join(header), True, (255, 215, 0))
            screen.blit(hdr_surf, (20, y))
            y += 40

        # Render filas
        for line in rows:
            txt_surf = font.render(line, True, (255, 255, 255))
            screen.blit(txt_surf, (20, y))
            y += 30  # espacio vertical entre filas

        # Pie indicación
        tip = font.render("Pulsa cualquier tecla para volver", True, (200, 200, 200))
        screen.blit(tip, (20, WINDOW_HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)

def run_menu():
    while True:
        choice = show_menu(MAIN_OPTIONS, title="Máquina Arcade Distribuida")
        if choice == "NReinas":
            nreinas_main()
        elif choice == "Knight’s Tour":
            caballo_main()
        elif choice == "Torres de Hanói":
            hanoi_main()
        elif choice == "Ver mejores tiempos":
            sel = show_menu(
                ["NReinas", "Knight’s Tour", "Torres de Hanói", "Volver"],
                title="Selecciona juego",
                prompt="Consultar top 5"
            )
            if sel in GAMES:
                display_top_times(sel)
            # si sel == "Volver", regresa automáticamente
        else:  # "Salir"
            sys.exit()

if __name__ == "__main__":
    run_menu()
