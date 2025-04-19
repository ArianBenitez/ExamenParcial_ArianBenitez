import pygame
import sys
from client.nreinas.nreinas import main as nreinas_main
from client.caballo.caballo import main as caballo_main
from client.hanoi.hanoi import main as hanoi_main

# Configuración de ventana
WINDOW_WIDTH, WINDOW_HEIGHT = 600, 400
FPS = 60
OPTIONS = ["N‑Reinas", "Knight’s Tour", "Torres de Hanói", "Salir"]

def run_menu():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Máquina Arcade Distribuida")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 36)
    selected = 0

    while True:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif evt.type == pygame.KEYDOWN:
                if evt.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(OPTIONS)
                elif evt.key == pygame.K_UP:
                    selected = (selected - 1) % len(OPTIONS)
                elif evt.key == pygame.K_RETURN:
                    choice = OPTIONS[selected]
                    pygame.quit()  # cierra Pygame antes de lanzar el juego
                    if choice == "N‑Reinas":
                        nreinas_main()
                    elif choice == "Knight’s Tour":
                        caballo_main()
                    elif choice == "Torres de Hanói":
                        hanoi_main()
                    else:
                        sys.exit()
                    # al volver del juego, reinicializa Pygame y el menú
                    pygame.init()
                    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
                    pygame.display.set_caption("Máquina Arcade Distribuida")
                    clock = pygame.time.Clock()

        # Dibujado del menú
        screen.fill((30, 30, 30))
        for idx, opt in enumerate(OPTIONS):
            color = (255, 255, 0) if idx == selected else (255, 255, 255)
            txt = font.render(opt, True, color)
            rect = txt.get_rect(center=(WINDOW_WIDTH // 2,
                                        WINDOW_HEIGHT // 2 + idx * 50 - 50))
            screen.blit(txt, rect)

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    run_menu()
