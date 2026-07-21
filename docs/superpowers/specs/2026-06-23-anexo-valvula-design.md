# Anexos de Válvula — Design

**Data:** 2026-06-23
**Status:** Aprovado para implementação

## Objetivo

Adicionar campo opcional de **anexo** na criação (e edição/visualização) de válvulas.
Cada válvula pode ter **zero, um ou vários** anexos (PDF, PNG, JPG/JPEG). Anexos
persistem em **Supabase Storage** (não no disco efêmero do servidor), aparecem no
detalhe da válvula na web, são incluídos nos ZIPs de exportação e anexados nos
e-mails de envio.

## Decisões de design

- **Storage:** Supabase Storage via REST API usando a lib `requests` (já presente
  em `requirements.txt`). Sem novas dependências (sem `boto3`, sem `supabase-py`).
- **Multiplicidade:** vários anexos por válvula → tabela própria `AnexoValvula`.
- **Tipos aceitos:** `pdf`, `png`, `jpg`, `jpeg`.
- **Tamanho máximo:** 10 MB por arquivo.
- **Exportação:** anexos entram no ZIP (`valvula_pdf`, `valvula_export_lote`) e
  são anexados no e-mail (`valvula_email`).
- **Permissão de exclusão de anexo:** apenas `ESPECIAL` (igual editar/excluir válvula).
  Upload de anexo: qualquer usuário autenticado (igual criar válvula).

## Passo manual (pré-requisito do deploy)

Antes do código funcionar em produção, o usuário precisa:

1. No painel Supabase → Storage → criar bucket (ex.: `anexos-valvulas`), privado.
2. Adicionar 3 variáveis de ambiente (local `.env` + servidor de produção):
   - `SUPABASE_URL` — URL do projeto (ex.: `https://xneoxfztyodycdswzawt.supabase.co`)
   - `SUPABASE_KEY` — chave `service_role` (secreta, server-side only)
   - `SUPABASE_BUCKET` — nome do bucket (ex.: `anexos-valvulas`)
3. Atualizar `.env.example` com placeholders dessas 3 vars.

## Modelo de dados

Nova tabela `AnexoValvula` em `core/models.py`:

| Campo          | Tipo                              | Notas                                  |
|----------------|-----------------------------------|----------------------------------------|
| `id`           | AutoField PK                      |                                        |
| `valvula`      | FK → Valvula (CASCADE)            | `related_name="anexos"`                |
| `storage_key`  | CharField                         | Path do objeto no bucket (único)       |
| `nome_original`| CharField                         | Nome do arquivo enviado pelo usuário   |
| `content_type` | CharField                         | MIME (ex.: `application/pdf`)          |
| `tamanho`      | PositiveIntegerField              | Bytes                                  |
| `enviado_em`   | DateTimeField(auto_now_add=True)  |                                        |

`storage_key` formato sugerido: `valvulas/{valvula_id}/{uuid4}.{ext}` para evitar colisão.
Migration nova gerada via `makemigrations`.

## Módulo de storage — `core/storage.py` (novo)

Encapsula Supabase Storage REST. Lê config de `settings` (que lê env).

Funções:
- `upload(key, conteudo_bytes, content_type) -> None`
  `POST {SUPABASE_URL}/storage/v1/object/{bucket}/{key}` com header
  `Authorization: Bearer {SUPABASE_KEY}` e `Content-Type`.
- `download(key) -> bytes`
  `GET {SUPABASE_URL}/storage/v1/object/{bucket}/{key}` autenticado. Usado pelo
  export/email (server baixa e re-empacota).
- `delete(key) -> None`
  `DELETE {SUPABASE_URL}/storage/v1/object/{bucket}/{key}`.
- `signed_url(key, expires=3600) -> str`
  `POST {SUPABASE_URL}/storage/v1/object/sign/{bucket}/{key}` → URL temporária
  para download direto pelo browser.

Erros de storage → levantam exceção tratada nas views (retorna 502/500 JSON).

## Validação de upload

No endpoint de upload, antes de mandar pro storage:
- Extensão ∈ {`pdf`, `png`, `jpg`, `jpeg`} (case-insensitive).
- Tamanho ≤ 10 MB (`request.FILES[...].size`).
- Falha → `400` JSON com mensagem clara.

## Endpoints (core/urls.py + core/views.py)

| Rota                                | Método | View                  | Permissão        |
|-------------------------------------|--------|-----------------------|------------------|
| `/api/valvulas/<pk>/anexos/`        | POST   | `anexo_upload`        | autenticado      |
| `/api/anexos/<id>/download/`        | GET    | `anexo_download`      | autenticado      |
| `/api/anexos/<id>/excluir/`         | POST   | `anexo_excluir`       | ESPECIAL         |

- `anexo_upload`: recebe `multipart/form-data` (1+ arquivos), valida cada um, faz
  upload pro storage, cria registros `AnexoValvula`. Retorna lista dos anexos criados (JSON).
- `anexo_download`: gera `signed_url` e responde `302` redirect (browser baixa direto do Supabase).
- `anexo_excluir`: `especial_required`; deleta do storage e o registro.
- `valvula_detalhe_api` (existente, view ~linha 646): passa a incluir lista de
  anexos (`id`, `nome_original`, `tamanho`, `content_type`, `url_download`).

`valvula_criar` **não muda** — continua JSON puro. O frontend cria a válvula primeiro
(JSON) e, em seguida, faz POST multipart dos anexos para o `pk` retornado.

## Exportação

- `valvula_pdf` (view ~linha 2235) e `valvula_export_lote` (~2564): após montar
  PDF+Excel, para cada anexo da válvula chamam `storage.download(key)` e gravam o
  arquivo na subpasta da válvula dentro do ZIP (ex.: `{codigo}/anexos/{nome_original}`).
- `valvula_email` (~2595): além dos PDFs, baixa os anexos das válvulas selecionadas
  e os adiciona como anexos do e-mail.
- Anexo ausente/erro de download no storage: log + pula aquele arquivo, não quebra
  a exportação inteira.

## Frontend — `templates/core/index.html`

- **Modal criar válvula:** input `<input type="file" multiple accept=".pdf,.png,.jpg,.jpeg">`
  (opcional). Após o POST de criação ter sucesso e retornar o `pk`, o JS envia os
  arquivos via `FormData` para `/api/valvulas/<pk>/anexos/`.
- **Modal visualizar válvula:** bloco "Anexos" listando cada anexo com nome, tamanho,
  link de download e botão excluir (botão excluir só renderiza para usuário ESPECIAL).
- Mensagens de erro de upload (tipo/tamanho) exibidas no modal.

## Configuração — `config/settings.py`

Adicionar leitura das 3 vars:
```python
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "")
```
`MEDIA_ROOT`/`MEDIA_URL` existentes permanecem (não usados para anexos).

## Fora de escopo (YAGNI)

- Versionamento de anexos / histórico.
- Preview inline de imagens (só link de download).
- Anexos em PDF individual da válvula (`valvula_pdf.html` template) — anexos vão no
  ZIP como arquivos separados, não embutidos no PDF.
- Anexos por projeto.

## Testes / verificação

- `core/tests.py` está vazio; adicionar testes mínimos:
  validação de extensão/tamanho rejeitando inválidos; criação de `AnexoValvula`;
  `anexo_excluir` bloqueando usuário COMUM (403).
- Storage real (Supabase) mockado nos testes (sem chamada de rede).