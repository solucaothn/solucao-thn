import reflex as rx

from doafacil.login import LoginState


def _header() -> rx.Component:
    return rx.box(
        rx.image(
            src="/logo.svg",
            alt="DoaFácil",
            width="190px",
            height="72px",
            object_fit="contain",
            margin="0 auto",
        ),
        width="100%",
        background="white",
        padding="12px 24px",
    )


def _screen(card: rx.Component) -> rx.Component:
    return rx.box(
        rx.vstack(
            _header(),
            rx.vstack(
                card,
                align="center",
                spacing="4",
                width="100%",
                max_width="440px",
                padding="32px 24px",
            ),
            align="center",
            width="100%",
            spacing="0",
        ),
        min_height="100vh",
        width="100%",
        background="#FFF6E8",
        font_family="'LINE Seed JP', Arial, sans-serif",
    )


def _error_message() -> rx.Component:
    return rx.cond(
        LoginState.recovery_error_message != "",
        rx.text(
            LoginState.recovery_error_message,
            color="#B42318",
            role="alert",
            width="100%",
        ),
        rx.fragment(),
    )


def _submit_button(label: str, loading_label: str) -> rx.Component:
    return rx.button(
        rx.cond(LoginState.recovery_is_loading, loading_label, label),
        type="submit",
        disabled=LoginState.recovery_is_loading,
        background="#168447",
        color="white",
        width="100%",
        height="50px",
        border_radius="8px",
        cursor="pointer",
    )


def request_recovery_page() -> rx.Component:
    return _screen(
        rx.box(
            rx.vstack(
                rx.link(
                    "← Voltar",
                    href="/login",
                    on_click=LoginState.return_to_login,
                    color="#168447",
                    align_self="start",
                    cursor="pointer",
                ),
                rx.form(
                    rx.vstack(
                        rx.heading(
                            "Esqueceu a senha?",
                            color="#333333",
                            font_size="2rem",
                            font_weight="700",
                            text_align="center",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.text(
                                "E-mail",
                                color="#333333",
                                font_weight="700",
                                width="100%",
                            ),
                            rx.input(
                                name="email",
                                id="recovery-email",
                                type="email",
                                placeholder="Insira seu e-mail",
                                value=LoginState.recovery_email,
                                on_change=LoginState.set_recovery_email,
                                required=True,
                                width="100%",
                                height="48px",
                                background="white",
                                color="#333333",
                                border="1px solid #C8C8C8",
                                border_radius="8px",
                            ),
                            align="start",
                            spacing="2",
                            width="100%",
                        ),
                        _error_message(),
                        _submit_button("Continuar", "Enviando..."),
                        align="start",
                        spacing="5",
                        width="100%",
                    ),
                    on_submit=LoginState.request_recovery_code,
                    no_validate=True,
                    width="100%",
                ),
                align="center",
                spacing="5",
                width="100%",
            ),
            background="white",
            border_radius="16px",
            box_shadow="0 8px 24px rgba(0, 0, 0, 0.08)",
            padding=rx.breakpoints(initial="24px", md="40px"),
            width="100%",
            class_name="auth-card-enter",
        )
    )


def verify_recovery_page() -> rx.Component:
    return _screen(
        rx.box(
            rx.vstack(
                rx.link(
                    "← Voltar",
                    href="/recuperar-senha",
                    color="#168447",
                    align_self="start",
                    cursor="pointer",
                ),
                rx.form(
                    rx.vstack(
                        rx.heading(
                            "Verifique seu e-mail",
                            color="#333333",
                            font_size="2rem",
                            font_weight="700",
                            text_align="center",
                            width="100%",
                        ),
                        rx.text(
                            "Se existir uma conta com esse e-mail, enviamos "
                            "um código de 6 dígitos para ",
                            LoginState.masked_recovery_email,
                            ".",
                            color="#555555",
                            width="100%",
                            text_align="center",
                        ),
                        rx.vstack(
                            rx.text(
                                "Código",
                                color="#333333",
                                font_weight="700",
                                width="100%",
                            ),
                            rx.input(
                                name="code",
                                id="recovery-code",
                                type="text",
                                input_mode="numeric",
                                max_length=6,
                                pattern="[0-9]{6}",
                                placeholder="Digite o código de 6 dígitos",
                                required=True,
                                width="100%",
                                height="48px",
                                background="white",
                                color="#333333",
                                border="1px solid #C8C8C8",
                                border_radius="8px",
                            ),
                            align="start",
                            spacing="2",
                            width="100%",
                        ),
                        rx.text(
                            "Pode demorar um minutinho. Olha também no spam.",
                            color="#666666",
                            font_size="0.9rem",
                            width="100%",
                        ),
                        rx.cond(
                            LoginState.recovery_resend_seconds > 0,
                            rx.text(
                                LoginState.recovery_resend_label,
                                color="#555555",
                                font_size="0.9rem",
                            ),
                            rx.button(
                                "Reenviar código",
                                type="button",
                                on_click=LoginState.resend_recovery_code,
                                disabled=LoginState.recovery_is_loading,
                                color="#168447",
                                background="transparent",
                                border="none",
                                padding="0",
                                cursor="pointer",
                            ),
                        ),
                        _error_message(),
                        _submit_button("Continuar", "Verificando..."),
                        rx.link(
                            "Usar outro e-mail",
                            href="/recuperar-senha",
                            on_click=LoginState.use_another_recovery_email,
                            color="#168447",
                            align_self="center",
                        ),
                        align="start",
                        spacing="5",
                        width="100%",
                    ),
                    on_submit=LoginState.verify_recovery_code,
                    no_validate=True,
                    width="100%",
                ),
                align="center",
                spacing="5",
                width="100%",
            ),
            background="white",
            border_radius="16px",
            box_shadow="0 8px 24px rgba(0, 0, 0, 0.08)",
            padding=rx.breakpoints(initial="24px", md="40px"),
            width="100%",
            class_name="auth-card-enter",
        )
    )


