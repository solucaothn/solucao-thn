"""State and clearly labeled demonstration data for fundraising pages."""

from typing import TypedDict

import reflex as rx


class Campaign(TypedDict):
    id: int
    title: str
    category: str
    location: str
    creator: str
    raised_amount: int
    goal_amount: int
    supporters: int
    progress_percent: int
    image_path: str
    summary: str
    story: str
    updates: str
    messages: str


DEMO_CAMPAIGNS: list[Campaign] = [
    {
        "id": 1,
        "title": "Um recomeço para a Dona Lúcia",
        "category": "Saúde",
        "location": "São Paulo",
        "creator": "Mariana Costa",
        "raised_amount": 7850,
        "goal_amount": 12000,
        "supporters": 86,
        "progress_percent": 65,
        "image_path": "/campaigns/health.svg",
        "summary": "Ajude a custear o tratamento e a recuperação da Dona Lúcia.",
        "story": (
            "Esta é uma história demonstrativa criada para visualizar a página "
            "de campanha. As informações e os valores não representam uma "
            "arrecadação real."
        ),
        "updates": "Exemplo: atualização da campanha aparecerá nesta aba.",
        "messages": "Exemplo: recados de apoiadores aparecerão nesta aba.",
    },
    {
        "id": 2,
        "title": "Material escolar para nossa comunidade",
        "category": "Educação",
        "location": "Recife",
        "creator": "Instituto Sementes",
        "raised_amount": 4320,
        "goal_amount": 8000,
        "supporters": 54,
        "progress_percent": 54,
        "image_path": "/campaigns/education.svg",
        "summary": "Uma corrente de apoio para começar o ano com mais oportunidades.",
        "story": (
            "Campanha e números fictícios para demonstração da interface. "
            "Nenhuma contribuição foi recebida."
        ),
        "updates": "Exemplo: novidades do projeto serão exibidas aqui.",
        "messages": "Exemplo: mensagens de apoio serão exibidas aqui.",
    },
    {
        "id": 3,
        "title": "Equipando a cozinha solidária",
        "category": "Comunidade",
        "location": "Belo Horizonte",
        "creator": "Coletivo Mesa Aberta",
        "raised_amount": 2950,
        "goal_amount": 10000,
        "supporters": 39,
        "progress_percent": 30,
        "image_path": "/campaigns/community.svg",
        "summary": "Ajude a renovar os equipamentos usados nas refeições comunitárias.",
        "story": (
            "Conteúdo ilustrativo. Esta campanha não existe no Xano e não recebe "
            "pagamentos."
        ),
        "updates": "Exemplo: atualizações serão conectadas ao Xano futuramente.",
        "messages": "Exemplo: recados serão conectados ao Xano futuramente.",
    },
    {
        "id": 4,
        "title": "Acessibilidade para o centro cultural",
        "category": "Comunidade",
        "location": "Curitiba",
        "creator": "Associação Viver Junto",
        "raised_amount": 6150,
        "goal_amount": 15000,
        "supporters": 72,
        "progress_percent": 41,
        "image_path": "/campaigns/culture.svg",
        "summary": "Construindo um espaço mais acolhedor e acessível para todos.",
        "story": (
            "Dados fictícios de interface. O progresso exibido é apenas um "
            "exemplo visual."
        ),
        "updates": "Exemplo: atualizações da obra aparecerão aqui.",
        "messages": "Exemplo: recados da comunidade aparecerão aqui.",
    },
]


class CampaignState(rx.State):
    """Presentation state only; no campaign or payment data is persisted."""

    campaigns: list[Campaign] = DEMO_CAMPAIGNS
    categories: list[str] = ["Todas", "Saúde", "Educação", "Comunidade"]
    search_text: str = ""
    search_location: str = ""
    selected_category: str = "Todas"
    selected_campaign_id: str = "1"

    selected_amount: int = 50
    custom_amount: str = ""
    use_custom_amount: bool = False
    is_anonymous: bool = False
    support_message: str = ""
    payment_method: str = "pix"
    checkout_notice: str = ""

    def set_search_text(self, value: str) -> None:
        self.search_text = value

    def set_search_location(self, value: str) -> None:
        self.search_location = value

    def set_category(self, value: str) -> None:
        self.selected_category = value

    def set_custom_amount(self, value: str) -> None:
        self.custom_amount = value
        self.use_custom_amount = True

    def select_amount(self, value: int) -> None:
        self.selected_amount = value
        self.use_custom_amount = False
        self.custom_amount = ""
        self.checkout_notice = ""

    def select_payment_method(self, value: str) -> None:
        self.payment_method = value
        self.checkout_notice = ""

    def set_support_message(self, value: str) -> None:
        self.support_message = value

    def toggle_anonymous(self, value: bool) -> None:
        self.is_anonymous = value

    @rx.var
    def filtered_campaigns(self) -> list[Campaign]:
        query = self.search_text.strip().casefold()
        location = self.search_location.strip().casefold()
        return [
            campaign
            for campaign in self.campaigns
            if (self.selected_category == "Todas" or campaign["category"] == self.selected_category)
            and (
                not query
                or query in campaign["title"].casefold()
                or query in campaign["summary"].casefold()
                or query in campaign["category"].casefold()
            )
            and (not location or location in campaign["location"].casefold())
        ]

    @rx.var
    def current_campaign(self) -> Campaign:
        return next(
            (
                campaign
                for campaign in self.campaigns
                if str(campaign["id"]) == self.selected_campaign_id
            ),
            self.campaigns[0],
        )

    @rx.var
    def checkout_amount_label(self) -> str:
        if self.use_custom_amount:
            return self.custom_amount or "0"
        return str(self.selected_amount)

    @rx.event
    def load_campaign(self) -> None:
        campaign_id = str(self.router.page.params.get("campaign_id", ""))
        self.selected_campaign_id = (
            campaign_id
            if any(str(campaign["id"]) == campaign_id for campaign in self.campaigns)
            else ""
        )
        self.checkout_notice = ""

    @rx.event
    def open_campaign(self, campaign_id: int):
        self.selected_campaign_id = str(campaign_id)
        return rx.redirect(f"/vaquinhas/{campaign_id}")

    @rx.event
    def open_checkout(self):
        self.checkout_notice = ""
        return rx.redirect(f"/checkout/{self.selected_campaign_id}")

    @rx.event
    def return_to_campaign(self):
        return rx.redirect(f"/vaquinhas/{self.selected_campaign_id}")

    @rx.event
    def open_feed(self):
        return rx.redirect("/vaquinhas")

    @rx.event
    def scroll_to_results(self):
        return rx.redirect("/#causas")

    @rx.event
    def load_campaigns(self) -> None:
        # Future Xano GET integration belongs here; demo fixtures remain local
        # until a campaign endpoint and response contract are approved.
        self.campaigns = DEMO_CAMPAIGNS

    @rx.event
    def prepare_demo_checkout(self) -> None:
        # Future Xano POST integration belongs here; do not submit until a
        # payment provider and backend contract are approved.
        self.checkout_notice = (
            "Esta é uma demonstração. Nenhum pagamento foi iniciado."
        )

    @rx.event
    def clear_checkout_notice(self) -> None:
        self.checkout_notice = ""

    @rx.event
    def reset_filters(self) -> None:
        self.search_text = ""
        self.search_location = ""
        self.selected_category = "Todas"
