from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum


class Intent(str, Enum):
    GREETING = "GREETING"
    SERVICE_SEARCH = "SERVICE_SEARCH"
    PRODUCT_SEARCH = "PRODUCT_SEARCH"
    APPOINTMENT = "APPOINTMENT"
    BEAUTY_ADVICE = "BEAUTY_ADVICE"
    IMAGE_ADVICE = "IMAGE_ADVICE"
    CLARIFY = "CLARIFY"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


@dataclass(frozen=True)
class IntentResult:
    intent: Intent
    category: str | None
    confidence: float
    explicit_product: bool = False
    explicit_service: bool = False


def normalize(text: str) -> str:
    clean = unicodedata.normalize("NFD", (text or "").lower())
    return "".join(c for c in clean if unicodedata.category(c) != "Mn")


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "maquillaje": ("maquillaje", "makeup", "maquillar", "novia", "social", "fiesta", "editorial"),
    "cabello": (
        "cabello", "pelo", "peinado", "corte", "tinte", "color", "mechas", "balayage",
        "alisado", "keratina", "hidratacion", "reparacion", "frizz", "maltratado", "danado",
        "seco", "reseco", "quebradizo", "canas", "shampoo", "acondicionador", "mascarilla capilar",
    ),
    "unas": ("una", "unas", "manicure", "pedicure", "acrilico", "esmaltado", "gel", "nail"),
    "facial": ("rostro", "cara", "facial", "piel", "limpieza facial", "hidratacion facial"),
    "cejas_pestanas": ("ceja", "cejas", "pestana", "pestanas", "lifting", "laminado", "extension"),
    "depilacion": ("depilacion", "depilar", "cera"),
    "masajes": ("masaje", "relajacion", "relajante", "descontracturante", "spa", "estres"),
    "barberia": ("barba", "afeitado", "barberia", "shaving"),
}

DOMAIN_WORDS = {
    "salon", "spa", "belleza", "servicio", "producto", "precio", "costo", "cita", "reserva",
    "reservar", "comprar", "tienda", "stock", "tratamiento", "promocion", "horario",
}

PRODUCT_WORDS = {
    "producto", "comprar", "tienda", "stock", "shampoo", "acondicionador", "mascarilla", "serum",
    "crema", "spray", "aceite", "ampolla", "locion", "gel", "kit", "para casa",
}
SERVICE_WORDS = {
    "servicio", "cita", "reserva", "reservar", "tratamiento", "hacerme",
}
GREETING_WORDS = {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches"}
VAGUE_WORDS = {"quiero", "necesito", "ayuda", "recomiendame", "que tienen", "opciones"}


def detect_intent(message: str, has_image: bool = False) -> IntentResult:
    text = normalize(message).strip()
    if has_image:
        category = detect_category(text)
        return IntentResult(Intent.IMAGE_ADVICE, category, 0.95 if category else 0.75)

    if not text or text in GREETING_WORDS:
        return IntentResult(Intent.GREETING, None, 1.0)

    category = detect_category(text)
    explicit_product = any(word in text for word in PRODUCT_WORDS)
    explicit_service = any(word in text for word in SERVICE_WORDS)

    in_domain = category is not None or explicit_product or explicit_service or any(word in text for word in DOMAIN_WORDS)
    if not in_domain:
        return IntentResult(Intent.OUT_OF_SCOPE, None, 0.99)

    if text in VAGUE_WORDS or (len(text.split()) <= 2 and category is None):
        return IntentResult(Intent.CLARIFY, None, 0.8)

    if any(word in text for word in ("agendar", "reservar", "cita", "disponibilidad")):
        return IntentResult(Intent.APPOINTMENT, category, 0.95, explicit_product, True)

    if explicit_product and not explicit_service:
        return IntentResult(Intent.PRODUCT_SEARCH, category, 0.95, True, False)

    if category and (explicit_service or any(k in text for k in ("quiero", "busco", "recomienda", "hacerme"))):
        return IntentResult(Intent.SERVICE_SEARCH, category, 0.9, explicit_product, True)

    if category:
        return IntentResult(Intent.BEAUTY_ADVICE, category, 0.85, explicit_product, explicit_service)

    return IntentResult(Intent.CLARIFY, None, 0.6, explicit_product, explicit_service)


def detect_category(text: str) -> str | None:
    normalized = normalize(text)
    best: tuple[int, str] | None = None
    for category, keywords in CATEGORY_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in normalized)
        if score and (best is None or score > best[0]):
            best = (score, category)
    return best[1] if best else None
