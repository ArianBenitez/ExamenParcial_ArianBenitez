import pygame
import sys
from datetime import datetime
from client.common.communication import send_and_receive
from client.common.threading_utils import run_async
from client.common.ia_client import solicitar_sugerencia_async

# — Configuración Pygame —
WINDOW_SIZE   = 640
BOTTOM_HEIGHT = 120
BOARD_SIZE    = 8
TILE_SIZE     = WINDOW_SIZE // BOARD_SIZE
FPS           = 60

WHITE      = (255,255,255)
GRAY       = (200,200,200)
BLUE       = (100,149,237)
GREEN      = (34,139,34)
RED        = (220,20,60)
BLACK      = (0,0,0)
BUTTON_BG  = (50,50,200)
BUTTON_FG  = (255,255,255)
HIGHLIGHT  = (255,0,0)

KNIGHT_MOVES = [
    (2,1),(1,2),(-1,2),(-2,1),
    (-2,-1),(-1,-2),(1,-2),(2,-1)
]

@run_async
def enviar_resultado(initial_pos, movimientos, completado):
    msg = {
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
        send_and_receive(msg)
    except:
        pass


def warnsdorff_next(visited, current):
    """Heurística de Warnsdorff para el siguiente movimiento."""
    def onward_degree(pos):
        cnt = 0
        for dx, dy in KNIGHT_MOVES:
            nx, ny = pos[0] + dx, pos[1] + dy
            if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and (nx, ny) not in visited:
                cnt += 1
        return cnt

    candidates = []
    for dx, dy in KNIGHT_MOVES:
        nx, ny = current[0] + dx, current[1] + dy
        if 0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and (nx, ny) not in visited:
            candidates.append(((nx, ny), onward_degree((nx, ny))))
    if not candidates:
        return None
    # devuelve la posición con menor grado de salida
    return min(candidates, key=lambda x: x[1])[0]


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + BOTTOM_HEIGHT))
    pygame.display.set_caption("Knight’s Tour")
    clock     = pygame.time.Clock()
    font_small = pygame.font.SysFont(None, 24)

    visited     = set()
    initial_pos = None
    current_pos = None
    move_count  = 0
    finished    = False
    message     = "Click to choose start square"
    ayuda_rect  = pygame.Rect(10, WINDOW_SIZE + 10, 120, 30)
    suggestion  = None

    # Chat state
    chat_mode    = False
    chat_hist    = []   # lista de (role, texto)
    input_chat   = ""
    cursor_vis   = True
    cursor_timer = 0.0
    suggestion_keys = ("suger", "siguiente", "movimiento", "posición")

    while True:
        dt = clock.tick(FPS) / 1000.0
        cursor_timer += dt
        if cursor_timer >= 0.5:
            cursor_timer = 0.0
            cursor_vis = not cursor_vis

        for e in pygame.event.get():
            # Salir
            if e.type == pygame.QUIT:
                if initial_pos is not None and not finished:
                    enviar_resultado(initial_pos, move_count, False)
                pygame.quit()
                return

            # Si estamos en modo chat
            if chat_mode:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        chat_mode = False
                        input_chat = ""
                    elif e.key == pygame.K_RETURN and input_chat.strip():
                        pregunta = input_chat.strip()
                        chat_hist.append(("Tú", pregunta))
                        chat_hist.append(("IA", "…pensando…"))
                        low = pregunta.lower()

                        # Si pregunta por siguiente, uso heurística
                        if any(k in low for k in suggestion_keys):
                            if current_pos:
                                sug = warnsdorff_next(visited, current_pos)
                                if sug:
                                    resp = f"Siguiente movimiento: ({sug[0]},{sug[1]})"
                                    suggestion = sug
                                else:
                                    resp = "No quedan movimientos válidos."
                            else:
                                resp = "Selecciona primero la posición inicial."
                            chat_hist[-1] = ("IA", resp)
                        else:
                            # fallback a LLM
                            prompt = ""
                            for role, txt in chat_hist:
                                pref = "User:" if role == "Tú" else "Assistant:"
                                prompt += f"{pref} {txt}\n"
                            prompt += "Assistant: "
                            def on_resp(txt):
                                chat_hist.append(("IA", txt))
                            solicitar_sugerencia_async(prompt, on_resp)
                        input_chat = ""
                    elif e.key == pygame.K_BACKSPACE:
                        input_chat = input_chat[:-1]
                    else:
                        c = e.unicode
                        if c.isprintable():
                            input_chat += c
                continue

            # Tecla TAB abre el chat
            if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
                chat_mode = True
                chat_hist = [("IA", "¿En qué puedo ayudarte?")]
                input_chat = ""
            # Clic en botón Ayuda IA
            if e.type == pygame.MOUSEBUTTONDOWN and not finished:
                mx, my = e.pos
                if ayuda_rect.collidepoint(mx, my):
                    chat_mode = True
                    chat_hist = [("IA", "¿Sugerencia o consulta?")]
                    input_chat = ""
                elif my <= WINDOW_SIZE:
                    # Lógica del juego
                    x, y = mx // TILE_SIZE, my // TILE_SIZE
                    if initial_pos is None:
                        initial_pos = (x, y)
                        current_pos = (x, y)
                        visited.add((x, y))
                        message = "Movimientos: 0"
                    else:
                        dx, dy = x - current_pos[0], y - current_pos[1]
                        if (dx, dy) in KNIGHT_MOVES and (x, y) not in visited:
                            current_pos = (x, y)
                            visited.add((x, y))
                            move_count += 1
                            message = f"Movimientos: {move_count}"
                        else:
                            message = "Movimiento inválido"

        # Comprueba si se completa el tour
        if initial_pos and not finished:
            if len(visited) == BOARD_SIZE * BOARD_SIZE:
                finished = True
                message = "¡Completado!"
                enviar_resultado(initial_pos, move_count, True)

        # — Dibujo del tablero —
        screen.fill(BLACK)
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                color = WHITE if (r + c) % 2 == 0 else GRAY
                pygame.draw.rect(screen, color,
                                 (c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE))
        # Casillas visitadas
        for (c, r) in visited:
            pygame.draw.rect(screen, GREEN,
                             pygame.Rect(c * TILE_SIZE, r * TILE_SIZE,
                                         TILE_SIZE, TILE_SIZE).inflate(-8, -8))
        # Posición actual del caballo
        if current_pos:
            cx, cy = current_pos
            pygame.draw.circle(screen, BLUE,
                               (cx * TILE_SIZE + TILE_SIZE // 2,
                                cy * TILE_SIZE + TILE_SIZE // 2),
                               TILE_SIZE // 3)
        # Resaltado de sugerencia
        if suggestion:
            c, r = suggestion
            pygame.draw.rect(screen, HIGHLIGHT,
                             (c * TILE_SIZE, r * TILE_SIZE, TILE_SIZE, TILE_SIZE), 3)

        # — Zona inferior —
        pygame.draw.rect(screen, WHITE,
                         (0, WINDOW_SIZE, WINDOW_SIZE, BOTTOM_HEIGHT))
        screen.blit(font_small.render(message, True,
                    RED if "inválido" in message else BLACK),
                    (150, WINDOW_SIZE + 10))
        pygame.draw.rect(screen, BUTTON_BG, ayuda_rect)
        screen.blit(font_small.render("Ayuda IA", True, BUTTON_FG),
                    (ayuda_rect.x + 5, ayuda_rect.y + 5))

        # — Overlay de chat —
        if chat_mode:
            overlay = pygame.Surface((WINDOW_SIZE, BOTTOM_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, WINDOW_SIZE))
            y = WINDOW_SIZE + 5
            for role, txt in chat_hist[-5:]:
                pref = "Tú: " if role == "Tú" else "IA: "
                surf = font_small.render(pref + txt, True, WHITE)
                screen.blit(surf, (10, y))
                y += surf.get_height() + 2
            # Entrada de texto
            pygame.draw.rect(screen, WHITE,
                             (0, WINDOW_SIZE + BOTTOM_HEIGHT - 30,
                              WINDOW_SIZE, 30))
            prompt = input_chat + ("|" if cursor_vis else "")
            surf = font_small.render(prompt, True, BLACK)
            screen.blit(surf, (5, WINDOW_SIZE + BOTTOM_HEIGHT - 25))

        pygame.display.flip()


if __name__ == "__main__":
    main()
