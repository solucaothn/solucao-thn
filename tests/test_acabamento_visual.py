"""Change acabamento-visual: correções visuais da auditoria de 27/11/2026.

Os testes conferem o código gerado de cada componente; a conferência no
navegador (1280 e 360 px) fica anotada nas tarefas da change."""

import unittest

import reflex as rx


class AccordionQuestionTests(unittest.TestCase):
    def test_two_line_questions_have_line_height(self) -> None:
        import doafacil.institucional as inst

        rendered = str(inst.faq_accordion(inst.MOST_ASKED))
        self.assertEqual(inst.ACCORDION_QUESTION_LINE_HEIGHT, "1.35")
        trigger = rendered[rendered.index('["& .AccordionTrigger"]') :]
        trigger = trigger[: trigger.index("})")]
        self.assertIn('["lineHeight"] : "1.35"', trigger)


class SignupStateSelectTests(unittest.TestCase):
    def test_state_trigger_has_the_height_of_the_other_fields(self) -> None:
        from doafacil.cadastro import SIGNUP_FIELD_HEIGHT, signup_page

        rendered = str(signup_page())
        self.assertEqual(SIGNUP_FIELD_HEIGHT, "48px")
        # O nome e a obrigatoriedade continuam no root (dados do formulário).
        self.assertIn('RadixThemesSelect.Root,{name:"state",required:true,size:"3"}', rendered)
        trigger = rendered[rendered.index("RadixThemesSelect.Trigger") :]
        trigger = trigger[: trigger.index("placeholder:")]
        for expected in (
            '["height"] : "48px"',
            '["background"] : "white"',
            '["border"] : "1px solid #C8C8C8"',
            '["borderRadius"] : "8px"',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, trigger)
        # Os outros campos têm a mesma altura.
        self.assertEqual(rendered.count('["height"] : "48px"'), 6)


class HeaderButtonsTests(unittest.TestCase):
    def test_entrar_and_quero_doar_share_height_and_corners(self) -> None:
        from doafacil.cabecalho import (
            HEADER_BUTTON_HEIGHT,
            HEADER_BUTTON_RADIUS,
            account_control,
            donate_link,
        )

        self.assertEqual((HEADER_BUTTON_HEIGHT, HEADER_BUTTON_RADIUS), ("44px", "6px"))
        for touch in (False, True):
            with self.subTest(touch=touch):
                entrar = str(account_control(touch=touch))
                self.assertIn('["minHeight"] : "44px"', entrar)
                self.assertIn('["borderRadius"] : "6px"', entrar)
        quero_doar = str(donate_link())
        self.assertIn('["minHeight"] : "44px"', quero_doar)
        self.assertIn('["borderRadius"] : "6px"', quero_doar)


class ExploreTitleTests(unittest.TestCase):
    def test_title_is_bold(self) -> None:
        from doafacil.explorar import explore_page

        rendered = str(explore_page())
        title = rendered[: rendered.index("explore_state.title_rx_state_")]
        title = title[title.rindex("RadixThemesHeading") :]
        self.assertIn('["fontWeight"] : "700"', title)
        self.assertNotIn('["fontWeight"] : "400"', title)


class PeopleReachedTests(unittest.TestCase):
    def test_hidden_only_while_zero(self) -> None:
        from doafacil.doafacil import donation_count_view

        rendered = str(donation_count_view())
        # A estatística fica dentro de um cond que a mostra carregando, com
        # erro ou com número maior que zero (os três ligados por “ou”).
        condition_end = rendered.index("completed_count_rx_state_ > 0)))?")
        condition = rendered[rendered.rindex("count_loading_rx_state_", 0, condition_end) : condition_end]
        self.assertIn("completed_error_rx_state_", condition)
        self.assertIn('=== ""', condition)
        # “Pessoas alcançadas” só aparece depois da condição, no ramo visível.
        self.assertGreater(rendered.index("Pessoas alcan"), condition_end)
        # “Doações em circulação!” continua fora do cond, antes dele.
        circulation = rendered.index("Doa\\u00e7\\u00f5es em circula\\u00e7\\u00e3o!")
        self.assertLess(circulation, condition_end)


class FooterSpacingTests(unittest.TestCase):
    def test_gaps_have_units(self) -> None:
        from doafacil.rodape import (
            FOOTER_BLOCK_GAP,
            FOOTER_LINK_COLUMN_GAP_PX,
            public_home_footer,
        )

        rendered = str(public_home_footer())
        self.assertEqual((FOOTER_BLOCK_GAP, FOOTER_LINK_COLUMN_GAP_PX), ("16px", 12))
        # Antes era gap:"4", sem unidade, e o navegador ignorava.
        self.assertNotIn('gap:"4"', rendered)
        self.assertNotIn('["gap"] : "4"', rendered)
        self.assertIn('["gap"] : "16px"', rendered)
        self.assertIn('["columnGap"] : "12px"', rendered)
        self.assertIn("calc(50% - 6px)", rendered)
        self.assertIn("calc(25% - 9px)", rendered)


class ChatFabPositionTests(unittest.TestCase):
    def test_button_stays_in_the_corner(self) -> None:
        # Revertido em 27/11/2026: o selo “Built with Reflex” só aparece em
        # --env prod; no modo dev (como o projeto roda), o botão fica no canto.
        from doafacil.chat import CHAT_FAB_CLEARANCE, CHAT_FAB_OFFSET

        def values(breakpoints: rx.Var) -> dict:
            return {key: str(value) for key, value in dict(breakpoints).items()}

        self.assertEqual(values(CHAT_FAB_OFFSET), {"initial": "16px", "md": "24px"})
        self.assertEqual(values(CHAT_FAB_CLEARANCE), {"initial": "88px", "md": "104px"})


if __name__ == "__main__":
    unittest.main()
