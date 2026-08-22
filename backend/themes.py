"""
Theme presets for the deck export + in-browser preview.

Each preset is a plain dict of hex color strings plus font names, so it can
be used both to drive python-pptx (via `export.pptx_builder`, which turns
the hex strings into RGBColor) and returned as-is over the API for the
frontend's theme picker / slide preview to render with.

Keep this the single source of truth for palettes -- nothing else should
hardcode a color.
"""
from __future__ import annotations

TITLE_FONT = "Segoe UI Semibold"
LABEL_FONT = "Consolas"
BODY_FONT = "Segoe UI"

THEMES: dict[str, dict] = {
    "midnight": {
        "id": "midnight",
        "name": "Midnight",
        "description": "Near-black charcoal with magenta/violet/mint accents.",
        "background": "#18181F",
        "card_bg": "#23232C",
        "card_bg_alt": "#2A2A35",
        "ink": "#F7F4FA",
        "muted": "#AFA9BC",
        "chip_text": "#17171D",
        "accents": ["#FF6BD8", "#8C7CFF", "#45E6C4"],
        "title_font": TITLE_FONT,
        "label_font": LABEL_FONT,
        "body_font": BODY_FONT,
    },
    "daylight": {
        "id": "daylight",
        "name": "Daylight",
        "description": "Clean white deck with indigo/pink/emerald accents.",
        "background": "#FFFFFF",
        "card_bg": "#F5F5F8",
        "card_bg_alt": "#ECEBF3",
        "ink": "#1B1B23",
        "muted": "#6B6878",
        "chip_text": "#FFFFFF",
        "accents": ["#4F46E5", "#EC4899", "#10B981"],
        "title_font": TITLE_FONT,
        "label_font": LABEL_FONT,
        "body_font": BODY_FONT,
    },
    "sunset": {
        "id": "sunset",
        "name": "Sunset",
        "description": "Warm dark brown with orange/amber/coral accents.",
        "background": "#1F1410",
        "card_bg": "#2B1D17",
        "card_bg_alt": "#33231C",
        "ink": "#FDF3EC",
        "muted": "#D9B8A8",
        "chip_text": "#1F1410",
        "accents": ["#FF7A45", "#FFC24B", "#FF4D6D"],
        "title_font": TITLE_FONT,
        "label_font": LABEL_FONT,
        "body_font": BODY_FONT,
    },
    "ocean": {
        "id": "ocean",
        "name": "Ocean",
        "description": "Deep navy with cyan/blue/teal accents.",
        "background": "#0B1B2B",
        "card_bg": "#12283D",
        "card_bg_alt": "#173349",
        "ink": "#EAF4FB",
        "muted": "#9FB8CC",
        "chip_text": "#0B1B2B",
        "accents": ["#22D3EE", "#3B82F6", "#34D399"],
        "title_font": TITLE_FONT,
        "label_font": LABEL_FONT,
        "body_font": BODY_FONT,
    },
    "forest": {
        "id": "forest",
        "name": "Forest",
        "description": "Warm cream with green/brown/olive accents.",
        "background": "#F6F5EE",
        "card_bg": "#ECEBDF",
        "card_bg_alt": "#E2E1D2",
        "ink": "#22301F",
        "muted": "#5C6B52",
        "chip_text": "#F6F5EE",
        "accents": ["#3F7D4E", "#A3763B", "#6B8E23"],
        "title_font": TITLE_FONT,
        "label_font": LABEL_FONT,
        "body_font": BODY_FONT,
    },
    "slate": {
        "id": "slate",
        "name": "Slate",
        "description": "Corporate white/gray with blue/slate/sky accents.",
        "background": "#FFFFFF",
        "card_bg": "#F2F3F5",
        "card_bg_alt": "#E7E9EC",
        "ink": "#14181F",
        "muted": "#5B6472",
        "chip_text": "#FFFFFF",
        "accents": ["#1D4ED8", "#64748B", "#0EA5E9"],
        "title_font": TITLE_FONT,
        "label_font": LABEL_FONT,
        "body_font": BODY_FONT,
    },
}

DEFAULT_THEME = "midnight"


def get_theme(theme_id: str | None) -> dict:
    return THEMES.get((theme_id or DEFAULT_THEME).lower(), THEMES[DEFAULT_THEME])


def list_themes() -> list[dict]:
    return list(THEMES.values())
