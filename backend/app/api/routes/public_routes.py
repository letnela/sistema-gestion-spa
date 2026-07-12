"""
Rutas públicas: no requieren sesión iniciada.
Pensadas para la página de inicio (landing) y el asistente virtual.

IMPORTANTE sobre el chat con IA:
Las claves de los proveedores (ANTHROPIC_API_KEY, NVIDIA_API_KEY, N8N_WEBHOOK_SECRET)
viven SOLO en el backend (archivo .env, nunca se sube a git). El frontend nunca las ve:
solo le habla a este endpoint, y este endpoint es el único que le habla al proveedor
elegido. Si expusieras una clave en el frontend, cualquiera podría copiarla y gastar tu
saldo.

MEMORIA DE SESIÓN:
Cada conversación se guarda en la tabla chat_mensajes, indexada por sesion_id (un UUID
que el navegador genera una sola vez y guarda en localStorage). El backend arma el
historial leyendo esos mensajes de la base de datos — no depende de que el frontend
reenvíe el historial completo en cada mensaje, así que sobrevive a un F5 o a cerrar y
volver a abrir el navegador.
"""
import uuid
import logging
import time
import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from pydantic import BaseModel, Field
from decimal import Decimal

from app.database.session import get_db
from app.models.service_model import Servicio
from app.models.product_model import Producto
from app.models.chat_model import ChatMensaje
from app.core.config import settings
from app.core.exceptions import ConflictException
from app.ai.beauty_assistant import advise_locally, rerank_with_ai_text
from app.ai.intent_detector import Intent, detect_intent

