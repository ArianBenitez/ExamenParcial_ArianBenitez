# client/common/ia_client.py

import os
import requests
import json
import threading

# Intento de usar la API remota
API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
API_KEY = os.getenv("HF_API_KEY")

# Fallback local
_local_model = None
_local_tokenizer = None
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

def _load_local():
    global _local_model, _local_tokenizer
    if _local_model is None:
        _local_tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
        _local_model     = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
    return pipeline("text-generation", model=_local_model, tokenizer=_local_tokenizer, 
                    # ajustar estos parámetros a tu gusto:
                    max_length=100, do_sample=True, top_p=0.9, temperature=0.7)

# historial de chat para contexto
chat_history = [
    {"role": "system", "content": "Eres un asistente experto en problemas algorítmicos."}
]

def consultar_chatbot(user_msg: str) -> str:
    """
    Devuelve la respuesta del chatbot, intentando primero la API remota.
    Si recibimos 404, cae al modelo local.
    """
    # primero intentamos la API
    headers = {"Authorization": f"Bearer {API_KEY}"}
    prompt_obj = chat_history + [{"role": "user", "content": user_msg}]
    payload = {"inputs": json.dumps(prompt_obj)}
    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        if resp.status_code == 404 or resp.status_code == 503:
            raise RuntimeError("Servicio HF caído, usando modelo local")
        resp.raise_for_status()
        data = resp.json()
        # el campo generated_text puede estar en data[0] o en data
        if isinstance(data, list) and "generated_text" in data[0]:
            text = data[0]["generated_text"]
        elif "generated_text" in data:
            text = data["generated_text"]
        else:
            text = str(data)
    except Exception as e:
        # fallback local
        try:
            gen = _load_local()
            # concatenamos todo el chat como contexto en un string
            context = "\n".join(m["content"] for m in prompt_obj)
            out = gen(context, max_length=100, num_return_sequences=1)
            text = out[0]["generated_text"]
        except Exception as e2:
            text = f"[Error IA local: {e2}]"
    # actualizamos historial y devolvemos
    chat_history.append({"role": "assistant", "content": text})
    return text

def solicitar_chatbot_async(user_msg: str, callback):
    """
    Lanza consultar_chatbot en hilo y pasa el resultado a callback(respuesta).
    """
    def job():
        resp = consultar_chatbot(user_msg)
        callback(resp)
    t = threading.Thread(target=job, daemon=True)
    t.start()
    return t
