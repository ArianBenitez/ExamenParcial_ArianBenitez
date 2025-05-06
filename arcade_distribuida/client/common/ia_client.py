# client/common/ia_client.py

import json
import threading
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

_local_pipe = None

# Mensaje guía más directo
INITIAL_INSTRUCTION = (
    "Eres un asistente útil. "
    "Responde de forma concisa y concreta."
)

PIPELINE_CONFIG = {
    "do_sample": True,
    "top_p": 0.9,
    "temperature": 0.7,
    "return_full_text": False
}

CALL_CONFIG = {
    "max_new_tokens": 25,
    "truncation": True,
}

def _get_pipe():
    global _local_pipe
    if _local_pipe is None:
        tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
        model     = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
        _local_pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            **PIPELINE_CONFIG
        )
    return _local_pipe

def solicitar_sugerencia_async(input_prompt, callback):
    """
    input_prompt: str o dict.
      - str: prompt humano
      - dict: se serializa a JSON
    callback(text): se llama con la respuesta generada
    """
    # Construir prompt completo
    if isinstance(input_prompt, str):
        full_prompt = INITIAL_INSTRUCTION + "\n" + input_prompt
    else:
        full_prompt = INITIAL_INSTRUCTION + "\n" + json.dumps(input_prompt)

    def job():
        pipe = _get_pipe()
        out = pipe(full_prompt, **CALL_CONFIG)
        raw = out[0]["generated_text"].strip()

        # Nos quedamos sólo con la primera línea, así rompemos bucles
        first_line = raw.split("\n", 1)[0].strip()

        # Si está vacío o coincide con parte del prompt, devolvemos fallback
        if not first_line or first_line.lower() in full_prompt.lower():
            result = "Lo siento, no puedo sugerir nada más ahora."
        else:
            result = first_line

        callback(result)

    t = threading.Thread(target=job, daemon=True)
    t.start()
    return t
