import pygame
import sys
from datetime import datetime
from client.common.threading_utils import run_async
from client.common.communication import send_and_receive
from client.common.ia_client import solicitar_sugerencia_async

# Config ventana y juego
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
BOTTOM_HEIGHT = 40
FPS = 60

PEG_COUNT = 3
DISK_HEIGHT = 20

# Colores
WHITE = (255,255,255)
BG_COLOR = (240,240,240)
PEG_COLOR = (160,82,45)
DISK_COLOR = (65,105,225)
HIGHLIGHT_COLOR = (34,139,34)
TEXT_COLOR = (0,0,0)
ERROR_COLOR = (220,20,60)
BUTTON_BG    = (50,50,200)
BUTTON_FG    = (255,255,255)
OVERLAY_BG   = (0,0,0,180)

# Estado global IA
suggestion_text = None

@run_async
def enviar_resultado(discos, movimientos, completado):
    msg = {
        "juego": "hanoi",
        "acción": "guardar_resultado",
        "datosPartida": {
            "discos": discos,
            "movimientos": movimientos,
            "completado": completado
        },
        "timestamp": datetime.utcnow().isoformat()+"Z"
    }
    try:
        send_and_receive(msg)
    except:
        pass

def main():
    global suggestion_text

    # Pedir número de discos
    try:
        NUM_DISKS = int(input("Introduce número de discos para Hanoi: "))
        assert NUM_DISKS>0
    except:
        print("Inválido")
        sys.exit(1)

    PEG_X = [WINDOW_WIDTH*(i+1)/(PEG_COUNT+1) for i in range(PEG_COUNT)]
    PEG_Y_TOP    = 50
    PEG_Y_BOTTOM = WINDOW_HEIGHT - BOTTOM_HEIGHT - 20
    MAX_DISK_WIDTH = WINDOW_WIDTH/(PEG_COUNT+1)

    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH,WINDOW_HEIGHT))
    pygame.display.set_caption("Torres de Hanói")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None,24)

    towers = [list(range(NUM_DISKS,0,-1)), [], []]
    selected_peg = None
    move_count = 0
    finished = False
    message = "Click en torre origen"

    ayuda_rect = pygame.Rect(10, WINDOW_HEIGHT-BOTTOM_HEIGHT+5, 100, BOTTOM_HEIGHT-10)

    def on_suggestion(text):
        global suggestion_text
        suggestion_text = text

    while True:
        for event in pygame.event.get():
            # cerrar popup IA
            if suggestion_text and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                suggestion_text = None

            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and not finished:
                mx,my = event.pos

                # Botón Ayuda IA
                if ayuda_rect.collidepoint(mx,my):
                    human_prompt = (
                        "Eres un asistente experto en Torres de Hanói.\n"
                        f"Número de discos: {NUM_DISKS}\n"
                        f"Estado de torres: {[list(t) for t in towers]}\n"
                        "Por favor, sugiere el siguiente movimiento (origen,destino)."
                    )
                    solicitar_sugerencia_async(human_prompt, on_suggestion)

                # Lógica del juego
                elif my <= WINDOW_HEIGHT - BOTTOM_HEIGHT:
                    for i,x in enumerate(PEG_X):
                        if abs(mx-x) < MAX_DISK_WIDTH/2:
                            if selected_peg is None:
                                if towers[i]:
                                    selected_peg = i
                                    message = f"Torre {i+1} seleccionada"
                                else:
                                    message = "Torre vacía"
                            else:
                                disk = towers[selected_peg][-1]
                                if not towers[i] or towers[i][-1] > disk:
                                    towers[selected_peg].pop()
                                    towers[i].append(disk)
                                    move_count += 1
                                    message = f"Movs: {move_count}"
                                    if len(towers[-1]) == NUM_DISKS:
                                        finished = True
                                        message = "¡Resuelto!"
                                        enviar_resultado(NUM_DISKS, move_count, True)
                                else:
                                    message = "Movimiento ilegal"
                                selected_peg = None
                            break

        # Dibujado del escenario
        screen.fill(BG_COLOR)
        for i,x in enumerate(PEG_X):
            pygame.draw.line(screen, PEG_COLOR, (x,PEG_Y_TOP), (x,PEG_Y_BOTTOM), 5)
            if i == selected_peg:
                pygame.draw.circle(screen, HIGHLIGHT_COLOR, (int(x), int(PEG_Y_BOTTOM+10)), 15)
            for depth, disk in enumerate(towers[i]):
                width = disk/NUM_DISKS * MAX_DISK_WIDTH
                rect = pygame.Rect(x-width/2, PEG_Y_BOTTOM-(depth+1)*DISK_HEIGHT, width, DISK_HEIGHT-2)
                pygame.draw.rect(screen, DISK_COLOR, rect)

        # Mensaje y botón IA
        pygame.draw.rect(screen, BG_COLOR, (0, WINDOW_HEIGHT-BOTTOM_HEIGHT, WINDOW_WIDTH, BOTTOM_HEIGHT))
        color = TEXT_COLOR if "ilegal" not in message.lower() else ERROR_COLOR
        screen.blit(font.render(message, True, color), (20, WINDOW_HEIGHT-BOTTOM_HEIGHT+10))
        pygame.draw.rect(screen, BUTTON_BG, ayuda_rect)
        screen.blit(font.render("Ayuda IA", True, BUTTON_FG), (ayuda_rect.x+5, ayuda_rect.y+5))

        # Popup IA
        if suggestion_text:
            ov = pygame.Surface((WINDOW_WIDTH,WINDOW_HEIGHT), pygame.SRCALPHA)
            ov.fill(OVERLAY_BG)
            screen.blit(ov,(0,0))
            y0 = 50
            for line in suggestion_text.split("\n"):
                surf = font.render(line, True, WHITE)
                screen.blit(surf, (20, y0))
                y0 += 30
            screen.blit(font.render("Pulsa tecla para cerrar", True, WHITE), (20, y0+20))

        pygame.display.flip()
        clock.tick(FPS)
