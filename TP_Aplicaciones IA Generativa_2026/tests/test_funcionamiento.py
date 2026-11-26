"""Pruebas técnicas sin API ni descarga del modelo de embeddings."""
import csv
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "etapa1"))

import agentes
import tools
from streamlit.testing.v1 import AppTest


class FlujoTest(unittest.TestCase):
    def setUp(self):
        self.temporal = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporal.cleanup)
        self.historial = Path(self.temporal.name) / "historial.csv"
        shutil.copyfile(tools.HISTORIAL, self.historial)
        parche = patch.object(tools, "HISTORIAL", self.historial)
        parche.start()
        self.addCleanup(parche.stop)
        self.original = self.historial.read_bytes()
        agentes._grafo.cache_clear()
        self.addCleanup(agentes._grafo.cache_clear)

    def ejecutar(self, veredictos, guardar=True):
        revisiones = iter(veredictos)
        llamadas = []

        def consultar(esquema, instrucciones, entrada):
            llamadas.append(esquema)
            if esquema is agentes.Pedido:
                return agentes.Pedido(canal="Instagram", segmento="Premium",
                                      promocion="ninguna", guardar=guardar, es_marketing=True)
            if esquema is agentes.Pieza:
                return agentes.Pieza(titulo="Pieza de prueba", texto="Conocé la nueva colección.")
            return agentes.Revision(veredicto=next(revisiones), observacion="Revisión de prueba")

        brief = {"pedido": "Pedido de prueba", "reglas_aplicables": {}, "historial": [],
                 "estrategia": {"objetivo": "Comunicar", "enfoque": "Colección",
                                "antecedentes_a_evitar": [], "datos_faltantes": []}}
        with patch.object(agentes, "_consultar", side_effect=consultar), \
                patch.object(agentes, "preparar_brief", return_value=brief):
            resultado = agentes.responder("Pedido de prueba")
        self.assertIsInstance(resultado["respuesta"], str)
        self.assertIsInstance(resultado["detalle"], list)
        for paso in resultado["detalle"]:
            self.assertIn("titulo", paso)
            self.assertIn("contenido", paso)
        return resultado, llamadas

    def test_aprobacion_sin_pedido_de_guardado_no_escribe(self):
        self.ejecutar(["aprobar"], guardar=False)
        self.assertEqual(self.original, self.historial.read_bytes())

    def test_correccion_y_aprobacion_guarda_una_fila(self):
        with self.historial.open(encoding="utf-8-sig", newline="") as archivo:
            antes = list(csv.DictReader(archivo))
        resultado, llamadas = self.ejecutar(["corregir", "aprobar"])
        with self.historial.open(encoding="utf-8-sig", newline="") as archivo:
            despues = list(csv.DictReader(archivo))
        self.assertEqual(len(despues), len(antes) + 1)
        self.assertEqual(despues[-1]["titulo"], "Pieza de prueba")
        self.assertEqual(llamadas.count(agentes.Pieza), 2)
        self.assertIn("Pieza guardada", resultado["respuesta"])

    def test_segunda_correccion_termina_sin_escribir(self):
        resultado, llamadas = self.ejecutar(["corregir", "corregir"])
        self.assertEqual(llamadas.count(agentes.Revision), 2)
        self.assertIn("pendiente", resultado["respuesta"])
        self.assertEqual(self.original, self.historial.read_bytes())

    def test_pedir_datos_termina_sin_escribir(self):
        resultado, llamadas = self.ejecutar(["pedir_datos"])
        self.assertEqual(llamadas.count(agentes.Pieza), 1)
        self.assertIn("pendiente", resultado["respuesta"])
        self.assertEqual(self.original, self.historial.read_bytes())

    def test_whatsapp_sin_enlace_no_redacta_ni_guarda(self):
        pedido = agentes.Pedido(canal="WhatsApp", segmento="Nuevos", promocion="descuento",
                                guardar=True, es_marketing=True)
        with patch.object(agentes, "_consultar", return_value=pedido) as consulta:
            resultado = agentes.responder(
                "Proponé un WhatsApp para Nuevos con un 15% de descuento en Cocina y guardalo.")
        self.assertEqual(consulta.call_count, 1)
        self.assertIn("[enlace oficial]", resultado["respuesta"])
        self.assertEqual(self.original, self.historial.read_bytes())

    def test_app_muestra_respuesta_y_detalle(self):
        respuesta = {"respuesta": "Respuesta técnica de prueba", "detalle": [
            {"titulo": "Paso de prueba", "contenido": "Sin llamada externa"}]}
        with patch.object(agentes, "responder", return_value=respuesta):
            app = AppTest.from_file(str(BASE / "etapa1/main.py"), default_timeout=30).run()
            self.assertEqual(len(app.exception), 0)
            app.chat_input[0].set_value("Consulta de prueba").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.chat_message), 2)
        self.assertTrue(any("Respuesta técnica" in item.value for item in app.markdown))
        self.assertEqual(self.original, self.historial.read_bytes())


if __name__ == "__main__":
    unittest.main()
