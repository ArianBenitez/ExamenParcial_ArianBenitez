# client/caballo/caballo.py

import os
import requests
import json
import pygame
import sys
from datetime import datetime
from client.common.threading_utils import run_async
from client.common.communication import send_and_receive

# Configuración IA
API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
API_KEY = os.getenv("HF_API_KEY")

# Configuración de la ventana y tablero
WINDOW_SIZE = 640
BOTTOM_HEIGHT = 40
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
BUTTON_BG = (50, 50, 200)
BUTTON_FG = (255, 255, 255)
OVERLAY_BG = (0, 0, 0, 180)

KNIGHT_MOVES = [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]

# Estado de la sugerencia
suggestion_text = None

@run_async
def solicitar_ayuda_ia(state):
    global suggestion_text
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        resp = requests.post(API_URL, headers=headers, json=state, timeout=10)
        data = resp.json()
        suggestion_text = data.get("generated_text", resp.text)
    except Exception as e:
        suggestion_text = f"Error IA: {e}"

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
        "timestamp": datetime.utcnow().isoformat()+"Z"
    }
    try:
        send_and_receive(msg)
    except:
        pass

def coord_to_notation(pos):
    return f"{pos}"

def main():
    global suggestion_text
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE+BOTTOM_HEIGHT))
    pygame.display.set_caption("Knight’s Tour")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 24)

    visited = set()
    initial_pos = None
    current_pos = None
    move_count = 0
    finished = False
    message = "Click to choose start square"

    # Botón IA
    ayuda_rect = pygame.Rect(10, WINDOW_SIZE+5, 100, BOTTOM_HEIGHT-10)

    while True:
        for event in pygame.event.get():
            # cerrar sugerencia con cualquier tecla/click
            if suggestion_text and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                suggestion_text = None
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and not finished:
                mx,my = event.pos
                if mx>=ayuda_rect.x and my>=ayuda_rect.y and ayuda_rect.collidepoint(mx,my):
                    # construir estado y solicitar IA
                    state = {
                        "juego": "caballo",
                        "estado": {
                            "posicion_inicial": list(initial_pos) if initial_pos else None,
                            "visitadas": [list(p) for p in visited],
                            "actual": list(current_pos) if current_pos else None
                        }
                    }
                    solicitar_ayuda_ia(state)
                elif my <= WINDOW_SIZE:
                    x,y = mx//TILE_SIZE, my//TILE_SIZE
                    if initial_pos is None:
                        initial_pos = (x,y)
                        current_pos = (x,y)
                        visited.add(current_pos)
                        move_count=0
                        message="Movimientos: 0"
                    else:
                        dx,dy = x-current_pos[0], y-current_pos[1]
                        if (dx,dy) in KNIGHT_MOVES and (x,y) not in visited:
                            current_pos=(x,y)
                            visited.add(current_pos)
                            move_count+=1
                            message=f"Movimientos: {move_count}"
                        else:
                            message="Movimiento inválido"

        # Fin de juego
        if initial_pos and not finished:
            if len(visited)==BOARD_SIZE*BOARD_SIZE:
                finished=True
                message="¡Completado!"
                enviar_resultado(initial_pos, move_count, True)
            else:
                moves=[(current_pos[0]+dx,current_pos[1]+dy) for dx,dy in KNIGHT_MOVES
                       if 0<=current_pos[0]+dx<BOARD_SIZE and 0<=current_pos[1]+dy<BOARD_SIZE]
                if all(p in visited for p in moves):
                    finished=True
                    message="No completado"
                    enviar_resultado(initial_pos, move_count, False)

        # Dibujado básico
        screen.fill(BLACK)
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                rect=pygame.Rect(c*TILE_SIZE, r*TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, WHITE if (r+c)%2==0 else GRAY, rect)
                if (c,r) in visited:
                    pygame.draw.rect(screen, GREEN, rect.inflate(-8,-8))
        if current_pos:
            cx,cy=current_pos
            center=(cx*TILE_SIZE+TILE_SIZE//2, cy*TILE_SIZE+TILE_SIZE//2)
            pygame.draw.circle(screen, BLUE, center, TILE_SIZE//3)

        # Mensaje
        text_surf=font.render(message,True,RED if "inválido" in message.lower() else BLACK)
        screen.fill(WHITE,(0,WINDOW_SIZE,WINDOW_SIZE,BOTTOM_HEIGHT))
        screen.blit(text_surf,(WINDOW_SIZE//2 - text_surf.get_width()//2, WINDOW_SIZE+10))

        # Botón IA
        pygame.draw.rect(screen, BUTTON_BG, ayuda_rect)
        ia_txt=font.render("Ayuda IA",True,BUTTON_FG)
        screen.blit(ia_txt,(ayuda_rect.x+5,ayuda_rect.y+5))

        # Popup de sugerencia
        if suggestion_text:
            overlay=pygame.Surface((WINDOW_SIZE, WINDOW_SIZE+BOTTOM_HEIGHT), pygame.SRCALPHA)
            overlay.fill(OVERLAY_BG)
            screen.blit(overlay,(0,0))
            lines = suggestion_text.split("\n")
            y0=50
            for line in lines:
                surf = font.render(line,True,WHITE)
                screen.blit(surf,(20,y0))
                y0+=30
            tip=font.render("Pulsa cualquier tecla para cerrar",True,WHITE)
            screen.blit(tip,(20,y0+20))

        pygame.display.flip()
        clock.tick(FPS)
