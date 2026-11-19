"""Versión de respaldo del asistente basada en Selenium.

Reutiliza el orquestador de `main.py` para no duplicar la configuración del
navegador ni el enrutamiento por intención.
"""

from main import chatbot


if __name__ == "__main__":
    chatbot()
