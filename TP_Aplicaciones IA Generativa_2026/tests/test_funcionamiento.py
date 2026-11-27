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


def revision_editorial(**errores):
    campos = dict(ortografia=[], tono=[], respaldo=[], repeticion=[], contenido=[], datos_faltantes=[])
    return agentes.RevisionEditorial(**{**campos, **errores})


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
                return agentes.Pieza(titulo="Pieza de prueba",
                                     texto="Conocé la colección. #HorneroEnCasa #Exterior #Colección")
            veredicto = next(revisiones)
            if veredicto == "corregir":
                return revision_editorial(tono=[agentes.AjusteTexto(fragmento="Conocé", reemplazo="Descubrí")])
            if veredicto == "pedir_datos":
                return revision_editorial(datos_faltantes=["¿Qué dato comercial está autorizado?"])
            return revision_editorial()

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
        self.assertEqual(llamadas.count(agentes.RevisionEditorial), 2)
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

    def test_revision_reune_formato_y_ortografia_desde_primera_pasada(self):
        estado = {
            "pregunta": "Post de Instagram", "pedido": agentes.Pedido(
                canal="Instagram", segmento="Premium", promocion="ninguna", guardar=False, es_marketing=True),
            "brief": {"pedido": "Post de Instagram", "reglas_aplicables": {}, "historial": []},
            "pieza": agentes.Pieza(titulo="Colección", texto="Elegi " + "x" * 2200 + " 🌿✨🏡🌞"),
        }
        with patch.object(agentes, "_consultar", return_value=revision_editorial(
                ortografia=[agentes.AjusteTexto(fragmento="Elegi", reemplazo="Elegí")])):
            revision = agentes._revisor(estado)["revision"]
        self.assertEqual(revision.veredicto, "corregir")
        for hallazgo in ("2200", "hashtags", "#HorneroEnCasa", "emojis", "Elegí"):
            self.assertIn(hallazgo, revision.observacion)

    def test_datos_faltantes_conservan_otros_hallazgos(self):
        estado = {
            "pregunta": "Post de Instagram", "pedido": agentes.Pedido(
                canal="Instagram", segmento="Premium", promocion="ninguna", guardar=True, es_marketing=True),
            "brief": {"pedido": "Post de Instagram", "reglas_aplicables": {}, "historial": []},
            "pieza": agentes.Pieza(titulo="Colección", texto="Elegi la colección."),
        }
        with patch.object(agentes, "_consultar", return_value=revision_editorial(
                ortografia=[agentes.AjusteTexto(fragmento="Elegi", reemplazo="Elegí")],
                datos_faltantes=["¿Cuál es la vigencia?"])):
            revision = agentes._revisor(estado)["revision"]
        self.assertEqual(revision.veredicto, "pedir_datos")
        self.assertIn("hashtags", revision.observacion)
        self.assertIn("Elegí", revision.observacion)
        self.assertIn("vigencia", revision.observacion)

    def test_revision_descarta_cambios_identicos_y_no_duplica_correcciones(self):
        estado = {
            "pregunta": "Post de Instagram", "pedido": agentes.Pedido(
                canal="Instagram", segmento="Premium", promocion="ninguna", guardar=False, es_marketing=True),
            "brief": {"pedido": "Post de Instagram", "reglas_aplicables": {}, "historial": []},
            "pieza": agentes.Pieza(titulo="Colección", texto="Elegi. Abrí la app. #HorneroEnCasa #Exterior #Colección"),
        }
        ajuste = agentes.AjusteTexto(fragmento="Elegi", reemplazo="Elegí")
        with patch.object(agentes, "_consultar", return_value=revision_editorial(
                ortografia=[ajuste], tono=[ajuste, agentes.AjusteTexto(fragmento="Abrí", reemplazo="Abrí")])):
            revision = agentes._revisor(estado)["revision"]
        self.assertEqual(revision.veredicto, "corregir")
        self.assertEqual(revision.observacion.count("Reemplazá"), 1)
        self.assertNotIn("Tono:", revision.observacion)

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
