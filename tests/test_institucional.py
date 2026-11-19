"""Páginas institucionais (change paginas-institucionais, spec
institutional-pages): estrutura comum, conteúdo verdadeiro, Central de ajuda
(busca, categorias, acordeão), Segurança, Quem somos, Contato, Termos e
Privacidade."""

import re
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from doafacil import institucional as inst
from doafacil.institucional import (
    ACADEMIC_NOTICE,
    ALL_QUESTIONS,
    CONTACT_PENDING_TEXT,
    HELP_CATEGORIES,
    MOST_ASKED,
    PRIVACY_DATA_ROWS,
    SEARCH_SHORTCUTS,
    HelpCategoryState,
    HelpState,
    about_page,
    category_count_label,
    contact_page,
    help_category_page,
    help_page,
    normalize,
    privacy_page,
    search_questions,
    security_page,
    terms_page,
)
from doafacil.rodape import CONTACT_EMAIL, INSTITUTIONAL_ROUTES, contact_href

# E-mail de contato do projeto, definido pelo grupo (change endpoints-antigos).
PROJECT_EMAIL = "solucaothn@gmail.com"

PAGES = {
    "/duvidas": help_page,
    "/duvidas/[categoria]": help_category_page,
    "/seguranca": security_page,
    "/termos": terms_page,
    "/privacidade": privacy_page,
    "/quem-somos": about_page,
    "/contato": contact_page,
}
# Palavras de serviços e dados que o DoaFácil não tem (os textos do Figma
# eram de uma plataforma de doações em dinheiro).
FORBIDDEN = (
    "pix", "cartao", "credito", "cpf", "cnpj", "doafacil.com.br", "2019", "osasco",
    "banco central", "criptograf", "milhares", "saque", "boleto", "ltda", "kyc",
)


def _all_texts() -> list[str]:
    texts = [inst.SECURITY_INTRO, inst.ABOUT_STORY, CONTACT_PENDING_TEXT, ACADEMIC_NOTICE]
    for question in ALL_QUESTIONS:
        texts += [question["question"], question["answer"]]
    for _, title, text in inst.SECURITY_BENEFITS + inst.SECURITY_CARDS:
        texts += [title, text]
    for sections in (inst.TERMS_SECTIONS, inst.PRIVACY_SECTIONS):
        for title, paragraphs in sections:
            texts += [title, *paragraphs]
    for row in PRIVACY_DATA_ROWS:
        texts += list(row)
    return texts


def _heading_levels(rendered: str) -> list[int]:
    """Níveis dos títulos na ordem em que aparecem (os cabeçalhos do acordeão
    do Radix são h3)."""
    levels = []
    for match in re.finditer(r'as:"h(\d)"|RadixAccordionHeader', rendered):
        levels.append(int(match.group(1)) if match.group(1) else 3)
    return levels


class StructureTests(unittest.TestCase):
    def test_every_page_has_shell_parts(self) -> None:
        for route, page in PAGES.items():
            with self.subTest(route=route):
                r = str(page())
                self.assertIn('className:"institutional-header"', r)
                self.assertIn('"aria-label":"DoaF\\u00e1cil \\u2014 in\\u00edcio"', r)
                self.assertIn('className:"institutional-back-link"', r)
                self.assertIn("Links r\\u00e1pidos", r)  # rodapé da home
                self.assertEqual(r.count("chat-fab"), 1)
                self.assertEqual(r.count('className:"page-fade-enter"'), 1)
                self.assertIn('["paddingBottom"] : "88px"', r)  # espaço do botão do chat

    def test_headings_in_order(self) -> None:
        for route, page in PAGES.items():
            with self.subTest(route=route):
                levels = _heading_levels(str(page()))
                self.assertEqual(levels[0], 1)
                seen = 1
                for level in levels[1:]:
                    self.assertLessEqual(level, seen + 1, levels)
                    seen = max(seen, level)
                # Um único h1 (a página de categoria tem dois ramos: a
                # categoria e “não encontrada”, só um é exibido).
                self.assertEqual(levels.count(1), 2 if route.endswith("[categoria]") else 1)

    def test_no_fixed_width_over_360(self) -> None:
        for route, page in PAGES.items():
            with self.subTest(route=route):
                self.assertIsNone(re.search(r'\["width"\] : "(3[7-9]\d|[4-9]\d\d|\d{4,})px"', str(page())))

    def test_routes_registered_with_chat_loader(self) -> None:
        from doafacil.chat import ChatState
        from doafacil.doafacil import app

        for route in PAGES:
            with self.subTest(route=route):
                on_load = app._unevaluated_pages[route.strip("/")].on_load
                handlers = on_load if isinstance(on_load, list) else [on_load]
                self.assertIn(ChatState.load_unread_total.fn, [h.fn for h in handlers])


