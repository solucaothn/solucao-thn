"""Páginas institucionais (change paginas-institucionais, spec
institutional-pages): Central de ajuda e categorias, Segurança e
transparência, Termos de uso, Política de privacidade, Quem somos e Contato.

Páginas estáticas, sem Xano. Layout do Figma (docs/design/19-*.png a
23-*.png); os textos do Figma valem onde descrevem o DoaFácil. Os Termos e a
Privacidade foram reescritos (os do Figma eram de uma plataforma de doações
em dinheiro) e as frases falsas das outras telas foram trocadas (decisão 9 do
design). Todo texto escrito ou trocado aqui passa pela revisão do Higor.
"""

from __future__ import annotations

import unicodedata
from typing import Any

import reflex as rx

from doafacil.cabecalho import FOCUS_RING, HEADER_MAX_WIDTH, HEADER_PADDING_X, back_link
from doafacil.chat import CHAT_FAB_CLEARANCE, chat_fab
from doafacil.navegacao import logo_header
from doafacil.rodape import (
    CONTACT_EMAIL,
    INSTITUTIONAL_ROUTES,
    contact_href,
    public_home_footer,
)

# Cores (as mesmas da home): textos verdes sobre o creme em #166B3B (6,1:1).
CREAM = "#FFF6E8"
GREEN = "#168447"
DARK_GREEN = "#166B3B"
TEXT_DARK = "#1F1F1F"
TEXT_BODY = "#2A2A2A"
TEXT_MUTED = "#555555"
BORDER = "#D9D9D9"
READING_WIDTH = "860px"
HELP_ROUTE = INSTITUTIONAL_ROUTES["duvidas"]
# Lupa e placeholder da busca, sobre o branco: 8,9:1 e 5,3:1.
SEARCH_ICON_COLOR = "#4A4A4A"
SEARCH_PLACEHOLDER_COLOR = "#6B6B6B"
# Cabeçalho da tabela da Privacidade.
TABLE_HEADER_BACKGROUND = "#F3F1EC"
ACADEMIC_NOTICE ="Documento de projeto acadêmico, sem valor jurídico."
# Reserva: só aparece se o CONTACT_EMAIL (rodape.py) ficar vazio.
CONTACT_PENDING_TEXT = "O canal de contato do projeto ainda vai ser publicado."
# Nos parágrafos dos Termos e da Privacidade, “{email}” vira o link mailto:
# do CONTACT_EMAIL; sem e-mail, o parágrafo inteiro vira o texto pendente.
EMAIL_MARK = "{email}"
CONTACT_DATA_TEXT = "Pelo mesmo e-mail você pode pedir para saber, corrigir ou apagar os seus dados."


# ---------------------------------------------------------------------------
# Conteúdo da Central de ajuda
# ---------------------------------------------------------------------------

def _q(qid: str, question: str, answer: str) -> dict[str, str]:
    return {"id": qid, "question": question, "answer": answer}


