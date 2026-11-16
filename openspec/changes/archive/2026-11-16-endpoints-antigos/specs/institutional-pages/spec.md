## MODIFIED Requirements

### Requirement: Conteúdo verdadeiro
As páginas institucionais SHALL descrever só o que o DoaFácil realmente é e faz: um projeto acadêmico de doação de objetos, sem dinheiro, com os dados que o site de fato coleta. O e-mail de contato do projeto é `solucaothn@gmail.com`, definido na configuração do site.

#### Scenario: Sem dados ou serviços inexistentes
- **WHEN** qualquer página institucional é exibida
- **THEN** ela MUST NOT mencionar pagamentos, Pix, cartão, saques, tarifas, CPF, CNPJ, razão social, foro ou e-mails e endereços que o projeto não tem
- **AND** MUST NOT afirmar datas de fundação, números de doações ou medidas de segurança que o site não tem
- **AND** o único e-mail mostrado MUST ser o de contato do projeto, `solucaothn@gmail.com`

#### Scenario: Contato ainda não definido
- **WHEN** o e-mail de contato do projeto não está definido na configuração do site
- **THEN** os convites de contato (“Fale com a gente”, “Clique aqui para falar conosco”) MUST levar a `/contato`
- **AND** a página `/contato`, a caixa da Central de ajuda e as seções de contato dos Termos e da Privacidade MUST informar que o canal de contato ainda vai ser publicado, sem mostrar um endereço inventado

#### Scenario: Contato definido
- **WHEN** o e-mail de contato do projeto está definido na configuração do site (hoje, `solucaothn@gmail.com`)
- **THEN** “Fale com a gente” (Central de ajuda) e “Clique aqui para falar conosco” (rodapé) MUST levar a `/contato`, onde o e-mail aparece escrito, e não direto a um `mailto:` que não mostra o endereço
- **AND** a página `/contato` MUST mostrar o e-mail escrito e com link `mailto:`, e os links para a Central de ajuda e para a Política de privacidade
- **AND** nenhuma página institucional MUST dizer que o canal de contato ainda vai ser publicado

#### Scenario: Contato nos textos da Central de ajuda, dos Termos e da Privacidade
- **WHEN** o e-mail de contato está definido e a pessoa lê a caixa “Não encontrou o que procurava?”, a seção de contato dos Termos ou a seção de direitos da Política de privacidade
- **THEN** o texto MUST indicar esse e-mail, escrito e com link `mailto:`, como o canal de contato do projeto, inclusive para os pedidos sobre dados pessoais
