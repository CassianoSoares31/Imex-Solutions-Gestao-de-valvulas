# Sistemas Dormindo (desativados só na UI)

Estes sistemas foram **colocados para dormir**: ocultados na interface, mas com
backend, endpoints, models e migrações **intactos**. Nada foi removido — é só
esconder para o usuário não usar. Para **acordar**, reverter as marcações abaixo.

Data: 2026-07-01

## O que está dormindo

1. **Projetos** — filtro de pesquisa, coluna da tabela, botão "Atribuir a projeto",
   modal de atribuição e a linha "Projetos" no detalhe.
2. **Anexos** — seção de anexos no cadastro e na edição, e o modal de duplicata
   com anexos pendentes.
3. **Observação** — campo de observação no cadastro e na edição.

## Como está implementado

Tudo em `templates/core/index.html`:

- Classe CSS central no topo do arquivo:
  ```html
  <style>.dormant{display:none !important;}</style>
  ```
- Cada elemento dos 3 sistemas recebeu a classe `dormant` (ou um wrapper com ela).
  Nas linhas geradas por JS (tabela, form de edição, detalhe) a classe também
  foi adicionada nas strings de template.

## Como acordar

1. Buscar `dormant` em `templates/core/index.html`.
2. Remover a classe `dormant` de cada elemento marcado (e os wrappers
   `<div class="dormant">...</div>` do form de edição).
3. Opcional: remover a regra `.dormant` e este arquivo.

## Backend (não mexido — segue funcionando)

- Endpoints: `projeto_lista_api`, `projeto_criar`, `valvula_atribuir_projeto`,
  `anexo_upload`, `anexo_excluir`, e o campo `observacao` em criar/editar válvula.
- Models: `Projeto`, `Anexo` (relação com `Valvula`), campo `Valvula.observacao`.
- A **Observação continua saindo no PDF/Excel** (Notas), pois o campo no banco não
  foi tocado — só o input na UI ficou oculto. Válvulas já salvas mantêm o valor.
