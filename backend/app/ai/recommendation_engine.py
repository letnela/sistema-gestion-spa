from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .intent_detector import CATEGORY_KEYWORDS, Intent, IntentResult, normalize


@dataclass(frozen=True)
class RankedRecommendation:
    score: int
    kind: str
    payload: dict[str, Any]


def _item_text(item: Any) -> str:
    category = getattr(getattr(item, "categoria", None), "nombre", "") or ""
    return normalize(" ".join(filter(None, [
        getattr(item, "nombre", ""), getattr(item, "descripcion", ""),
        getattr(item, "marca", ""), category,
    ])))


def _category_score(item: Any, item_text: str, category: str | None) -> int:
    if not category:
        return 0
    keywords = CATEGORY_KEYWORDS.get(category, ())
    category_name = normalize(getattr(getattr(item, "categoria", None), "nombre", "") or "")
    category_matches = sum(1 for keyword in keywords if keyword in category_name)
    if category_matches:
        return 80 + category_matches * 10

    # Si la categoría registrada pertenece claramente a otra área, se descarta aunque
    # la descripción contenga una palabra secundaria como "peinado" en un pack de novia.
    registered_other = any(
        keyword in category_name
        for other_category, words in CATEGORY_KEYWORDS.items()
        if other_category != category
        for keyword in words
    )
    if registered_other:
        return -140

    matches = sum(1 for keyword in keywords if keyword in item_text)
    if matches:
        return 40 + matches * 8
    # Penalización dura para evitar resultados como crema de afeitar ante "maquillaje".
    other_matches = any(
        keyword in item_text
        for other_category, words in CATEGORY_KEYWORDS.items()
        if other_category != category
        for keyword in words
    )
    return -80 if other_matches else -35


def _query_score(item_text: str, query: str) -> int:
    words = {word for word in normalize(query).replace(",", " ").replace(".", " ").split() if len(word) >= 4}
    return sum(10 for word in words if word in item_text)


def rank_recommendations(
    services: list[Any],
    products: list[Any],
    query: str,
    intent: IntentResult,
    limit: int = 4,
) -> list[dict[str, Any]]:
    ranked: list[RankedRecommendation] = []

    allow_services = intent.intent not in {Intent.PRODUCT_SEARCH}
    allow_products = intent.intent in {Intent.PRODUCT_SEARCH, Intent.BEAUTY_ADVICE, Intent.IMAGE_ADVICE}

    # Una consulta como "quiero maquillaje" debe mostrar solo servicios, no productos aleatorios.
    if intent.intent in {Intent.SERVICE_SEARCH, Intent.APPOINTMENT}:
        allow_products = False
    if intent.explicit_product:
        allow_products = True
    if intent.explicit_service and not intent.explicit_product:
        allow_products = False

    if allow_services:
        for service in services:
            text = _item_text(service)
            score = 25 + _category_score(service, text, intent.category) + _query_score(text, query)
            if intent.intent in {Intent.SERVICE_SEARCH, Intent.APPOINTMENT}:
                score += 25
            ranked.append(RankedRecommendation(score, "SERVICIO", {
                "tipo": "SERVICIO", "id": str(service.id), "nombre": service.nombre,
                "descripcion": service.descripcion, "imagen_url": service.imagen_url,
                "precio": float(service.precio or 0), "duracion_minutos": service.duracion_minutos,
                "stock": None, "accion": "RESERVAR",
            }))

    if allow_products:
        for product in products:
            text = _item_text(product)
            score = 10 + _category_score(product, text, intent.category) + _query_score(text, query)
            if intent.intent == Intent.PRODUCT_SEARCH:
                score += 40
            ranked.append(RankedRecommendation(score, "PRODUCTO", {
                "tipo": "PRODUCTO", "id": str(product.id), "nombre": product.nombre,
                "descripcion": product.descripcion, "imagen_url": product.imagen_url,
                "precio": float(product.precio_venta or 0), "duracion_minutos": None,
                "stock": int(product.stock or 0), "accion": "COMPRAR",
            }))

    ranked.sort(key=lambda item: (item.score, item.kind == "SERVICIO"), reverse=True)
    minimum = 20 if intent.category else 35
    selected = [item.payload for item in ranked if item.score >= minimum]
    return selected[:limit]
