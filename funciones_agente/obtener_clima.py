# Módulo encargado de obtener el clima actual mediante Selenium y Google
import re
from urllib.parse import quote_plus

import requests
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from utils.sanitizar import sanitizar

# Palabras de intención o relleno que no forman parte del nombre de la ubicación
PALABRAS_CLIMA = {
    "cual", "cuales", "que", "es", "esta", "estan", "el", "la", "los", "las",
    "un", "una", "en", "clima", "temperatura", "tiempo", "actual", "hoy",
    "ahora", "dime", "me", "puedes", "decir", "favor", "por", "para", "hay",
    "hace", "como", "cuanto", "grados",
}

CONECTORES = {"de", "del"}

MENSAJE_SIN_UBICACION = (
    "No pude identificar la ciudad. "
    "Prueba con algo como 'clima en Guadalajara' o 'temperatura en Madrid'."
)


def _extraer_ubicacion(consulta: str) -> str:
    """Aísla el nombre de la ciudad/región quitando palabras de intención."""
    tokens = re.findall(r"[^\W\d_]+", str(consulta), flags=re.UNICODE)
    tokens = [
        t for t in tokens
        if sanitizar(t) in CONECTORES or sanitizar(t) not in PALABRAS_CLIMA
    ]
    while tokens and sanitizar(tokens[0]) in CONECTORES:
        tokens.pop(0)
    while tokens and sanitizar(tokens[-1]) in CONECTORES:
        tokens.pop()
    return " ".join(tokens)


def _capitalizar(nombre: str) -> str:
    """Presenta el nombre de la ubicación con mayúsculas legibles."""
    partes = []
    for indice, palabra in enumerate(nombre.split()):
        limpia = sanitizar(palabra)
        if indice > 0 and limpia in CONECTORES:
            partes.append(palabra.lower())
        elif palabra.isupper() and len(palabra) > 2:
            partes.append(palabra)
        elif limpia in {"cdmx", "df", "eeuu"}:
            partes.append(limpia.upper())
        else:
            partes.append(palabra[:1].upper() + palabra[1:].lower())
    return " ".join(partes)


def _a_temperatura(texto: str):
    """Convierte el texto de temperatura del widget en un número (o None)."""
    if not texto:
        return None
    valor = texto.strip().replace("+", "").replace("°C", "").replace("C", "")
    valor = valor.replace(",", ".").strip()
    try:
        return float(valor)
    except ValueError:
        return None


def _consultar_google(driver, ubicacion: str):
    """Lee la tarjeta del clima de Google con espera explícita."""
    url = f"https://www.google.com/search?q=clima+{quote_plus(ubicacion)}&hl=es"
    driver.get(url)
    espera = WebDriverWait(driver, 8)
    elemento = espera.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#wob_tm, span.wob_t"))
    )
    return _a_temperatura(elemento.text)


def _consultar_wttr(ubicacion: str):
    """Respaldo: consulta wttr.in cuando Google no muestra la tarjeta."""
    respuesta = requests.get(
        f"https://wttr.in/{quote_plus(ubicacion)}?format=%t", timeout=10
    )
    if respuesta.status_code != 200:
        return None
    return _a_temperatura(respuesta.text)


def obtener_clima(driver, consulta: str) -> str:
    """
    Obtiene la temperatura actual de una ciudad.

    Usa Google mediante Selenium y, si no hay tarjeta de clima o el navegador
    no está disponible, recurre a wttr.in como respaldo.

    Argumentos:
        driver: Instancia de Selenium WebDriver (puede ser None).
        consulta: Texto del usuario con la ciudad o región.

    Retorna:
        Cadena con la ciudad y la temperatura, o un mensaje controlado.
    """
    ubicacion = _extraer_ubicacion(consulta)
    if not ubicacion:
        return MENSAJE_SIN_UBICACION

    temperatura = None
    if driver is not None:
        try:
            temperatura = _consultar_google(driver, ubicacion)
        except Exception:
            temperatura = None

    if temperatura is None:
        try:
            temperatura = _consultar_wttr(ubicacion)
        except Exception:
            temperatura = None

    if temperatura is None:
        return (
            f"No pude obtener el clima de {_capitalizar(ubicacion)} en este momento. "
            "Intenta de nuevo más tarde."
        )

    return f"La temperatura actual en {_capitalizar(ubicacion)} es {temperatura:g}°C."
