import pygame
import sys
from datetime import datetime
from client.common.communication import send_and_receive
from client.common.threading_utils import run_async

# Configuración de la ventana y tablero
WINDOW_SIZE = 640
BOARD_SIZE = 8
TILE_SIZE = WINDOW_SIZE // BOARD_SIZE
FPS = 60

# Colores
WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
BLUE = (100, 149, 237)
GREEN = (34, 139, 34)
RED = (220, 20, 60)
BLACK = (0, 0, 0)

# Movimientos posibles del caballo
KNIGHT_MOVES = [
    (2, 1), (1, 2), (-1, 2), (-2, 1),
    (-2, -1), (-1, -2), (1, -2), (2, -1)
]

@run_async
def enviar_resultado(initial_pos, movimientos, completado):
    """
    Envía el resultado al servidor sin bloquear la GUI.
    """
    mensaje = {
        "juego": "caballo",
        "acción": "guardar_resultado",
        "datosPartida": {
            "posicion_inicial": str(initial_pos),
            "movimientos": movimientos,
            "completado": completado
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    try:
        resp = send_and_receive(mensaje)
        print("Servidor respondió:", resp)
    except Exception as e:
        print("Error al enviar resultado:", e)

def coord_to_notation(pos):
    # Opcional: convierte (x,y) en notación tipo "(x,y)"
    return f"{pos}"

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 40))
    pygame.display.set_caption("Knights Tour")
    clock = pygame.time.Clock()

    visited = set()
    initial_pos = None
    current_pos = None
    move_count = 0
    running = True
    finished = False
    message = "Click to choose start square"

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not finished:
                mx, my = pygame.mouse.get_pos()
                # Ignorar clicks sobre la zona de texto inferior
                if my <= WINDOW_SIZE:
                    x, y = mx // TILE_SIZE, my // TILE_SIZE
                    if initial_pos is None:
                        # Elegir posición inicial
                        initial_pos = (x, y)
                        current_pos = (x, y)
                        visited.add(current_pos)
                        move_count = 0
                        message = "Movimientos: 0"
                    else:
                        # Intentar mover caballo
                        dx, dy = x - current_pos[0], y - current_pos[1]
                        if (dx, dy) in KNIGHT_MOVES and (x, y) not in visited:
                            current_pos = (x, y)
                            visited.add(current_pos)
                            move_count += 1
                            message = f"Movimientos: {move_count}"
                        else:
                            message = "Movimiento inválido"

        # Detección de fin
        if initial_pos is not None and not finished:
            if len(visited) == BOARD_SIZE * BOARD_SIZE:
                finished = True
                message = "¡Completado!"
                enviar_resultado(coord_to_notation(initial_pos), move_count, True)
            else:
                # Verificar si no hay más movimientos válidos
                moves = [
                    (current_pos[0] + dx, current_pos[1] + dy)
                    for dx, dy in KNIGHT_MOVES
                    if 0 <= current_pos[0] + dx < BOARD_SIZE and 0 <= current_pos[1] + dy < BOARD_SIZE
                ]
                if all(pos in visited for pos in moves):
                    finished = True
                    message = "No completado"
                    enviar_resultado(coord_to_notation(initial_pos), move_count, False)

        # Dibujado
        screen.fill(BLACK)
        # Tablero
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                rect = pygame.Rect(col * TILE_SIZE, row * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                color = WHITE if (row + col) % 2 == 0 else GRAY
                pygame.draw.rect(screen, color, rect)
                if (col, row) in visited:
                    pygame.draw.rect(screen, GREEN, rect.inflate(-8, -8))
        # Caballo
        if current_pos:
            cx, cy = current_pos
            center = (cx * TILE_SIZE + TILE_SIZE // 2, cy * TILE_SIZE + TILE_SIZE // 2)
            pygame.draw.circle(screen, BLUE, center, TILE_SIZE // 3)

        # Mensaje inferior
        font = pygame.font.SysFont(None, 24)
        text_surf = font.render(message, True, RED if "inválido" in message.lower() or "no completado" in message.lower() else BLACK)
        text_rect = text_surf.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE + 20))
        screen.fill(WHITE, (0, WINDOW_SIZE, WINDOW_SIZE, 40))
        screen.blit(text_surf, text_rect)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