router = APIRouter(prefix="/public", tags=["Público"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Catálogo público (servicios y productos)
# ---------------------------------------------------------------------------

def _servicios_activos(db: Session):
    return (db.query(Servicio)
            .options(joinedload(Servicio.categoria))
            .filter(Servicio.estado == "ACTIVO")
            .order_by(Servicio.nombre).all())


def _productos_activos(db: Session):
    return (db.query(Producto)
            .options(joinedload(Producto.categoria))
            .filter(Producto.estado == "ACTIVO", Producto.stock > 0)
            .order_by(Producto.nombre).all())


@router.get("/services")
def servicios_publicos(db: Session = Depends(get_db)):
    """Catálogo de servicios activos, sin datos sensibles, para mostrar en la landing."""
    items = _servicios_activos(db)
    return {"data": [{
        "id": str(x.id), "nombre": x.nombre, "descripcion": x.descripcion,
        "precio": x.precio, "duracion_minutos": x.duracion_minutos,
        "imagen_url": x.imagen_url,
        "categoria_nombre": x.categoria.nombre if x.categoria else None,
    } for x in items]}


@router.get("/products")
def productos_publicos(db: Session = Depends(get_db)):
    """Catálogo de productos activos y con stock, para mostrar en la landing."""
    items = _productos_activos(db)
    return {"data": [{
        "id": str(x.id), "nombre": x.nombre, "marca": x.marca, "descripcion": x.descripcion,
        "precio": x.precio_venta, "imagen_url": x.imagen_url,
        "categoria_nombre": x.categoria.nombre if x.categoria else None,
    } for x in items]}


# ---------------------------------------------------------------------------
# Memoria de sesión del chat
# ---------------------------------------------------------------------------

def _historial_sesion(db: Session, sesion_id: str, limite: int | None = None) -> list[dict]:
    limite = limite or settings.CHAT_MAX_HISTORY_MESSAGES
    q = (select(ChatMensaje).where(ChatMensaje.sesion_id == sesion_id)
         .order_by(ChatMensaje.fecha.desc()).limit(limite))
    items = list(db.scalars(q))[::-1]  # de más viejo a más nuevo
    return [{"role": m.role, "content": m.contenido} for m in items]


def _guardar_mensaje(db: Session, sesion_id: str, role: str, contenido: str):
    db.add(ChatMensaje(sesion_id=sesion_id, role=role, contenido=contenido))
    db.commit()


@router.get("/chat/{sesion_id}")
def historial_chat(sesion_id: str, db: Session = Depends(get_db)):
    """Devuelve la conversación guardada de una sesión, para restaurarla al recargar la página."""
    return {"data": _historial_sesion(db, sesion_id, limite=50)}


# ---------------------------------------------------------------------------
# Chat con IA (proveedor intercambiable: anthropic | nvidia | n8n)
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    sesion_id: str = Field(min_length=1, max_length=100)
    mensaje: str = Field(default="", max_length=2000)
    imagen_base64: str | None = Field(default=None)
    imagen_media_type: str | None = Field(default=None, pattern="^image/(jpeg|png|webp|gif)$")


class RecomendacionChat(BaseModel):
    tipo: str
    id: str
    nombre: str
    descripcion: str | None = None
    imagen_url: str | None = None
    precio: float
    duracion_minutos: int | None = None
    stock: int | None = None
    accion: str


def _precio_float(valor) -> float:
    return float(valor or 0)


def _es_tema_del_salon(mensaje: str, tiene_imagen: bool = False) -> bool:
    """Filtro estricto de dominio. Permite saludos, fotos y consultas relacionadas al negocio."""
    if tiene_imagen:
        return True
    texto = _normalizar_texto(mensaje.strip())
    if not texto or texto in {"hola", "buenas", "buenos dias", "buenas tardes", "ayuda", "quiero", "necesito"}:
        return True
    claves = (
        "salon", "spa", "belleza", "cabello", "pelo", "peinado", "corte", "tinte", "color",
        "mechas", "balayage", "alisado", "keratina", "hidratacion", "reparacion", "frizz",
        "maltratado", "danado", "seco", "reseco", "quebradizo", "canas", "uñas", "unas",
        "manicure", "pedicure", "acrilico", "gel", "rostro", "cara", "facial", "piel",
        "maquillaje", "cejas", "pestañas", "pestanas", "depilacion", "masaje", "relajacion",
        "servicio", "producto", "precio", "costo", "cita", "reserva", "comprar", "tienda",
        "stock", "tratamiento", "shampoo", "mascarilla", "acondicionador", "serum"
    )
    return any(clave in texto for clave in claves)


def _seleccionar_recomendaciones(db: Session, texto_consulta: str, limite: int = 4) -> list[dict]:
    """Selecciona únicamente servicios/productos reales y activos para las tarjetas del chat."""
    texto = _normalizar_texto(texto_consulta)
    palabras = {p for p in texto.replace(',', ' ').replace('.', ' ').split() if len(p) > 3}
    grupos = {
        "cabello": ("cabello", "pelo", "maltratado", "danado", "seco", "reseco", "frizz", "quebradizo", "tinte", "color", "keratina", "hidratacion", "reparador"),
        "unas": ("unas", "manicure", "pedicure", "gel", "acrilico"),
        "rostro": ("rostro", "cara", "facial", "piel", "maquillaje", "cejas", "pestanas"),
        "relajacion": ("masaje", "relajacion", "estres", "spa"),
    }
    categoria = next((g for g, claves in grupos.items() if any(c in texto for c in claves)), None)

    def score(item) -> int:
        base = _normalizar_texto(" ".join(filter(None, [
            getattr(item, "nombre", ""), getattr(item, "descripcion", ""),
            getattr(item, "marca", ""), getattr(getattr(item, "categoria", None), "nombre", "")
        ])))
        total = sum(4 for palabra in palabras if palabra in base)
        if categoria:
            total += sum(3 for clave in grupos[categoria] if clave in base)
        return total

    candidatos=[]
    for s in _servicios_activos(db):
        candidatos.append((score(s), 1, {
            "tipo": "SERVICIO", "id": str(s.id), "nombre": s.nombre,
            "descripcion": s.descripcion, "imagen_url": s.imagen_url,
            "precio": _precio_float(s.precio), "duracion_minutos": s.duracion_minutos,
            "stock": None, "accion": "RESERVAR"
        }))
    for p in _productos_activos(db):
        candidatos.append((score(p), 0, {
            "tipo": "PRODUCTO", "id": str(p.id), "nombre": p.nombre,
            "descripcion": p.descripcion, "imagen_url": p.imagen_url,
            "precio": _precio_float(p.precio_venta), "duracion_minutos": None,
            "stock": int(p.stock or 0), "accion": "COMPRAR"
        }))
    candidatos.sort(key=lambda x: (x[0], x[1]), reverse=True)
    positivos=[item for puntaje, _, item in candidatos if puntaje > 0]
    return positivos[:limite]


def _system_prompt(db: Session) -> str:
    """Arma el prompt con el catálogo REAL de servicios y productos, para que el asistente
    solo recomiende cosas que el salón de verdad ofrece (nunca inventa nada que no esté
    en la base de datos)."""
    servicios = _servicios_activos(db)
    productos = _productos_activos(db)
    lista_servicios = "\n".join(
        f"- {s.nombre} ({s.duracion_minutos} min, S/ {s.precio}): {s.descripcion or 'sin descripción'}"
        for s in servicios
    ) or "- (todavía no hay servicios cargados)"
    lista_productos = "\n".join(
        f"- {p.nombre}{' · ' + p.marca if p.marca else ''} (S/ {p.precio_venta}): {p.descripcion or 'sin descripción'}"
        for p in productos
    ) or "- (todavía no hay productos cargados)"
    return f"""Eres el asistente virtual de "Elegance Salon Manager", un salón de belleza.
Respondes en español, de forma breve, cálida y profesional (máximo 4-5 líneas por respuesta).
Estás estrictamente limitado al negocio del salón. No contestes preguntas de política, programación,
tareas escolares, deportes, noticias, finanzas, medicina general ni ningún tema ajeno.

TU ÚNICO TRABAJO es dar consejos y recomendaciones sobre los SERVICIOS y PRODUCTOS que ofrece
el salón, usando EXCLUSIVAMENTE estas listas reales (nunca inventes un servicio, producto,
precio o duración que no esté aquí):

SERVICIOS (se hacen en el salón, con cita):
{lista_servicios}

PRODUCTOS (se compran para llevar a casa, recojo en el salón):
{lista_productos}

Reglas:
- Si te preguntan algo que no tiene que ver con el salón, NO respondas el contenido de esa pregunta.
  Contesta solamente: "Puedo ayudarte únicamente con servicios, productos, citas y cuidados de belleza del salón. ¿Qué deseas mejorar?"
- Si te mandan una foto (de un peinado, color de cabello, rostro, etc.), analízala y
  recomienda qué servicio y/o producto de las listas le conviene más, explicando brevemente
  por qué en 2-3 líneas. No des un diagnóstico médico ni dermatológico, solo una recomendación
  de servicio o producto del salón.
- Para reservar un servicio o comprar un producto, el cliente debe crear una cuenta gratis en
  /registro-cliente y hacerlo desde el portal — tú no puedes agendar citas ni generar pedidos
  directamente, no tienes esa herramienta.
- Si no estás seguro de algo (disponibilidad, promociones vigentes, stock exacto), dilo
  honestamente en vez de inventar una respuesta."""



def _normalizar_texto(texto: str) -> str:
    import unicodedata
    limpio = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in limpio if unicodedata.category(c) != "Mn")


def _llamar_local(system: str, historial: list[dict], datos: ChatRequest, db: Session | None = None) -> str:
    """Asistente local sin API externa. Recomienda únicamente elementos reales del catálogo."""
    if db is None:
        return "Cuéntame un poco más sobre lo que necesitas y te recomendaré una opción del salón."

    mensaje = _normalizar_texto(datos.mensaje.strip())
    servicios = _servicios_activos(db)
    productos = _productos_activos(db)

    aviso_imagen = ""
    if datos.imagen_base64 and not mensaje:
        return ("Recibí tu foto. El modo local no puede evaluar visualmente la imagen todavía, "
                "pero si me describes el problema te recomendaré servicios y productos reales del catálogo.")
    if datos.imagen_base64:
        aviso_imagen = ("No puedo diagnosticar visualmente la foto en modo local, pero sí puedo orientarte "
                        "usando la descripción que escribiste. ")

    if not mensaje or mensaje in {"quiero", "necesito", "ayuda", "hola", "buenas"}:
        return ("Claro 😊 ¿Qué deseas mejorar: cabello, uñas, rostro o relajación? "
                "Cuéntame el problema y te recomendaré un servicio o producto disponible.")

    grupos = {
        "cabello": ["cabello", "pelo", "maltratado", "seco", "reseco", "frizz", "quebradizo", "tinte", "color", "canas", "alisado", "keratina"],
        "unas": ["una", "unas", "manicure", "pedicure", "gel", "acrilico"],
        "rostro": ["rostro", "cara", "facial", "piel", "acne", "manchas"],
        "relajacion": ["masaje", "relajar", "estres", "dolor", "spa"],
    }
    palabras = set(mensaje.replace(',', ' ').replace('.', ' ').split())
    categoria = next((g for g, claves in grupos.items() if any(c in mensaje for c in claves)), None)

    def puntaje(item) -> int:
        texto = _normalizar_texto(" ".join(filter(None, [getattr(item, "nombre", ""), getattr(item, "descripcion", ""), getattr(getattr(item, "categoria", None), "nombre", "")])))
        score = sum(3 for p in palabras if len(p) > 3 and p in texto)
        if categoria:
            score += sum(2 for c in grupos[categoria] if c in texto)
        return score

    servicios_ordenados = sorted(servicios, key=puntaje, reverse=True)
    productos_ordenados = sorted(productos, key=puntaje, reverse=True)
    mejor_servicio = servicios_ordenados[0] if servicios_ordenados and puntaje(servicios_ordenados[0]) > 0 else None
    mejor_producto = productos_ordenados[0] if productos_ordenados and puntaje(productos_ordenados[0]) > 0 else None

    if categoria == "cabello" and ("maltratado" in mensaje or "seco" in mensaje or "reseco" in mensaje or "quebradizo" in mensaje):
        partes = ["Para un cabello maltratado te conviene empezar con una evaluación y un tratamiento reparador o hidratante."]
        if mejor_servicio:
            partes.append(f"Del catálogo te recomiendo **{mejor_servicio.nombre}** (S/ {mejor_servicio.precio}), porque es la opción más relacionada con lo que describes.")
        if mejor_producto:
            partes.append(f"Para el cuidado en casa puedes complementar con **{mejor_producto.nombre}** (S/ {mejor_producto.precio_venta}).")
        if not mejor_servicio and not mejor_producto:
            partes.append("Ahora mismo no encuentro un tratamiento específico cargado en el catálogo; puedes consultar en recepción para una evaluación capilar.")
        return aviso_imagen + " ".join(partes)

    if mejor_servicio or mejor_producto:
        partes=[]
        if mejor_servicio:
            partes.append(f"Te recomiendo el servicio **{mejor_servicio.nombre}** (S/ {mejor_servicio.precio}).")
        if mejor_producto:
            partes.append(f"También puedes considerar **{mejor_producto.nombre}** (S/ {mejor_producto.precio_venta}) para continuar el cuidado en casa.")
        partes.append("Para reservar o comprar, crea tu cuenta e ingresa al portal del cliente.")
        return aviso_imagen + " ".join(partes)

    return aviso_imagen + ("Puedo ayudarte con servicios y productos del salón. Dime si buscas algo para cabello, uñas, rostro o relajación, "
            "y qué resultado deseas obtener.")

def _debe_responder_local_rapido(datos: ChatRequest) -> bool:
    """Evita una llamada externa para consultas frecuentes que el catálogo local resuelve mejor y más rápido."""
    if not settings.CHAT_FAST_LOCAL_ENABLED:
        return False
    mensaje = _normalizar_texto(datos.mensaje.strip())
    if datos.imagen_base64:
        return False
    claves = (
        "cabello", "pelo", "maltratado", "danado", "seco", "reseco", "frizz",
        "quebradizo", "unas", "manicure", "pedicure", "rostro", "facial",
        "masaje", "relajacion", "producto", "servicio", "precio"
    )
    return any(clave in mensaje for clave in claves)


def _llamar_anthropic(system: str, historial: list[dict], datos: ChatRequest) -> str:
    if not settings.ANTHROPIC_API_KEY:
        raise ConflictException(
            "El asistente no está activado (AI_PROVIDER=anthropic pero falta ANTHROPIC_API_KEY "
            "en backend/.env). Genera una clave en https://console.anthropic.com"
        )
    contenido: list[dict] = []
    if datos.imagen_base64 and datos.imagen_media_type:
        contenido.append({"type": "image", "source": {
            "type": "base64", "media_type": datos.imagen_media_type, "data": datos.imagen_base64}})
    contenido.append({"type": "text", "text": datos.mensaje.strip() or
                       "Analiza esta imagen y recomiéndame cuál de sus servicios o productos me conviene."})
    mensajes = historial + [{"role": "user", "content": contenido}]
    try:
        r = httpx.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": settings.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": settings.ANTHROPIC_MODEL, "max_tokens": 400, "system": system, "messages": mensajes},
            timeout=settings.CHAT_PROVIDER_TIMEOUT_SECONDS)
        r.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ConflictException(f"Anthropic devolvió un error ({exc.response.status_code}).")
    except httpx.RequestError:
        raise ConflictException("No se pudo contactar a Anthropic. Intenta de nuevo.")
    data = r.json()
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def _llamar_openai_compatible(nombre: str, base_url: str, api_key: str, model: str,
                               env_hint: str, system: str, historial: list[dict], datos: ChatRequest) -> str:
    """Helper compartido para proveedores que hablan el formato de chat de OpenAI
    (mensajes {role, content}, respuesta en choices[0].message.content). NVIDIA NIM y
    Groq son compatibles con este mismo formato, así que reutilizan esta función."""
    if not api_key:
        raise ConflictException(
            f"El asistente no está activado (AI_PROVIDER={nombre} pero falta {env_hint} "
            f"en backend/.env)."
        )
    mensajes = [{"role": "system", "content": system}] + historial
    if datos.imagen_base64 and datos.imagen_media_type:
        contenido = [
            {"type": "text", "text": datos.mensaje.strip() or "Analiza esta foto únicamente para recomendar servicios o productos reales del salón."},
            {"type": "image_url", "image_url": {"url": f"data:{datos.imagen_media_type};base64,{datos.imagen_base64}"}},
        ]
        mensajes.append({"role": "user", "content": contenido})
    else:
        mensajes.append({"role": "user", "content": datos.mensaje.strip()})
    try:
        r = httpx.post(base_url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "messages": mensajes, "max_tokens": 220, "temperature": 0.35},
            timeout=settings.CHAT_PROVIDER_TIMEOUT_SECONDS)
        r.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ConflictException(f"{nombre.capitalize()} devolvió un error ({exc.response.status_code}): {exc.response.text[:200]}")
    except httpx.RequestError:
        raise ConflictException(f"No se pudo contactar a {nombre}. Intenta de nuevo.")
    data = r.json()
    return data["choices"][0]["message"]["content"]


