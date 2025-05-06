# client/hanoi/hanoi.py

import pygame
import sys
from datetime import datetime
from client.common.communication import send_and_receive
from client.common.threading_utils import run_async
from client.common.ia_client import solicitar_sugerencia_async

# — Configuración Pygame —
WINDOW_WIDTH   = 600
WINDOW_HEIGHT  = 400
BOTTOM_HEIGHT  = 120
FPS            = 60

PEG_COUNT   = 3
DISK_HEIGHT = 20

RED          = (220,20,60)
BLACK        = (0,0,0)
WHITE        = (255,255,255)
BG_COLOR     = (240,240,240)
PEG_COLOR    = (160,82,45)
DISK_COLOR   = (65,105,225)
HIGHLIGHT    = (255,0,0)
BUTTON_BG    = (50,50,200)
BUTTON_FG    = (255,255,255)

@run_async
def enviar_resultado(discos, movimientos, completado):
    """Envía el resultado al servidor sin bloquear la UI."""
    msg = {
        "juego": "hanoi",
        "acción": "guardar_resultado",
        "datosPartida": {
            "discos": discos,
            "movimientos": movimientos,
            "completado": completado
        },
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    try:
        send_and_receive(msg)
    except:
        pass

def generar_solucion(n, src, dst, aux, moves):
    """Genera la secuencia óptima de movimientos con backtracking."""
    if n == 0:
        return
    generar_solucion(n-1, src, aux, dst, moves)
    moves.append((src, dst))
    generar_solucion(n-1, aux, dst, src, moves)

def prompt_integer(prompt_text, screen, clock, font):
    """Pide un entero al usuario en la misma ventana Pygame."""
    input_str = ""
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    try:
                        v = int(input_str)
                        if v > 0:
                            return v
                    except:
                        pass
                    input_str = ""
                elif e.key == pygame.K_BACKSPACE:
                    input_str = input_str[:-1]
                elif e.unicode.isdigit():
                    input_str += e.unicode
        screen.fill(BLACK)
        screen.blit(font.render(prompt_text, True, WHITE), (20, 200))
        screen.blit(font.render(input_str, True, WHITE), (20, 240))
        pygame.display.flip()
        clock.tick(FPS)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT + BOTTOM_HEIGHT))
    pygame.display.set_caption("Torres de Hanói: nº discos")
    clock      = pygame.time.Clock()
    font       = pygame.font.SysFont(None, 24)

    # --- 1) Entrada de nº de discos ---
    NUM_DISKS = prompt_integer("Introduce nº de discos para Hanói:", screen, clock, font)

    # --- 2) Precalcular movimientos óptimos ---
    optimal = []
    generar_solucion(NUM_DISKS, 0, 2, 1, optimal)
    suggestion_index = 0

    # --- 3) Estado inicial de las torres ---
    towers     = [list(range(NUM_DISKS, 0, -1)), [], []]
    move_count = 0
    finished   = False
    message    = "Click en torre origen"
    ayuda_rect = pygame.Rect(10, WINDOW_HEIGHT + 10, 120, 30)
    suggestion = None

    # --- 4) Variables de chat ---
    chat_mode       = False
    chat_history    = []   # lista de (role, texto)
    input_chat      = ""
    cursor_visible  = True
    cursor_timer    = 0.0
    suggestion_keys = ("suger", "siguiente", "movimiento", "posición")

    while True:
        dt = clock.tick(FPS) / 1000.0
        cursor_timer += dt
        if cursor_timer >= 0.5:
            cursor_timer = 0.0
            cursor_visible = not cursor_visible

        for e in pygame.event.get():
            # Salir siempre posible
            if e.type == pygame.QUIT:
                if not finished:
                    enviar_resultado(NUM_DISKS, move_count, False)
                pygame.quit()
                return

            # Si estamos en chat, capturamos todo el teclado aquí
            if chat_mode:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        chat_mode = False
                        input_chat = ""
                    elif e.key == pygame.K_RETURN and input_chat.strip():
                        pregunta = input_chat.strip()
                        chat_history.append(("Tú", pregunta))
                        chat_history.append(("IA", "…pensando…"))
                        low = pregunta.lower()

                        # Si la pregunta pide la siguiente jugada
                        if any(k in low for k in suggestion_keys):
                            if suggestion_index < len(optimal):
                                src, dst = optimal[suggestion_index]
                                resp = f"Mueve disco de pilar {src+1} a {dst+1}"
                                suggestion = (src, dst)
                            else:
                                resp = "No hay más movimientos."
                            chat_history[-1] = ("IA", resp)
                        else:
                            # Fallback a LLM para respuesta libre
                            prompt = ""
                            for role, txt in chat_history:
                                pref = "User:" if role=="Tú" else "Assistant:"
                                prompt += f"{pref} {txt}\n"
                            prompt += "Assistant: "
                            def on_resp(text):
                                chat_history.append(("IA", text))
                            solicitar_sugerencia_async(prompt, on_resp)

                        input_chat = ""
                    elif e.key == pygame.K_BACKSPACE:
                        input_chat = input_chat[:-1]
                    else:
                        if e.unicode.isprintable():
                            input_chat += e.unicode
                # No procesar juego si estamos en chat
                continue

            # Tecla TAB abre chat
            if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
                chat_mode = True
                chat_history = [("IA", "¿Sugerencia o consulta?")]
                input_chat = ""
            # Clic en Ayuda IA abre chat
            if e.type == pygame.MOUSEBUTTONDOWN and not finished:
                mx, my = e.pos
                if ayuda_rect.collidepoint(mx, my):
                    chat_mode = True
                    chat_history = [("IA", "¿Sugerencia o consulta?")]
                    input_chat = ""
                # Lógica de mover discos
                elif my <= WINDOW_HEIGHT:
                    peg_x = [WINDOW_WIDTH*(i+1)/(PEG_COUNT+1) for i in range(PEG_COUNT)]
                    for i, x in enumerate(peg_x):
                        if abs(mx - x) < (WINDOW_WIDTH/(PEG_COUNT+1))/2:
                            if 'selected' not in locals():
                                if towers[i]:
                                    selected = i
                                    message = f"Pilar {i+1} seleccionado"
                                else:
                                    message = "Pilar vacío"
                            else:
                                disk = towers[selected][-1]
                                if not towers[i] or towers[i][-1] > disk:
                                    towers[selected].pop()
                                    towers[i].append(disk)
                                    move_count += 1
                                    suggestion_index = move_count
                                    message = f"Movimientos: {move_count}"
                                    if len(towers[-1]) == NUM_DISKS:
                                        finished = True
                                        message = "¡Resuelto!"
                                        enviar_resultado(NUM_DISKS, move_count, True)
                                else:
                                    message = "Movimiento ilegal"
                                del selected
                            break

        # — Dibujo de la escena —
        screen.fill(BG_COLOR)
        peg_x = [WINDOW_WIDTH*(i+1)/(PEG_COUNT+1) for i in range(PEG_COUNT)]
        top, bottom = 50, WINDOW_HEIGHT - 20
        max_w = WINDOW_WIDTH/(PEG_COUNT+1)
        for i, x in enumerate(peg_x):
            pygame.draw.line(screen, PEG_COLOR, (x, top), (x, bottom), 5)
            for depth, disk in enumerate(towers[i]):
                w = disk/NUM_DISKS * max_w
                rect = pygame.Rect(x - w/2, bottom - (depth+1)*DISK_HEIGHT, w, DISK_HEIGHT-2)
                pygame.draw.rect(screen, DISK_COLOR, rect)
        # Highlight de sugerencia
        if suggestion:
            src, _ = suggestion
            x = peg_x[src]
            pygame.draw.circle(screen, HIGHLIGHT, (int(x), int(bottom+10)), 15, 3)

        # — UI inferior y botón —
        pygame.draw.rect(screen, WHITE, (0, WINDOW_HEIGHT, WINDOW_WIDTH, BOTTOM_HEIGHT))
        screen.blit(
            font.render(message, True, RED if "ilegal" in message else BLACK),
            (150, WINDOW_HEIGHT + 10)
        )
        pygame.draw.rect(screen, BUTTON_BG, ayuda_rect)
        screen.blit(
            font.render("Ayuda IA", True, BUTTON_FG),
            (ayuda_rect.x + 5, ayuda_rect.y + 5)
        )

        # — Overlay de chat si está activo —
        if chat_mode:
            overlay = pygame.Surface((WINDOW_WIDTH, BOTTOM_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, WINDOW_HEIGHT))
            y = WINDOW_HEIGHT + 5
            for role, txt in chat_history[-5:]:
                prefix = "Tú: " if role == "Tú" else "IA: "
                surf = font.render(prefix + txt, True, WHITE)
                screen.blit(surf, (10, y))
                y += surf.get_height() + 2
            pygame.draw.rect(screen, WHITE, (0, WINDOW_HEIGHT + BOTTOM_HEIGHT - 30, WINDOW_WIDTH, 30))
            prompt = input_chat + ("|" if cursor_visible else "")
            surf = font.render(prompt, True, BLACK)
            screen.blit(surf, (5, WINDOW_HEIGHT + BOTTOM_HEIGHT - 25))

        pygame.display.flip()

if __name__ == "__main__":
    main()
