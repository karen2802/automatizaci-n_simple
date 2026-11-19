import unittest
from unittest.mock import patch

from main import es_comando_salida, procesar_input
from funciones_agente.obtener_clima import _extraer_ubicacion, obtener_clima
from funciones_agente.obtener_precio_accion import (
    COMPANY_TICKERS,
    obtener_precio_accion,
)
from utils.sanitizar import sanitizar


class TickerFalso:
    """Sustituto de yfinance.Ticker para pruebas sin red."""

    def __init__(self, symbol):
        self.symbol = symbol
        self.fast_info = {"last_price": 220.15, "currency": "USD"}
        self.info = {"currency": "USD"}

    def history(self, period="1d"):
        raise AssertionError("history no debería usarse si fast_info responde")


class TestSanitizar(unittest.TestCase):
    def test_ejemplos_de_la_especificacion(self):
        self.assertEqual(sanitizar("Oaxaca de Juárez"), "oaxaca de juarez")
        self.assertEqual(
            sanitizar("Precio de la acción Microsoft"),
            "precio de la accion microsoft",
        )
        self.assertEqual(sanitizar("Clima en España"), "clima en espana")

    def test_dieresis_enie_y_espacios(self):
        self.assertEqual(sanitizar("  Pingüino Ñandú  "), "pinguino nandu")


class TestProcesarInput(unittest.TestCase):
    def test_intencion_clima(self):
        self.assertIs(procesar_input("cuál es el clima en la CDMX"), obtener_clima)
        self.assertIs(procesar_input("temperatura en Madrid"), obtener_clima)

    def test_intencion_acciones(self):
        self.assertIs(
            procesar_input("precio de la acción Microsoft"), obtener_precio_accion
        )
        self.assertIs(procesar_input("valor de tesla"), obtener_precio_accion)

    def test_intencion_desconocida(self):
        self.assertIsNone(procesar_input("cuéntame un chiste"))


class TestPrecioAccion(unittest.TestCase):
    @patch("funciones_agente.obtener_precio_accion.yf.Ticker", TickerFalso)
    def test_precio_y_divisa_por_nombre_de_empresa(self):
        respuesta = obtener_precio_accion(
            None, "cual es el precio de una accion de amazon"
        )
        self.assertIn("AMZN", respuesta)
        self.assertIn("220.15", respuesta)
        self.assertIn("USD", respuesta)

    @patch("funciones_agente.obtener_precio_accion.yf.Ticker", TickerFalso)
    def test_ticker_directo(self):
        respuesta = obtener_precio_accion(None, "precio accion msft")
        self.assertIn("MSFT", respuesta)

    def test_mapeo_incluye_tesla(self):
        self.assertEqual(COMPANY_TICKERS["tesla"], "TSLA")
        self.assertEqual(COMPANY_TICKERS["tesla motors"], "TSLA")

    @patch("funciones_agente.obtener_precio_accion.yf.Ticker", TickerFalso)
    def test_sin_empresa_ni_ticker(self):
        respuesta = obtener_precio_accion(None, "cual es el precio")
        self.assertIn("No pude identificar", respuesta)


class TestComandoSalida(unittest.TestCase):
    def test_palabras_de_salida(self):
        for texto in ("salir", "SALIR", "exit", "quit", "adiós", "bye"):
            self.assertTrue(es_comando_salida(texto), texto)

    def test_frase_con_palabra_de_salida(self):
        self.assertTrue(es_comando_salida("quiero salir ya"))
        self.assertTrue(es_comando_salida("me puedes decir adios"))

    def test_no_confunde_palabras_que_la_contienen(self):
        self.assertFalse(es_comando_salida("éxito"))
        self.assertFalse(es_comando_salida("cual es el clima en la cdmx"))

    def test_texto_vacio(self):
        self.assertFalse(es_comando_salida("   "))


class TestUbicacion(unittest.TestCase):
    def test_extrae_cdmx(self):
        self.assertEqual(_extraer_ubicacion("cuál es el clima en la CDMX"), "CDMX")

    def test_conserva_nombre_compuesto(self):
        ubicacion = sanitizar(
            _extraer_ubicacion("cual es el clima en ciudad de mexico")
        )
        self.assertEqual(ubicacion, "ciudad de mexico")

    def test_sin_ubicacion(self):
        self.assertEqual(_extraer_ubicacion("cual es el clima"), "")

    def test_respaldo_sin_driver(self):
        with patch(
            "funciones_agente.obtener_clima._consultar_wttr", return_value=21.0
        ):
            respuesta = obtener_clima(None, "cual es el clima en la cdmx")
        self.assertEqual(respuesta, "La temperatura actual en CDMX es 21°C.")


if __name__ == "__main__":
    unittest.main()
