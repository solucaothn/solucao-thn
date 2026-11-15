"""Campos de formulário compartilhados.

``select_field`` é o select com o estilo no Trigger (o botão visível): fundo
branco, borda e altura dos campos de texto, texto #1F1F1F e foco verde. Com o
estilo no Root (o atalho ``rx.select(...)``), o botão ficava com o fundo cinza,
parecendo desativado. Usado na edição de doação, em “Editar perfil” e nos
quatro selects do cadastro de doação (change fotos-formulario-doacao).

Fica num módulo próprio porque ``minhas_doacoes.py`` importa de
``cadastro_doacao.py``: o cadastro não pode importar de “Minhas doações”.
"""

from __future__ import annotations

from typing import Any

import reflex as rx


FIELD_TEXT = "#1F1F1F"
FIELD_BORDER = "1px solid #C8C8C8"
SELECT_PLACEHOLDER = "#333333"
FOCUS_GREEN = "#007A42"
LABEL_TEXT = "#333333"


def field_label(text: str, html_for: str) -> rx.Component:
    return rx.el.label(
        text,
        html_for=html_for,
        color=LABEL_TEXT,
        font_weight="700",
        font_size="0.8rem",
        width="100%",
    )


def select_field(
    label: str,
    options: tuple[str, ...] | rx.Var,
    value: rx.Var,
    on_change: Any,
    placeholder: str,
    field_id: str,
) -> rx.Component:
    if isinstance(options, rx.Var):
        items = [rx.foreach(options, lambda option: rx.select.item(option, value=option))]
    else:
        # Cada opção como filho do grupo (uma lista única virava um nó só).
        items = [rx.select.item(option, value=option) for option in options]
    return rx.vstack(
        field_label(label, field_id),
        rx.select.root(
            rx.select.trigger(
                placeholder=placeholder,
                id=field_id,
                class_name="edit-donation-select",
                width="100%",
                height="40px",
                background="#FFFFFF",
                color=FIELD_TEXT,
                border=FIELD_BORDER,
                border_radius="8px",
                box_shadow="none",
                cursor="pointer",
                _focus_visible={
                    "outline": f"2px solid {FOCUS_GREEN}",
                    "outlineOffset": "1px",
                },
                style={
                    "&[data-placeholder] .rt-SelectTriggerInner": {
                        "color": SELECT_PLACEHOLDER,
                    },
                },
            ),
            rx.select.content(rx.select.group(*items), high_contrast=True),
            value=value,
            on_change=on_change,
        ),
        align="start",
        spacing="2",
        width="100%",
    )
