# Utilidades para el pre-procesamiento y limpieza de texto
import unicodedata


def sanitizar(texto: str) -> str:
    """
    Normaliza el texto del usuario para su posterior análisis.

    Reglas:
        - Convierte todo a minúsculas.
        - Elimina tildes y acentos (á, é, í, ó, ú -> a, e, i, o, u).
        - Elimina diéresis (ü -> u).
        - Reemplaza la letra ñ / Ñ por n.
        - Elimina espacios innecesarios al inicio y al final.

    Argumentos:
        texto (str): Cadena de texto a sanitizar.

    Retorna:
        str: El texto normalizado.
    """
    if texto is None:
        return ""
    normalizado = unicodedata.normalize("NFKD", str(texto))
    sin_diacriticos = "".join(c for c in normalizado if not unicodedata.combining(c))
    return sin_diacriticos.lower().strip()
