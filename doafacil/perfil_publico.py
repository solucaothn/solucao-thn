"""Identificação pública da pessoa: Sobre e avatar (foto de perfil ou inicial).

Usado na prévia da edição do perfil, no perfil público de quem doa, no cartão
da pessoa em “Minhas doações”, no cartão “Quem doa” do detalhe e no chat.

- Sobre: sempre texto simples (nunca HTML), preservando as quebras de linha;
  vazio, não mostra nada.
- Avatar: com foto, a imagem redonda (object-fit: cover) com texto alternativo
  “Foto de <primeiro nome>”; sem foto, o círculo com a inicial, como antes.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import reflex as rx


ABOUT_MAX_LENGTH = 300
ABOUT_TEXT_COLOR = "#2A2A2A"


def parse_about(value: object) -> str:
    """Sobre da resposta: texto (sem os espaços das pontas) ou nulo → vazio.

    Outro tipo é resposta inválida.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("O Sobre precisa ser texto ou nulo.")
    return value.strip()


def parse_photo_url(value: object) -> str:
    """URL pública da foto de perfil: http(s) ou nulo (sem foto) → vazio.

    Texto vazio também é “sem foto”. Outro tipo ou outro esquema é resposta
    inválida.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        raise ValueError("A foto precisa ser uma URL ou nula.")
    url = value.strip()
    if not url:
        return ""
    if urlsplit(url).scheme not in {"http", "https"} or not urlsplit(url).netloc:
        raise ValueError("A foto precisa ser uma URL HTTP(S).")
    return url


def about_text(value: rx.Var, **props: object) -> rx.Component:
    """O Sobre como texto simples, com as quebras de linha; vazio, nada."""
    return rx.cond(
        value != "",
        rx.text(
            value,
            class_name="profile-about-text",
            color=ABOUT_TEXT_COLOR,
            font_size="0.95rem",
            line_height="1.5",
            white_space="pre-wrap",
            overflow_wrap="anywhere",
            width="100%",
            **props,
        ),
        rx.fragment(),
    )


def avatar(
    photo: rx.Var,
    initial: rx.Var,
    first_name: rx.Var,
    size: Any,
    *,
    background: str,
    color: str,
    font_size: Any = "1rem",
    **props: Any,
) -> rx.Component:
    """Foto de perfil redonda ou, sem foto, o círculo com a inicial.

    Mesmo tamanho nos dois casos. A foto tem texto alternativo com o primeiro
    nome; o círculo da inicial é decorativo (o nome já aparece ao lado).
    """
    return rx.cond(
        photo != "",
        rx.image(
            src=photo,
            alt=rx.Var.create("Foto de ") + first_name.to(str),
            class_name="profile-avatar-photo",
            width=size,
            height=size,
            min_width=size,
            border_radius="999px",
            object_fit="cover",
            flex_shrink="0",
            background=background,
            **props,
        ),
        rx.box(
            rx.text(
                initial,
                color=color,
                font_weight="700",
                font_size=font_size,
                line_height="1",
            ),
            aria_hidden="true",
            class_name="profile-avatar-initial",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
            width=size,
            height=size,
            min_width=size,
            border_radius="999px",
            background=background,
            **props,
        ),
    )
