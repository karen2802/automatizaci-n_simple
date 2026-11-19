# Módulo para consultar precios de acciones en tiempo real usando yfinance
import re

import yfinance as yf

from utils.sanitizar import sanitizar

# Diccionario para mapear nombres comunes de empresas a sus Tickers de bolsa correspondientes
COMPANY_TICKERS = {
    "microsoft": "MSFT",
    "microsoft corp": "MSFT",
    "apple": "AAPL",
    "apple inc": "AAPL",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "tesla": "TSLA",
    "tesla motors": "TSLA",
    "meta": "META",
    "facebook": "META",
    "netflix": "NFLX",
    "nvidia": "NVDA",
}

# Palabras de intención o relleno que nunca deben interpretarse como ticker
PALABRAS_IGNORADAS = {
    "cual", "cuales", "que", "es", "el", "la", "los", "las", "un", "una",
    "de", "del", "en", "al", "por", "para", "con", "y",
    "precio", "precios", "accion", "acciones", "valor", "valores", "stock",
    "cotizacion", "cuanto", "cuesta", "vale", "dime", "me", "puedes",
    "decir", "actual", "hoy", "ahora", "favor", "hola", "quiero", "saber",
}

MENSAJE_SIN_TICKER = (
    "No pude identificar la empresa o el símbolo. "
    "Prueba con algo como 'precio de la acción Microsoft' o 'precio accion MSFT'."
)


def _resolver_ticker(consulta: str):
    """
    Identifica el ticker dentro de la consulta sanitizada.

    Primero busca nombres de empresa dentro del texto (el nombre más largo
    primero) y, si no hay coincidencia, interpreta un token corto como
    símbolo bursátil escrito directamente por el usuario.
    """
    texto = sanitizar(consulta)
    for empresa in sorted(COMPANY_TICKERS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(empresa)}\b", texto):
            return COMPANY_TICKERS[empresa]

    for token in re.findall(r"\b[a-z]{1,5}\b", texto):
        if token not in PALABRAS_IGNORADAS:
            return token.upper()

    return None


def _precio_y_divisa(ticker: str):
    """Obtiene el precio actual y la divisa de cotización de un ticker."""
    accion = yf.Ticker(ticker)
    precio = None
    divisa = None

    info = getattr(accion, "fast_info", None)
    if info is not None:
        try:
            precio = info["last_price"]
        except Exception:
            precio = None
        try:
            divisa = info["currency"]
        except Exception:
            divisa = None

    if precio is None:
        historial = accion.history(period="1d")
        if not historial.empty:
            precio = float(historial["Close"].iloc[-1])

    if divisa is None:
        try:
            divisa = accion.info.get("currency")
        except Exception:
            divisa = None

    return precio, divisa


def obtener_precio_accion(driver, consulta: str) -> str:
    """
    Busca y retorna el precio actual y la divisa de una acción usando yfinance.

    Argumentos:
        driver: Instancia de Selenium WebDriver (no se usa, se mantiene por compatibilidad).
        consulta: Texto del usuario que contiene el nombre de la empresa o el ticker.

    Retorna:
        Cadena con el precio y la divisa, o un mensaje amigable si no se encuentra.
    """
    ticker = _resolver_ticker(consulta)
    if not ticker:
        return MENSAJE_SIN_TICKER

    try:
        precio, divisa = _precio_y_divisa(ticker)
    except Exception:
        return f"No pude consultar el precio de {ticker} en este momento. Intenta de nuevo más tarde."

    if precio is None:
        return f"No encontré cotización para {ticker}. Verifica que el símbolo sea correcto."

    if divisa:
        return f"El precio actual de {ticker} es {float(precio):,.2f} {divisa}."
    return f"El precio actual de {ticker} es {float(precio):,.2f}."
