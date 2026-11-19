import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Importamos las funciones de lógica de negocio desde nuestro paquete de funciones
from funciones_agente.obtener_precio_accion import obtener_precio_accion
from funciones_agente.obtener_clima import obtener_clima
# Importamos utilidades para limpiar el texto del usuario
from utils.sanitizar import sanitizar

PALABRAS_SALIDA = {"salir", "exit", "quit", "adios", "bye"}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


def crear_driver():
    """Configura y crea el navegador Chrome en modo headless."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={USER_AGENT}")

    driver_path = ChromeDriverManager().install()
    basename = os.path.basename(driver_path).lower()
    if basename not in {"chromedriver", "chromedriver.exe"}:
        dir_path = os.path.dirname(driver_path)
        for candidato in ("chromedriver", "chromedriver.exe"):
            binary_path = os.path.join(dir_path, candidato)
            if os.path.exists(binary_path):
                driver_path = binary_path
                break

    if os.name != "nt":
        os.chmod(driver_path, 0o755)

    return webdriver.Chrome(service=Service(driver_path), options=options)


def es_comando_salida(user_input):
    """Indica si el texto del usuario contiene una palabra de salida."""
    texto = sanitizar(user_input)
    return any(re.search(rf"\b{palabra}\b", texto) for palabra in PALABRAS_SALIDA)


def procesar_input(user_input):
    """
    Determina la intención del usuario sobre el texto limpio.

    Retorna:
        La función del agente correspondiente o None si no se reconoce.
    """
    texto = sanitizar(user_input)
    if "clima" in texto or "temperatura" in texto:
        return obtener_clima
    if "precio" in texto or "accion" in texto or "valor" in texto:
        return obtener_precio_accion
    return None


def chatbot():
    """
    Función principal que inicia el chatbot interactivo por consola.
    Maneja el ciclo de vida del navegador, recibe el input del usuario y
    determina qué acción realizar según la intención detectada.
    """
    print("*** Chatbot v1.0.0***")
    print("Hola, soy el Chatbot v1.0.0. Puedo ayudarte a obtener precios de acciones o indicarte")
    print("la temperatura actual en cualquier ciudad del mundo.")
    print("Me puedes hacer preguntas, por ejemplo ¿cuál es el precio de una acción de Microsoft?")
    print("¿cuál es la temperatura actual en la Ciudad de México?")
    print("Para terminar, escribe 'salir', 'exit', 'quit' o 'adios' (por ejemplo: 'quiero salir').\n")

    driver = None
    try:
        try:
            driver = crear_driver()
        except Exception as e:
            print(f">>> Advertencia: no se pudo iniciar el navegador ({e}).")
            print(">>> El clima se consultará con el servicio de respaldo.\n")

        while True:
            try:
                user_input = input("---> ").strip()
                if not user_input:
                    continue

                if es_comando_salida(user_input):
                    print(">>> ¡Hasta luego!")
                    break

                funcion_agente = procesar_input(user_input)
                if funcion_agente is None:
                    print(">>> No estoy seguro de cómo ayudarte con eso. Prueba preguntando por el precio de una acción o el clima en una ciudad.")
                    continue

                respuesta = funcion_agente(driver, sanitizar(user_input))
                print(f">>> {respuesta}")

            except KeyboardInterrupt:
                print("\n>>> ¡Hasta luego!")
                break
            except Exception as e:
                print(f">>> Ocurrió un error: {e}")
    finally:
        if driver is not None:
            driver.quit()


if __name__ == "__main__":
    chatbot()
