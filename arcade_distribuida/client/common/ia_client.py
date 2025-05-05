import json
import threading
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Pipeline local de DialoGPT-medium
_local_pipe = None

def _get_pipe():
    global _local_pipe
    if _local_pipe is None:
        tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
        model     = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
        _local_pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_length=100,
            do_sample=True,
            top_p=0.9,
            temperature=0.7
        )
    return _local_pipe

def solicitar_sugerencia_async(input_prompt, callback):
    """
    Lanza en hilo la generación de texto a partir de:
    - un dict (se serializa a JSON), o
    - una cadena ya humana (se usa tal cual).
    Luego llama a callback(text).
    """
    # El prompt puede venir como dict o str
    prompt = json.dumps(input_prompt) if isinstance(input_prompt, dict) else input_prompt

    def job():
        pipe = _get_pipe()
        out = pipe(prompt, num_return_sequences=1)
        text = out[0]["generated_text"]
        callback(text)

    t = threading.Thread(target=job, daemon=True)
    t.start()
    return t
