# client/nreinas/nreinas.py

import pygame
import sys
from datetime import datetime
from client.common.communication import send_and_receive
from client.common.threading_utils import run_async
from client.common.ia_client import solicitar_sugerencia_async

# — Configuración ventana y constantes —
WINDOW_SIZE   = 600
BOTTOM_HEIGHT = 120
FPS           = 60

WHITE           = (255,255,255)
GRAY            = (200,200,200)
BLUE            = (65,105,225)
RED             = (220,20,60)
BLACK           = (0,0,0)
BUTTON_BG       = (50,50,200)
BUTTON_FG       = (255,255,255)
HIGHLIGHT_COLOR = (255,0,0)

@run_async
def enviar_resultado(N, intentos, resuelto):
    """Envía el resultado al servidor sin bloquear la UI."""
    msg = {
        "juego": "nreinas",
        "acción": "guardar_resultado",
        "datosPartida": {"N": N, "resuelto": resuelto, "intentos": intentos},
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    try:
        send_and_receive(msg)
    except:
        pass

def es_valido(pos, reinas):
    """Comprueba que una reina en pos no ataque a las existentes."""
    x0, y0 = pos
    return all(
        x0!=x1 and
        y0!=y1 and
        abs(x0-x1)!=abs(y0-y1)
        for x1,y1 in reinas
    )

def encontrar_solucion(parcial, N):
    """Backtracking para extender 'parcial' hasta una solución completa."""
    fila = len(parcial)
    if fila == N:
        return parcial[:]  # solución completa
    for col in range(N):
        if es_valido((col,fila), parcial):
            parcial.append((col,fila))
            sol = encontrar_solucion(parcial, N)
            if sol:
                return sol
            parcial.pop()
    return None

def sugerir_proximo(reinas, N):
    """Devuelve la siguiente posición de una solución completa."""
    sol = encontrar_solucion(reinas[:], N)
    if not sol or len(sol) <= len(reinas):
        return None
    return sol[len(reinas)]

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + BOTTOM_HEIGHT))
    pygame.display.set_caption("N-Reinas: introduce N")
    clock     = pygame.time.Clock()
    font_big   = pygame.font.SysFont(None, 32)
    font_small = pygame.font.SysFont(None, 24)

    # --- Fase de entrada de N ---
    input_text = ""
    N = None
    while N is None:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                return
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN:
                    try:
                        v = int(input_text)
                        if v > 0:
                            N = v
                    except:
                        pass
                    input_text = ""
                elif e.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif e.unicode.isdigit():
                    input_text += e.unicode
        screen.fill(BLACK)
        screen.blit(font_big.render("Introduce N para N-Reinas:", True, WHITE), (20,200))
        screen.blit(font_big.render(input_text, True, WHITE), (20,250))
        pygame.display.flip()
        clock.tick(FPS)

    # --- Inicialización del juego ---
    TILE = WINDOW_SIZE // N
    pygame.display.set_caption(f"N-Reinas (N={N})")

    reinas      = []       # lista de (col, fila)
    intentos    = 0
    finished    = False
    message     = f"Coloca {N} reinas"
    ayuda_rect  = pygame.Rect(10, WINDOW_SIZE+10, 120, 30)
    suggestion  = None     # la última sugerencia (col, fila)

    # --- Variables de chat ---
    chat_mode    = False
    chat_hist    = []      # lista de (role, texto)
    input_chat   = ""
    cursor_vis   = True
    cursor_timer = 0.0

    suggestion_keywords = ("suger", "siguiente", "movimiento", "posición")

    while True:
        dt = clock.tick(FPS) / 1000.0
        cursor_timer += dt
        if cursor_timer >= 0.5:
            cursor_timer = 0.0
            cursor_vis = not cursor_vis

        for e in pygame.event.get():
            # Cerrar ventana
            if e.type == pygame.QUIT:
                if not finished:
                    enviar_resultado(N, intentos, False)
                pygame.quit()
                return

            # Manejo de chat abierto
            if chat_mode:
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        chat_mode = False
                        input_chat = ""
                    elif e.key == pygame.K_RETURN and input_chat.strip():
                        pregunta = input_chat.strip()
                        chat_hist.append(("Tú", pregunta))
                        chat_hist.append(("IA", "…pensando…"))

                        lower = pregunta.lower()
                        # si pregunta pide la siguiente posición/movimiento
                        if any(k in lower for k in suggestion_keywords):
                            sug = sugerir_proximo(reinas, N)
                            if sug:
                                resp = (f"Sugerencia: fila {sug[1]+1}, "
                                        f"columna {sug[0]+1}")
                                suggestion = sug
                            else:
                                resp = "No encuentro solución válida desde aquí."
                            chat_hist[-1] = ("IA", resp)
                        else:
                            # fallback LLM para libre conversación
                            prompt = ""
                            for role, txt in chat_hist:
                                pref = "User:" if role=="Tú" else "Assistant:"
                                prompt += f"{pref} {txt}\n"
                            prompt += "Assistant: "
                            def on_resp(text):
                                chat_hist.append(("IA", text))
                            solicitar_sugerencia_async(prompt, on_resp)

                        input_chat = ""
                    elif e.key == pygame.K_BACKSPACE:
                        input_chat = input_chat[:-1]
                    else:
                        c = e.unicode
                        if c.isprintable():
                            input_chat += c
                continue

            # Si no chat: abrir chat con TAB o clic
            if e.type == pygame.KEYDOWN and e.key == pygame.K_TAB:
                chat_mode = True
                chat_hist = [("IA","¿En qué puedo ayudarte?")]
                input_chat = ""
            if e.type == pygame.MOUSEBUTTONDOWN and not finished:
                mx,my = e.pos
                if ayuda_rect.collidepoint(mx, my):
                    chat_mode = True
                    chat_hist = [("IA","¿Sugerencia o consulta?")]
                    input_chat = ""
                elif my <= WINDOW_SIZE:
                    col,row = mx//TILE, my//TILE
                    pos = (col,row)
                    if e.button == 1:
                        if pos not in reinas and es_valido(pos, reinas):
                            reinas.append(pos)
                            intentos += 1
                            if len(reinas) == N:
                                finished = True
                                message = "¡Resuelto!"
                                enviar_resultado(N, intentos, True)
                            else:
                                message = f"Reinas: {len(reinas)}/{N}"
                        else:
                            message = "Movimiento inválido"
                    elif e.button == 3 and pos in reinas:
                        reinas.remove(pos)
                        message = f"Reinas: {len(reinas)}/{N}"

        # — Dibujo del tablero —
        screen.fill(BLACK)
        for r in range(N):
            for c in range(N):
                color = WHITE if (r+c)%2==0 else GRAY
                pygame.draw.rect(screen, color,
                                 (c*TILE, r*TILE, TILE, TILE))
        # dibujar reinas
        for (c,r) in reinas:
            pygame.draw.circle(screen, BLUE,
                               (c*TILE+TILE//2, r*TILE+TILE//2),
                               TILE//3)
        # highlight de sugerencia
        if suggestion:
            c,r = suggestion
            pygame.draw.rect(screen, HIGHLIGHT_COLOR,
                             (c*TILE, r*TILE, TILE, TILE), 3)

        # — Zona inferior de estado y botón —
        screen.fill(WHITE, (0, WINDOW_SIZE, WINDOW_SIZE, BOTTOM_HEIGHT))
        screen.blit(font_small.render(message, True,
                    RED if "inválido" in message else BLACK),
                    (150, WINDOW_SIZE+10))
        pygame.draw.rect(screen, BUTTON_BG, ayuda_rect)
        screen.blit(font_small.render("Ayuda IA", True, BUTTON_FG),
                    (ayuda_rect.x+5, ayuda_rect.y+5))

        # — Overlay de chat si corresponde —
        if chat_mode:
            # fondo semitransparente
            overlay = pygame.Surface((WINDOW_SIZE, BOTTOM_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0,0,0,180))
            screen.blit(overlay, (0, WINDOW_SIZE))

            # historial (últimos 5 mensajes)
            y = WINDOW_SIZE + 5
            for role, txt in chat_hist[-5:]:
                pref = "Tú: " if role=="Tú" else "IA: "
                surf = font_small.render(pref+txt, True, WHITE)
                screen.blit(surf, (10, y))
                y += surf.get_height() + 2

            # caja de entrada
            pygame.draw.rect(screen, WHITE,
                             (0, WINDOW_SIZE + BOTTOM_HEIGHT - 30,
                              WINDOW_SIZE, 30))
            prompt = input_chat + ("|" if cursor_vis else "")
            surf = font_small.render(prompt, True, BLACK)
            screen.blit(surf, (5, WINDOW_SIZE + BOTTOM_HEIGHT - 25))

        pygame.display.flip()

if __name__ == "__main__":
    main()
