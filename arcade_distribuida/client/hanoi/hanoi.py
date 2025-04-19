import pygame
import sys
from datetime import datetime
from client.common.communication import send_and_receive
from client.common.threading_utils import run_async

# Pide el número de discos
try:
    NUM_DISKS = int(input("Introduce el número de discos para Torres de Hanói: "))
    assert NUM_DISKS > 0
except Exception:
    print("Número de discos inválido. Saliendo.")
    sys.exit(1)

# Configuración de ventana
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
MESSAGE_HEIGHT = 40
FPS = 60

# Cálculos de torre y disco
PEG_COUNT = 3
PEG_X = [
    WINDOW_WIDTH * (i + 1) / (PEG_COUNT + 1)
    for i in range(PEG_COUNT)
]
PEG_Y_TOP = 50
PEG_Y_BOTTOM = WINDOW_HEIGHT - MESSAGE_HEIGHT - 20
DISK_HEIGHT = 20
MAX_DISK_WIDTH = WINDOW_WIDTH / (PEG_COUNT + 1)

# Colores
BG_COLOR = (240, 240, 240)
PEG_COLOR = (160, 82, 45)
DISK_COLOR = (65, 105, 225)
HIGHLIGHT_COLOR = (34, 139, 34)
TEXT_COLOR = (0, 0, 0)
ERROR_COLOR = (220, 20, 60)

@run_async
def enviar_resultado(discos, movimientos, completado):
    """
    Envía el resultado al servidor sin bloquear la GUI.
    """
    mensaje = {
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
        resp = send_and_receive(mensaje)
        print("Servidor respondió:", resp)
    except Exception as e:
        print("Error al enviar resultado:", e)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Torres de Hanói")
    clock = pygame.time.Clock()

    # Inicializar torres: la primera con todos los discos, los demás vacíos
    # Discos representados por enteros: tamaño N (más grande) a 1 (más pequeño)
    towers = [list(range(NUM_DISKS, 0, -1)), [], []]
    selected_peg = None
    move_count = 0
    finished = False
    message = "Click en torre origen"

    font = pygame.font.SysFont(None, 24)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Si sale sin resolver, envía resultado incompleto
                if not finished:
                    enviar_resultado(NUM_DISKS, move_count, False)
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN and not finished:
                mx, my = pygame.mouse.get_pos()
                # Ignorar clicks en zona de mensaje inferior
                if my <= WINDOW_HEIGHT - MESSAGE_HEIGHT:
                    # Determinar peg tocada
                    for i, x in enumerate(PEG_X):
                        if abs(mx - x) < MAX_DISK_WIDTH / 2:
                            # Click en peg i
                            if selected_peg is None:
                                # Primer click: seleccionar torre origen
                                if towers[i]:
                                    selected_peg = i
                                    message = f"Seleccionada torre {i+1}, elige destino"
                                else:
                                    message = "Torre vacía, elige otra"
                            else:
                                # Segundo click: intentar mover a torre i
                                if selected_peg != i:
                                    disk = towers[selected_peg][-1]
                                    if not towers[i] or towers[i][-1] > disk:
                                        towers[selected_peg].pop()
                                        towers[i].append(disk)
                                        move_count += 1
                                        message = f"Movimientos: {move_count}"
                                        # Comprobar final
                                        if len(towers[-1]) == NUM_DISKS:
                                            finished = True
                                            message = "¡Resuelto!"
                                            enviar_resultado(NUM_DISKS, move_count, True)
                                    else:
                                        message = "Movimiento ilegal"
                                selected_peg = None
                            break

        # Dibujar fondo
        screen.fill(BG_COLOR)

        # Dibujar pegs y discos
        for i, x in enumerate(PEG_X):
            # Poste
            pygame.draw.line(
                screen, PEG_COLOR,
                (x, PEG_Y_TOP), (x, PEG_Y_BOTTOM), 5
            )
            # Si está seleccionado, dibujar highlight
            if i == selected_peg:
                pygame.draw.circle(screen, HIGHLIGHT_COLOR, (int(x), int(PEG_Y_BOTTOM + 10)), 15)

            # Dibujar discos
            for depth, disk in enumerate(towers[i]):
                width = disk / NUM_DISKS * MAX_DISK_WIDTH
                rect = pygame.Rect(
                    x - width/2,
                    PEG_Y_BOTTOM - (depth+1)*DISK_HEIGHT,
                    width,
                    DISK_HEIGHT - 2
                )
                pygame.draw.rect(screen, DISK_COLOR, rect)

        # Área de mensaje inferior
        pygame.draw.rect(
            screen, BG_COLOR,
            (0, WINDOW_HEIGHT - MESSAGE_HEIGHT, WINDOW_WIDTH, MESSAGE_HEIGHT)
        )
        text_color = TEXT_COLOR if "ilegal" not in message.lower() else ERROR_COLOR
        text_surf = font.render(message, True, text_color)
        screen.blit(text_surf, (20, WINDOW_HEIGHT - MESSAGE_HEIGHT + 10))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
