"""Shared visual tokens for the demonstrative fundraising pages."""

NAVY = "#0F2C59"
GOLD = "#D4AF37"
GOLD_HOVER = "#C59B27"
PAGE = "#F8FAFC"
WHITE = "#FFFFFF"
TEXT = "#1E293B"
MUTED = "#64748B"
BORDER = "#E2E8F0"

GOLD_BUTTON_STYLE = {
    "background": GOLD,
    "color": NAVY,
    "font_weight": "700",
    "border": "none",
    "cursor": "pointer",
    "_hover": {"background": GOLD_HOVER},
}

NAVY_BUTTON_STYLE = {
    "background": NAVY,
    "color": WHITE,
    "font_weight": "600",
    "border": "none",
    "cursor": "pointer",
    "_hover": {"background": "#173B70"},
}

CARD_STYLE = {
    "background": WHITE,
    "border": f"1px solid {BORDER}",
    "border_radius": "16px",
    "box_shadow": "0 8px 24px rgba(15, 44, 89, 0.06)",
}