# Perguntas do Figma: “O DoaFácil cobra alguma taxa?”, “Posso doar qualquer
# coisa?”, “Quem paga a entrega do item?”, “A pessoa não respondeu. O que eu
# faço?”, as 6 de “Doar um item” e “Preciso pagar para publicar uma doação?”.
# Respostas do Figma: a da taxa e a de “Como publico uma doação?”. As demais
# foram escritas a partir do que o site faz hoje.
HELP_CATEGORIES: list[dict[str, Any]] = [
    {
        "slug": "primeiros-passos",
        "name": "Primeiros passos",
        "topic": "como começar a usar o DoaFácil",
        "questions": [
            _q(
                "o-que-e",
                "O que é o DoaFácil?",
                "Um site que conecta quem tem objetos para doar com quem precisa deles. É um "
                "projeto acadêmico: não há venda, troca por dinheiro nem cobrança.",
            ),
            _q(
                "taxa",
                "O DoaFácil cobra alguma taxa?",
                "Não. O DoaFácil não cobra nada de quem doa nem de quem recebe, e não intermedeia "
                "dinheiro. A combinação da entrega é feita direto entre as duas pessoas.",
            ),
            _q(
                "pagar-publicar",
                "Preciso pagar para publicar uma doação?",
                "Não. Publicar, procurar e conversar sobre doações é gratuito.",
            ),
            _q(
                "criar-conta",
                "Como crio minha conta?",
                "Clique em Entrar e depois em Criar conta. Informe nome, e-mail, cidade, estado e "
                "senha, e confirme o código de 6 dígitos que enviamos para o seu e-mail.",
            ),
        ],
    },
    {
        "slug": "doar-um-item",
        "name": "Doar um item",
        "topic": "publicar e gerenciar suas doações",
        "questions": [
            _q(
                "como-publico",
                "Como publico uma doação?",
                "Clique em Quero Doar, preencha as cinco etapas com fotos, estado de conservação e "
                "categoria, e publique. A doação aparece em Explorar na mesma hora.",
            ),
            _q(
                "quantas-fotos",
                "Quantas fotos posso colocar?",
                "De 1 a 5 fotos por doação, em JPEG, PNG, GIF ou WEBP, com até 5 MB cada. A "
                "primeira foto é a capa, e você pode mudar a ordem antes de publicar.",
            ),
            _q(
                "editar",
                "Posso editar uma doação já publicada?",
                "Sim. Em Minhas doações, escolha a doação e use Editar para mudar título, "
                "descrição, categoria, condição e forma de contato. A entrega é sempre “A combinar”. "
                "Doações concluídas não podem mais ser editadas.",
            ),
            _q(
                "marcar-entregue",
                "Como marco uma doação como entregue?",
                "Em Minhas doações, marque a doação como concluída. Ela sai de Explorar e passa a "
                "contar em Pessoas alcançadas.",
            ),
            _q(
                "cancelar",
                "Posso cancelar uma doação?",
                "Sim. Em Minhas doações, use Apagar. A doação e as conversas sobre ela são apagadas, "
                "e as fotos deixam de aparecer no site.",
            ),
            _q(
                "categoria",
                "Por que preciso escolher uma categoria?",
                "A categoria ajuda quem procura a encontrar o item em Explorar e na lista de "
                "Categorias.",
            ),
        ],
    },
    {
        "slug": "receber-uma-doacao",
        "name": "Receber uma doação",
        "topic": "encontrar e combinar uma doação",
        "questions": [
            _q(
                "encontrar",
                "Como encontro uma doação?",
                "Use Explorar Doações ou a busca da página inicial. Você pode filtrar por texto, "
                "categoria e estado.",
            ),
            _q(
                "falar-com-doador",
                "Como falo com quem está doando?",
                "No detalhe da doação, use o contato que a pessoa escolheu: o chat do DoaFácil ou o "
                "e-mail. Para os dois, é preciso entrar na sua conta.",
            ),
            _q(
                "quem-paga-entrega",
                "Quem paga a entrega do item?",
                "O DoaFácil não cobra nada e não cuida da entrega. Quem doa e quem recebe combinam "
                "juntos como e onde entregar, inclusive se houver algum custo de transporte.",
            ),
            _q(
                "mais-de-uma",
                "Posso pedir mais de uma doação?",
                "Pode. Cada doação é combinada com a pessoa que a publicou.",
            ),
            _q(
                "reservada",
                "O que significa uma doação reservada?",
                "Quem doou marcou a doação como reservada, em geral porque já combinou com alguém. "
                "Enquanto estiver reservada, ela não aparece em Explorar, mas quem já conversa sobre "
                "ela continua no chat.",
            ),
        ],
    },
    {
        "slug": "conta-e-perfil",
        "name": "Conta e perfil",
        "topic": "a sua conta e o seu perfil",
        "questions": [
            _q(
                "editar-perfil",
                "Como edito meu perfil?",
                "No menu da conta, use Editar perfil para mudar nome, foto, texto Sobre, cidade e "
                "estado.",
            ),
            _q(
                "trocar-email",
                "Posso trocar meu e-mail?",
                "Por enquanto, não. O e-mail aparece em Editar perfil só para leitura.",
            ),
            _q(
                "esqueci-senha",
                "Esqueci minha senha. E agora?",
                "Na tela de entrar, use Esqueci minha senha. Enviamos um código de 6 dígitos, "
                "válido por 10 minutos, para você criar uma senha nova.",
            ),
            _q(
                "perfil-publico",
                "O que aparece no meu perfil público?",
                "Seu primeiro nome, a foto, a cidade e o estado, o texto Sobre, as suas doações "
                "disponíveis e, se o seu e-mail foi confirmado, o selo E-mail verificado. Seu e-mail "
                "e sua senha não aparecem.",
            ),
        ],
    },
    {
        "slug": "seguranca",
        "name": "Segurança",
        "topic": "doar e receber com segurança",
        "questions": [
            _q(
                "doar-qualquer-coisa",
                "Posso doar qualquer coisa?",
                "Não. O DoaFácil é para objetos físicos seus, em condições de uso. Alimentos não "
                "são aceitos, e itens ilegais ou perigosos são proibidos pelos Termos de uso.",
            ),
            _q(
                "verifica-itens",
                "O DoaFácil verifica os itens?",
                "Não. O site não confere os itens: confira o objeto na hora da entrega e combine "
                "tudo antes, pelo chat ou pelo e-mail.",
            ),
            _q(
                "combinar-com-seguranca",
                "Como combino uma entrega com segurança?",
                "Prefira lugares públicos e movimentados, vá com alguém se puder e não compartilhe "
                "dados que você não precisa, como documentos ou endereço completo.",
            ),
            _q(
                "email-visivel",
                "Meu e-mail fica visível?",
                "Só quando você escolhe o contato por e-mail numa doação. Nesse caso, quem tem "
                "conta pode ver o e-mail para falar com você sobre aquela doação.",
            ),
            _q(
                "selo",
                "O que é o selo E-mail verificado?",
                "Ele mostra que o e-mail da conta foi confirmado com o código enviado no cadastro.",
            ),
        ],
    },
    {
        "slug": "conversas",
        "name": "Conversas",
        "topic": "o chat entre quem doa e quem recebe",
        "questions": [
            _q(
                "como-chat",
                "Como funciona o chat?",
                "Cada conversa é sobre uma doação em que quem doa escolheu o chat. Abra pelo botão "
                "de chat no detalhe da doação ou pelo botão de mensagens no canto da tela. Depois "
                "que a doação é concluída, não dá mais para enviar mensagens nela.",
            ),
            _q(
                "nao-respondeu",
                "A pessoa não respondeu. O que eu faço?",
                "Espere um pouco: a outra pessoa vê as mensagens novas quando volta ao site. Se não "
                "houver resposta, procure outras doações em Explorar.",
            ),
            _q(
                "editar-mensagem",
                "Posso editar uma mensagem?",
                "Sim, as suas próprias mensagens, até 15 minutos depois de enviar e enquanto a "
                "doação não estiver concluída.",
            ),
        ],
    },
]
# “Mais perguntadas” (Figma): ids de perguntas que estão nas categorias.
MOST_ASKED_IDS = ("taxa", "doar-qualquer-coisa", "quem-paga-entrega", "nao-respondeu")
# Atalhos de busca do Figma: rótulo → termo procurado.
SEARCH_SHORTCUTS = (
    ("Tem taxa?", "taxa"),
    ("Quem paga a entrega", "entrega"),
    ("O que não pode doar", "doar qualquer"),
)

ALL_QUESTIONS: list[dict[str, str]] = [
    {**question, "category": category["slug"]}
    for category in HELP_CATEGORIES
    for question in category["questions"]
]
_QUESTIONS_BY_ID = {question["id"]: question for question in ALL_QUESTIONS}
MOST_ASKED = [_QUESTIONS_BY_ID[qid] for qid in MOST_ASKED_IDS]
_CATEGORIES_BY_SLUG = {category["slug"]: category for category in HELP_CATEGORIES}


def normalize(text: object) -> str:
    """Minúsculas e sem acento, para a busca."""
    if not isinstance(text, str):
        return ""
    plain = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in plain if not unicodedata.combining(char)).strip()


