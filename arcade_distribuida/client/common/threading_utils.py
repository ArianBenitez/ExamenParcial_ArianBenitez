import threading
from typing import Any, Callable, Optional, Tuple

def start_thread(
    target: Callable[..., Any],
    args: Tuple[Any, ...] = (),
    daemon: bool = True
) -> threading.Thread:
    """
    Inicia una función en un hilo separado.

    :param target: Función a ejecutar en el hilo.
    :param args: Tupla de argumentos a pasar a la función.
    :param daemon: Si True, el hilo será daemon y no bloqueará el cierre de la app.
    :return: El objeto Thread iniciado.
    """
    thread = threading.Thread(target=target, args=args)
    thread.daemon = daemon
    thread.start()
    return thread

def run_async(
    func: Callable[..., Any]
) -> Callable[..., threading.Thread]:
    """
    Decorador para ejecutar una función de forma asíncrona en un hilo daemon.

    Uso:
        @run_async
        def mi_funcion_larga(param1, param2):
            …

        # Llamada no bloqueante:
        mi_funcion_larga(x, y)
    """
    def wrapper(*args: Any, **kwargs: Any) -> threading.Thread:
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper

def delayed_call(
    delay: float,
    callback: Callable[..., Any],
    args: Tuple[Any, ...] = (),
    daemon: bool = True
) -> threading.Timer:
    """
    Ejecuta callback(*args) después de 'delay' segundos en un hilo separado.

    :param delay: Tiempo en segundos antes de ejecutar el callback.
    :param callback: Función a llamar tras el retraso.
    :param args: Argumentos para la función callback.
    :param daemon: Si True, el Timer será daemon.
    :return: El objeto Timer iniciado.
    """
    timer = threading.Timer(delay, callback, args=args)
    timer.daemon = daemon
    timer.start()
    return timer