def _llamar_nvidia(system: str, historial: list[dict], datos: ChatRequest) -> str:
    return _llamar_openai_compatible(
        "nvidia", "https://integrate.api.nvidia.com/v1/chat/completions",
        settings.NVIDIA_API_KEY, settings.NVIDIA_MODEL, "NVIDIA_API_KEY (genera una gratis en https://build.nvidia.com)",
        system, historial, datos)


def _llamar_groq(system: str, historial: list[dict], datos: ChatRequest) -> str:
    modelo = settings.GROQ_VISION_MODEL if datos.imagen_base64 else settings.GROQ_MODEL
    return _llamar_openai_compatible(
        "groq", "https://api.groq.com/openai/v1/chat/completions",
        settings.GROQ_API_KEY, modelo, "GROQ_API_KEY (genera una gratis en https://console.groq.com/keys)",
        system, historial, datos)


def _llamar_n8n(system: str, historial: list[dict], datos: ChatRequest) -> str:
    if not settings.N8N_WEBHOOK_URL:
        raise ConflictException(
            "El asistente no está activado (AI_PROVIDER=n8n pero falta N8N_WEBHOOK_URL "
            "en backend/.env). Configura la URL de tu webhook de n8n."
        )
    headers = {"Content-Type": "application/json"}
    if settings.N8N_WEBHOOK_SECRET:
        headers["Authorization"] = f"Bearer {settings.N8N_WEBHOOK_SECRET}"
    try:
        r = httpx.post(settings.N8N_WEBHOOK_URL, headers=headers, timeout=settings.CHAT_PROVIDER_TIMEOUT_SECONDS, json={
            "sesion_id": datos.sesion_id,
            "mensaje": datos.mensaje.strip(),
            "historial": historial,
            "system_prompt": system,
            "imagen_base64": datos.imagen_base64,
            "imagen_media_type": datos.imagen_media_type,
        })
        r.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ConflictException(f"Tu flujo de n8n devolvió un error ({exc.response.status_code}).")
    except httpx.RequestError:
        raise ConflictException("No se pudo contactar el webhook de n8n. Revisa la URL y que n8n esté corriendo.")
    data = r.json()
    # Formato flexible: acepta cualquiera de estos nombres de campo en la respuesta de n8n.
    if isinstance(data, list) and data:
        data = data[0]
    return data.get("respuesta") or data.get("output") or data.get("text") or data.get("reply") or ""