def search_questions(query: object) -> list[dict[str, str]]:
    """Perguntas cuja pergunta ou resposta contém o termo (sem acento e sem
    diferenciar maiúsculas)."""
    term = normalize(query)
    if not term:
        return []
    return [
        question
        for question in ALL_QUESTIONS
        if term in normalize(question["question"]) or term in normalize(question["answer"])
    ]


def category_count_label(category: dict[str, Any]) -> str:
    count = len(category["questions"])
    return "1 pergunta" if count == 1 else f"{count} perguntas"


class HelpState(rx.State):
    query: str = ""

    @rx.event
    def set_query(self, value: str) -> None:
        self.query = value if isinstance(value, str) else ""

    @rx.event
    def clear_query(self) -> None:
        self.query = ""

    @rx.var
    def searching(self) -> bool:
        return bool(normalize(self.query))

    @rx.var
    def results(self) -> list[dict[str, str]]:
        return search_questions(self.query)

    @rx.var
    def results_title(self) -> str:
        count = len(search_questions(self.query))
        term = self.query.strip()
        if count == 0:
            return f"Nenhuma resposta para “{term}”"
        noun = "resultado" if count == 1 else "resultados"
        return f"{count} {noun} para “{term}”"


class HelpCategoryState(rx.State):
    slug: str = ""

    @rx.event
    def load(self) -> None:
        path = str(self.router.url.path).rstrip("/")
        self.slug = path.rsplit("/", 1)[-1] if "/duvidas/" in path + "/" else ""

    @rx.var
    def found(self) -> bool:
        return self.slug in _CATEGORIES_BY_SLUG

    @rx.var
    def name(self) -> str:
        category = _CATEGORIES_BY_SLUG.get(self.slug)
        return category["name"] if category else ""

    @rx.var
    def subtitle(self) -> str:
        category = _CATEGORIES_BY_SLUG.get(self.slug)
        if not category:
            return ""
        return f"{category_count_label(category)} sobre {category['topic']}."

    @rx.var
    def questions(self) -> list[dict[str, str]]:
        category = _CATEGORIES_BY_SLUG.get(self.slug)
        return list(category["questions"]) if category else []


# ---------------------------------------------------------------------------
# Componentes comuns
# ---------------------------------------------------------------------------

def _link(label: str, href: str, **props: Any) -> rx.Component:
    return rx.link(
        label,
        href=href,
        color=DARK_GREEN,
        font_weight="700",
        underline="always",
        _focus_visible=FOCUS_RING,
        **props,
    )


def institutional_shell(*content: rx.Component, back: rx.Component | None = None) -> rx.Component:
    """Cabeçalho com o logotipo, “Voltar”, o conteúdo (com animação de
    entrada), o rodapé da home e o botão flutuante do chat. A página ocupa
    pelo menos a altura da tela e o conteúdo cresce, então o rodapé fica no
    fim mesmo numa página curta (sem faixa creme abaixo dele)."""
    return rx.box(
        logo_header(),
        rx.box(
            back if back is not None else back_link(),
            rx.box(
                *content,
                display="flex",
                flex_direction="column",
                gap="24px",
                width="100%",
                min_width="0",
                class_name="page-fade-enter",
            ),
            display="flex",
            flex_direction="column",
            gap="16px",
            width="100%",
            max_width=HEADER_MAX_WIDTH,
            margin="0 auto",
            padding_x=HEADER_PADDING_X,
            padding_top="8px",
            padding_bottom="64px",
            box_sizing="border-box",
            overflow_wrap="anywhere",
            flex="1 0 auto",
            class_name="institutional-main",
        ),
        public_home_footer(),
        chat_fab(),
        class_name="institutional-page",
        display="flex",
        flex_direction="column",
        width="100%",
        min_height="100vh",
        background=CREAM,
        font_family="'LINE Seed JP', Arial, sans-serif",
    )


def _h1(text: str | rx.Var, **props: Any) -> rx.Component:
    """O título de nível 1 da página (um só por página)."""
    style = {
        "color": TEXT_DARK,
        "font_weight": "700",
        "line_height": "1.15",
        "style": {"fontSize": rx.breakpoints(initial="2rem", md="2.5rem")},
        **props,
    }
    return rx.heading(text, as_="h1", **style)


def _h2(text: str | rx.Var, **props: Any) -> rx.Component:
    """Título de nível 2; cor, peso e tamanho podem ser trocados."""
    style = {"color": DARK_GREEN, "font_weight": "700", "font_size": "1.5rem", **props}
    return rx.heading(text, as_="h2", **style)


def _sr_only(component: rx.Component) -> rx.Component:
    """Visível só para leitor de tela (mantém os títulos em ordem)."""
    return rx.box(
        component,
        style={
            "position": "absolute",
            "width": "1px",
            "height": "1px",
            "overflow": "hidden",
            "clip": "rect(0 0 0 0)",
            "whiteSpace": "nowrap",
        },
    )


# Fotos do Figma (change fotos-site). Os arquivos são JPEG 2x, gerados com
# scripts/converter_fotos.py; os cantos arredondados vêm do CSS.
# O raio de cada foto é o dos cantos transparentes do PNG exportado (metade,
# porque o arquivo é 2x).
PHOTO_CREDIT_COLOR = TEXT_MUTED
ABOUT_PHOTO = {
    "src": "/sobre/quem-somos.jpg",
    "alt": (
        "Grupo de jovens agachados no chão de um escritório, sorrindo e apontando "
        "para papéis com gráficos."
    ),
    "credit": "Foto: Freepik",
    "width": 375,
    "height": 421,
    "radius": "8px",
}
SECURITY_PHOTO = {
    "src": "/seguranca/seguranca.jpg",
    "alt": (
        "Cinco jovens sorrindo, de pé em fila num escritório claro, usando fones de "
        "ouvido com microfone."
    ),
    "credit": "Foto: Freepik",
    "width": 507,
    "height": 339,
    "radius": "16px",
}


