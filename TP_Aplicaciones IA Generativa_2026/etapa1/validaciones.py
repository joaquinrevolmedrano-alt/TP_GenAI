"""Reglas objetivas de la guía, sección 4. Sin llamadas al LLM ni acceso a datos."""
import re
import unicodedata

import regex


REGLAS_POR_CANAL = {
    "Instagram": {"max_pieza": 2200, "hashtags": (3, 5),
                  "hashtag_obligatorio": "#HorneroEnCasa", "max_emojis": 3},
    "Email": {"max_titulo": 50, "max_palabras_texto": 150, "hashtags": (0, 0),
              "max_emojis": 3, "max_emojis_titulo": 1},
    "WhatsApp": {"max_pieza": 300, "hashtags": (0, 0), "max_emojis": 2},
    "Push": {"max_titulo": 40, "max_texto": 90, "hashtags": (0, 0), "max_emojis": 1},
    "LinkedIn": {"max_pieza": 1300, "hashtags": (2, 3), "max_emojis": 0},
}


def reglas_formato(canal: str) -> dict:
    """Contrato común para el redactor y el validador. Los emojis no tienen mínimo."""
    return {**REGLAS_POR_CANAL[canal], "min_emojis": 0}


def contar_emojis(texto: str) -> int:
    """Cuenta secuencias visibles: familias, tonos de piel y banderas cuentan una vez."""
    return sum(bool(regex.search(r"\p{Extended_Pictographic}|\p{Regional_Indicator}|\u20e3", grupo))
               for grupo in regex.findall(r"\X", texto))


def validar_formato(canal: str, titulo: str, texto: str) -> list[str]:
    """Devuelve todos los incumplimientos objetivos, sin decidir hechos comerciales.

    Instagram, WhatsApp y LinkedIn cuentan título y cuerpo tal como se publican.
    Email y Push tienen límites separados. Los caracteres se cuentan con len
    sobre Unicode NFC; los emojis se cuentan aparte por secuencia visible.
    """
    reglas = reglas_formato(canal)
    titulo, texto = (unicodedata.normalize("NFC", parte) for parte in (titulo, texto))
    pieza = "\n\n".join(parte for parte in (titulo, texto) if parte)
    errores = []
    medidas = (("max_titulo", len(titulo), "título", "caracteres"),
               ("max_texto", len(texto), "texto", "caracteres"),
               ("max_pieza", len(pieza), "pieza completa", "caracteres"),
               ("max_palabras_texto", len(texto.split()), "cuerpo", "palabras"))
    for clave, cantidad, campo, unidad in medidas:
        if clave in reglas and cantidad > reglas[clave]:
            errores.append(f"{canal}: el {campo} tiene {cantidad} {unidad}; máximo {reglas[clave]}.")

    hashtags = re.findall(r"(?<!\w)#\w+", pieza)
    minimo, maximo = reglas["hashtags"]
    if not minimo <= len(hashtags) <= maximo:
        requisito = "no admite hashtags" if maximo == 0 else f"requiere entre {minimo} y {maximo} hashtags"
        errores.append(f"{canal}: {requisito}; se encontraron {len(hashtags)}.")
    obligatorio = reglas.get("hashtag_obligatorio")
    if obligatorio and obligatorio.casefold() not in {h.casefold() for h in hashtags}:
        errores.append(f"{canal}: falta el hashtag obligatorio {obligatorio}.")

    emojis = contar_emojis(pieza)
    if emojis > reglas["max_emojis"]:
        errores.append(f"{canal}: hay {emojis} emojis; máximo {reglas['max_emojis']}.")
    if "max_emojis_titulo" in reglas and contar_emojis(titulo) > reglas["max_emojis_titulo"]:
        errores.append(f"{canal}: el asunto admite hasta {reglas['max_emojis_titulo']} emoji.")
    return errores
