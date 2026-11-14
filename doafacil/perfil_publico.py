"""Identificação pública da pessoa: Sobre, avatar, contadores e selo.

Usado na prévia da edição do perfil, no perfil público de quem doa, no cartão
da pessoa em “Minhas doações”, no cartão “Quem doa” do detalhe e no chat.

- Sobre: sempre texto simples (nunca HTML), preservando as quebras de linha;
  vazio, não mostra nada.
- Avatar: com foto, a imagem redonda (object-fit: cover) com texto alternativo
  “Foto de <primeiro nome>”; sem foto, o círculo com a inicial, como antes.
- Contadores (change perfil-credibilidade): “Doações” (disponíveis e
  reservadas) e “Doações realizadas” (concluídas), no singular com 1.
- Selo “E-mail verificado”: só com o e-mail verificado; sem ele, nada (nem
  texto, nem espaço reservado).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

import reflex as rx


ABOUT_MAX_LENGTH = 300
ABOUT_TEXT_COLOR = "#2A2A2A"

# Contadores: número em verde, rótulo em cinza, como em “Minhas doações”.
COUNT_NUMBER_COLOR = "#166B3B"
COUNT_LABEL_COLOR = "#555555"
ACTIVE_LABELS = ("Doação", "Doações")
COMPLETED_LABELS = ("Doação realizada", "Doações realizadas")

# Selo “E-mail verificado” (decisão 6): texto e ícone sobre o fundo claro,
# com borda suave para separar do cartão branco.
VERIFIED_LABEL = "E-mail verificado"
VERIFIED_ICON = "badge-check"
VERIFIED_TEXT_COLOR = "#166B3B"
VERIFIED_BACKGROUND = "#E8F5EC"
VERIFIED_BORDER = "#B7DEC4"


def count_label(count: int, singular: str, plural: str) -> str:
    return singular if count == 1 else plural


def parse_email_verified(value: object) -> bool:
    """O selo vem sempre como booleano; outro tipo (inclusive nulo ou
    ausente) é resposta inválida."""
    if not isinstance(value, bool):
        raise ValueError("O e-mail verificado precisa ser verdadeiro ou falso.")
    return value


def parse_count(value: object) -> int:
    """Contador: inteiro >= 0 (booleano não vale)."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("O contador precisa ser um inteiro não negativo.")
    return value


def parse_counts(value: object) -> tuple[int, int]:
    """Objeto {active, completed} → (ativas, concluídas)."""
    if not isinstance(value, dict):
        raise ValueError("Os contadores precisam ser um objeto.")
    return parse_count(value.get("active")), parse_count(value.get("completed"))


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


def _count(value: rx.Var, singular: str, plural: str) -> rx.Component:
    return rx.vstack(
        rx.text(
            value,
            color=COUNT_NUMBER_COLOR,
            font_size="1.5rem",
            font_weight="700",
            line_height="1",
        ),
        rx.text(
            rx.cond(value == 1, singular, plural),
            color=COUNT_LABEL_COLOR,
            font_size="0.85rem",
            text_align="center",
        ),
        class_name="profile-count",
        align="center",
        spacing="1",
        min_width="0",
    )


def donation_counts(active: rx.Var, completed: rx.Var, **props: Any) -> rx.Component:
    """“Doações” (ativas) e “Doações realizadas” (concluídas), lado a lado."""
    return rx.hstack(
        _count(active, *ACTIVE_LABELS),
        _count(completed, *COMPLETED_LABELS),
        class_name="profile-counts",
        spacing="6",
        align="start",
        wrap="wrap",
        **props,
    )


def verified_badge(flag: rx.Var, **props: Any) -> rx.Component:
    """Pílula com o ícone (decorativo) e “E-mail verificado”; falso, nada."""
    return rx.cond(
        flag,
        rx.hstack(
            rx.icon(
                VERIFIED_ICON,
                size=16,
                color=VERIFIED_TEXT_COLOR,
                aria_hidden="true",
                flex_shrink="0",
            ),
            rx.text(
                VERIFIED_LABEL,
                color=VERIFIED_TEXT_COLOR,
                font_size="0.8rem",
                font_weight="700",
                line_height="1.2",
            ),
            class_name="verified-badge",
            spacing="1",
            align="center",
            display="inline-flex",
            width="fit-content",
            max_width="100%",
            padding="4px 10px",
            background=VERIFIED_BACKGROUND,
            border=f"1px solid {VERIFIED_BORDER}",
            border_radius="999px",
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