def _photo(
    src: str, alt: str, credit: str, width: int, height: int, radius: str, **props: Any
) -> rx.Component:
    """Foto com a proporção do retângulo do Figma (width × height), que
    preenche a área sem distorcer, e o crédito da origem logo abaixo."""
    children = [
        rx.image(
            src=src,
            alt=alt,
            width="100%",
            height="auto",
            display="block",
            object_fit="cover",
            border_radius=radius,
            overflow="hidden",
            style={"aspectRatio": f"{width} / {height}"},
        )
    ]
    if credit:
        children.append(
            rx.el.figcaption(
                credit,
                class_name="photo-credit",
                color=PHOTO_CREDIT_COLOR,
                font_size="0.75rem",
                line_height="1.3",
                margin_top="6px",
            )
        )
    return rx.el.figure(
        *children,
        class_name="institutional-photo",
        width="100%",
        max_width=f"{width}px",
        margin="0",
        justify_self=rx.breakpoints(initial="center", md="end"),
        **props,
    )


# ---------------------------------------------------------------------------
# Central de ajuda
# ---------------------------------------------------------------------------

# Item aberto: fundo creme claro, com a pergunta e a resposta escuras. As
# cores são fixas em todos os estados (fechado, aberto, mouse e foco) e as
# variáveis do Radix são redefinidas aqui, para o acordeão não seguir o tema
# escuro do sistema (era isso que deixava o item aberto preto).
ACCORDION_OPEN_BACKGROUND = "#FFFAF1"
ACCORDION_HOVER_BACKGROUND = "#F7F3EA"
_TRIGGER_COLORS = {"color": TEXT_BODY, "background": "transparent"}
ACCORDION_STYLE = {
    "--accent-4": ACCORDION_HOVER_BACKGROUND,
    "--accent-11": TEXT_BODY,
    "--accent-contrast": TEXT_BODY,
    "--gray-a6": BORDER,
    "width": "100%",
    "background": "white",
    "color": TEXT_BODY,
    "border": f"1px solid {BORDER}",
    "borderRadius": "8px",
    "overflow": "hidden",
    "& .AccordionItem": {"borderBottom": f"1px solid {BORDER}", "background": "white"},
    "& .AccordionItem:last-child": {"borderBottom": "none"},
    "& .AccordionItem[data-state='open']": {"background": ACCORDION_OPEN_BACKGROUND},
    "& .AccordionHeader": {"margin": "0"},
    "& .AccordionItem .AccordionTrigger, & .AccordionItem .AccordionTrigger[data-state='open']": _TRIGGER_COLORS,
    "& .AccordionItem .AccordionTrigger:hover": {"color": TEXT_BODY, "background": ACCORDION_HOVER_BACKGROUND},
    "& .AccordionItem .AccordionChevron": {"color": TEXT_BODY},
    "& .AccordionItem .AccordionContent": {"color": TEXT_MUTED, "background": "transparent"},
    "& .AccordionTrigger": {
        "width": "100%",
        "minHeight": "58px",
        "padding": "18px 24px",
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "gap": "16px",
        "textAlign": "left",
        "background": "transparent",
        "color": TEXT_BODY,
        "fontFamily": "inherit",
        "fontWeight": "700",
        "fontSize": "1rem",
        "cursor": "pointer",
    },
    "& .AccordionTrigger:focus-visible": {"outline": f"2px solid {GREEN}", "outlineOffset": "-2px"},
    "& .AccordionContent": {"padding": "0 24px 18px", "color": TEXT_MUTED, "lineHeight": "1.5"},
}


def _question_item(question: rx.Var[dict[str, str]] | dict[str, str]) -> rx.Component:
    return rx.accordion.item(
        header=question["question"],
        content=question["answer"],
        value=question["id"],
    )


def faq_accordion(questions: rx.Var | list[dict[str, str]]) -> rx.Component:
    """Perguntas expansíveis (Radix): o cabeçalho é um botão (Enter e Espaço),
    com aria-expanded; abrir uma fecha a outra (tipo single, recolhível)."""
    items = (
        [_question_item(question) for question in questions]
        if isinstance(questions, list)
        else [rx.foreach(questions, _question_item)]
    )
    return rx.accordion.root(
        *items,
        type="single",
        collapsible=True,
        variant="ghost",
        color_scheme="gray",
        class_name="faq-accordion",
        style=ACCORDION_STYLE,
    )


def _email_link(**props: Any) -> rx.Component:
    """O e-mail de contato, escrito e com link mailto:."""
    email = CONTACT_EMAIL.strip()
    return _link(email, f"mailto:{email}", **props)


def _with_email(text: str, **props: Any) -> rx.Component:
    """Um parágrafo com o marcador {email}: o e-mail entra como link. Sem
    e-mail definido, o parágrafo vira o texto pendente (reserva)."""
    if not CONTACT_EMAIL.strip():
        return rx.text(CONTACT_PENDING_TEXT, **props)
    before, _, after = text.partition(EMAIL_MARK)
    return rx.text(before, _email_link(), after, **props)


def _paragraph(text: str) -> rx.Component:
    props = {"color": TEXT_BODY, "line_height": "1.6", "margin_top": "10px"}
    return _with_email(text, **props) if EMAIL_MARK in text else rx.text(text, **props)


def contact_box() -> rx.Component:
    """“Não encontrou o que procurava?” (Figma), com o e-mail do projeto."""
    return rx.flex(
        rx.box(
            rx.text("Não encontrou o que procurava?", color=DARK_GREEN, font_weight="700", font_size="1.15rem"),
            _with_email(f"Escreva para {EMAIL_MARK}", color=TEXT_MUTED, font_size="0.85rem", class_name="help-contact-text"),
        ),
        rx.link(
            "Fale com a gente",
            href=contact_href(),
            class_name="help-contact-button",
            display="inline-flex",
            align_items="center",
            min_height="44px",
            padding="0 18px",
            border_radius="999px",
            background=GREEN,
            color="white",
            underline="none",
            white_space="nowrap",
            _focus_visible=FOCUS_RING,
        ),
        class_name="help-contact-box",
        justify="between",
        align="center",
        wrap="wrap",
        gap="16px",
        width="100%",
        padding="24px 28px",
        background="#FFF1D6",
        border="1px solid #E8D9B5",
        border_radius="8px",
        box_sizing="border-box",
    )


