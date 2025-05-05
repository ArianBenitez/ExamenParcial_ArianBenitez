# client/nreinas/nreinas.py

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

# Configuración ventana
WINDOW_SIZE = 600
BOTTOM_HEIGHT = 40
FPS = 60

# Colores
WHITE = (255,255,255)
GRAY  = (200,200,200)
BLUE  = (65,105,225)
RED   = (220,20,60)
BLACK = (0,0,0)
BUTTON_BG = (50,50,200)
BUTTON_FG = (255,255,255)
OVERLAY_BG = (0,0,0,180)

suggestion_text = None

@run_async
def solicitar_ayuda_ia_nreinas(payload):
    global suggestion_text
    headers={"Authorization":f"Bearer {API_KEY}"}
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        data=resp.json()
        suggestion_text=data.get("generated_text", resp.text)
    except Exception as e:
        suggestion_text=f"Error IA: {e}"

@run_async
def enviar_resultado(N, movimientos, resuelto):
    msg = {
      "juego":"nreinas",
      "acción":"guardar_resultado",
      "datosPartida":{"N":N,"resuelto":resuelto,"intentos":movimientos},
      "timestamp":datetime.utcnow().isoformat()+"Z"
    }
    try:
        send_and_receive(msg)
    except:
        pass

def es_valido(pos, reinas):
    x0,y0=pos
    return all(x0!=x1 and y0!=y1 and abs(x0-x1)!=abs(y0-y1) for x1,y1 in reinas)

def main():
    global suggestion_text
    # pedir N
    try:
        N=int(input("Introduce el valor de N para N-Reinas: "))
        assert N>0
    except:
        print("N inválido"); sys.exit(1)

    BOARD_SIZE=N
    TILE_SIZE=WINDOW_SIZE//BOARD_SIZE

    pygame.init()
    screen=pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE+BOTTOM_HEIGHT))
    pygame.display.set_caption(f"N-Reinas (N={N})")
    clock=pygame.time.Clock()
    font=pygame.font.SysFont(None,24)

    reinas=set()
    move_count=0
    finished=False
    message=f"Coloca {N} reinas"

    ayuda_rect=pygame.Rect(10, WINDOW_SIZE+5, 100, BOTTOM_HEIGHT-10)

    while True:
        for event in pygame.event.get():
            if suggestion_text and event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                suggestion_text=None
            if event.type==pygame.QUIT:
                if not finished:
                    enviar_resultado(N, move_count, False)
                pygame.quit(); sys.exit()
            if event.type==pygame.MOUSEBUTTONDOWN:
                mx,my=event.pos
                if ayuda_rect.collidepoint(mx,my):
                    payload={"juego":"nreinas","estado":{"N":N,"reinas":[list(p) for p in reinas]}}
                    solicitar_ayuda_ia_nreinas(payload)
                elif not finished and my<=WINDOW_SIZE:
                    col, row = mx//TILE_SIZE, my//TILE_SIZE
                    pos=(col,row)
                    if event.button==1:
                        if pos not in reinas and es_valido(pos,reinas):
                            reinas.add(pos); move_count+=1
                            if len(reinas)==N:
                                finished=True; message="¡Resuelto!"
                                enviar_resultado(N,move_count,True)
                            else:
                                message=f"Reinas: {len(reinas)}/{N}"
                        else:
                            message="Conflicto" if pos not in reinas else "Ya hay reina"
                    elif event.button==3 and pos in reinas:
                        reinas.remove(pos); message=f"Reinas: {len(reinas)}/{N}"

        # fin de juego implícito sólo al resolver
        screen.fill(BLACK)
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                rect=pygame.Rect(c*TILE_SIZE,r*TILE_SIZE,TILE_SIZE,TILE_SIZE)
                pygame.draw.rect(screen, WHITE if (r+c)%2==0 else GRAY, rect)
                if (c,r) in reinas:
                    pygame.draw.circle(screen, BLUE, rect.center, TILE_SIZE//3)

        # mensaje
        screen.fill(WHITE,(0,WINDOW_SIZE,WINDOW_SIZE,BOTTOM_HEIGHT))
        txt=font.render(message,True,RED if "Conflic" in message else BLACK)
        screen.blit(txt,(WINDOW_SIZE//2-txt.get_width()//2,WINDOW_SIZE+10))

        # botón IA
        pygame.draw.rect(screen,BUTTON_BG,ayuda_rect)
        ia_txt=font.render("Ayuda IA",True,BUTTON_FG)
        screen.blit(ia_txt,(ayuda_rect.x+5,ayuda_rect.y+5))

        # popup
        if suggestion_text:
            ov=pygame.Surface((WINDOW_SIZE,WINDOW_SIZE+BOTTOM_HEIGHT),pygame.SRCALPHA)
            ov.fill(OVERLAY_BG); screen.blit(ov,(0,0))
            y0=50
            for line in suggestion_text.split("\n"):
                surf=font.render(line,True,WHITE); screen.blit(surf,(20,y0)); y0+=30
            tip=font.render("Pulsa tecla para cerrar",True,WHITE)
            screen.blit(tip,(20,y0+20))

        pygame.display.flip(); clock.tick(FPS)
