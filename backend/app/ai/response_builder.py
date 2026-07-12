from __future__ import annotations

from .intent_detector import Intent, IntentResult

CATEGORY_LABELS = {
    "maquillaje": "maquillaje",
    "cabello": "cabello",
    "unas": "uñas",
    "facial": "cuidado facial",
    "cejas_pestanas": "cejas y pestañas",
    "depilacion": "depilación",
    "masajes": "masajes y relajación",
    "barberia": "barbería",
}

QUICK_REPLIES = {
    "root": ["Cabello", "Maquillaje", "Uñas", "Rostro", "Masajes"],
    "maquillaje": ["Maquillaje social", "Maquillaje de novia", "Ver precios"],
    "cabello": ["Cabello maltratado", "Cambiar color", "Corte y peinado", "Productos capilares"],
    "unas": ["Manicure", "Pedicure", "Uñas en gel"],
    "facial": ["Limpieza facial", "Hidratación facial"],
}


def build_local_response(intent: IntentResult, recommendations: list[dict], has_image: bool = False) -> tuple[str, list[str]]:
    if intent.intent == Intent.OUT_OF_SCOPE:
        return (
            "Puedo ayudarte únicamente con servicios, productos, citas y cuidados de belleza del salón. ¿Qué deseas mejorar?",
            QUICK_REPLIES["root"],
        )
    if intent.intent in {Intent.GREETING, Intent.CLARIFY}:
        return (
            "¡Claro! ¿Qué deseas mejorar o qué servicio buscas?",
            QUICK_REPLIES["root"],
        )

    label = CATEGORY_LABELS.get(intent.category or "", "belleza")
    if not recommendations:
        message = f"No encontré una opción activa de {label} en el catálogo. Puedes consultar en recepción para una evaluación personalizada."
        return message, QUICK_REPLIES.get(intent.category or "", QUICK_REPLIES["root"])

    first = recommendations[0]
    if intent.intent == Intent.PRODUCT_SEARCH:
        message = f"Encontré estas opciones para comprar. La más relacionada es {first['nombre']} por S/ {first['precio']:.2f}."
    elif intent.intent == Intent.APPOINTMENT:
        message = f"Puedes reservar {first['nombre']} por S/ {first['precio']:.2f}. Usa el botón Reservar para continuar."
    elif has_image:
        message = (
            f"Según tu foto y descripción, la opción más relacionada del catálogo es {first['nombre']}. "
            "La recomendación es orientativa y no reemplaza una evaluación presencial."
        )
    else:
        message = f"Para {label}, te recomiendo primero {first['nombre']} por S/ {first['precio']:.2f}. Te muestro solo opciones relacionadas."

    return message, QUICK_REPLIES.get(intent.category or "", [])