def _category_card(category: dict[str, Any]) -> rx.Component:
    return rx.link(
        rx.text(category["name"], color=DARK_GREEN, font_weight="700", font_size="1.1rem"),
        rx.text(category_count_label(category), color=TEXT_MUTED, font_size="0.85rem"),
        href=f"{HELP_ROUTE}/{category['slug']}",
        class_name="help-category-card",
        display="flex",
        flex_direction="column",
        gap="4px",
        padding="20px",
        min_height="81px",
        background="white",
        border=f"1px solid {BORDER}",
        border_radius="8px",
        underline="none",
        _hover={"borderColor": GREEN},
        _focus_visible=FOCUS_RING,
    )


def help_page() -> rx.Component:
    """Central de ajuda (Figma 479:2738, 621:2648 e 621:2752)."""
    return institutional_shell(
        rx.box(
            _h1("Central de ajuda"),
            rx.text("Encontre uma resposta ou fale com a gente.", color=TEXT_DARK, font_size="1.15rem", margin_top="8px"),
        ),
        rx.debounce_input(
            rx.input(
                rx.input.slot(rx.icon("search", size=20, color=SEARCH_ICON_COLOR, aria_hidden="true")),
                value=HelpState.query,
                on_change=HelpState.set_query,
                placeholder="Buscar por uma dúvida",
                aria_label="Buscar por uma dúvida",
                id="help-search",
                class_name="help-search",
                size="3",
                width="100%",
                background="white",
                color=TEXT_DARK,
                # Texto, placeholder e lupa com cor fixa (não seguem o tema
                # escuro do sistema).
                style={
                    "--gray-12": TEXT_DARK,
                    "--gray-a10": SEARCH_PLACEHOLDER_COLOR,
                    "--gray-a11": SEARCH_ICON_COLOR,
                    "& input::placeholder": {"color": SEARCH_PLACEHOLDER_COLOR},
                },
            ),
            debounce_timeout=300,
        ),
        rx.flex(
            *[
                rx.button(
                    label,
                    on_click=HelpState.set_query(term),
                    class_name="help-shortcut",
                    variant="outline",
                    color=DARK_GREEN,
                    border_color=GREEN,
                    radius="full",
                    min_height="44px",
                    _focus_visible=FOCUS_RING,
                )
                for label, term in SEARCH_SHORTCUTS
            ],
            wrap="wrap",
            gap="10px",
        ),
        rx.cond(
            HelpState.searching,
            rx.box(
                _h2(HelpState.results_title, role="status"),
                rx.cond(
                    HelpState.results.length() > 0,
                    faq_accordion(HelpState.results),
                    rx.box(
                        rx.text("Tente outra palavra ou escolha uma categoria.", color=TEXT_MUTED),
                        rx.button(
                            "Limpar a busca",
                            on_click=HelpState.clear_query,
                            variant="ghost",
                            color=DARK_GREEN,
                            min_height="44px",
                            _focus_visible=FOCUS_RING,
                        ),
                        class_name="help-empty",
                        padding="32px 24px",
                        background="white",
                        border=f"1px solid {BORDER}",
                        border_radius="8px",
                        text_align="center",
                    ),
                ),
                display="flex",
                flex_direction="column",
                gap="16px",
            ),
            rx.box(
                _sr_only(_h2("Categorias")),
                rx.grid(
                    *[_category_card(category) for category in HELP_CATEGORIES],
                    class_name="help-categories",
                    gap="24px",
                    width="100%",
                    style={"gridTemplateColumns": "repeat(auto-fill, minmax(min(100%, 280px), 1fr))"},
                ),
                _h2("Mais perguntadas", margin_top="32px", margin_bottom="16px"),
                faq_accordion(MOST_ASKED),
                position="relative",
            ),
        ),
        contact_box(),
    )


def help_category_page() -> rx.Component:
    """Uma categoria da Central de ajuda (Figma 621:2530)."""
    return institutional_shell(
        rx.cond(
            HelpCategoryState.found,
            rx.fragment(
                rx.box(
                    _h1(HelpCategoryState.name),
                    rx.text(HelpCategoryState.subtitle, color=TEXT_DARK, font_size="1.15rem", margin_top="8px"),
                ),
                rx.box(_sr_only(_h2("Perguntas")), faq_accordion(HelpCategoryState.questions), position="relative"),
            ),
            rx.box(
                _h1("Categoria não encontrada"),
                rx.text("Essa categoria não existe na Central de ajuda.", color=TEXT_MUTED, margin_top="8px"),
                _link("Ver todas as dúvidas frequentes", HELP_ROUTE, margin_top="8px", display="inline-block"),
            ),
        ),
        contact_box(),
        back=back_link("Voltar para dúvidas frequentes", HELP_ROUTE),
    )


# ---------------------------------------------------------------------------
# Segurança e transparência (Figma 406:1243)
# ---------------------------------------------------------------------------

SECURITY_INTRO = (
    "No DoaFácil, a nossa prioridade é a segurança e a transparência para todos. É por essa razão "
    "que nos empenhamos intensamente para garantir uma experiência confiável e tranquila para você."
)
# (ícone, título, texto). Trocas em relação ao Figma estão na decisão 9.
SECURITY_BENEFITS = (
    (
        "lock",
        "Segurança em primeiro lugar",
        "A sua segurança é nossa prioridade número um. Sua senha é guardada com hash, o e-mail da "
        "conta é confirmado por um código e as fotos das doações são publicadas sem os dados de "
        "localização que o celular grava nelas.",
    ),
    (
        "user-lock",
        "Sua privacidade importa",
        "Nós respeitamos muito a sua privacidade. Seu e-mail e sua senha não aparecem no seu perfil "
        "público, e só usamos seus dados para o site funcionar. Todos os dados são tratados com o "
        "máximo de cuidado para garantir sua segurança e tranquilidade.",
    ),
    (
        "search",
        "Transparência total",
        "A transparência é um dos principais pilares do DoaFácil. Você vê as informações de cada "
        "doação disponível antes de combinar, e em Minhas doações acompanha a situação das suas: "
        "disponível, reservada ou concluída.",
    ),
    (
        "shield-check",
        "Seu parceiro de confiança",
        "Nosso compromisso é oferecer apoio, proteção e todas as informações necessárias para que "
        "você navegue com confiança. Priorizando a segurança e a transparência, estamos criando um "
        "espaço onde todos possam se sentir acolhidos e valorizados.",
    ),
)
SECURITY_CARDS = (
    (
        "users",
        "Criei uma doação",
        "A doação aparece em Explorar assim que você a publica, com o seu primeiro nome, a cidade e "
        "o estado. Em Minhas doações, você pode editá-la, marcá-la como reservada ou concluída, ou "
        "apagá-la.",
    ),
    (
        "hand-heart",
        "Recebi uma doação",
        "O DoaFácil não confere os itens: a entrega é combinada direto entre as pessoas, pelo chat "
        "ou pelo contato escolhido. Combine em lugar público e confira o item antes de levar.",
    ),
)


