import reflex as rx

config = rx.Config(
    app_name="doafacil",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
        # Tema claro fixo (change paginas-institucionais): o site só tem o
        # visual claro, e com o tema seguindo o sistema os componentes do
        # Radix ficavam escuros no modo escuro (acordeão preto, tabela com
        # texto claro, links azuis). O acento azul é o padrão do Reflex.
        rx.plugins.RadixThemesPlugin(
            theme=rx.theme(appearance="light", accent_color="blue"),
        ),
    ]
)
