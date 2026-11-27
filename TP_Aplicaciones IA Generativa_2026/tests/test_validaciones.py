"""Casos de la guía y regresiones de la prueba manual de Instagram."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etapa1"))
from validaciones import contar_emojis, validar_formato


class FormatoTest(unittest.TestCase):
    def test_cero_emojis_es_valido_para_todos_los_canales(self):
        casos = {"Instagram": ("Colección", "Elegí en la app. #HorneroEnCasa #Exterior #Colección"),
                 "Email": ("Nueva colección", "Hola, {nombre}. Elegí en la app."),
                 "WhatsApp": ("", "Elegí en https://hornero.example/coleccion"),
                 "Push": ("Nueva colección", "Elegí en la app."),
                 "LinkedIn": ("Colección", "Conocé la propuesta. #Hornero #Hogar")}
        for canal, (titulo, texto) in casos.items():
            with self.subTest(canal=canal):
                self.assertEqual(validar_formato(canal, titulo, texto), [])

    def test_instagram_cuenta_hashtags_y_obligatorio_por_separado(self):
        for texto in ("Descubrí la colección.", "Descubrí. #Deco #Exterior #Colección"):
            with self.subTest(texto=texto):
                errores = validar_formato("Instagram", "Colección", texto)
                self.assertTrue(any("#HorneroEnCasa" in error for error in errores))
        errores = validar_formato("Instagram", "", "#HorneroEnCasa #A #B #C #D #E")
        self.assertTrue(any("se encontraron 6" in error for error in errores))

    def test_largo_incluye_titulo_y_cuerpo_y_respeta_el_limite(self):
        self.assertEqual(validar_formato("WhatsApp", "", "a" * 300), [])
        errores = validar_formato("WhatsApp", "Título", "a" * 300)
        self.assertTrue(any("máximo 300" in error for error in errores))

    def test_push_reporta_ambos_largos_y_hashtags_juntos(self):
        errores = validar_formato("Push", "x" * 41, "x" * 91 + " #Hogar")
        self.assertEqual(len(errores), 3)
        self.assertTrue(any("máximo 40" in error for error in errores))
        self.assertTrue(any("máximo 90" in error for error in errores))
        self.assertTrue(any("no admite hashtags" in error for error in errores))

    def test_email_controla_asunto_palabras_y_emoji_en_asunto(self):
        errores = validar_formato("Email", "x" * 51 + " 🌿✨", "palabra " * 151)
        for esperado in ("máximo 50", "máximo 150", "asunto admite hasta 1"):
            self.assertTrue(any(esperado in error for error in errores))

    def test_emojis_compuestos_cuentan_una_vez(self):
        self.assertEqual(contar_emojis("Familia 👨‍👩‍👧‍👦, saludo 👍🏽, Argentina 🇦🇷 y 1️⃣"), 4)
        self.assertEqual(contar_emojis("2026, 15%, texto y #HorneroEnCasa"), 0)
        self.assertEqual(validar_formato("Push", "", "Hola 👨‍👩‍👧‍👦"), [])

    def test_maximos_de_emojis_se_aplican_por_canal(self):
        for canal, texto in (("Instagram", "🌿✨🏡🌞 #HorneroEnCasa #A #B"),
                             ("WhatsApp", "🌿✨🏡"), ("Push", "🌿✨"),
                             ("LinkedIn", "🌿 #Hornero #Hogar")):
            with self.subTest(canal=canal):
                self.assertTrue(any("emojis" in error for error in validar_formato(canal, "", texto)))


if __name__ == "__main__":
    unittest.main()