def _icon_circle(icon: str, size: str = "32px") -> rx.Component:
    return rx.box(
        rx.icon(icon, size=16, color="white", aria_hidden="true"),
        display="flex",
        align_items="center",
        justify_content="center",
        width=size,
        height=size,
        flex_shrink="0",
        border_radius="50%",
        background=GREEN,
    )


def security_page() -> rx.Component:
    return institutional_shell(
        rx.grid(
            rx.box(
                rx.text("SAIBA MAIS SOBRE NOSSA", color=DARK_GREEN, font_size="1.05rem", letter_spacing="0.02em"),
                _h1("Segurança e Transparência", margin_top="16px"),
                rx.text(SECURITY_INTRO, color=TEXT_DARK, font_size="1.25rem", line_height="1.3", margin_top="12px"),
            ),
            _photo(**SECURITY_PHOTO),
            gap="32px",
            width="100%",
            style={"gridTemplateColumns": rx.breakpoints(initial="minmax(0, 1fr)", md="minmax(0, 1.1fr) minmax(0, 1fr)")},
        ),
        rx.grid(
            rx.grid(
                *[
                    rx.box(
                        rx.flex(_icon_circle(icon), _h2(title, color=TEXT_BODY, font_size="1.1rem"), align="center", gap="8px"),
                        rx.text(text, color=TEXT_BODY, font_size="0.85rem", line_height="1.45", margin_top="10px"),
                        class_name="security-benefit",
                    )
                    for icon, title, text in SECURITY_BENEFITS
                ],
                gap="24px",
                padding="24px",
                background="#F1F1F1",
                border_radius="4px",
                style={"gridTemplateColumns": rx.breakpoints(initial="minmax(0, 1fr)", sm="repeat(2, minmax(0, 1fr))")},
            ),
            rx.flex(
                *[
                    rx.flex(
                        _icon_circle(icon, "26px"),
                        rx.box(
                            _h2(title, color=TEXT_BODY, font_size="1rem", font_weight="400"),
                            rx.text(text, color=TEXT_MUTED, font_size="0.8rem", line_height="1.45", margin_top="6px"),
                        ),
                        class_name="security-card",
                        gap="12px",
                        padding="20px",
                        background="white",
                        border_radius="8px",
                        box_shadow="0 2px 8px rgba(0, 0, 0, 0.08)",
                    )
                    for icon, title, text in SECURITY_CARDS
                ],
                direction="column",
                gap="24px",
            ),
            gap="32px",
            width="100%",
            style={"gridTemplateColumns": rx.breakpoints(initial="minmax(0, 1fr)", md="minmax(0, 1.7fr) minmax(0, 1fr)")},
        ),
    )


# ---------------------------------------------------------------------------
# Quem somos (Figma 354:851)
# ---------------------------------------------------------------------------

ABOUT_STORY = (
    "O DoaFácil nasceu como um projeto acadêmico de um grupo de estudantes que percebeu quanta "
    "coisa boa ficava parada dentro das casas enquanto tanta gente precisava. Já existiam sites "
    "para vender, mas nenhum pensado para doar sem gastar um real. Por isso criamos um lugar "
    "simples para quem tem algo para doar encontrar quem precisa."
)


def about_page() -> rx.Component:
    mission = rx.heading(
        "Conectar quem tem algo para ",
        # O oval é a borda de uma caixa própria da palavra (inline-block):
        # fica centrado em “doar” em qualquer quebra de linha e não invade a
        # linha de cima, como acontecia com a borda de um span inline.
        rx.el.span(
            "doar",
            class_name="about-highlight",
            display="inline-block",
            line_height="1",
            white_space="nowrap",
            vertical_align="baseline",
            border=f"3px solid {GREEN}",
            border_radius="50%",
            padding="0.06em 0.22em 0.1em",
            margin="0 0.02em",
        ),
        " com quem precisa, de um jeito simples, gratuito e transparente.",
        as_="h1",
        color=TEXT_DARK,
        font_weight="700",
        line_height="1.05",
        style={"fontSize": "clamp(2rem, 4.2vw, 3.6rem)"},
    )
    green_block = {"background": "#1EBA5C", "borderRadius": "8px"}
    return institutional_shell(
        rx.grid(
            mission,
            _photo(**ABOUT_PHOTO),
            gap="32px",
            width="100%",
            style={"gridTemplateColumns": rx.breakpoints(initial="minmax(0, 1fr)", md="minmax(0, 1.4fr) minmax(0, 0.9fr)")},
        ),
        rx.grid(
            # Blocos verdes decorativos do Figma; somem no celular.
            rx.flex(
                rx.box(height="220px", flex="1", style=green_block),
                rx.box(height="190px", flex="1", margin_top="30px", style=green_block),
                rx.box(height="160px", flex="1", margin_top="60px", style=green_block),
                aria_hidden="true",
                class_name="about-decor",
                gap="32px",
                align="start",
                display=rx.breakpoints(initial="none", md="flex"),
            ),
            rx.box(
                rx.text("COMO FOI", color=DARK_GREEN, font_weight="700", font_size="1.4rem", letter_spacing="0.02em"),
                _h2("O início do DoaFácil", color=TEXT_DARK, font_size="2rem", margin_top="12px"),
                rx.text(ABOUT_STORY, color=TEXT_DARK, font_size="1.3rem", line_height="1.35", margin_top="20px"),
            ),
            gap="48px",
            width="100%",
            style={"gridTemplateColumns": rx.breakpoints(initial="minmax(0, 1fr)", md="minmax(0, 1fr) minmax(0, 1.1fr)")},
        ),
    )


