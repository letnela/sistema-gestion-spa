from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .intent_detector import Intent, IntentResult, detect_intent
from .recommendation_engine import rank_recommendations
from .response_builder import build_local_response


@dataclass
class BeautyAdvisorResult:
    response: str
    recommendations: list[dict[str, Any]]
    quick_replies: list[str]
    intent: IntentResult


def advise_locally(message: str, has_image: bool, services: list[Any], products: list[Any]) -> BeautyAdvisorResult:
    intent = detect_intent(message, has_image)
    recommendations = rank_recommendations(services, products, message, intent)
    response, quick_replies = build_local_response(intent, recommendations, has_image)
    return BeautyAdvisorResult(response, recommendations, quick_replies, intent)


def rerank_with_ai_text(
    message: str,
    ai_text: str,
    has_image: bool,
    services: list[Any],
    products: list[Any],
) -> BeautyAdvisorResult:
    # El texto del modelo visual aporta señales como "cabello", "maquillaje" o "uñas",
    # pero los resultados finales siguen saliendo exclusivamente de la base de datos.
    combined = f"{message} {ai_text}".strip()
    intent = detect_intent(combined, has_image)
    recommendations = rank_recommendations(services, products, combined, intent)
    _, quick_replies = build_local_response(intent, recommendations, has_image)
    return BeautyAdvisorResult(ai_text, recommendations, quick_replies, intent)
