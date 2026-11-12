"""Cartões de doação da home, compartilhados com o perfil público de quem doa.

Ficam num módulo próprio para que a home (doafacil.doafacil, que registra as
rotas) e o perfil (doafacil.perfil_doador) usem a mesma validação, a mesma
regra do NOVO e o mesmo cartão, sem import circular.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import reflex as rx


GENERIC_DONATION_IMAGE = "/doacao-generica.svg"
AVAILABLE_CONDITIONS = {"Ótimo", "Bom", "Regular"}


def _is_new_donation(
    created_at: str | int, now: datetime | None = None
) -> bool:
    if isinstance(created_at, bool):
        raise ValueError("A data de criação da doação é inválida.")
    if isinstance(created_at, int):
        try:
            created = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(
                milliseconds=created_at
            )
        except OverflowError as error:
            raise ValueError(
                "A data de criação da doação é inválida."
            ) from error
    elif isinstance(created_at, str):
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    else:
        raise ValueError("A data de criação da doação é inválida.")

    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)

    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)
    age = current_time - created
    return timedelta(0) <= age <= timedelta(days=7)


def _parse_donations(
    payload: object, now: datetime | None = None
) -> list[dict[str, str | int | bool]]:
    if not isinstance(payload, list):
        raise ValueError("A resposta de doações recentes precisa ser uma lista.")

    donations: list[dict[str, str | int | bool]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue

        donation_id = item.get("id")
        created_at = item.get("created_at")
        title = item.get("title")
        photo = item.get("photo")
        condition = item.get("condition")

        if (
            isinstance(donation_id, bool)
            or not isinstance(donation_id, int)
            or isinstance(created_at, bool)
            or not isinstance(created_at, (str, int))
            or not isinstance(title, str)
            or not title.strip()
        ):
            continue
        if photo is not None and not isinstance(photo, str):
            continue
        if condition is not None and (
            not isinstance(condition, str)
            or condition not in AVAILABLE_CONDITIONS
        ):
            continue

        try:
            is_new = _is_new_donation(created_at, now)
        except ValueError:
            continue

        donations.append(
            {
                "id": donation_id,
                "title": title,
                "photo": photo or GENERIC_DONATION_IMAGE,
                "condition_label": (
                    f"Condição: {condition}"
                    if condition
                    else "Condição não informada"
                ),
                "is_new": is_new,
            }
        )

    if payload and not donations:
        raise ValueError("A resposta não contém nenhuma doação válida.")

    return donations


def donation_card(donation: rx.Var[dict[str, Any]]) -> rx.Component:
    """Cartão da home (carrossel), com 280 px fixos.

    Um argumento só: o rx.foreach passa o índice como segundo argumento.
    """
    return _donation_card(donation, fluid=False)


def donation_grid_card(donation: rx.Var[dict[str, Any]]) -> rx.Component:
    """O mesmo cartão ocupando a largura da célula da grade (perfil público)."""
    return _donation_card(donation, fluid=True)


def _donation_card(
    donation: rx.Var[dict[str, Any]], fluid: bool
) -> rx.Component:
    """Foto, NOVO, título, condição e “Acessar”."""
    size_props: dict[str, str] = (
        {"min_width": "0", "width": "100%", "max_width": "none"}
        if fluid
        else {"min_width": "280px", "width": "280px", "max_width": "280px"}
    )
    return rx.box(
        rx.cond(
            donation["photo"] == GENERIC_DONATION_IMAGE,
            rx.fragment(),
            rx.image(
                src=donation["photo"],
                alt=donation["title"],
                position="absolute",
                inset="0",
                width="100%",
                height="100%",
                object_fit="cover",
            ),
        ),
        rx.cond(
            donation["photo"] == GENERIC_DONATION_IMAGE,
            rx.image(
                src=donation["photo"],
                alt=donation["title"],
                position="absolute",
                top="4%",
                left="16%",
                width="68%",
                height="68%",
                object_fit="contain",
            ),
            rx.fragment(),
        ),
        rx.cond(
            donation["is_new"],
            rx.badge(
                "NOVO",
                position="absolute",
                top="12px",
                left="12px",
                background="#C62828",
                color="white",
            ),
            rx.fragment(),
        ),
        rx.vstack(
            rx.heading(
                donation["title"],
                font_size="1.1rem",
                font_weight="700",
                color="white",
                no_of_lines=2,
            ),
            rx.text(
                donation["condition_label"],
                color="white",
                font_size="0.85rem",
                white_space="normal",
                width="100%",
                overflow_wrap="anywhere",
            ),
            rx.link(
                rx.button(
                    "Acessar",
                    color_scheme="green",
                    variant="solid",
                    size="1",
                    cursor="pointer",
                    align_self="end",
                ),
                href=f"/doacao/{donation['id']}",
                align_self="end",
            ),
            align="start",
            spacing="2",
            position="absolute",
            bottom="0",
            left="0",
            width="100%",
            padding="16px",
            min_height="48%",
            background=rx.cond(
                donation["photo"] == GENERIC_DONATION_IMAGE,
                "linear-gradient(180deg, transparent 0%, "
                "rgba(15, 123, 62, 0.92) 55%)",
                "linear-gradient(180deg, transparent 0%, "
                "rgba(0, 0, 0, 0.78) 55%)",
            ),
        ),
        position="relative",
        overflow="hidden",
        border_radius="16px",
        **size_props,
        aspect_ratio="1 / 1",
        flex_shrink="0",
        scroll_snap_align="start",
        background=rx.cond(
            donation["photo"] == GENERIC_DONATION_IMAGE,
            "#DDF3E5",
            "#FFF6E8",
        ),
        box_shadow="0 4px 16px rgba(39, 39, 39, 0.12)",
    )