# ---------------------------------------------------------------------------
# Contato (sem tela no Figma)
# ---------------------------------------------------------------------------

def contact_page() -> rx.Component:
    if CONTACT_EMAIL.strip():
        body = rx.fragment(
            rx.text(
                "Escreva para ",
                _email_link(class_name="contact-mailto"),
                ".",
                color=TEXT_DARK,
                font_size="1.1rem",
            ),
            rx.text(CONTACT_DATA_TEXT, color=TEXT_DARK, line_height="1.6", class_name="contact-data"),
        )
        more = "Muitas respostas também estão na "
    else:
        body = rx.text(CONTACT_PENDING_TEXT, color=TEXT_DARK, font_size="1.1rem", class_name="contact-pending")
        more = "Enquanto isso, muitas respostas estão na "
    return institutional_shell(
        _h1("Fale com a gente"),
        body,
        rx.text(
            more,
            _link("Central de ajuda", HELP_ROUTE),
            ". Para saber como tratamos seus dados, veja a ",
            _link("Política de privacidade", INSTITUTIONAL_ROUTES["privacidade"]),
            ".",
            color=TEXT_DARK,
            line_height="1.6",
        ),
    )


# ---------------------------------------------------------------------------
# Termos de uso e Política de privacidade (textos novos, decisão 5)
# ---------------------------------------------------------------------------

TERMS_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "1. Sobre o DoaFácil",
        (
            "O DoaFácil é um projeto acadêmico, feito por um grupo de estudantes, que conecta quem "
            "tem objetos para doar com quem precisa deles.",
            "O site não vende nada, não cobra taxas e não intermedeia dinheiro. Ele só ajuda as "
            "pessoas a se encontrarem.",
            "Ao criar uma conta ou usar o site, você concorda com estes Termos e com a Política de "
            "privacidade.",
        ),
    ),
    (
        "2. Cadastro e conta",
        (
            "Para publicar e conversar, é preciso criar uma conta com nome, e-mail, cidade, estado e "
            "senha. A conta só é criada depois que você confirma o código enviado para o seu e-mail.",
            "Use dados verdadeiros e uma conta por pessoa. Guarde sua senha em sigilo: o que for feito "
            "na sua conta é responsabilidade sua.",
        ),
    ),
    (
        "3. Publicação de doações",
        (
            "Publique só objetos físicos que sejam seus, em condições de uso, com fotos e descrição "
            "que mostrem o item como ele é. Cada doação tem de 1 a 5 fotos.",
            "Não é permitido publicar alimentos, itens ilegais, perigosos ou falsificados, nem "
            "anúncios de venda ou troca por dinheiro.",
            "Você pode editar, marcar como concluída ou apagar as suas doações em Minhas doações.",
        ),
    ),
    (
        "4. Combinação e entrega",
        (
            "A entrega é combinada direto entre quem doa e quem recebe, pelo chat ou pelo contato "
            "escolhido na doação.",
            "O DoaFácil não participa da entrega, não confere os itens e não garante que a doação "
            "aconteça. Combine em lugares seguros e confira o item antes de levar.",
        ),
    ),
    (
        "5. Conversas e conduta",
        (
            "Trate as outras pessoas com respeito. Não envie ofensas, golpes, propaganda nem pedidos "
            "de dinheiro.",
            "Evite compartilhar no chat dados que você não precisa, como documentos ou endereço "
            "completo.",
        ),
    ),
    (
        "6. Responsabilidades e limites",
        (
            "Cada pessoa responde pelo que publica e pelo que combina. Por ser um projeto acadêmico, "
            "o site pode ficar fora do ar ou mudar sem aviso.",
            "Contas ou doações que desrespeitem estes Termos podem ser removidas.",
        ),
    ),
    (
        "7. Alterações e contato",
        (
            "Estes Termos podem mudar. A versão em vigor é sempre a publicada nesta página.",
            f"Dúvidas sobre estes Termos: escreva para {EMAIL_MARK}.",
        ),
    ),
)