class TruthfulContentTests(unittest.TestCase):
    def test_no_forbidden_words_anywhere(self) -> None:
        for text in _all_texts():
            plain = normalize(text)
            for word in FORBIDDEN:
                with self.subTest(word=word, text=text[:40]):
                    self.assertNotIn(word, plain)

    def test_no_invented_email(self) -> None:
        """O único e-mail das páginas é o do projeto (change endpoints-antigos)."""
        self.assertEqual(CONTACT_EMAIL, PROJECT_EMAIL)
        for route, page in PAGES.items():
            with self.subTest(route=route):
                r = str(page())
                self.assertNotIn("doafacil.com", r)
                self.assertEqual(set(re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", r)), {PROJECT_EMAIL} if PROJECT_EMAIL in r else set())
                self.assertEqual(set(re.findall(r"mailto:[^\"']*", r)), {f"mailto:{PROJECT_EMAIL}"} if "mailto:" in r else set())

    def test_contact_email_where_it_was_pending(self) -> None:
        # Os convites levam à /contato, onde o endereço aparece escrito.
        self.assertEqual(contact_href(), "/contato")
        self.assertIn('to:"/contato"', str(help_page()))
        mailto = f'to:"mailto:{PROJECT_EMAIL}"'  # o React Router trata o mailto: como externo
        contact = str(contact_page())
        self.assertIn(mailto, contact)
        self.assertIn(f'"{PROJECT_EMAIL}"', contact)  # escrito, além do link
        self.assertIn('className:"contact-mailto"', contact)
        self.assertIn(inst.CONTACT_DATA_TEXT.replace("ê", "\\u00ea").replace("ó", "\\u00f3"), contact)
        self.assertIn('to:"/duvidas"', contact)
        self.assertIn('to:"/privacidade"', contact)
        self.assertNotIn("contact-pending", contact)
        for name, page in (("ajuda", help_page), ("termos", terms_page), ("privacidade", privacy_page)):
            with self.subTest(page=name):
                self.assertIn(mailto, str(page()))
        for route, page in PAGES.items():
            with self.subTest(route=route):
                self.assertNotIn("ainda vai ser publicado", str(page()).encode().decode("unicode_escape"))

    def test_sections_7_point_to_the_email(self) -> None:
        terms = dict(inst.TERMS_SECTIONS)["7. Alterações e contato"]
        privacy = dict(inst.PRIVACY_SECTIONS)["7. Seus direitos"]
        self.assertIn("Dúvidas sobre estes Termos: escreva para {email}.", terms)
        self.assertIn("Para os outros pedidos, como saber quais dados temos ou apagar a sua conta, escreva para {email}.", privacy)

    def test_without_email_falls_back_to_pending_text(self) -> None:
        with patch("doafacil.institucional.CONTACT_EMAIL", ""):
            for name, page in (("contato", contact_page), ("ajuda", help_page), ("termos", terms_page), ("privacidade", privacy_page)):
                with self.subTest(page=name):
                    r = str(page())
                    self.assertNotIn("mailto:", r)
                    self.assertNotIn(PROJECT_EMAIL, r)
                    self.assertIn("ainda vai ser publicado", r)
            self.assertIn('className:"contact-pending"', str(contact_page()))


class HelpCenterTests(unittest.TestCase):
    def test_categories_counts_are_real(self) -> None:
        self.assertEqual([c["name"] for c in HELP_CATEGORIES], [
            "Primeiros passos", "Doar um item", "Receber uma doação", "Conta e perfil", "Segurança", "Conversas",
        ])
        self.assertEqual(sum(len(c["questions"]) for c in HELP_CATEGORIES), 27)
        r = str(help_page())
        for category in HELP_CATEGORIES:
            with self.subTest(category=category["slug"]):
                self.assertTrue(category["questions"])
                self.assertIn(f'to:"/duvidas/{category["slug"]}"', r)
                self.assertIn(category_count_label(category), r)
        self.assertEqual(len({q["id"] for q in ALL_QUESTIONS}), len(ALL_QUESTIONS))
        self.assertEqual(len(MOST_ASKED), 4)

    def test_figma_answers_kept(self) -> None:
        answers = {q["question"]: q["answer"] for q in ALL_QUESTIONS}
        self.assertTrue(answers["O DoaFácil cobra alguma taxa?"].startswith("Não. O DoaFácil não cobra nada"))
        self.assertTrue(answers["Como publico uma doação?"].startswith("Clique em Quero Doar, preencha as cinco etapas"))

    def test_search_ignores_case_and_accents(self) -> None:
        for term in ("TAXA", "taxa", "Táxa"):
            with self.subTest(term=term):
                self.assertIn("taxa", [q["id"] for q in search_questions(term)])
        self.assertEqual([q["id"] for q in search_questions("doacao reservada")], ["reservada"])
        self.assertEqual(search_questions("boleto"), [])
        self.assertEqual(search_questions("   "), [])

    def test_shortcuts_find_something(self) -> None:
        for label, term in SEARCH_SHORTCUTS:
            with self.subTest(shortcut=label):
                self.assertTrue(search_questions(term))

    def test_state_titles(self) -> None:
        count = len(search_questions("taxa"))
        expected = "1 resultado" if count == 1 else f"{count} resultados"
        self.assertEqual(HelpState.computed_vars["results_title"].fget(SimpleNamespace(query="taxa")), f"{expected} para “taxa”")
        self.assertEqual(
            HelpState.computed_vars["results_title"].fget(SimpleNamespace(query="doação")),
            f"{len(search_questions('doação'))} resultados para “doação”",
        )
        state = SimpleNamespace(query="boleto")
        self.assertEqual(HelpState.computed_vars["results_title"].fget(state), "Nenhuma resposta para “boleto”")
        self.assertFalse(HelpState.computed_vars["searching"].fget(SimpleNamespace(query="  ")))

    def test_accordion_single_collapsible_and_shortcuts(self) -> None:
        r = str(help_page())
        self.assertIn('collapsible:true', r)
        self.assertIn('type:"single"', r)
        self.assertIn("RadixAccordionTrigger", r)
        self.assertIn('id:"help-search"', r)
        self.assertIn('"aria-label":"Buscar por uma d\\u00favida"', r)
        self.assertEqual(r.count('className:"help-shortcut'), 3)
        self.assertIn("Mais perguntadas", r)
        self.assertNotIn("Esta resposta ajudou", r)

    def test_category_page_loads_slug(self) -> None:
        def load(path: str) -> SimpleNamespace:
            state = SimpleNamespace(router=SimpleNamespace(url=SimpleNamespace(path=path)), slug="")
            HelpCategoryState.load.fn(state)
            return state

        state = load("/duvidas/doar-um-item")
        self.assertEqual(state.slug, "doar-um-item")
        computed = HelpCategoryState.computed_vars
        self.assertTrue(computed["found"].fget(state))
        self.assertEqual(computed["name"].fget(state), "Doar um item")
        self.assertEqual(computed["subtitle"].fget(state), "6 perguntas sobre publicar e gerenciar suas doações.")
        self.assertEqual(len(computed["questions"].fget(state)), 6)
        unknown = load("/duvidas/nao-existe/")
        self.assertFalse(computed["found"].fget(unknown))
        self.assertEqual(computed["questions"].fget(unknown), [])
        r = str(help_category_page())
        self.assertIn("Voltar para d\\u00favidas frequentes", r)
        self.assertIn("Categoria n\\u00e3o encontrada", r)


class OtherPagesTests(unittest.TestCase):
    def test_security_blocks(self) -> None:
        r = str(security_page())
        self.assertIn("SAIBA MAIS SOBRE NOSSA", r)
        self.assertIn("Seguran\\u00e7a e Transpar\\u00eancia", r)
        self.assertEqual(r.count('className:"security-benefit"'), 4)
        self.assertEqual(r.count('className:"security-card"'), 2)
        # A única imagem do conteúdo é a foto da página (change fotos-site).
        # Conteúdo depois do cabeçalho (que tem a foto da conta, change
        # navegacao-celular) e antes do rodapé.
        content = r.split('className:"institutional-back-link"')[1].split("Links r")[0]
        content = content.replace('src:"/logo.svg"', "").replace('src:"/seguranca/seguranca.jpg"', "", 1)
        self.assertNotIn("src:", content)

    def test_about_mission_highlight_and_story(self) -> None:
        r = str(about_page())
        self.assertIn('className:"about-highlight"', r)
        self.assertIn('"doar"', r)
        self.assertIn("COMO FOI", r)
        self.assertIn("O in\\u00edcio do DoaF\\u00e1cil", r)
        self.assertIn("projeto acad\\u00eamico", r)
        self.assertIn('className:"about-decor"', r)
        self.assertIn('"aria-hidden":"true"', r)

    def test_legal_pages_notice_links_and_sections(self) -> None:
        for page, other, title in ((terms_page, "/privacidade", "Termos de uso"), (privacy_page, "/termos", "Pol\\u00edtica de privacidade")):
            with self.subTest(page=title):
                r = str(page())
                self.assertIn(title, r)
                self.assertIn('className:"academic-notice"', r)
                self.assertIn("Documento de projeto acad\\u00eamico, sem valor jur\\u00eddico.", r)
                self.assertIn(f'to:"{other}"', r)
                self.assertGreaterEqual(r.count('className:"legal-section"'), 7)
                # O aviso logo depois do título.
                self.assertLess(r.index(title), r.index("academic-notice"))

    def test_privacy_table_has_only_real_data(self) -> None:
        self.assertEqual(
            [row[0] for row in PRIVACY_DATA_ROWS],
            ["Nome", "E-mail", "Senha", "Cidade e estado", "Foto de perfil e texto Sobre", "Doações e fotos",
             "Mensagens do chat", "Registros de uso"],
        )
        r = str(privacy_page())
        self.assertIn('className:"privacy-table"', r)
        self.assertIn('["overflowX"] : "auto"', r)  # rola dentro do contêiner em 360 px
        self.assertIn('scope:"col"', r)
        self.assertIn('scope:"row"', r)

    def test_institutional_routes(self) -> None:
        self.assertEqual(
            set(INSTITUTIONAL_ROUTES.values()),
            {"/duvidas", "/seguranca", "/termos", "/privacidade", "/quem-somos", "/contato"},
        )


if __name__ == "__main__":
    unittest.main()


def _luminance(hex_color: str) -> float:
    channels = [int(hex_color.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(foreground: str, background: str) -> float:
    """Razão de contraste da WCAG 2.1."""
    lighter, darker = sorted((_luminance(foreground), _luminance(background)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


AA_TEXT = 4.5


class ContrastHelperTests(unittest.TestCase):
    def test_known_ratios(self) -> None:
        self.assertAlmostEqual(contrast("#000000", "#FFFFFF"), 21.0, places=1)
        self.assertAlmostEqual(contrast("#777777", "#FFFFFF"), 4.48, places=2)


class AccordionContrastTests(unittest.TestCase):
    """Roteiro 5.4: o item aberto ficava preto com o texto invisível (o Radix
    seguia o tema escuro do sistema). Agora as cores são fixas."""

    def test_question_and_answer_pass_aa_in_every_state(self) -> None:
        for background in ("#FFFFFF", inst.ACCORDION_OPEN_BACKGROUND, inst.ACCORDION_HOVER_BACKGROUND):
            with self.subTest(background=background):
                self.assertGreaterEqual(contrast(inst.TEXT_BODY, background), AA_TEXT)
                self.assertGreaterEqual(contrast(inst.TEXT_MUTED, background), AA_TEXT)

    def test_open_and_hover_are_light(self) -> None:
        # Fundo claro (branco/creme), nunca uma faixa escura.
        for background in (inst.ACCORDION_OPEN_BACKGROUND, inst.ACCORDION_HOVER_BACKGROUND):
            self.assertGreater(_luminance(background), 0.85)

    def test_colors_are_fixed_and_radix_vars_overridden(self) -> None:
        r = str(inst.faq_accordion(MOST_ASKED))
        self.assertIn(f'["--accent-4"] : "{inst.ACCORDION_HOVER_BACKGROUND}"', r)
        self.assertIn(f'["--accent-11"] : "{inst.TEXT_BODY}"', r)
        self.assertIn(f'["--accent-contrast"] : "{inst.TEXT_BODY}"', r)
        self.assertIn(
            "[\"& .AccordionItem .AccordionTrigger, & .AccordionItem .AccordionTrigger[data-state='open']\"] : "
            f'({{ ["color"] : "{inst.TEXT_BODY}", ["background"] : "transparent" }})',
            r,
        )
        self.assertIn(f'["& .AccordionItem[data-state=\'open\']"] : ({{ ["background"] : "{inst.ACCORDION_OPEN_BACKGROUND}" }})', r)
        self.assertIn(f'["& .AccordionItem .AccordionContent"] : ({{ ["color"] : "{inst.TEXT_MUTED}"', r)


class SearchContrastTests(unittest.TestCase):
    def test_icon_and_placeholder_pass_aa_on_white(self) -> None:
        self.assertGreaterEqual(contrast(inst.SEARCH_ICON_COLOR, "#FFFFFF"), AA_TEXT)
        self.assertGreaterEqual(contrast(inst.SEARCH_PLACEHOLDER_COLOR, "#FFFFFF"), AA_TEXT)
        self.assertGreaterEqual(contrast(inst.TEXT_DARK, "#FFFFFF"), AA_TEXT)

    def test_search_field_uses_fixed_colors(self) -> None:
        r = str(help_page())
        self.assertIn(f'LucideSearch,{{"aria-hidden":"true",css:({{ ["color"] : "{inst.SEARCH_ICON_COLOR}"', r)
        self.assertIn(f'["--gray-a11"] : "{inst.SEARCH_ICON_COLOR}"', r)
        self.assertIn(f'["--gray-12"] : "{inst.TEXT_DARK}"', r)


class PrivacyTableContrastTests(unittest.TestCase):
    """Roteiro 5.4: o texto da tabela estava quase transparente."""

    def test_cells_pass_aa(self) -> None:
        self.assertGreaterEqual(contrast(inst.TEXT_BODY, "#FFFFFF"), AA_TEXT)
        self.assertGreaterEqual(contrast(inst.TEXT_DARK, "#FFFFFF"), AA_TEXT)
        self.assertGreaterEqual(contrast(inst.TEXT_DARK, inst.TABLE_HEADER_BACKGROUND), AA_TEXT)

    def test_table_colors_are_fixed_and_header_bold(self) -> None:
        r = str(inst._privacy_table())
        header = f'["color"] : "{inst.TEXT_DARK}", ["fontWeight"] : "700", ["background"] : "{inst.TABLE_HEADER_BACKGROUND}"'
        self.assertEqual(r.count(header), 4)  # as 4 colunas
        self.assertEqual(r.count(f'RadixThemesTable.Cell,{{css:({{ ["color"] : "{inst.TEXT_BODY}" }})'), 3 * len(PRIVACY_DATA_ROWS))
        self.assertEqual(r.count(f'["color"] : "{inst.TEXT_DARK}", ["fontWeight"] : "700" }})'), len(PRIVACY_DATA_ROWS))
        self.assertIn(f'["--gray-12"] : "{inst.TEXT_BODY}"', r)
        self.assertIn('["background"] : "white"', r)


class RoteiroLayoutTests(unittest.TestCase):
    def test_footer_at_the_bottom_on_short_pages(self) -> None:
        r = str(contact_page())
        self.assertIn('className:"institutional-page"', r)
        self.assertRegex(r, r'\["display"\] : "flex", \["flexDirection"\] : "column", \["width"\] : "100%", \["minHeight"\] : "100vh"')
        self.assertIn('["flex"] : "1 0 auto"', r)
        self.assertLess(r.index("institutional-main"), r.index("Links r"))

    def test_about_oval_is_its_own_box_around_doar(self) -> None:
        r = str(about_page())
        oval = r[r.index('className:"about-highlight"') :]
        oval = oval[: oval.index('"doar"')]
        for prop in ('["display"] : "inline-block"', '["whiteSpace"] : "nowrap"', '["borderRadius"] : "50%"'):
            self.assertIn(prop, oval)

    def test_back_link_same_on_explore_and_institutional(self) -> None:
        from doafacil.explorar import back_home_link

        explore = str(back_home_link())
        institutional = str(inst.back_link())
        self.assertIn('className:"explore-back-link"', explore)
        self.assertEqual(
            explore.replace("explore-back-link", "institutional-back-link"), institutional
        )
        for r in (explore, institutional):
            self.assertIn("LucideChevronLeft", r)
            self.assertIn('["color"] : "#166B3B"', r)
            self.assertIn('["&:visited"] : ({ ["color"] : "#166B3B" })', r)
        self.assertGreaterEqual(contrast("#166B3B", inst.CREAM), AA_TEXT)


class LightThemeTests(unittest.TestCase):
    """Tema claro fixo em todo o app (decisão do Higor no roteiro 5.4)."""

    def test_radix_theme_is_light(self) -> None:
        import reflex as rx
        from reflex.compiler.compiler import _resolve_default_color_mode

        import rxconfig

        plugins = [p for p in rxconfig.config.plugins if isinstance(p, rx.plugins.RadixThemesPlugin)]
        self.assertEqual(len(plugins), 1)
        self.assertEqual(_resolve_default_color_mode(plugins[0].theme), "light")


# ---------------------------------------------------------------------------
# Fotos do Figma (change fotos-site)
# ---------------------------------------------------------------------------

import json  # noqa: E402
from pathlib import Path  # noqa: E402

from PIL import Image  # noqa: E402

ASSETS = Path(__file__).resolve().parent.parent / "assets"


def _photo_markup(rendered: str) -> str:
    """Trecho do componente compilado, do `figure` até o fim do crédito."""
    start = rendered.index('className:"institutional-photo"')
    end = rendered.find('className:"photo-credit"', start)
    return rendered[start : (end if end != -1 else start + 1000) + 200]


# (página, dados da foto, src, proporção do Figma, raio, largura máxima, início do alt)
PAGE_PHOTOS = (
    (about_page, inst.ABOUT_PHOTO, "/sobre/quem-somos.jpg", "375 / 421", "8px", "375px",
     "Grupo de jovens agachados no chão de um escritório"),
    (security_page, inst.SECURITY_PHOTO, "/seguranca/seguranca.jpg", "507 / 339", "16px", "507px",
     "Cinco jovens sorrindo, de pé em fila"),
)


class PagePhotoTests(unittest.TestCase):
    def test_pages_show_photo_with_alt_ratio_and_credit(self) -> None:
        for page, data, src, ratio, radius, max_width, alt_start in PAGE_PHOTOS:
            with self.subTest(src=src):
                r = str(page())
                photo = _photo_markup(r)
                self.assertIn('jsx("figure"', r)
                self.assertIn(f'src:"{src}"', photo)
                self.assertIn(f"alt:{json.dumps(data['alt'])}", photo)
                self.assertTrue(data["alt"].startswith(alt_start))
                self.assertIn(f'["aspectRatio"] : "{ratio}"', photo)
                self.assertIn('["objectFit"] : "cover"', photo)
                self.assertIn(f'["borderRadius"] : "{radius}"', photo)
                self.assertIn(f'["maxWidth"] : "{max_width}"', photo)
                self.assertIn('jsx("figcaption",{className:"photo-credit"', photo)
                self.assertIn('"Foto: Freepik"', photo)

    def test_pages_have_no_placeholder(self) -> None:
        for page in (about_page, security_page):
            with self.subTest(page=page.__name__):
                self.assertNotIn("institutional-photo-placeholder", str(page()))
        self.assertFalse(hasattr(inst, "_placeholder"))
        self.assertFalse(hasattr(inst, "PLACEHOLDER_GRADIENT"))

    def test_alts_are_descriptive_portuguese(self) -> None:
        for _, data, *_rest in PAGE_PHOTOS:
            alt = data["alt"]
            with self.subTest(alt=alt):
                self.assertGreaterEqual(len(alt.split()), 8)
                self.assertNotIn("foto", alt.lower().split()[0])
                self.assertTrue(alt.endswith("."))

    def test_photo_without_credit_has_no_caption(self) -> None:
        r = str(inst._photo("/x.jpg", "Descrição.", "", 10, 20, "8px"))
        self.assertNotIn("figcaption", r)

    def test_credit_passes_aa_on_white(self) -> None:
        self.assertGreaterEqual(contrast(inst.PHOTO_CREDIT_COLOR, "#FFFFFF"), AA_TEXT)


class PhotoFilesTests(unittest.TestCase):
    def _check_jpeg(self, path: Path, size: tuple[int, int]) -> None:
        self.assertTrue(path.is_file(), path)
        with Image.open(path) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.size, size)
            self.assertEqual(len(image.getexif()), 0)
            self.assertNotIn("icc_profile", image.info)

    def test_jpegs_are_2x_of_figma_without_metadata(self) -> None:
        # Retângulos do Figma exportados em 2x: 375 x 421 e 507 x 339.
        for data, size in ((inst.ABOUT_PHOTO, (750, 842)), (inst.SECURITY_PHOTO, (1014, 678))):
            with self.subTest(src=data["src"]):
                self._check_jpeg(ASSETS / data["src"].lstrip("/"), size)
                self.assertEqual((data["width"] * 2, data["height"] * 2), size)