PROVEEDORES = {
    "local": _llamar_local,
    "anthropic": _llamar_anthropic,
    "nvidia": _llamar_nvidia,
    "groq": _llamar_groq,
    "n8n": _llamar_n8n,
}


@router.post("/chat")
def chat_publico(datos: ChatRequest, db: Session = Depends(get_db)):
    """Beauty Advisor especializado.

    - Clasifica la intención antes de recomendar.
    - Rechaza temas ajenos al salón.
    - Para texto responde localmente y rápido con catálogo real.
    - Para imágenes usa el proveedor visual configurado y aplica fallback local.
    - Las tarjetas siempre se filtran y ordenan desde PostgreSQL.
    """
    if not datos.mensaje.strip() and not datos.imagen_base64:
        raise ConflictException("Escribe un mensaje o adjunta una imagen.")

    mensaje_usuario = datos.mensaje.strip()
    tiene_imagen = bool(datos.imagen_base64)
    servicios = _servicios_activos(db)
    productos = _productos_activos(db)
    resultado_local = advise_locally(mensaje_usuario, tiene_imagen, servicios, productos)

    _guardar_mensaje(db, datos.sesion_id, "user", mensaje_usuario or "[imagen enviada]")

    if resultado_local.intent.intent == Intent.OUT_OF_SCOPE:
        _guardar_mensaje(db, datos.sesion_id, "assistant", resultado_local.response)
        return {"data": {
            "respuesta": resultado_local.response,
            "recomendaciones": [],
            "opciones_rapidas": resultado_local.quick_replies,
            "intencion": resultado_local.intent.intent.value,
            "categoria": None,
            "origen": "filtro_negocio",
        }}

    inicio = time.perf_counter()
    provider_name = (settings.AI_PROVIDER or "local").strip().lower()
    origen_respuesta = "local"
    respuesta = resultado_local.response
    recomendaciones = resultado_local.recommendations
    opciones_rapidas = resultado_local.quick_replies
    intencion = resultado_local.intent

    # El modelo externo se reserva para imágenes. Las consultas de texto se resuelven
    # con el clasificador y ranking local para evitar esperas y resultados irrelevantes.
    if tiene_imagen and provider_name != "local":
        proveedor = PROVEEDORES.get(provider_name)
        if proveedor:
            try:
                historial = _historial_sesion(db, datos.sesion_id)
                system = _system_prompt(db) + """
Analiza la imagen únicamente dentro del contexto de belleza del salón. Describe en pocas palabras
qué área parece corresponder (cabello, maquillaje, uñas, rostro, cejas/pestañas, depilación o masaje)
y recomienda solo elementos existentes en el catálogo proporcionado. No diagnostiques enfermedades.
"""
                texto_ia = proveedor(system, historial, datos)
                if texto_ia:
                    refinado = rerank_with_ai_text(
                        mensaje_usuario, texto_ia, True, servicios, productos
                    )
                    respuesta = refinado.response
                    recomendaciones = refinado.recommendations
                    opciones_rapidas = refinado.quick_replies
                    intencion = refinado.intent
                    origen_respuesta = provider_name
            except Exception as exc:
                logger.warning(
                    "Fallback local del Beauty Advisor. proveedor=%s error=%s",
                    provider_name, exc,
                )

    respuesta = respuesta or "Cuéntame qué deseas mejorar y te mostraré opciones reales del salón."
    _guardar_mensaje(db, datos.sesion_id, "assistant", respuesta)

    logger.info(
        "Beauty Advisor respondido. proveedor=%s origen=%s intencion=%s categoria=%s duracion_ms=%s sesion=%s",
        provider_name,
        origen_respuesta,
        intencion.intent.value,
        intencion.category,
        round((time.perf_counter() - inicio) * 1000),
        datos.sesion_id,
    )

    return {"data": {
        "respuesta": respuesta,
        "recomendaciones": recomendaciones,
        "opciones_rapidas": opciones_rapidas,
        "intencion": intencion.intent.value,
        "categoria": intencion.category,
        "origen": origen_respuesta,
    }}

