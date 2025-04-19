import pygame
import sys
from datetime import datetime
from client.common.communication import send_and_receive
from client.common.threading_utils import run_async

# Configuración inicial: pedir N por consola
try:
    N = int(input("Introduce el valor de N para el puzzle de las N-Reinas: "))
    assert N > 0
except Exception:
    print("Valor de N inválido. Saliendo.")
    sys.exit(1)

# Tamaño de ventana dinámico según N
WINDOW_SIZE = 600
BOARD_SIZE = N
TILE_SIZE = WINDOW_SIZE // BOARD_SIZE
FPS = 60
MESSAGE_HEIGHT = 40

# Colores
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLUE = (65, 105, 225)
RED = (220, 20, 60)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)

@run_async
def enviar_resultado(N, movimientos, resuelto):
    """
    Envía el resultado al servidor sin bloquear la GUI.
    """
    mensaje = {
        "juego": "nreinas",
        "acción": "guardar_resultado",
        "datosPartida": {
            "N": N,
            "resuelto": resuelto,
            "intentos": movimientos
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    try:
        resp = send_and_receive(mensaje)
        print("Servidor respondió:", resp)
    except Exception as e:
        print("Error al enviar resultado:", e)

def es_valido(pos, reinas):
    """
    Comprueba que colocar reina en pos no entra en conflicto
    con las ya existentes.
    """
    x0, y0 = pos
    for x1, y1 in reinas:
        if x0 == x1 or y0 == y1 or abs(x0 - x1) == abs(y0 - y1):
            return False
    return True

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + MESSAGE_HEIGHT))
    pygame.display.set_caption(f"N-Reinas (N={N})")
    clock = pygame.time.Clock()

    reinas = set()
    move_count = 0
    finished = False
    message = f"Coloca {N} reinas"

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Enviar resultado incompleto si no se resolvió
                if not finished:
                    enviar_resultado(N, move_count, False)
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and not finished:
                mx, my = pygame.mouse.get_pos()
                if my <= WINDOW_SIZE:
                    col = mx // TILE_SIZE
                    row = my // TILE_SIZE
                    pos = (col, row)
                    if event.button == 1:
                        # Izquierdo: intentar colocar
                        if pos not in reinas:
                            if es_valido(pos, reinas):
                                reinas.add(pos)
                                move_count += 1
                                if len(reinas) == N:
                                    finished = True
                                    message = "¡Resuelto!"
                                    enviar_resultado(N, move_count, True)
                                else:
                                    message = f"Reinas: {len(reinas)} / {N}"
                            else:
                                message = "Conflicto"
                        else:
                            message = "Ya hay reina ahí"
                    elif event.button == 3:
                        # Derecho: remover reina
                        if pos in reinas:
                            reinas.remove(pos)
                            message = f"Reinas: {len(reinas)} / {N}"
                        else:
                            message = "Nada que quitar"

        # Dibujado
        screen.fill(BLACK)
        # Tablero
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                rect = pygame.Rect(c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                color = WHITE if (r + c) % 2 == 0 else GRAY
                pygame.draw.rect(screen, color, rect)
                if (c, r) in reinas:
                    center = rect.center
                    pygame.draw.circle(screen, BLUE, center, TILE_SIZE // 3)
        # Mensaje inferior
        font = pygame.font.SysFont(None, 24)
        text_color = RED if "Conflicto" in message or "invalid" in message.lower() else BLACK
        text_surf = font.render(message, True, text_color)
        text_rect = text_surf.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE + MESSAGE_HEIGHT // 2))
        # fondo blanco para mensaje
        pygame.draw.rect(screen, WHITE, (0, WINDOW_SIZE, WINDOW_SIZE, MESSAGE_HEIGHT))
        screen.blit(text_surf, text_rect)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
