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
    "N‑Reinas",
    "Knight’s Tour",
    "Torres de Hanói",
    "Ver mejores tiempos",
    "Salir"
]

GAMES = {
    "N‑Reinas": "nreinas",
    "Knight’s Tour": "caballo",
    "Torres de Hanói": "hanoi"
}

def show_menu(options, title="Menú", prompt=None):
    """
    Muestra un menú con las opciones dadas y devuelve la seleccionada.
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
    y los muestra en pantalla hasta que el usuario pulse una tecla.
    """
    # Construir mensaje y consultar
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

    # Preparar texto a mostrar
    lines = []
    if mejores:
        lines.append(f"Top 5 de {game_key}")
        for i, entry in enumerate(mejores, start=1):
            # entry es dict con columnas de la tabla
            if game_key == "N‑Reinas":
                info = f"{i}. N={entry['N']} ➔ intentos={entry['intentos']} @ {entry['timestamp']}"
            else:
                movs = entry.get("movimientos", entry.get("intentos", "?"))
                info = f"{i}. movs={movs} @ {entry['timestamp']}"
            lines.append(info)
    else:
        lines.append("No hay datos de mejores tiempos.")
        if 'error_text' in locals():
            lines.append(error_text)

    # Mostrar en Pygame
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(f"Mejores tiempos: {game_key}")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    while True:
        for evt in pygame.event.get():
            if evt.type in (pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return  # volver al menú principal

        screen.fill((50, 50, 50))
        for idx, line in enumerate(lines):
            txt = font.render(line, True, (255, 255, 255))
            screen.blit(txt, (20, 20 + idx * 30))

        prompt = font.render("Pulsa cualquier tecla para volver", True, (200, 200, 200))
        screen.blit(prompt, (20, WINDOW_HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)

def run_menu():
    while True:
        choice = show_menu(MAIN_OPTIONS, title="Máquina Arcade Distribuida")
        if choice == "NReinas":
            nreinas_main()
        elif choice == "Knights Tour":
            caballo_main()
        elif choice == "Torres de Hanói":
            hanoi_main()
        elif choice == "Ver mejores tiempos":
            # Submenú para elegir juego
            juego = show_menu(
                ["NReinas", "Knights Tour", "Torres de Hanoi", "Volver"],
                title="Selecciona juego",
                prompt="Consultar top 5"
            )
            if juego in GAMES:
                display_top_times(juego)
            # si elige "Volver", simplemente regresa al menú principal
        else:  # "Salir"
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    run_menu()