def _password_field(
    label: str,
    name: str,
    field_id: str,
    placeholder: str,
    visible: rx.Var[bool],
    toggle: rx.EventHandler,
) -> rx.Component:
    return rx.vstack(
        rx.text(label, color="#333333", font_weight="700", width="100%"),
        rx.box(
            rx.input(
                name=name,
                id=field_id,
                type=rx.cond(visible, "text", "password"),
                placeholder=placeholder,
                required=True,
                width="100%",
                height="48px",
                background="white",
                color="#333333",
                border="1px solid #C8C8C8",
                border_radius="8px",
                padding_right="44px",
            ),
            rx.button(
                rx.cond(
                    visible,
                    rx.icon("eye-off", size=18),
                    rx.icon("eye", size=18),
                ),
                type="button",
                aria_label=rx.cond(visible, "Ocultar senha", "Mostrar senha"),
                on_click=toggle,
                position="absolute",
                right="8px",
                top="6px",
                width="36px",
                height="36px",
                padding="0",
                color="#168447",
                background="transparent",
                border="none",
                box_shadow="none",
                cursor="pointer",
            ),
            position="relative",
            width="100%",
        ),
        align="start",
        spacing="2",
        width="100%",
    )


def new_password_page() -> rx.Component:
    return _screen(
        rx.box(
            rx.vstack(
                rx.link(
                    "← Voltar",
                    href="/login",
                    on_click=LoginState.return_to_login,
                    color="#168447",
                    align_self="start",
                    cursor="pointer",
                ),
                rx.form(
                    rx.vstack(
                        rx.heading(
                            "Altere sua senha",
                            color="#333333",
                            font_size="2rem",
                            font_weight="700",
                            text_align="center",
                            width="100%",
                        ),
                        _password_field(
                            "Nova senha",
                            "password",
                            "recovery-password",
                            "Insira sua nova senha",
                            LoginState.recovery_password_visible,
                            LoginState.toggle_recovery_password_visibility,
                        ),
                        _password_field(
                            "Confirmar senha",
                            "password_confirmation",
                            "recovery-password-confirmation",
                            "Confirme sua nova senha",
                            LoginState.recovery_confirmation_visible,
                            LoginState.toggle_recovery_confirmation_visibility,
                        ),
                        _error_message(),
                        rx.cond(
                            LoginState.recovery_error_message
                            == "O tempo para trocar a senha acabou. "
                            "Peça um novo código.",
                            rx.link(
                                "Pedir um novo código",
                                href="/recuperar-senha",
                                on_click=LoginState.use_another_recovery_email,
                                color="#168447",
                                align_self="center",
                            ),
                            rx.fragment(),
                        ),
                        _submit_button("Salvar nova senha", "Salvando..."),
                        align="start",
                        spacing="5",
                        width="100%",
                    ),
                    on_submit=LoginState.confirm_recovery_password,
                    no_validate=True,
                    width="100%",
                ),
                align="center",
                spacing="5",
                width="100%",
            ),
            background="white",
            border_radius="16px",
            box_shadow="0 8px 24px rgba(0, 0, 0, 0.08)",
            padding=rx.breakpoints(initial="24px", md="40px"),
            width="100%",
            class_name="auth-card-enter",
        )
    )