# (dado, para que usamos, onde fica, quem vê)
PRIVACY_DATA_ROWS: tuple[tuple[str, str, str, str], ...] = (
    ("Nome", "Identificar você no site", "Banco de dados do site (Xano)", "Todos veem o primeiro nome"),
    ("E-mail", "Entrar na conta e enviar códigos", "Banco de dados do site (Xano)",
     "Só você; quem tem conta, se você escolher o contato por e-mail numa doação"),
    ("Senha", "Proteger a sua conta", "Banco de dados do site (Xano), com hash", "Ninguém"),
    ("Cidade e estado", "Mostrar onde estão as doações", "Banco de dados do site (Xano)", "Todos"),
    ("Foto de perfil e texto Sobre", "Mostrar o seu perfil", "Banco de dados do site (Xano)", "Todos"),
    ("Doações e fotos", "Publicar as doações", "Banco de dados do site (Xano)",
     "Todos, enquanto a doação estiver disponível"),
    ("Mensagens do chat", "Conversar sobre uma doação", "Banco de dados do site (Xano)",
     "Só as duas pessoas da conversa"),
    ("Registros de uso", "Saber que ações aconteceram: o número da conta, a ação e o horário, sem "
     "textos de mensagens nem senhas", "Banco de dados do site (Xano)", "Você e a equipe do projeto"),
)
PRIVACY_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "1. Quem somos",
        (
            "O DoaFácil é um projeto acadêmico de um grupo de estudantes. Esta política explica quais "
            "dados o site trata, para quê e quais são os seus direitos.",
        ),
    ),
    # A seção 2 é a tabela (PRIVACY_DATA_ROWS).
    (
        "3. Para que usamos",
        (
            "Usamos os dados só para o site funcionar: criar e proteger a sua conta, publicar as "
            "doações, mostrar os perfis e permitir as conversas.",
            "O site não usa os seus dados para publicidade e não usa ferramentas de análise de "
            "terceiros.",
        ),
    ),
    (
        "4. O que é público",
        (
            "Qualquer pessoa vê o seu primeiro nome, a sua foto, a cidade e o estado, o texto Sobre "
            "e as suas doações disponíveis.",
            "O seu e-mail não é público. Ele só aparece para quem tem conta numa doação em que você "
            "escolheu o contato por e-mail.",
        ),
    ),
    (
        "5. Com quem compartilhamos",
        (
            "Os dados ficam guardados no Xano, o serviço que mantém o banco de dados do site, e os "
            "e-mails com códigos são enviados pelo SendGrid, que recebe o seu e-mail e o código.",
            "A fonte do site é carregada do Google Fonts, que recebe o endereço IP do seu navegador ao "
            "abrir as páginas, como em qualquer site que usa essas fontes.",
            "Não vendemos nem repassamos seus dados a mais ninguém.",
        ),
    ),
    (
        "6. Por quanto tempo guardamos",
        (
            "Os dados ficam guardados enquanto a sua conta existir. Ao apagar uma doação, ela e as "
            "conversas sobre ela são apagadas e as fotos deixam de aparecer no site, mas os arquivos "
            "das fotos ainda podem ficar guardados no Xano.",
        ),
    ),
    (
        "7. Seus direitos",
        (
            "Pela Lei Geral de Proteção de Dados (LGPD), você pode pedir para saber quais dados temos, "
            "corrigi-los ou apagá-los. Nome, foto, texto Sobre, cidade e estado podem ser corrigidos "
            "em Editar perfil.",
            f"Para os outros pedidos, como saber quais dados temos ou apagar a sua conta, escreva para {EMAIL_MARK}.",
        ),
    ),
    (
        "8. Segurança",
        (
            "A senha é guardada com hash, os códigos enviados por e-mail valem por 10 minutos e as "
            "fotos são publicadas sem os dados de localização que o celular grava nelas.",
        ),
    ),
    (
        "9. Alterações",
        ("Esta política pode mudar. A versão em vigor é sempre a publicada nesta página.",),
    ),
)


def _section(title: str, paragraphs: tuple[str, ...]) -> rx.Component:
    return rx.box(
        _h2(title, color=TEXT_DARK, font_size="1.3rem"),
        *[_paragraph(paragraph) for paragraph in paragraphs],
        class_name="legal-section",
    )


def _legal_header(title: str, other_label: str, other_href: str) -> rx.Component:
    return rx.box(
        _h1(title),
        rx.text(ACADEMIC_NOTICE, class_name="academic-notice", color=DARK_GREEN, font_weight="700", margin_top="12px"),
        rx.text("Veja também: ", _link(other_label, other_href), ".", color=TEXT_BODY, margin_top="8px"),
    )


def _legal_body(*content: rx.Component) -> rx.Component:
    return rx.box(
        *content,
        display="flex",
        flex_direction="column",
        gap="28px",
        width="100%",
        max_width=READING_WIDTH,
    )


def terms_page() -> rx.Component:
    return institutional_shell(
        _legal_body(
            _legal_header("Termos de uso", "Política de privacidade", INSTITUTIONAL_ROUTES["privacidade"]),
            *[_section(title, paragraphs) for title, paragraphs in TERMS_SECTIONS],
        )
    )


def _privacy_table() -> rx.Component:
    """Tabela dos dados tratados (Figma 398:1697), com os dados reais. Em telas
    estreitas, rola dentro do contêiner, nunca a página."""
    headers = ("Dado", "Para que usamos", "Onde fica", "Quem vê")
    header_cell = {"color": TEXT_DARK, "font_weight": "700", "background": TABLE_HEADER_BACKGROUND}
    body_cell = {"color": TEXT_BODY}
    return rx.box(
        rx.table.root(
            rx.table.header(
                rx.table.row(
                    *[rx.table.column_header_cell(header, scope="col", **header_cell) for header in headers]
                ),
            ),
            rx.table.body(
                *[
                    rx.table.row(
                        rx.table.row_header_cell(row[0], scope="row", color=TEXT_DARK, font_weight="700"),
                        *[rx.table.cell(value, **body_cell) for value in row[1:]],
                    )
                    for row in PRIVACY_DATA_ROWS
                ]
            ),
            variant="surface",
            size="2",
            min_width="640px",
            background="white",
            color=TEXT_BODY,
            # Cores fixas: sem isso, a tabela do Radix segue o tema escuro do
            # sistema e o texto fica claro sobre o fundo claro.
            style={"--gray-12": TEXT_BODY, "--gray-a5": BORDER, "--gray-a6": BORDER},
        ),
        class_name="privacy-table",
        width="100%",
        overflow_x="auto",
        tab_index=0,
        aria_label="Dados tratados pelo DoaFácil",
        role="region",
    )


def privacy_page() -> rx.Component:
    sections = list(PRIVACY_SECTIONS)
    return institutional_shell(
        _legal_body(
            _legal_header("Política de privacidade", "Termos de uso", INSTITUTIONAL_ROUTES["termos"]),
            _section(*sections[0]),
            rx.box(
                _h2("2. Dados que tratamos", color=TEXT_DARK, font_size="1.3rem"),
                rx.text(
                    "O site não pede documentos, telefone, endereço nem data de nascimento. Os dados tratados "
                    "são estes:",
                    color=TEXT_BODY,
                    line_height="1.6",
                    margin_top="10px",
                    margin_bottom="12px",
                ),
                _privacy_table(),
                class_name="legal-section",
            ),
            *[_section(title, paragraphs) for title, paragraphs in sections[1:]],
        )
    )


__all__ = [
    "ALL_QUESTIONS",
    "HELP_CATEGORIES",
    "HelpCategoryState",
    "HelpState",
    "MOST_ASKED",
    "about_page",
    "contact_page",
    "help_category_page",
    "help_page",
    "privacy_page",
    "search_questions",
    "security_page",
    "terms_page",
]
