"""Texto de “Sobre” do perfil: leitura da resposta do Xano e exibição.

Usado na prévia da edição do perfil, no perfil público de quem doa e no cartão
da pessoa em “Minhas doações”. O texto é sempre mostrado como texto simples
(nunca HTML), preservando as quebras de linha; vazio, não mostra nada.
"""

from __future__ import annotations

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
