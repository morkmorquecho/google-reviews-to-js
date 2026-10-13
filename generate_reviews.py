#!/usr/bin/env python3
"""
Genera googleReviews.js a partir de un JSON de reseñas de Google.

Uso:
    python generate_reviews.py reseñas.json
    python generate_reviews.py reseñas.json -o src/data/googleReviews.js \
        --rating 4.9 --total-reviews 127 \
        --maps-url "https://www.google.com/maps/search/?api=1&query=Mi+clinica"
"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from string import Template

# Paleta del sitio (los 3 colores del ejemplo + tonos cercanos)
PALETTE = [
    "#7cc6e0",
    "#47c1bf",
    "#aedcee",
    "#5bb8d4",
    "#8fd3d1",
    "#9ad0e6",
    "#62c7c5",
    "#bde5f2",
]

JS_TEMPLATE = Template(
    """export const googleReviews = {
  rating: $rating,
  totalReviews: $total_reviews,
  googleMapsUrl: $maps_url,
  title: $title,
  intro: $intro,

  reviews: [
$reviews
  ],
};
"""
)

REVIEW_TEMPLATE = Template(
    """    {
      id: $id,
      name: $name,
      date: $date,
      rating: $rating,
      text: $text,
      url: $url,
      avatar: $avatar,
      avatarColor: $avatar_color,
    },"""
)


def js_str(value) -> str:
    """Convierte un valor a literal de string JS con comillas simples."""
    s = str(value)
    s = s.replace("\\", "\\\\").replace("'", "\\'")
    s = s.replace("\r", "").replace("\n", "\\n")
    s = s.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return f"'{s}'"


def js_nullable(value) -> str:
    return js_str(value) if value else "null"


def clean_text(text: str) -> str:
    """Colapsa saltos de línea y espacios múltiples en un solo espacio."""
    return re.sub(r"\s+", " ", text or "").strip()


def review_timestamp(r: dict) -> float:
    """Marca de tiempo (segundos) para ordenar por fecha de publicación."""
    micros = r.get("posted_at_unix_micros")
    if micros:
        return micros / 1_000_000
    published = r.get("published_at")
    if published:
        # Python <3.11 no tolera fracciones de longitud variable; las recortamos.
        published = re.sub(r"(\.\d{1,6})\d*Z$", r"\1Z", published)
        try:
            return datetime.fromisoformat(published.replace("Z", "+00:00")).timestamp()
        except ValueError:
            pass
    return 0.0


def avatar_color(name: str) -> str:
    """Color de la paleta, 'aleatorio' pero estable para cada nombre
    (así el archivo no cambia de colores cada vez que se regenera)."""
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    return PALETTE[int(digest, 16) % len(PALETTE)]


def build_reviews(raw: list, limit: int, fallback_url: str) -> list:
    raw = sorted(raw, key=review_timestamp, reverse=True)[:limit]
    reviews = []
    for i, r in enumerate(raw, start=1):
        name = (r.get("Name") or "Anónimo").strip()
        text = clean_text(r.get("Description") or r.get("text_original") or "")
        reviews.append(
            {
                "id": i,
                "name": name,
                "date": r.get("When") or "",
                "rating": int(round(r.get("Rating") or r.get("rating_float") or 5)),
                "text": text,
                # No se usa author_url (perfil del autor): todas las reseñas
                # redirigen a la página de reseñas del lugar (--maps-url).
                "url": fallback_url,
                "avatar": r.get("ProfilePicture") or None,
                "avatarColor": avatar_color(name),
            }
        )
    return reviews


def render(reviews: list, args) -> str:
    rating = args.rating
    if rating is None:
        rating = round(sum(r["rating"] for r in reviews) / len(reviews), 1) if reviews else 0
    total = args.total_reviews if args.total_reviews is not None else len(reviews)

    blocks = [
        REVIEW_TEMPLATE.substitute(
            id=r["id"],
            name=js_str(r["name"]),
            date=js_str(r["date"]),
            rating=r["rating"],
            text=js_str(r["text"]),
            url=js_str(r["url"]),
            avatar=js_nullable(r["avatar"]),
            avatar_color=js_str(r["avatarColor"]),
        )
        for r in reviews
    ]

    return JS_TEMPLATE.substitute(
        rating=rating,
        total_reviews=total,
        maps_url=js_str(args.maps_url),
        title=js_str(args.title),
        intro=js_str(args.intro),
        reviews="\n".join(blocks),
    )


def main() -> int:
    p = argparse.ArgumentParser(description="Genera googleReviews.js desde un JSON de reseñas.")
    p.add_argument("input", type=Path, help="JSON con las reseñas")
    p.add_argument("-o", "--output", type=Path, default=Path("googleReviews.js"))
    p.add_argument("--limit", type=int, default=30, help="máximo de reseñas (default: 30)")
    p.add_argument("--rating", type=float, help="calificación global (default: promedio de las reseñas)")
    p.add_argument("--total-reviews", type=int, help="total en Google (default: nº de reseñas incluidas)")
    p.add_argument("--maps-url", default="https://www.google.com/maps/search/?api=1&query=Tu+clinica")
    p.add_argument("--title", default="Lo que dicen nuestros pacientes")
    p.add_argument("--intro", default="Tu experiencia nos ayuda a seguir cuidando cada sonrisa.")
    args = p.parse_args()

    raw = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        print("El JSON debe ser una lista de reseñas.", file=sys.stderr)
        return 1

    reviews = build_reviews(raw, args.limit, args.maps_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(reviews, args), encoding="utf-8")
    print(f"✔ {len(reviews)} reseñas escritas en {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())