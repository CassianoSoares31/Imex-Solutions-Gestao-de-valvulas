 # Imex Solutions - Sistema de Gestao de Valvulas Industriais

## Visao Geral

Sistema web para cadastro, consulta e exportacao de especificacoes tecnicas de valvulas industriais. Desenvolvido em **Django 6.0** com **PostgreSQL** (Supabase).

O sistema e uma SPA (single-page application) server-rendered: o Django renderiza templates HTML e toda a interacao acontece via chamadas AJAX (JSON) para endpoints da API REST interna. Nao existe framework JS de frontend separado.

---

## Stack Tecnica

- **Backend**: Django 6.0 (Python)
- **Banco de dados**: PostgreSQL via Supabase (psycopg 3)
- **Frontend**: HTML + Bootstrap 5.3 + JavaScript vanilla (sem React/Vue)
- **PDF**: xhtml2pdf (+ reportlab, pypdf, svglib para medir/renderizar)
- **Excel**: openpyxl
- **Email**: SMTP Gmail
- **Arquivos estaticos**: WhiteNoise
- **Anexos**: Supabase Storage via REST (`requests`), com fallback no banco

---

## Estrutura de Arquivos

```
Imex-Solutions/
├── config/                     # Configuracao do projeto Django
│   ├── settings.py             # Settings principal (DB, email, static, storage)
│   ├── settings_test.py        # Settings para testes (SQLite em memoria, MD5 hasher)
│   ├── urls.py                 # URL raiz: admin/ + core/
│   ├── wsgi.py                 # Entrypoint WSGI (gunicorn)
│   └── asgi.py                 # Entrypoint ASGI
├── core/                       # App unica do projeto
│   ├── models.py               # ~1.7k linhas: choices por tipo + modelos
│   ├── views.py                # ~5.3k linhas: TUDO (auth, CRUD, regras, PDF, codigo universal)
│   ├── storage.py              # Backend de anexos (Supabase REST | StorageBlob no banco)
│   ├── urls.py                 # Rotas da app core (API + paginas)
│   ├── forms.py                # ValvulaForm, formsets, MaterialForm, PesquisaForm
│   ├── admin.py                # Tb_Usuario, Material, OpcaoFlange, OpcaoPlacaIdentificacao
│   ├── apps.py                 # AppConfig
│   ├── tests.py                # ~190 testes (models, auth, CRUD, regras, export)
│   └── migrations/             # Migracoes do banco
├── templates/core/             # Templates HTML
│   ├── base.html               # Layout base (navbar, tema claro/escuro)
│   ├── index.html              # ~6k linhas: dashboard + CRUD + formulario dinamico
│   ├── auth.html               # Login e cadastro
│   ├── usuarios.html           # Gestao de usuarios (so ESPECIAL)
│   ├── projetos.html           # Gestao de projetos (so ESPECIAL)
│   ├── estatisticas.html       # Dashboard de estatisticas (so ESPECIAL)
│   ├── valvula_pdf.html        # Template da folha de dados (PDF e preview)
│   ├── esqueci_senha.html      # Formulario esqueci senha
│   ├── redefinir_senha.html    # Formulario nova senha (via token)
│   ├── redefinir_senha_resultado.html  # Resultado da redefinicao
│   └── verificacao_resultado.html      # Resultado da verificacao de email
├── static/                     # Fonte dos estaticos (logo, css)
├── staticfiles/                # Coletados pelo collectstatic (WhiteNoise serve daqui)
├── manage.py                   # CLI do Django
├── requirements.txt            # Dependencias Python
├── .env / .env.example         # Variaveis de ambiente
└── README.MD                   # Requisitos e opcoes por tipo de valvula
```

**Nao existe camada de services/**: toda a logica vive em `core/views.py`. Mapa aproximado do arquivo:

| Linhas | Conteudo |
|--------|----------|
| 1-150 | Helpers de diametro, `especial_required`, `_lock_tipo_valvula`, `gerar_codigo` |
| 156-830 | Auth, cadastro, reset de senha, usuarios, estatisticas |
| 864-1330 | Listagem, detalhe, anexos, projetos |
| 1429-2350 | **Motor de regras**: constantes de campo, regras automaticas, validacoes, dup-check |
| 2350-2520 | CRUD de valvula + preview |
| 2651-4360 | Traducao PT/EN, folha de dados, **codigo universal A-N** |
| 4363-4930 | PDF/Excel/ZIP, export em lote, email |

---

## Modelos (core/models.py)

### Tb_Usuario (AUTH_USER_MODEL customizado)
- Extende `AbstractBaseUser` + `PermissionsMixin` com `UsuarioManager`
- **Campos**: nome, email (unique, USERNAME_FIELD), nivel_permissao, confirmado, is_active, is_staff
- **Permissoes**: `ESPECIAL` (admin) e `COMUM` (usuario padrao)
- **Verificacao**: token_verificacao (UUID), token_expiracao (para reset de senha)
- **Controle de senha**: senha_alterada_em, trocas_senha_hoje (max 3/dia), ultima_data_troca
- Superusuarios sao criados como ESPECIAL e ja confirmados

### Projeto
- id_projeto (PK), nome (unique), status (ATIVO/CONCLUIDO), criado_em
- Relacao com Valvula e **N:N** (`Valvula.projetos` / `Projeto.valvulas`)

### Valvula (tabela central)
- id_valvula (PK), codigo (unique, gerado automaticamente)
- tipo_valvula: ESFERA, GAVETA, GLOBO, RETENCAO, BORBOLETA, GLOBO_CONTROLE
- funcao: BLOQUEIO ou CONTROLE (decide se a secao de instrumentacao existe)
- ~120 campos de especificacao tecnica, incluindo 4 subcategorias de instrumentacao
  (posicionador, solenoide, chave_fim_curso, sensor_posicao) x 8 campos cada
  (ex/protecao/grupo/temp/epl + tensao/corrente/potencia)
- Campos dinamicos por tipo (`CAMPOS_POR_TIPO` define quais campos sao visiveis)
- `criado_por` (FK Tb_Usuario, SET_NULL) para estatisticas
- Codigo formato: prefixo 3 letras + 6 digitos (ex: VES000001, VGA000001)

### Material
- id_material (PK), nome. Tabela de lookup (ASTM, AISI, etc.)

### ValvulaMaterial (N:N entre Valvula e Material)
- valvula (FK), material (FK), tipo_material
- Tipos: CORPO_TAMPA, OBTURADOR, SEDE, INSERTO_SEDE, HASTE, MOLAS, JUNTA, GAXETA, PARAFUSOS, PORCAS
- `unique_together: [valvula, tipo_material]`
- `clean()` duplica a regra da gaxeta NBR (a validacao real acontece na view)

### Vedacao
- valvula (FK), vedacao_corpo_tampa, vedacao_junta
- O dado atual vive em `vedacao_junta`; `vedacao_corpo_tampa` e o fallback de dados antigos

### ComponentesInternos
- valvula (FK), inserto_rede

### AnexoValvula
- valvula (FK), storage_key (unique), nome_original, content_type, tamanho, enviado_em
- So metadados; o binario vive no backend de storage

### StorageBlob
- key (unique), data (BinaryField). Fallback de conteudo quando Supabase nao configurado

### TentativaDuplicata
- tipo_valvula, valvula_existente (FK), usuario (FK), criado_em
- Gravado toda vez que uma criacao bate em duplicata (409); alimenta as estatisticas

### OpcaoFlange / OpcaoPlacaIdentificacao
- Subclasses de `OpcaoSimples` (valor, ordem, ativo)
- Listas "folha" editaveis pelo admin; so alimentam dropdowns, nao entram em regra NBR

---

## Rotas e Endpoints (core/urls.py)

### Paginas HTML
| Rota | View | Descricao |
|------|------|-----------|
| `/` | `index` | Dashboard principal (requer auth) |
| `/auth/` | `auth_page` | Login/Cadastro |
| `/logout/` | `logout_api` | Logout (redirect) |
| `/usuarios/` | `usuarios_page` | Gestao de usuarios (so ESPECIAL) |
| `/projetos/` | `projetos_page` | Gestao de projetos (so ESPECIAL) |
| `/estatisticas/` | `estatisticas_page` | Dashboard de estatisticas (so ESPECIAL) |
| `/esqueci-senha/` | `esqueci_senha_page` | Formulario esqueci senha |
| `/redefinir-senha/<token>/` | `redefinir_senha_form` | Formulario nova senha |
| `/verificar-email/<token>/` | `verificar_email` | Confirmacao de email |

### API REST (JSON)
| Rota | Metodo | View | Auth |
|------|--------|------|------|
| `/api/login/` | POST | `login_api` | - |
| `/api/cadastro/` | POST | `cadastro_api` | - (csrf_exempt) |
| `/api/esqueci-senha/` | POST | `esqueci_senha_api` | - (csrf_exempt) |
| `/api/redefinir-senha/` | POST | `redefinir_senha_api` | - |
| `/api/usuarios/` | GET | `usuario_lista_api` | ESPECIAL |
| `/api/usuarios/<pk>/permissao/` | POST | `usuario_alterar_permissao` | ESPECIAL |
| `/api/usuarios/<pk>/confirmar/` | POST | `usuario_confirmar` | ESPECIAL |
| `/api/estatisticas/` | GET | `estatisticas_api` | ESPECIAL |
| `/api/dashboard-contadores/` | GET | `dashboard_contadores_api` | auth |
| `/api/valvulas/` | GET | `valvula_lista_api` | **nenhuma** |
| `/api/valvulas/<pk>/` | GET | `valvula_detalhe_api` | **nenhuma** |
| `/api/valvulas/criar/` | POST | `valvula_criar` | auth |
| `/api/valvulas/preview/` | POST | `valvula_preview` | auth |
| `/api/valvulas/<pk>/editar/` | POST | `valvula_editar` | ESPECIAL |
| `/api/valvulas/<pk>/excluir/` | POST | `valvula_excluir` | ESPECIAL |
| `/api/valvulas/excluir-lote/` | POST | `valvula_excluir_lote` | ESPECIAL |
| `/api/valvulas/exportar-lote/` | POST | `valvula_export_lote` | auth |
| `/api/valvulas/email/` | POST | `valvula_email` | auth |
| `/api/valvulas/<pk>/anexos/` | POST | `anexo_upload` | auth |
| `/api/anexos/<id>/download/` | GET | `anexo_download` | auth |
| `/api/anexos/<id>/excluir/` | POST | `anexo_excluir` | ESPECIAL |
| `/api/projetos/` | GET | `projeto_lista_api` | **nenhuma** |
| `/api/projetos/criar/` | POST | `projeto_criar` | ESPECIAL |
| `/api/projetos/<pk>/status/` | POST | `projeto_alterar_status` | ESPECIAL |
| `/api/projetos/<pk>/excluir/` | POST | `projeto_excluir` | ESPECIAL |
| `/api/valvulas/atribuir-projeto/` | POST | `valvula_atribuir_projeto` | ESPECIAL |
| `/api/valvulas/desatribuir-projeto/` | POST | `valvula_desatribuir_projeto` | ESPECIAL |
| `/api/pesquisa-avancada/` | GET | `pesquisa_avancada_api` | **nenhuma** |
| `/api/opcoes-por-tipo/` | GET | `opcoes_por_tipo` | **nenhuma** |
| `/api/materiais-por-tipo/` | GET | `materiais_por_tipo` | **nenhuma** |
| `/api/materiais/` | GET | `material_lista_api` | **nenhuma** |
| `/api/materiais/criar/` | GET/POST | `material_criar` | **nenhuma** |
| `/api/debug/verification-tokens/` | GET | `debug_verification_tokens` | so DEBUG=True |
| `/valvulas/<pk>/pdf/` | GET | `valvula_pdf` | **nenhuma** |

---

## Permissoes e Autenticacao

### Niveis de acesso
- **ESPECIAL**: Pode tudo (editar/excluir valvulas, gerenciar usuarios, projetos, ver estatisticas)
- **COMUM**: Cria valvulas, visualiza, exporta, pesquisa, sobe anexos

### Decorator `especial_required` (views.py:72)
- Retorna 403 JSON se nao autenticado ou nao ESPECIAL
- A maioria das views repete o check inline em vez de usar o decorator

### Fluxo de cadastro
1. Usuario preenche nome, email, senha
2. Sistema cria usuario com `confirmado=False`
3. Email de verificacao enviado (async via thread)
4. Usuario clica no link -> `confirmado=True`, token invalidado
5. Se email ja existe mas nao confirmado, atualiza dados e reenvia

### Fluxo de reset de senha
1. Usuario informa email em `/esqueci-senha/`
2. Token UUID gerado com expiracao de 30 minutos
3. Email enviado com link `/redefinir-senha/<token>/`
4. Limite de 3 trocas de senha por dia
5. Apos troca, todas as sessoes do usuario sao invalidadas
6. Nao revela se o email existe ou nao (seguranca)

---

## Travas (o que garante a integridade)

### 1. Concorrencia: advisory lock (`_lock_tipo_valvula`, views.py:139)
`pg_advisory_xact_lock(crc32("valvula_criar:<tipo>"))` dentro de `transaction.atomic()`.
Serializa dup-check + `gerar_codigo` + save por tipo de valvula. Sem ele, requests
concorrentes passam juntos no check (TOCTOU -> duplicatas) e geram o mesmo codigo
(colisao no unique -> IntegrityError/500). Lock liberado no commit/rollback.
**So funciona em PostgreSQL**; vira no-op nos testes (SQLite).

### 2. Regras de negocio: 3 estagios compartilhados por criacao e edicao
1. **`_aplicar_regras_automaticas(tipo, data)`** — forca valores derivados
2. **`_validar_regras_valvula(tipo, data)`** — 42 regras, retorna 400 no primeiro erro
3. **`_limpar_campos_por_tipo(valvula, tipo)`** — no objeto ja montado, zera todo campo
   fora de `CAMPOS_POR_TIPO[tipo]` e forca `classe_pmt` / `anexo_nbr`

Alterar regra em um helper vale para as duas views. `valvula_preview` **duplica**
a mao parte das regras automaticas (nao chama o helper) — mexer no helper exige
mexer no preview.

### 3. Dup-check (`_encontrar_duplicata`)
Monta um `Q` com `CAMPOS_TEXTO_DUP` + `CAMPOS_BOOL_VALVULA` + qsl + funcao; campos
nullable usam `Q(campo="") | Q(campo__isnull=True)`. Depois compara materiais,
vedacoes e componentes em Python por candidato. **Duplicata e global** — a mesma
spec so pode existir 1x, projetos sao associacoes a parte. Retorna 409 e grava
`TentativaDuplicata`.

### 4. Bypass de validacao
`valvula_editar` aceita `bypass_validacao: true` no payload: pula `_validar_regras_valvula`
**e** o dup-check. As regras automaticas e a limpeza por tipo continuam rodando. So
ESPECIAL chega nessa view.

### 5. Anexos
Extensoes `{pdf, png, jpg, jpeg}`, maximo 10 MB (`ANEXO_TAMANHO_MAX`).

---

## Regras de Negocio (Validacoes)

### Formulario dinamico por tipo de valvula
Cada tipo tem campos visiveis (`CAMPOS_POR_TIPO`), normas (`NORMAS_POR_TIPO`),
materiais por componente (`MATERIAIS_POR_TIPO`), diametros, classes, extremidades,
acionamentos e vedacoes proprios.

### Codigo automatico
- Formato: 3 letras + 6 digitos sequenciais
- Prefixos: VES (Esfera), VGA (Gaveta), VGL (Globo), VRE (Retencao), VBO (Borboleta), VGC (Globo Controle)
- Sequencia por tipo: carrega todas as valvulas do prefixo e incrementa o maior numero (O(n) por criacao)

### Regras automaticas (`_aplicar_regras_automaticas`)
1. **Retencao**: `juncao_corpo_castelo = APARAFUSADO` sempre
2. **Funcao = Bloqueio**: limpa todos os `CAMPOS_INSTRUMENTACAO` e forca `caracteristicas = "On - Off"`
3. **Funcao = Controle**: forca solenoide / chave fim de curso / sensor de posicao = "SIM"
4. **Acionamento manual** (Alavanca / Volante / Volante c/ Caixa de Reducao): posicao de falha N/A,
   marca do atuador "Padrao Fabricante", zera flange de acoplamento e dados eletricos
5. **Pintura** "Padrao Fabricante" -> cor/condicao "Padrao do Fabricante"; "Sem Pintura" -> N/A.
   Mesma regra espelhada para a pintura do atuador. `norma_pintura` esta aposentado (a norma virou o proprio campo `pintura`)
6. **Esfera + NBR + Trunnion + DIB-1**: `valvula_alivio = True`

### Regras validadas (`_validar_regras_valvula`)
Nao-NBR:
- Funcao = Controle -> caracteristica nao pode ser "On - Off"
- Pintura com norma -> exige cor especifica (nem Padrao do Fabricante nem N/A). Idem atuador
- Norma API 6D -> QSL obrigatorio; classe nao pode ser PN/400/800/4500 (400 existe no modelo so' pra Retencao/BS 1868); diametro maximo por classe (900: 48", 1500: 36", 2500: 20")
- Classe PMT (Borboleta) -> `classe_pmt` (texto livre) obrigatorio

NBR 15827 habilitado:
1. **Gaveta + gaxeta**: obrigatoriamente "Grafite Flex. + Fio Inconel c/ Inibidor (molibdato bario/zinco)"
2. **Gaveta/Retencao + vedacao corpo/tampa**: restrita por classe (`_VED_NBR_POR_CLASSE`, views.py:37)
3. **Gaveta/Retencao + junta**: nao pode ser N/A
4. **Corpo carbono** (A105/A181/A216 WCB): parafusos B7 + porcas 2H
5. **Corpo liga** (A350 LF2/LF3, A352 LCB/LC3): parafusos A320 L7/B8M/B8M CL2 + porcas 8M/4L/7L
6. **Corpo cromo-molib** (A182 F11 CL2/F5, A217 WC6/C5): parafusos B16 + porcas Gr 7
7. **Corpo inox austenitico**: parafusos B8M/B8M CL2 + porcas 8M + revestimento N/A
8. **Esfera**: haste = mesmo material do obturador
9. **Esfera**: dispositivo antiestatico obrigatorio
10. **Esfera + Trunnion + DIB-1**: valvula de alivio obrigatoria
11. **Esfera + diametro >= 6" + classe ANSI**: montagem Trunnion
12. **Esfera + extremidade Niple**: forcada por material do corpo (SCH 80 ou SCH 160)
13. **Por extremidade** (Flange/Butt-Welding/Socket-Welding/Rosca/Wafer): cada combinacao
    tipo + extremidade restringe diametro, classe e norma
14. **Borboleta**: Wafer/Lug + Concentrica + corpo A536 (classe PMT, norma API 609);
    Bi/Tri-Excentrica com restricoes por corpo.
    (As regras de Categoria A/B **nao** dependem de NBR — ver secao API 609 abaixo)
15. **anexo_nbr** e derivado, nao vem do frontend: Gaveta -> "Anexo A", Retencao -> "Anexo B", Esfera -> "Anexo C"
16. **Niple (Tabela C.2)**: 150/300/600/800 -> SCH 160 (carbono/liga) ou SCH 80S (inox);
    900 e 1500 -> SCH 160 (ambos); 2500 -> XXS (ambos). So valida quando a extremidade
    escolhida ja e um Niple — Socket-Welding e Rosca tem regra propria e escapam antes

Ver `views.py:1535-2173` para as tabelas completas.

---

## API 609 (Borboleta) — independe de NBR

Norma em `normas/035_API 609_2016 ...md` (mesmo aviso de OCR: para duvida, abrir o PDF
original). As travas saem da **seccao 1.3**, que define escopo de tamanho e classe por
categoria. Valem sempre que `norma = API 609`, com ou sem NBR.

- **Categoria A** (CWP, disco concentrico): diametro 2"-48"; classe 125/150/PMT; disco
  Concentrica; **face a face so Lug ou Wafer** — a norma so da face a face de Categoria A em
  lug/wafer (Tabela 2); as tabelas de duplo flange (3B/3C) sao exclusivas de Categoria B
- **Categoria B** (ASME class, sede com offset): classe 150/300/600; diametro **3"-48"** por
  padrao, com o face a face apertando o teto: Flangeada Padrao Longo -> 36";
  Flangeada Padrao Curto + classe 600 -> 24"; Lug/Wafer ou face a face em branco -> 48"
- **Qualquer Borboleta + API 609**: classe em {125, 150, 300, 600, PMT} — a norma cobre so
  Classes 125-600. Roda depois das regras de Categoria A/B (que dao mensagem mais especifica)
  e existe para pegar o caso de `categoria_borboleta` em branco

Espelhadas no frontend em `aplicarRegraBorboletaCategoriaA` / `aplicarRegraBorboletaCategoriaB`.
Cobertas por `BorboletaApi609EscopoTest`.

**Candidato nao implementado** (precisa de confirmacao da engenharia): 4.2.2 manda o corpo de
ferro dutil de Categoria B ter o rating pela ASME B16.42, e a Secao 2 anota que a B16.42 vale
so `[Class 150 and 300]` — o que implicaria Categoria B + corpo ASTM A536 -> classe 150 ou
300, barrando 600. E inferencia encadeada (duas afirmacoes normativas ligadas por deducao),
nao texto direto; por isso nao virou trava.

**Fora de alcance do modelo**: Tabela 1 (rating P-T de sede PTFE/RPTFE por classe — a classe
600 so lista RPTFE, mas 4.3.1 deixa o fabricante estabelecer rating para material fora da
tabela, entao nao proibe PTFE), Tabela D.2 (schedule do tubo x categoria/tamanho/classe),
Anexo D (folga disco-tubo), 5.5/5.10 (acabamento de haste, gland bolting), 6.5 (temperatura
de fusao do mecanismo). Nenhum tem campo correspondente na Valvula.

---

## ISO 14313 (7.2) — Esfera, Gaveta, Retencao

Norma em `normas/027_ISO 14313_2007 ...md` (OCR RapidOCR — **tabelas sairam embaralhadas**;
para numero/tabela, confirmar no PDF). So a **7.2** aterrissa nos campos existentes:

> "Valves covered by this International Standard shall be furnished in one of the following
> classes: PN 20 (class 150); PN 50 (class 300); PN 64 (class 400); PN 100 (class 600);
> PN 150 (class 900); PN 250 (class 1500); PN 420 (class 2500)"

```
norma = ISO 14313 -> classe em {150, 300, 600, 900, 1500, 2500,
                                PN 20, PN 50, PN 100, PN 150, PN 250, PN 420}
```
Barra **800**, **4500** e **PN 10/16/25/40**. Class 400 / PN 64 nao existe no `CLASSES` do
modelo, por isso esta fora da lista.

### ISO 14313 e API 6D sao harmonizadas, mas NAO intercambiaveis

A Introduction diz que a ISO 14313:2007 "is the result of harmonizing the requirements of
ISO 14313:1999 and API Spec 6D-2002" — e por isso que as tabelas da NBR escrevem
"ISO 14313 (API 6D)". Mas as regras **nao** podem ser reusadas de uma para a outra:

- **PN**: a ISO 14313 aceita a serie PN como designacao primaria; a API 6D (2021) e so
  Class. A regra da API 6D barra PN de proposito — nao "consertar" para casar com a ISO
- **QSL**: e conceito da API 6D (Anexo I). **Nao existe na ISO 14313** (zero ocorrencias no
  texto). Por isso a ISO nao exige QSL

Fica no fim de `_validar_regras_valvula`, junto da B16.34, pelo mesmo motivo (vale para
qualquer tipo -> regras especificas falam primeiro). Espelhada em
`aplicarRegraISO14313Classe`, chamada pelo atalho `aplicarRegrasNorma` (que roda as
genericas de norma: ISO 14313 + B16.34). Coberta por `Iso14313EscopoTest`.

**Fora de alcance**: Tabela 1 (bore minimo por DN/classe — OCR ilegivel, nao derivar dela),
7.7.3 (*"Other end connections can be specified by the purchaser"* — extremidade nao e
restrita), 7.8 (alivio de cavidade: depende de servico liquido/condensavel, que nao e campo,
e termina em "by agreement"), 7.6 (piggability e especificada pelo comprador).
Cobertura de tipo ja esta certa: a norma cobre gate/plug/ball/check — "butterfly" e "globe"
nao aparecem no texto, e `NORMA_GLOBO`/`NORMA_BORBOLETA` ja nao oferecem ISO 14313.

**Varredura completa feita (2026-07-15)** — 7.9-7.21, 8.1-8.8, 9-13 e todos os "shall not"
da norma conferidos; **nada mais aterrissa em campo existente**. Nao reabrir sem campo novo:
7.9/Tabela 7 (tamanho de dreno/vent — `dreno`/`vent` sao booleanos, mesmo muro do 6.3.6 da
B16.34), 7.10-7.14 e 7.17 ("if specified by the purchaser"), 7.13 (forca <=360 N e sentido
horario — sem campo), 7.18-7.21 (projeto do trem de acionamento — fabricante), 8.4 (quimica
C/S/P/CE<=0,43% — sem campo), 8.5 (Charpy exige temperatura de projeto — sem campo), 8.6
(dureza de parafuso HRC 34 — dureza nao e derivavel do grau escolhido sem inferencia de
engenharia), 11 (ensaios de fabrica), 13 (marcacao de plaqueta). O `dib` (DBB/DIB-1/DIB-2)
aparece so em 11.4.4.3/Anexo B como escolha do comprador que define o ensaio — nao restringe.

---

## ISO 17292 (Secao 1 + 5.2.7) — Esfera

Norma em `normas/036_ISO 17292_2015 ...md` (pymupdf4llm, nao escaneado — texto confiavel).
Metal ball valves; so a Esfera oferece a norma (`NORMA_ESFERA`). Escopo da Secao 1:

```
norma = ISO 17292 →
  classe em {150, 300, 600, 800, PN 16, PN 25, PN 40, PN 100}
    (PN 63 existe na norma mas nao no CLASSES do modelo, como o PN 64 da ISO 14313)
  classe 800 so em Rosca/Socket-Welding ("Class 800 applies only for valves with
    threaded and socket welding end")
  extremidade so Flange/Butt-Welding/Socket-Welding/Rosca — Niple conta como SW
    (NBR C.1.4.1); Wafer/Lug/Gray Loc Hub nao existem na norma
  diametro: Flange/BW ate 24" (DN 600); SW/Rosca ate 2" (DN 50)
    (minimos DN 8-15 ficam abaixo do menor diametro do modelo, 1/2" — sem validacao)
  dispositivo antiestatico obrigatorio (5.2.7 "Valves shall incorporate an
    anti-static feature") — vale com ou sem NBR
```

Fica no fim de `_validar_regras_valvula` junto das outras genericas de norma (ISO 14313,
B16.34). Espelho JS: `aplicarRegraISO17292` (padrao `_bloquearOptsPorNorma`, no atalho
`aplicarRegrasNorma`) + `aplicarRegraAntiestatico` estendida (forca o checkbox quando
norma = ISO 17292, badge "Obrigatorio (ISO 17292)"; re-rodada nos listeners de
`id_norma`/`edit_norma`). Coberta por `Iso17292EscopoTest`.

**Fora de alcance do modelo**: Tabela 1 (rating P-T de sede PTFE — exige temperatura de
processo, sem campo), Tabela 2 (bore minimo em mm por DN — `tipo_passagem` e so
Plena/Reduzida, sem mm; double reduced nao existe como choice), Tabela 3/6 (espessura de
parede — sem campo), 5.2.10 (esfera solida — sem campo de construcao da esfera),
5.2.11.11 (lockable device — sem campo), 6.9 (H2S/NACE — "when specified by purchaser",
opcao e nao restricao; o campo `nace` ja existe e e livre), 8.4.3 (fire test ISO 10497 e
"recommended" — nao trava).

## BS ISO 7121 (Cláusula 1 + 5.1/Tabela 2) — Esfera

Norma em `normas/Normas feitas/055_ISO 7121_2006 ...md` (texto e' o ISO 7121:2006 base;
BS ISO 7121 e' a adocao britanica identica — mesmo caso do BS EN ISO 17292). Steel ball
valves for general-purpose industrial applications; so a Esfera oferece a norma. Escopo
da Clausula 1 + nota de rodape da Tabela 2:

```
norma = BS ISO 7121 →
  classe em {150, 300, 600, 900, PN 10, PN 16, PN 25, PN 40, PN 100}
    (PN 63 existe na norma mas nao no CLASSES do modelo, mesmo caso do PN 63 da
    ISO 17292 e do PN 64 da ISO 14313)
  classe 900 → tipo_passagem so Reduzida ("only valves having reduced port are
    within the scope" — nota da Tabela 2; o modelo nao distingue reduced/double
    reduced bore, so' Plena/Reduzida)
  extremidade so Flange/Butt-Welding/Socket-Welding/Rosca — Niple conta como SW
    (NBR C.1.4.1); Wafer/Lug/Gray Loc Hub nao existem na norma
  diametro: Flange/BW ate 20" (DN 500); Socket-Welding ate 4" (DN 100);
    Rosca ate 2" (DN 50) — diferente da ISO 17292, aqui SW vai mais longe que Rosca
  dispositivo antiestatico e' OPCIONAL (5.2.7 "when specified in the purchase
    order") — nao trava, diferente da ISO 17292 onde e' mandatorio
```

Fica no fim de `_validar_regras_valvula` junto das outras genericas de norma (ISO 14313,
ISO 17292, B16.34) — depois da regra especifica `_ESF_ROSCA_*` (Esfera+NBR+Rosca), que
fala primeiro quando aplicavel. Espelho JS: `aplicarRegraBS7121` (padrao
`_bloquearOptsPorNorma`, no atalho `aplicarRegrasNorma`). Coberta por `Bs7121EscopoTest`.

**Fora de alcance do modelo**: Tabela 1 (rating P-T de sede PTFE — exige temperatura de
processo, sem campo), Tabela 3/6 (espessura de parede/casco — sem campo), 5.2.10 (esfera
com furo circular — sem campo de construcao), 5.2.11.11 (nao existe nesta norma, so' na
ISO 17292), 8.4.3 (fire test ISO 10497 e' "recommended" — nao trava).

## API 608 (Cláusula 1) — Esfera

Norma em `normas/Normas feitas/034_API 608_2002 ...md` (pymupdf4llm, não escaneado —
texto confiável). *Metal Ball Valves—Flanged, Threaded, and Welding Ends*: só a Esfera
oferece a norma (`NORMA_ESFERA`). 1.2 diz que cobre requisitos adicionais aos de
"ASME B16.34, Standard Class" — a regra genérica da B16.34 já roda depois, no fim de
`_validar_regras_valvula`. Escopo da Cláusula 1:

```
norma = API 608 (Esfera) →
  1.1: "butt-welding or flanged ends for ... NPS 1/2 through NPS 12 and threaded or
    socket-welding ends for sizes NPS 1/2 through NPS 2" →
    tipo_extremidade só Flange/Butt-Welding/Socket-Welding/Rosca — Niple conta como SW
      (NBR C.1.4.1); Wafer/Lug/Gray Loc Hub não existem na norma
    diâmetro: Flange/Butt-Welding até 12"; Socket-Welding/Rosca até 2"
  1.3: "flanged and butt-welding end valves in Standard Classes 150 and 300 and threaded
    and socket-welding end valves in Standard Classes 150, 300, and 600" →
    classe: Flange/Butt-Welding só 150 ou 300 (sem 600); Socket-Welding/Rosca 150/300/600
```

4.4 (continuidade elétrica/antiestático, "when specified in the purchase order") é
opcional — não trava, mesmo caso da BS ISO 7121 (diferente da ISO 17292, onde é
mandatório).

Fica logo após o bloco da BS ISO 7121 e antes da ISO 15761 (mesma posição de prioridade
das outras genéricas-por-norma — específica de tipo, antes da genérica-pra-qualquer-tipo
B16.34). Espelho JS: `aplicarRegraApi608` (padrão `_bloquearOptsPorNorma`, registrada em
`aplicarRegrasNorma` e na lista de bypass-de-edição). Coberta por `Api608EscopoTest`.

**Fora de alcance do modelo**: 3 (ratings P-T de sede/casco — Tabela 1, exige temperatura
de processo, sem campo), 4.2.1-4.2.8 (espessura de parede, face-a-face, rosca, teste de
sede da trunnion — dimensional/construtivo, sem campo), 4.2.9 (dreno/bypass "if specified
by the purchaser" — `dreno` já é booleano livre, mesmo caso de outras normas), 4.3 (porta
full/regular/reduced — `tipo_passagem` só tem Plena/Reduzida, sem "regular", e a norma não
restringe por classe/diâmetro, só oferece a opção ao comprador), 4.4 continuidade elétrica
em si (resistência <=10 ohms — sem campo de resistência, e é opcional), 4.5 (operação:
alavanca/volante, torque, sentido de fechamento, trava — sem campo correspondente;
4.5.10 lockable device é opcional), 4.6-4.11 (glândula, esfera oca, haste, furo de flange,
parafuso de casco/glândula — geometria construtiva, sem campo dimensional), 5 (materiais
de casco/trim/plaqueta/parafuso/vedação — já coberto por `MATERIAIS_POR_TIPO`, sem
mapeamento 1:1; 5.4 tem escape hatch de compra — "unless another bolt material is
specified" — sugestão, não trava, mesmo padrão da ISO 10434 6.1), 6-9 (inspeção/ensaio/
marcação/embalagem/peças sobressalentes — processo de fabricação, não especificação).

## NBR 14788 (Objetivo/Secoes 1, 5, 6) — Esfera

Norma em `normas/Normas feitas/001_ABNT NBR 14788 ...md` (pymupdf4llm, não escaneado —
texto confiável). *Válvulas de esfera - Requisitos*: baseada na ISO 7121:1986 e na
API 6D:1994; só a Esfera oferece a norma (`NORMA_ESFERA`). Escopo do Objetivo (Seção 1):

```
norma = NBR 14788 (Esfera) →
  1: "extremidades roscadas, flangeadas ou soldadas ... diâmetros nominais DN 10 a
    DN 500, nas pressões nominais ISO PN 10 a ISO PN 100, como definido nas seções
    5 e 6" →
    tipo_extremidade só Flange, Butt-Welding ou Rosca — "soldada" aqui é solda de
      topo (8.1.3.1 cita a ASME/ANSI B16.25, "Buttwelding ends", pro encaixe de solda;
      a Tabela 7 do documento se chama "extremidades de solda de topo"); a norma não
      tem Socket-Welding em lugar nenhum do texto (diferente da ISO 17292/BS ISO 7121/
      API 608, que o cobrem) — por isso também não cobre Niple/Wafer/Lug/Gray Loc Hub
    classe (Seções 5/6, "ISO PN 10 a ISO PN 100") só PN 10/16/20/25/40/50/100 — a
      norma usa exclusivamente a série ISO PN como designação de pressão, sem Class
      ASME (diferente da BS ISO 7121/ISO 17292, que cobrem as duas séries)
    diâmetro (Seção 5, DN 10-500): teto NPS 20" (DN 500); DN 10 não tem equivalente em
      NPS no modelo (o piso do modelo já é 1/2"/DN 15), então só o teto precisa de
      validação
    PN 20 só em Rosca: as Tabelas 6 e 7 (dimensão face a face) agrupam as colunas de
      pressão em "10 e 16" / "25 a 50" / "100" — PN 20 não tem coluna em nenhuma das
      duas (confirmado pela contagem de valores por linha, 5 colunas batendo com os
      3 grupos, sem espaço pra um 4º). Como 8.1.3.1 torna a dimensão face a face
      OBRIGATÓRIA pra Flange/Butt-Welding (só Rosca é isenta), PN 20 fica sem
      dimensão válida nessas duas extremidades — só sobra Rosca
```

8.6 (antiestático, "quando especificado") e 8.1.3.6 (dreno DN≥50, "quando especificado
pelo cliente") são opcionais — não travam, mesmo caso da BS ISO 7121/API 608 (diferente
da ISO 17292, onde o antiestático é mandatório).

Fica logo após o bloco da API 608 e antes da ISO 15761 (mesma posição de prioridade das
outras genéricas-por-norma — específica de tipo, antes da genérica-pra-qualquer-tipo
B16.34). Espelho JS: `aplicarRegraNBR14788` (padrão `_bloquearOptsPorNorma`, registrada
em `aplicarRegrasNorma` e na lista de bypass-de-edição). Coberta por `Nbr14788EscopoTest`.

**Fora de alcance do modelo**: 7 (relação pressão/temperatura — depende de temperatura
de processo, sem campo), 8.1.1-8.1.3 (espessura de parede do corpo — Tabelas 1/2/3,
dimensão face-a-face — Tabelas 6/7, dreno roscado por DN — Tabela 5 — geometria/processo
construtivo, sem campo dimensional; 8.1.1.3 proteção contra excesso de pressão na
cavidade é "quando solicitado pelo cliente", opcional, sem campo dedicado), 8.2 (esfera
de passagem cilíndrica — sem campo de construção da esfera, `tipo_passagem` só tem
Plena/Reduzida), 8.3 (haste antiexpulsão — requisito de projeto sem campo), 8.4 (sedes
substituíveis — sem campo), 8.5 (rosca de parafuso métrica/polegada — sem campo de
bitola/rosca), 9 (operação: sentido de fechamento horário "a menos que especificado",
indicador de posição, dispositivos de parada — sem campo correspondente), 10.2-10.4
(revestimento de esfera/haste/sede, material de sede/juntas/gaxetas — "a critério do
fabricante, a menos que especificado", já coberto por `MATERIAIS_POR_TIPO` sem
mapeamento 1:1), 10.1/Tabela 8 (material do corpo por PN — já coberto por
`MATERIAIS_POR_TIPO`, sem mapeamento 1:1 pras ligas de bronze/latão da tabela, que nem
existem como opção no modelo), 11 (ensaio de pressão conforme NBR ISO 5208 — processo de
fabricação), 12 (marcação de corpo/plaqueta), 13 (preparo para expedição).

## API 607 (Secao 1) — norma de metodo de ensaio, trava e' de escopo por tipo

Norma em `normas/Normas feitas/032_API 607_2016 ...md` (pymupdf4llm, nao escaneado — texto
confiavel). *Fire Test for Quarter-turn Valves and Valves Equipped with Nonmetallic Seats*:
e' um metodo de ensaio de fogo (procedimento, aparato, temperatura, vazao de vazamento,
qualificacao de outros tamanhos/classes pelo mesmo ensaio), **nao uma norma de construcao**
como a B16.34 — nao ha tabela de rating pressao-temperatura nem restricao dimensional de
projeto. Varredura completa da Secao 1 a` Bibliografia: nenhuma trava de diametro/classe/
extremidade aterrissa em campo existente (mesmo veredito ja registrado p/ ISO 10497, mesma
categoria de norma) — a unica trava real e' de **escopo por tipo de valvula** (abaixo).

O que ja existia no codigo (`_ESF_FB_USO`, `_ESF_ROSCA_USO_800`, `_ESF_SW_USO_800`/`_1500`,
`_USO_GERAL_FIRE_TEST`, views.py:2059-2141) trata "API 607" como **valor aceito em uso_geral
junto de ISO 10497/ISO 17292/ASME B16.34** — essa restricao vem das tabelas da NBR 15827
(celulas que citam "ISO 17292/ISO 10497/API 607" como equivalentes de teste a fogo), nao do
proprio texto da API 607. Isso continua certo e nao mudou.

**Escopo por tipo (Secao 1)**: a norma cobre valvulas **quarter-turn** (Esfera/Borboleta) OU
com **sede nao-metalica**. Gaveta/Globo/Globo Controle nao sao quarter-turn e nao tem campo
de sede/inserto nao-metalico no modelo (`MATERIAIS_SEDE` delas e' so AISI/STELLITE/MONEL;
`INSERTO_SEDE` so existe pra Esfera/Retencao) — ou seja, e' impossivel montar uma Gaveta/
Globo/GC que realmente caia no escopo da API 607. Antes `uso_geral = API 607` continuava
liberado pra esses tipos via `USO_GERAL_COM_NA`; removido (`models.py`, `USO_GERAL_COM_NA`).
`norma` (Norma de Construcao) ja so oferecia "API 607" em `NORMA_ESFERA` — sem mudanca ali.
Enforcement e' so por lista de opcoes (`opcoes_por_tipo` -> `USO_GERAL_POR_TIPO`), o mesmo
padrao usado pra escopar `norma` por tipo em todo o resto do codigo — nao ha (e nao precisa
de) check generico em `_validar_regras_valvula`, pois esse campo nunca teve um. Coberta por
`Api607UsoGeralEscopoTest`.

**Fora de alcance do modelo**: 4.1-4.2 (montagem/direcao do ensaio, valvula de alivio de
pressao da cavidade), 5 inteiro (metodo de ensaio: aparato, calorimetro, combustivel,
procedimento passo a passo), 6 (performance: taxas de vazamento maximas por DN — Tabela 1,
operabilidade pos-ensaio), 6.7 (conteudo do relatorio de ensaio), 7 (qualificacao de outros
tamanhos/classes/materiais pelo mesmo ensaio — Tabelas 2/3/4, sobre cobertura de teste, nao
sobre limite de projeto). Nenhum tem campo correspondente na Valvula.

## API 600 (Secao 1) — Gaveta

Norma em `normas/Normas feitas/030_API 600_2015 ...md` (pymupdf4llm, nao escaneado — texto
confiavel, mas com ruido OCR-like em blocos `--\`,\`,,,,...---\`` que sao so marca d'agua de
digitalizacao, nao conteudo). *Steel Gate Valves—Flanged and Butt-welding Ends, Bolted
Bonnets*: serie heavy-duty de gaveta com castelo aparafusado pra refinaria; so' a Gaveta
oferece a norma (`NORMA_GAVETA`). Escopo da Secao 1 ("This standard sets forth the
requirements for the following gate valve features: bolted bonnet, ... flanged or
butt-welding ends"):

```
norma = API 600 (Gaveta) →
  juncao_corpo_castelo forcado p/ APARAFUSADO, sem input manual ("bolted bonnet" e' a
    UNICA opcao dentro do escopo — nao "solda"/"rosca", que ficam com API 602/ISO 15761
    pra bonnet integral em tamanhos/classes menores). Por eliminacao ter so' 1 opcao
    valida, e' regra automatica (forca e sobrescreve), nao validacao (nao rejeita) —
    mesmo padrao ja usado pra Retencao (sempre Aparafusado)
  tipo_extremidade so' Flange (FACE PLANA/RF/RTJ) ou Butt-Welding (qualquer schedule) —
    a norma nao cobre Socket-Welding/Rosca/Niple/Wafer/Lug/Gray Loc Hub
  classe em {150, 300, 600, 900, 1500, 2500} — sem 800 nem PN (mesma designacao da
    ASME B16.34, citada em 4.1 pras tabelas P-T)
  diametro em DN 25-1050 (NPS 1-42), com buraco: nao cobre NPS 22 (a Tabela 1/5 pula de
    20" pra 24"), nem abaixo de 1" (sem 1/2"/3/4"), nem acima de 42"
  vedacao (junta) != CASTELO SOLDADO (5.5.11 cobre pressure-seal bonnet como opcao dentro
    do escopo, mas "Castelo Soldado" e' bonnet SOLDADO — views.py:2966 traduz p/ "Welded
    Bonnet" — contradiz o bonnet aparafusado)
```

`juncao_corpo_castelo` e' forcado em `_aplicar_regras_automaticas` (roda mesmo com bypass de
validacao ativo — igual a regra da Retencao). As outras 4 (extremidade/classe/diametro/
vedacao) ficam em `_validar_regras_valvula`, logo antes da ASME B16.34 (mesma posicao de
prioridade da BS ISO 7121 — norma especifica de um tipo, roda antes da generica-pra-qualquer-
tipo). Espelho JS: `aplicarRegraApi600` (padrao `_bloquearOptsPorNorma`, registrada em
`aplicarRegrasNorma` e na lista de bypass-de-edicao). `_bloquearOptsPorNorma` agora
auto-seleciona quando sobra so' 1 option habilitada apos o bloqueio (generico, vale pra
qualquer regra de norma que usa o helper, nao so' API 600) — sem isso o usuario via
"Aparafusado" como unica opcao do select mas tinha que clicar nela manualmente. Coberta por
`Api600EscopoTest`. Corrigiu de quebra um teste existente
(`Iso14313EscopoTest.test_outra_norma_nao_restringe`) cuja premissa era "API 600 nao tem
regra propria" — trocado pra ISO 15761 (que continua sem regra).

A trava de vedacao le `vedacao_junta` com fallback pra `vedacao_corpo_tampa` (dado antigo)
— o frontend sempre manda o valor em `vedacao_junta` (index.html:5681/5804/6063).

**Bug corrigido (2026-07-16)**: `_validar_vedacao_nbr_classe` (views.py:54, a trava de
vedacao por classe da NBR 15827 pra Gaveta/Retencao) lia SO `vedacao_corpo_tampa` — como o
frontend nunca preenche esse campo (so' `vedacao_junta`), a trava nunca disparava via API
real (confirmado com teste real via `valvula_criar`: payload com `vedacao_junta` passava
200 mesmo com vedacao invalida pra classe; com `vedacao_corpo_tampa` dava 400 certo). Agora
le `ved.get("vedacao_junta") or ved.get("vedacao_corpo_tampa")`, mesmo padrao das outras
leituras (views.py:2342, 2434). Coberta por `VedacaoNbrClasseRuleTest`.

**Fora de alcance do modelo** (sem campo correspondente na Valvula): 4.2-4.5 (restricoes de
temperatura/pressao concorrente, cavidade que aprisiona liquido — dependem de temperatura de
processo), 5.1-5.2 (espessura minima de parede corpo/castelo por DN/classe — Tabela 1, sem
campo de espessura), 5.3.3 (diametro minimo de sede — Tabela 3, redundante com o proprio
diametro da valvula), 5.5.2-5.5.6 (TIPO de junta corpo/castelo — flat face/raised face/
tongue-groove/spigot-recess/ring joint — e' "bonnet-to-body joint", diferente de
`tipo_extremidade` (extremidade de conexao a tubulacao) e de `vedacao_junta` (so' pega o caso
Castelo Soldado x aparafusado, nao o tipo de junta em si); sem campo dedicado), 5.5.8 (bitola
minima do parafuso do castelo por DN — sem campo de bitola, so' material via
`MATERIAIS_PARAFUSOS`), 5.6-5.9 (geometria de gaveta/haste/
gaxeta — wear travel, diametro de haste, largura de gaxeta — Tabelas 4-6, sem campo
dimensional), 5.8.14 (mancal de esfera/rolete na porca da haste p/ DN>=150 + classe>=600 —
sem campo), 6 (materiais — Tabela 7/8/9, ja' coberto por `MATERIAIS_POR_TIPO`/trim, sem
mapeamento 1:1 pros "Trim Numbers" da norma), 7-9 (inspecao/teste/marcacao/embarque —
processo de fabricacao, nao especificacao). 5.3.2.1 (extremidade Butt-Welding em DN<=50/
NPS<=2 deve tambem atender API 602) e' cross-reference de detalhe construtivo, nao troca de
norma — nao vira trava de "norma deve ser API 602" (API 600 continua sendo a norma
selecionada; so' antecipa que outro documento tambem se aplica).

## ISO 10434 (Secao 1) — Gaveta

Norma em `normas/Normas feitas/006_BS EN_ISO_10434_2004 ...md` (pymupdf4llm, nao escaneado —
texto confiavel, com ruido de OCR tipico de layout de tabela BSI, mas prosa legivel).
*Bolted Bonnet Steel Gate Valves*: e' a versao ISO/EN da API 600 — a propria Introducao diz
que estabelece requisitos que "parallel those given in American Petroleum Institute API
Standard 600" — mesmo escopo de caracteristicas definidoras (bolted bonnet, OS&Y, rising
stem, wedge/parallel seating, metallic seating, flanged/butt-welding ends) e mesma designacao
de classe, mas **faixa de diametro menor** (DN 25-600, NPS 1-24, contra NPS 1-42 da API 600)
e **sem opcao de bonnet pressure-seal** (a API 600 tem 5.5.11 permitindo-a como alternativa;
a ISO 10434 nao tem clausula equivalente — 5.5.1 restringe o bonnet-to-body joint a "flange
and gasket type", sem excecao). So' a Gaveta oferece a norma (`NORMA_GAVETA`).

```
norma = ISO 10434 (Gaveta) →
  juncao_corpo_castelo forcado p/ APARAFUSADO, sem input manual (mesma regra automatica
    da API 600 — "bolted bonnet" e' a UNICA opcao dentro do escopo)
  tipo_extremidade so' Flange (FACE PLANA/RF/RTJ) ou Butt-Welding (qualquer schedule) —
    a norma nao cobre Socket-Welding/Rosca/Niple/Wafer/Lug/Gray Loc Hub
  classe em {150, 300, 600, 900, 1500, 2500} — sem 800 nem PN
  diametro em DN 25-600 (NPS 1-24), com o mesmo buraco no NPS 22 da API 600 (a lista pula
    de 20" pra 24"), nem abaixo de 1" (sem 1/2"/3/4"), nem acima de 24" (teto menor que
    a API 600, que vai ate' 42")
  vedacao (junta) != CASTELO SOLDADO e != PRESSURE SEAL (diferente da API 600, aqui NENHUMA
    das duas cabe no escopo — so' Junta Espiralada ou RTJ (FJA), os dois unicos tipos de
    "flange and gasket" que a norma cobre)
```

`juncao_corpo_castelo` e' forcado em `_aplicar_regras_automaticas` (mesma condicao ja usada
pra API 600, agora com `data.get("norma") in ("API 600", "ISO 10434")`). As outras 4 ficam em
`_validar_regras_valvula`, logo apos o bloco da API 600 (mesma posicao de prioridade — norma
especifica de tipo, antes da generica-pra-qualquer-tipo B16.34). Espelho JS:
`aplicarRegraIso10434` (padrao `_bloquearOptsPorNorma`, registrada em `aplicarRegrasNorma` e
na lista de bypass-de-edicao). Coberta por `Iso10434EscopoTest`.

**Fora de alcance do modelo**: mesma lista da API 600 (espessura de parede/castelo, diametro
minimo de sede, tipo de junta corpo/castelo — flat face/tongue-groove/etc., bitola de
parafuso, geometria de gaveta/haste/gaxeta, mancal de haste, tabelas de trim/material,
inspecao/marcacao/embarque). Adicional: 6.1 (bolting corpo-castelo "shall be ASTM A193-B7...
unless otherwise specified by the purchaser" — tem escape hatch explicito de compra, mesmo
padrao da Tabela 7 NBR de redutor — sugestao, nao trava), 5.12.1 (conexoes auxiliares "not
permitted, except when specified" — default, purchaser pode pedir `dreno`/`vent`/
`alivio_externo` = true), 5.12.5-5.12.8/Tabelas 9-12 (dimensionamento de conexao auxiliar por
DN — campos sao booleanos, sem sub-campo de tamanho).

## ISO 15761 (Cláusula 1) — Gaveta, Globo, Retenção

Norma em `normas/Normas feitas/032_ISO 15761_2002 ...md` (pymupdf4llm, não escaneado — texto
confiável). *Steel gate, globe and check valves for sizes DN 100 and smaller, for the
petroleum and natural gas industries*: a própria Introdução diz que o "general construction
parallels that specified by ... API 602 ... and BS 5352" — é a versão ISO da API 602, série
compacta forjada. Gaveta/Globo/Retenção oferecem a norma (`NORMA_GAVETA`/`NORMA_GLOBO`/
`NORMA_RETENCAO`). Escopo da Cláusula 1:

```
norma = ISO 15761 →
  classe em {150, 300, 600, 800, 1500} — sem 900 (nota da 4.1: "Class 900 is not
    specifically referenced in this International Standard because this designation is
    seldom used for the compact valves described herein"), sem 2500/4500 nem PN
  extremidade só Flange/Butt-Welding/Socket-Welding/Rosca — Niple conta como SW
    (NBR C.1.4.1); Wafer/Lug/Gray Loc Hub não existem na norma
  "socket welding or threaded ends, in sizes 8≤DN≤65 and pressure designations of
    Class 800 and Class 1500" → SW/Rosca só em classe 800/1500 (não 150/300/600),
    diâmetro até 2 1/2"
  "flanged or butt-welding ends, in sizes 15≤DN≤100 and 150≤Class≤1500, excluding
    flanged end Class 800" → Flange/Butt-Welding até 4"; Flange não cobre classe 800
    (só Butt-Welding cobre 800 nessa faixa — igual ao caso da API 602, 5.4.4.1)
  5.5.1: bonnet fixado por 1 de 4 métodos (bolting/welding/threaded com seal weld/
    threaded union nut) — junção Roscado (union nut) só até classe 800 ("threaded
    union nut, provided it is of Class ⩽ 800"); vedação não pode ser Pressure Seal
    (não é um dos 4 métodos — texto idêntico ao 5.5.1 da API 602)
```

Fica logo após o bloco da BS ISO 7121 e antes da API 600 (mesma posição de prioridade das
outras genéricas-por-norma — específica de tipo, antes da genérica-pra-qualquer-tipo
B16.34). Espelho JS: `aplicarRegraISO15761` (padrão `_bloquearOptsPorNorma`, registrada em
`aplicarRegrasNorma` e na lista de bypass-de-edição). Coberta por `Iso15761EscopoTest`.

**Fora de alcance do modelo**: 4.1.2 (rating interpolado de Class 800 — depende de
temperatura de processo, sem campo), 5.2-5.3 (passageway mínimo/espessura de parede —
Tabelas 1-3, sem campo dimensional), 5.4.2-5.4.6 (dimensões de socket/rosca/face-a-face —
Tabelas 4-7, sem campo), 5.5-5.11 (bonnet/obturador/haste/gaxeta/volante — geometria
construtiva, sem campo dimensional; `juncao_corpo_castelo` só cobre o método de fixação, não
o detalhe de bolting/rosca de 5.5.5-5.5.8), 6 (materiais de trim — Tabela 11/12/13, já
coberto por `MATERIAIS_POR_TIPO`, sem mapeamento 1:1 pros "Combination Numbers" da norma),
7 (marcação de corpo/plaqueta), 8 (ensaios), 9 (preparo pra despacho), Anexo A (corpo de
extensão pra "extended body valve" — sem campo de construção equivalente), Anexos B/C
(bellows stem seal — sem campo), Anexo D (identificação de partes, informativo), Anexo E
(lista do que o comprador deve especificar, informativo).

## BS 1868 (Cláusulas 1, 4, 6, 9.3) — Retenção

Norma em `normas/Normas feitas/001_BS 1868_1975+A1_1990 ...md` (pymupdf4llm, não
escaneado — texto confiável). *Steel check valves (flanged and butt-welding ends) for
the petroleum, petrochemical and allied industries*: só a Retenção oferece a norma
(`NORMA_RETENCAO`). Escopo da Cláusula 1 ("cast or forged steel check valves with
flanged or butt-welding ends"):

```
norma = BS 1868 (Retenção) →
  tipo_extremidade só Flange ou Butt-Welding — a norma não cobre Socket-Welding/
    Rosca/Niple/Wafer/Lug/Gray Loc Hub
  classe (Cláusula 4, "Classes 150, 300, 400, 600, 900, 1 500 and 2 500") → sem 800
    (designação de forjado, fora do escopo cast/BW desta série) nem PN. Class 400 foi
    adicionada ao CLASSES_RETENCAO_GLOBO do modelo especificamente pra essa norma — API 6D
    e ASME B16.34 (as outras normas de Retenção/Globo que usam essa mesma lista) foram
    atualizadas pra bloquear 400 explicitamente, já que nenhuma das duas cobre essa
    designação (só a BS 1868 usa "Class 400")
  diâmetro (Cláusula 6) em DN 15-600 (NPS 1/2"-24"), com buraco no NPS 22" (a lista
    pula de 20" pra 24" — mesmo buraco já visto na API 600/ISO 10434)
  9.3 ("the body-to-cover connection shall be male-and-female, tongue-and-groove, or
    ring-joint type") → as três são junta parafusada (9.5/14 exigem stud bolts); sem
    bonnet soldado nem pressure-seal no escopo → vedação (junta) não pode ser Castelo
    Soldado nem Pressure Seal (mesma leitura já usada na ISO 10434)
```

Fica logo após o bloco da API 602 e antes da ASME B16.34 (mesma posição de prioridade
das outras genéricas-por-norma — específica de tipo, antes da genérica-pra-qualquer-tipo
B16.34). Espelho JS: `aplicarRegraBS1868` (padrão `_bloquearOptsPorNorma`, registrada em
`aplicarRegrasNorma` e na lista de bypass-de-edição). Coberta por `Bs1868EscopoTest`.

**Fora de alcance do modelo**: 5-15 (projeto construtivo de corpo/tampa/disco/pistão/
esfera/guias/dobradiça — geometria, sem campo dimensional; Tabela 1 é espessura/diâmetro
mínimo por DN/classe), 8.10 (tomada de dreno obrigatória >=50mm — `dreno` já é booleano
livre, mesmo caso do 6.3.6 da B16.34/7.9 da ISO 14313), 9.3 tipo de face (male-and-female/
tongue-and-groove — geometria da junta corpo/tampa, diferente de `vedacao_junta`, que só
pega o caso Castelo Soldado/Pressure Seal x parafusado), 14 (bitola de parafuso do
corpo/tampa — sem campo de bitola), 16-27 (materiais de casco/sede/trim/dobradiça/
parafuso — Tabela 2, já coberto por `MATERIAIS_POR_TIPO`, sem mapeamento 1:1 pros
"nominal trim symbols" da norma; 23 tem escape hatch de compra — "unless other bolting
material is specified in the order" — sugestão, não trava, mesmo padrão da Tabela 7 NBR),
28-36 (marcação de corpo/plaqueta, ensaio de produção — processo de fabricação, não
especificação), 37-39 (embarque), Apêndice A (aplicação com flanges BS 4504-1 — norma
alternativa de flange, não campo do modelo).

## API 594 (Seção 1) — Retenção

Norma em `normas/Normas feitas/022_API 594_2010 ...md` (OCR RapidOCR — tabelas do corpo do
texto saíram achatadas, mas as tabelas de dimensão foram reconferidas por visão e anexadas
no fim do arquivo, confiáveis; para qualquer outra dúvida, abrir o PDF original). *Check
Valves: Flanged, Lug, Wafer, and Butt-welding*: só a Retenção oferece a norma
(`NORMA_RETENCAO`). O próprio título já é o escopo de extremidade. A Seção 1 descreve dois
tipos construtivos sem campo que os distinga no modelo: **Type 'A'** (face-a-face curta:
wafer, lug ou duplo-flange) e **Type 'B'** (face-a-face longa: bolted cover, flange ou
butt-welding). Extremidade Flange serve aos dois tipos — sem campo pra saber qual, a trava
usa o teto mais permissivo (Type A, que é sempre >= Type B por classe); Butt-Welding só
existe no Type 'B', então usa sempre o teto do Type B:

```
norma = API 594 (Retenção) →
  tipo_extremidade só Flange, Lug, Wafer ou Butt-Welding — a norma não cobre
    Socket-Welding/Rosca/Niple/Gray Loc Hub
  classe (Seção 1): 150/300/600/900/1500/2500 — sem 800 (a norma nunca lista Class 800)
    nem PN. Classes 125/250 (ferro fundido/nodular, exclusivas do Type A) não existem no
    CLASSES_RETENCAO_GLOBO do modelo (mesmo buraco do Class 400 já visto na ISO 14313/
    BS 1873) — ficam fora da lista por falta de opção, não por regra
  diâmetro mínimo DN 50 (NPS 2) sempre — "Sizes: NPS 2, 2 1/2, 3, ..." não desce disso
    (DN 90/NPS 3 1/2 e DN 125/NPS 5 são "non-preferred... usage is discouraged" — "should",
    não "shall not"; e nem existem no DIAMETROS_RETENCAO do modelo — não vira trava)
  teto por classe/extremidade (Seção 1, ranges a)-e' do Type A e a)-b) do Type B):
    150/300  → NPS 48 (Wafer/Lug/Flange, Type A) ou NPS 24 (Butt-Welding, Type B).
      DIAMETROS_RETENCAO estendido até 48" (2026-07-17) pra bater com esse teto — antes
      disso a opção nem existia no modelo (parava em 42")
    600      → NPS 42 (Wafer/Lug/Flange, Type A) ou NPS 24 (Butt-Welding, Type B) — 42"
      aqui é o próprio teto do DIAMETROS_RETENCAO
    900/1500 → NPS 24 pra qualquer extremidade (Type A e B coincidem nessa faixa)
    2500     → NPS 12 pra qualquer extremidade (Type A e B coincidem)
```

`juncao_corpo_castelo` já vem forçado p/ APARAFUSADO por `_aplicar_regras_automaticas`
independente da norma (regra pré-existente pra qualquer Retenção — 5.1.14/5.1.15 do Type
'B' só descrevem junta parafusada mesmo, sem opção soldada/roscada). 5.1.14/6.3 (Type
'B'): body-to-cover joint é flat face (só Classe 150)/raised face/tongue-and-groove/
spigot-and-recess/ring-joint — nenhum soldado nem pressure-seal → vedação (junta) não
pode ser Castelo Soldado nem Pressure Seal, mesma leitura já usada na BS 1868/ISO 10434.

Fica logo após o bloco da BS 1868 e antes da ASME B16.34 (mesma posição de prioridade das
outras genéricas-por-norma — específica de tipo, antes da genérica-pra-qualquer-tipo
B16.34). Espelho JS: `aplicarRegraApi594` (padrão `_bloquearOptsPorNorma`, registrada em
`aplicarRegrasNorma` e na lista de bypass-de-edição). Coberta por `Api594EscopoTest`.

**Fora de alcance do modelo**: 4.2 (restrição de temperatura — depende de temperatura de
processo, sem campo), 5.1.1-5.1.16 (espessura de parede por classe/DN — Tabelas 1-2;
dimensão face-a-face — Tabelas 3-4; solda de flange, bolt patterns, ring-joint grooves,
acabamento de face, conexões auxiliares, tapped test opening, lifting eye bolt, furos de
flange — geometria/processo construtivo, sem campo dimensional equivalente), 5.2-5.3
(construção de disco/placa single/dual-plate, superfície de vedação — sem campo, o modelo
não distingue tipo de disco de retenção), 5.4 (bitola/rosca de parafuso externo — sem
campo de bitola), 5.5-5.6 (indicador de fluxo, gasket surface interruption — sem campo),
6.1-6.9 (materiais de corpo/disco/gaxeta-de-cover/trim/partes molhadas/mola/plugue/
plaqueta — Tabela 5, já coberto por `MATERIAIS_POR_TIPO`, sem mapeamento 1:1 pros
"nominal trim numbers"; 6.7 tem escape hatch de temperatura de projeto pra material de
mola — sem campo de temperatura de projeto), 7 (inspeção/ensaio — API 598, processo de
fabricação), 8 (marcação), 9-10 (embarque, peças sobressalentes), Anexo A (informação a
ser especificada pelo comprador — lista de opções que o comprador *pode* pedir, não
restrição em si).

## BS 1873 (Cláusulas 1, 4, 6, 9.3, Apêndice A) — Globo

Norma em `normas/Normas feitas/002_BS 1873_1975 ...md` (pymupdf4llm, não escaneado —
texto confiável). *Steel globe and globe stop and check valves (flanged and butt-welding
ends) for the petroleum, petrochemical and allied industries*: só o Globo oferece a norma
(`NORMA_GLOBO`). "Globe stop and check" é uma variante de check valve com corpo de globo
— não tem representação separada no modelo (a Retenção usa outras normas), então a norma
inteira aterrissa em Globo. Escopo da Cláusula 1 ("outside screw and yoke globe ... valves
... with flanged or butt-welding ends"):

```
norma = BS 1873 (Globo) →
  tipo_extremidade só Flange ou Butt-Welding — a norma não cobre Socket-Welding/
    Rosca/Niple/Wafer/Lug/Gray Loc Hub
  classe (Cláusula 4, "Class 150, Class 300, Class 400, Class 600, Class 900,
    Class 1500 and Class 2500") → sem 800 (a norma nunca lista Class 800) nem PN.
    Class 400 não existe no CLASSES_RETENCAO_GLOBO do modelo (mesmo buraco já
    registrado na ISO 14313/BS 1868) — fica fora da lista por falta de opção
  diâmetro por classe (Apêndice A, Tabelas 3-9 — cada classe tem faixa própria de DN,
    diferente das outras normas que usam 1 teto único):
      150   → 1/2"-16" (Tabela 3, DN 15-400)
      300   → 1/2"-12" (Tabela 4, DN 15-300)
      600   → 1/2"-12" (Tabela 6, DN 15-300)
      1500  → 1/2"-14" (Tabela 8, DN 15-350)
      2500  → 1/2"-12" (Tabela 9, DN 15-300)
      900   → 3"-14"   (Tabela 7, DN 80-350 — única com PISO, a tabela não desce de
                        NPS 3; nenhuma outra classe tem tamanho mínimo abaixo do 1/2"
                        que já é o piso do modelo)
  9.3 ("the body to bonnet connection shall be flanged", com facing male-and-female/
    tongue-and-groove/ring-joint, ou flat face só na Classe 150) → bonnet sempre
    flangeado aparafusado, sem opção soldada/roscada/union-nut no escopo — força
    juncao_corpo_castelo = APARAFUSADO (mesmo padrão API 600/ISO 10434/BS 1868); e
    nenhum dos facings é bonnet soldado nem pressure-seal → vedação (junta) não pode
    ser Castelo Soldado nem Pressure Seal (mesma leitura da ISO 10434/BS 1868)
```

`juncao_corpo_castelo` é forçado em `_aplicar_regras_automaticas` (mesma condição de tipo
+ norma já usada para API 600/ISO 10434, agora com `tipo_valvula == "GLOBO" and
data.get("norma") == "BS 1873"`). As outras 4 checagens ficam em `_validar_regras_valvula`,
logo após o bloco da ISO 15761 e antes da API 600 (mesma posição de prioridade — norma
específica de tipo, antes da genérica-pra-qualquer-tipo B16.34). Espelho JS:
`aplicarRegraBS1873` (padrão `_bloquearOptsPorNorma`, registrada em `aplicarRegrasNorma` e
na lista de bypass-de-edição). Coberta por `Bs1873EscopoTest`.

**Nota sobre os tamanhos NPS 1 1/4" e NPS 2 1/2"**: a Cláusula 6 e as Tabelas 3-9 marcam
esses dois tamanhos com nota "retained only for the purpose of replacing existing valves...
avoided for new construction" — linguagem de recomendação ("should"), não proibição
("shall not"). Mesmo padrão já registrado na Tabela 7 NBR (sugestão de redutor) e no
5.5.1/6.1 da ISO 10434 (bolting "unless otherwise specified") — **não vira trava**, os dois
tamanhos continuam liberados em todas as classes que os listam.

**Fora de alcance do modelo**: 7 (informação a ser fornecida pelo comprador — lista de
opções que o comprador *pode* especificar, não restrição), 8.1-8.10 (projeto construtivo
de corpo/sede/disco — Tabela 1 é espessura de parede por DN/classe, sem campo dimensional;
8.9 é tomada de dreno, `dreno` já é booleano livre, mesmo caso do 6.3.6 da B16.34/8.10 da
BS 1868), 9.1/9.2/9.4-9.7 (espessura de castelo, geometria de flange bonnet, back seat —
sem campo), 9.3 tipo de facing em si (male-and-female/tongue-and-groove/ring-joint/flat
face — geometria da junta corpo/bonnet, diferente de `vedacao_junta`, que só pega o caso
Castelo Soldado/Pressure Seal x parafusado), 10-14 (disco/haste/gaxeta/caixa de gaxeta —
geometria, Tabela 1 de bore de gaxeta), 15 (bitola de parafuso do corpo/bonnet — sem campo
de bitola), 16 (operação: direct handwheel/chainwheel/gear/actuator — "unless otherwise
specified", já coberto por `tipo_acionamento` sem granularidade de chainwheel), 17 (bypass
— "shall not be provided unless specified", opcional, sem campo dedicado), 18 (soft seal
rings — construção do disco, sem campo), 19-37 (materiais de casco/sede/gaxeta/parafuso —
Tabela 2, já coberto por `MATERIAIS_POR_TIPO`, sem mapeamento 1:1 pros "nominal trim
symbols"; 33.1 tem escape hatch de compra — sugestão, não trava, mesmo padrão da Tabela 7
NBR), 38-44 (marcação), 45 (ensaio de produção — processo de fabricação), 46-48
(embarque), Apêndice B (aplicação com flanges BS 4504 — norma alternativa de flange, não
campo do modelo).

## API 623 (Seção 1) — Globo

Norma em `normas/Normas feitas/044_API 623_2013 ...md` (OCR RapidOCR — as tabelas de
espessura de parede saíram bem degradadas no corpo do texto, mas foram reconferidas por
visão e anexadas no fim do arquivo, confiáveis; para qualquer outra dúvida, abrir o PDF
original). *Steel Globe Valves—Flanged and Butt-Welding Ends, Bolted Bonnets*: série
heavy-duty de globo com castelo aparafusado pra refinaria (mesma categoria da API 600 pra
Gaveta); só o Globo oferece a norma (`NORMA_GLOBO`). Escopo da Seção 1 ("This standard
sets forth the requirements for the following globe valve features: bolted bonnet, ...
flanged or butt-welding ends"):

```
norma = API 623 (Globo) →
  juncao_corpo_castelo forçado p/ APARAFUSADO, sem input manual ("bolted bonnet" é
    característica definidora do escopo — mesmo padrão API 600/ISO 10434/BS 1873)
  tipo_extremidade só Flange ou Butt-Welding — a norma não cobre Socket-Welding/Rosca/
    Niple/Wafer/Lug/Gray Loc Hub (5.3.3/5.3.4 citam SW/rosca como referência normativa
    genérica, mas o Escopo da Seção 1 só oferece "flanged or butt-welding ends")
  classe em {150, 300, 600, 900, 1500, 2500} — sem 800 nem PN (mesma designação da
    ASME B16.34; Tabelas 1/2/4/5 usam essas 6 classes)
  diâmetro: "NPS: 2, 2 1/2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24; DN 50-600" — sem
    1/2"-1 1/2" (a norma começa em NPS 2, diferente da API 600/ISO 10434, que começam
    em NPS 1), sem 22" (mesmo buraco da API 600/ISO 10434/BS 1868) nem acima de 24"
  5.5.1/5.5.2 ("the bonnet-to-body joint shall be a flange and gasket type", com facing
    raised face/tongue-and-groove/spigot-and-recess/ring-joint) → nenhum dos facings é
    bonnet soldado nem pressure-seal → vedação (junta) não pode ser Castelo Soldado nem
    Pressure Seal (mesma leitura da ISO 10434 — nenhuma das duas cabe no escopo)
  classe 2500 só até NPS 12: a Tabela 1 (espessura mínima de parede, mandatória por
    5.1 — "manufacture shall be as given in Table 1") não tem valor pra Classe 2500 em
    NPS 14-24 (célula "—" nas 5 colunas de NPS mais alto) — acima de NPS 12 a norma
    simplesmente não define espessura pra essa classe (mesmo padrão do buraco PN 20/
    face-a-face da NBR 14788, achado na mesma varredura)
```

`juncao_corpo_castelo` é forçado em `_aplicar_regras_automaticas` (mesma condição de tipo
+ norma já usada para BS 1873, agora com `data.get("norma") in ("BS 1873", "API 623")`).
As outras 3 checagens ficam em `_validar_regras_valvula`, logo após o bloco da BS 1873 e
antes da API 600 (mesma posição de prioridade — norma específica de tipo, antes da
genérica-pra-qualquer-tipo B16.34). Espelho JS: `aplicarRegraApi623` (padrão
`_bloquearOptsPorNorma`, registrada em `aplicarRegrasNorma` e na lista de
bypass-de-edição). Coberta por `Api623EscopoTest`.

**Fora de alcance do modelo**: 4 (relação pressão/temperatura — depende de temperatura de
processo, sem campo), 5.1-5.4 (espessura de parede corpo/castelo — Tabelas 1/2, tratamento
térmico de solda de flange — Tabela 3, dimensão face-a-face — ASME B16.10, diâmetro mínimo
de sede — Tabela 4 — geometria/processo construtivo, sem campo dimensional; 5.3.1.2 flange
integral vs. soldado é detalhe de fixação, não `tipo_extremidade`), 5.3.3/5.3.4 (Socket
Welding/Threaded Ends citados como referência normativa genérica, mas fora do Escopo da
Seção 1, que só lista flanged/butt-welding — por isso não abrem opção de extremidade),
5.4-5.9 (bonnet/disco/yoke/haste/gaxeta — geometria construtiva, Tabela 5 diâmetro mínimo
de haste, Tabela 6 largura de gaxeta — sem campo dimensional; 5.6.3 guia do disco por
classe ≥900 sem campo), 5.10 (bitola/rosca de parafuso — sem campo de bitola), 5.11
(operação: handwheel sentido anti-horário de abertura, chainwheel, gearbox — sem campo
correspondente; `tipo_acionamento` não distingue sentido de abertura), 5.12 (stop-check —
variante construtiva de disco livre, sem representação no modelo, mesmo caso do "globe
stop and check" da BS 1873), 5.13 (bypass/dreno — "shall be furnished only if specified",
`dreno`/`alivio_externo` já são booleanos livres, mesmo caso da ISO 10434/BS 1868), 6
(materiais de corpo/disco/parafuso/gaxeta/trim — Tabela 7/8/9, já coberto por
`MATERIAIS_POR_TIPO`, sem mapeamento 1:1 pros "Trim Numbers"; Anexo C tem tabela de
combinação corpo×parafuso, sugestão, não trava), 7-9 (inspeção/ensaio/marcação/expedição —
processo de fabricação, não especificação), Anexo A (informação a ser especificada pelo
comprador — lista de opções, não restrição).

## MSS SP-67 (Seção 1.3 + 3.1-3.3) — Borboleta

Norma em `normas/Normas em aberto/MSS SP-67.md` (Acrobat Capture 3.0, scan de 2002 — layout
de duas colunas reordenado, tabelas com aviso de conferência de dígitos contra a imagem;
para as tabelas de dimensão, abrir o PDF original). *Butterfly Valves*: cobre dimensão,
projeto, ensaio e marcação de válvulas borboleta flangeada, lug e wafer, alem de grooved e
shouldered end (essas duas últimas fora de alcance — sem opção em `face_a_face`/
`tipo_extremidade`); só a Borboleta oferece a norma (`NORMA_BORBOLETA`). Ao contrário da
API 609, não tem conceito de Categoria A/B nem exige disco Concêntrico — é genérica pra
qualquer configuração de disco dentro do escopo:

```
norma = MSS SP-67 (Borboleta) →
  diâmetro (1.3, "sizes 1½ NPS thru 72 NPS") em lista fechada, decisão de negócio
    (2026-07-21, não é leitura literal da 1.3, que cobre a faixa contínua): 1 1/2",
    2", 2 1/2", 3", 4", 5", 6", 8", 10", 12", 14", 16", 18", 20", 24", 30", 36", 42",
    48", 54", 60", 64", 66", 72" — 5"/64"/66"/72" não existem em DIAMETROS/
    DIAMETROS_POR_TIPO (o modelo não tem opção acima de 60" nem em 5"); injetados
    como <option> só quando a norma está ativa (função `_injetarDiametrosExtras`,
    índex.html), removidos ao trocar de norma — não entram no DIAMETROS global,
    então não ficam disponíveis pra Esfera/Gaveta/Globo nem Borboleta+outra norma
  classe 125/150/PMT — 3.1/3.2/3.3 (flanged/lug/wafer) só citam compatibilidade com
    flanges até Classe 150 (ASME B16.1 Cl 25/125, B16.5 Cl 150, B16.47 Cl 150 Série A,
    B16.24/B16.42 Cl 150, ou ANSI/AWWA C207) — nunca 300/600/900/1500/2500/800/PN. 4.3
    reforça: "flange ratings other than those listed ... are outside the scope". PMT
    cabe pelo teste de prova alternativo (4.1.1.3/4.1.3.3/4.1.4.3, "maximum allowable
    pressure determined using a proof test") — mesmo CWP do API 609 Categoria A
```

Fica no fim dos blocos de Borboleta em `_validar_regras_valvula`, DEPOIS das regras NBR
Bi/Tri-Excêntrica (que restringem `norma` a {API 609, ASME B16.34} por corpo — precisam
falar primeiro, senão a mensagem de classe da MSS SP-67 mascara a de norma esperada pelo
teste). Espelho JS: `aplicarRegraMssSp67` (padrão `_bloquearOptsPorNorma` p/ classe +
`_injetarDiametrosExtras`/`_bloquearOptsPorNorma` p/ diâmetro, registrada em
`aplicarRegrasNorma` e na lista de bypass-de-edição). Coberta por `MssSp67EscopoTest`
(atualizar o teste pra bater com a lista fechada, incluindo os 4 valores injetados).

**Fora de alcance do modelo**: 1.2/10.2 (Type I tight shut-off x Type II seat leakage —
sem campo de classe de estanqueidade), 3.4/3.5 (grooved/shouldered ends — sem opção em
`face_a_face`), 4.1 (espessura mínima de parede por equação/proof-test — Tabelas
implícitas, depende de pressão/diâmetro interno do corpo, sem campo dimensional),
4.1.5 (espessura reduzida entre furo de haste e parafuso — geometria construtiva), 4.2
(espessura de flange — sem campo), 4.4 (rosca de furo de flange — sem campo de bitola),
5 (folga disco-tubo — Tabela 1/Anexo A, depende de diâmetro interno de tubo adjacente,
não da válvula em si), 6 (trim — material a critério do fabricante "unless specified",
já coberto por `MATERIAIS_POR_TIPO` sem mapeamento 1:1), 7 (dimensão face-a-face —
Tabelas 2-4, geometria/OCR incerto, sem campo dimensional; nem diferencia diâmetro por
face_a_face como a API 609 faz, dado o OCR não confiável dessas tabelas), 8 (atuador —
"self locking", sem campo), 9 (informação de compra — lista de opções, não restrição),
11 (marcação de plaqueta — processo de fabricação).

## ASME B16.34 (2.1.1) — vale para qualquer tipo

Norma em `normas/009_ASME B16.34_2020 ...md`. O grosso dela sao as tabelas de rating
pressao-temperatura por grupo de material (2-1.1 a 2-3.19), que exigem **temperatura de
processo** — campo que a Valvula nao tem. So a **2.1.1** aterrissa nos campos existentes:

- **Designacao de classe**: a norma rateia por "Class" + numero (150, 300, 600, 900, 1500,
  2500, 4500). Entao `norma = ASME B16.34` -> classe nao pode ser **400** (designacao da
  BS 1868, que nao e' "Class" da B16.34; existe no modelo so' pra Retencao/Globo), **800**
  (designacao de forjado, API 602/ISO 15761), **PN** (designacao metrica), **125** (ferro
  fundido, ASME B16.1) nem **PMT** (CWP, Categoria A da API 609)
- **2.1.1 (b)**: "Class 4500 applies only to welding-end valves" -> classe 4500 exige
  extremidade Butt-Welding ou Socket-Welding
- **2.1.1 (d)**: "Threaded and socket welding-end valves larger than NPS 2 1/2 are beyond
  the scope" -> Rosca ou Socket-Welding -> diametro maximo 2 1/2". Butt-welding nao tem teto

Ficam **no fim de `_validar_regras_valvula`, de proposito**: valem para qualquer tipo de
valvula, entao as regras especificas (que sabem tipo/corpo/categoria) devem dar a mensagem
primeiro. Colocar no topo faz, por exemplo, Borboleta A536 + PMT + B16.34 responder "B16.34
nao aceita PMT" em vez do mais util "para esse corpo a norma deve ser API 609".

Espelhadas no frontend em `aplicarRegraB1634Classe` / `aplicarRegraB1634Classe4500` /
`aplicarRegraB1634RoscaSocket` (atalho `aplicarRegrasNorma`). Cobertas por `AsmeB1634EscopoTest`.

**Padrao obrigatorio no JS para regra de norma**: usar `_bloquearOptsPorNorma(sel, marca,
ativa, pred)` — cada regra marca (dataset) as options que ela bloqueou e, inativa, reverte
SO as suas. Regra que so retorna cedo deixa bloqueio pendurado ao trocar a norma (bug real:
diametro preso em 2 1/2"); regra que reabilita em bloco clobbera o bloqueio das outras.
O hook de `_aplicarPermitidosSelect` re-aplica as regras de norma apos QUALQUER chamada em
classe/diametro/tipo_extremidade (as listas das regras NBR reabilitavam 800/PN por fora —
era por isso que clone e NBR "perdiam" as travas da B16.34). API 6D so re-aplica quando
ativa: inativa ela reabilita tudo em bloco. `duplicarValvula` reafirma as travas no final.

### Classe 800: onde ela pode e nao pode aparecer

**Classe 800 e designacao de valvula forjada** (API 602 / ISO 15761). Nao existe na ASME
B16.34 (2.1.1 nao a lista) e nao existe flange classe 800 — a sequencia de flange e
150/300/600/900/1500/2500 (ASME B16.5). Nas Tabelas 1, 2 e 4 da NBR 15827, a classe 800
aparece **so na coluna "Encaixe para solda"**.

Isso ja rendeu dois bugs, ambos corrigidos:

1. **800 em flange/BW/wafer**: as regras liam "Classe 150 a 900" (Tabela 1) e "150 a 2500"
   (Tabelas 2 e 4) como se incluissem 800. `_RET_FB_CLASSES`, `_RET_WAFER_CLASSES`,
   `_GLOBO_FLANGE_CLASSES` e a condicao de flange da Gaveta tinham 800 — nao tem mais.
   A regra da Esfera (`_ESF_FB_CLASSES`) **sempre esteve certa** e serve de referencia.
2. **Achatamento de celula no socket-weld**: a celula "Classe 800 e 1500" das Tabelas 1 e 4
   lista as normas juntas ("ISO 15761 (API 602), ASME B16.34 e Anexo A") sem dizer qual vale
   para qual classe. As regras aceitavam qualquer uma das 3 para as 2 classes. Cruzando com
   a 2.1.1, ficou: **800 -> ISO 15761/API 602; 1500 -> as tres**
   (`_NORMAS_GAVETA_SW_800`/`_1500`, `_GLOBO_SW_NORMAS_800`/`_1500`). A Retencao ja estava
   correta — a Tabela 2 nao lista B16.34 nessa celula.

Coberto por `Classe800NaoEhDeFlangeTest`. Ao ler uma tabela da NBR com celula que cobre duas
classes, **nao achatar**: cruzar com a norma citada para ver o que cabe em cada uma.

### Retencao flangeada: passagem plena depende da norma

Terceiro caso do mesmo achatamento. A celula "Flange ou solda de topo" da Tabela 2 tem
**duas alternativas** de padrao construtivo:

- `BS 1868, ASME B16.34 e Anexo B` -> passagem livre
- `ISO 14313 (API 6D) e Anexo B` **(Passagem Plena)** -> passagem plena obrigatoria

`_RET_FB_NORMAS` juntava as 4 numa lista so, e nao havia **nenhuma** regra de
`tipo_passagem` no arquivo. Agora `_RET_FB_NORMAS_PLENA = {"ISO 14313", "API 6D"}` barra
REDUZIDA nessas duas. Coberto por `RetencaoPassagemPlenaTest`.

**Licao**: uma celula da NBR pode listar alternativas que nao sao equivalentes entre si —
o que esta entre parenteses ("Passagem Plena") pode valer so para uma delas.

---

### Fidelidade a NBR 15827 — o que e proposital

O texto da norma esta em `normas/002_ABNT NBR 15827_2014 ...md` (OCR do PDF; as tabelas
sairam degradadas — **para qualquer duvida, abrir o PDF original**). Pontos ja conferidos
contra a norma, para nao serem "corrigidos" por engano:

- **Tabela 7 (uso de redutores) e sugestao, nao trava.** Vive so no frontend
  (`aplicarRegraGavetaAcionamento`, index.html): pre-seleciona "Volante c/ Engrenagem de
  Reducao" e mostra um aviso, sem bloquear. E fiel a 5.5, que diz "desde que nao
  especificado em contrario" — ou seja, a propria norma abre excecao. Nao transformar em
  validacao 400 no backend.
- **Sistema mais restritivo que a norma de proposito** (nao "consertar" sem falar com
  engenharia): haste == obturador exato (C.5.1 aceita "ou superior"); corpo carbono -> so
  B7 (nota 5.6.5 aceita B16 como alternativa em esfera fire-tested); antiestatico exigido
  em toda Esfera+NBR (C.6 exige so em uso geral e fire-tested).
- **A lista de diametro esta certa como esta** (confirmado pelo usuario em 2026-07-15).
  `DIAMETROS` vai ate 60" e `DIAMETROS_POR_TIPO` mapeia por tipo, nao por norma — nao ha
  filtro de diametro por norma, e isso nao e bug. Nao mexer.

### Divida conhecida: `_VED_NBR_POR_CLASSE` na classe 150

`views.py:37` (e o espelho `VED_NBR_POR_CLASSE` em index.html) usa **uma tabela so** para
Gaveta e Retencao, mas os anexos divergem na classe 150:

- **Tabela A.1 (Gaveta), classe 150**: Espiralada/FJA/Pressure Seal/Castelo Soldado todos
  `-`; unica permitida e "junta de grafite flexivel com insercao metalica para juntas nao
  circulares"
- **Tabela B.1 (Retencao), classe 150**: Espiralada `X` + "junta nao metalica plana com
  fibra de aramida" `X`

O sistema permite `JUNTA ESPIRALADA` nas duas. Para Retencao esta certo; para **Gaveta esta
invertido** — libera justamente a que a A.1 marca com `-`. Classes 300 a 2500 batem
exatamente com as duas tabelas (que sao identicas ai).

Nao corrigido de proposito: as duas juntas exigidas na classe 150 **nao existem** em
`VEDACAO_CORPO_TAMPA_GAVETA_GLOBO` / `VEDACAO_CORPO_TAMPA_RETENCAO`, entao separar a tabela
sem adicionar as opcoes bloquearia Gaveta NBR 150 por completo. Decisao pendente com
engenharia: se Gaveta NBR classe 150 e caso real, adicionar as duas opcoes (mexe em choices
do modelo, `VEDACAO_POR_TIPO`, o mapa da parte L do codigo universal, traducao PT/EN e
PDF/Excel).

### Esfera + Rosca: a norma construtiva e o parametro (decisao de 2026-07-16)

A Tabela 3 tem leitura ambigua no OCR para a coluna "Roscada": a releitura (2026-07-16)
indica que a coluna so tem classe **150** / BS ISO 7121 / fogo `-`, e que o par
800/ISO 17292 e da coluna "Encaixe para solda" (reforcado por prosa confiavel: C.1.4 d)
liga 800 a encaixe para solda; C.1.4.2 veta rosca em valvula ensaiada a fogo).

Em vez de decidir a coluna, a regra `_ESF_ROSCA_*` foi invertida a pedido do usuario:
**a norma construtiva escolhida dita classe e uso geral** (antes a classe ditava a norma):

```
Esfera + NBR + Rosca + corpo A105/A182/A350/B564/B865 →
  diametro 1/2"-1 1/2"; norma em {BS ISO 7121, ISO 17292}
  BS ISO 7121 → classe 150; uso N/A
  ISO 17292   → classe 800; uso ISO 17292/ISO 10497/API 607
```

Espelho JS em `aplicarRegraEsferaFlangeButt` (ramo `isRosca`, agora separado do
`isSocket`, que segue por classe); o listener de `edit_norma` re-roda a regra no modal
de edicao. Coberto por `EsferaRoscaRuleTest`. **Pendencia com engenharia**: se o PDF
confirmar que Roscada so tem classe 150, remover o ramo ISO 17292 da Rosca (o par
800/ISO 17292 ja tem casa correta no Socket-Welding via `_esfera_socket_800`) — o
C.1.4.2 tambem barra o uso fire-test (ISO 10497/API 607) que esse ramo hoje permite.

---

## Codigo Universal (views.py:3456-4360)

Codigo tecnico no formato `AAAB.CCCD.EEE.FFF.GGHHII.JKLLMM(NNN-NNN)`, montado por
segmento a partir da spec da valvula. Cada letra tem sua funcao `_codigo_universal_<letra>`
e, quase sempre, um mapa de lookup:

| Parte | Deriva de |
|-------|-----------|
| AAA | tipo + subtipo (montagem, DIB, configuracao do disco, construcao do corpo, fire safe) |
| B | corpo fundido x forjado (pela spec ASTM do material do corpo) |
| CCC | diametro |
| D | classe |
| EEE | extremidade (mapas diretos + schedule BW + flange RF/face plana) |
| FFF / GG / HH / II | materiais (corpo, obturador, sede, inserto) via mapas normalizados |
| J | gaxeta |
| K | acionamento |
| LL | junta |
| MM | parafusos + porcas |
| NNN-NNN | niple / fire test |

Os mapas `_CODIGO_*_RAW` sao normalizados na importacao (`_norm_material`) para tolerar
variacao de escrita nos nomes de material.

---

## Exportacao (PDF/Excel/Email)

### Folha de dados
- Template unico `valvula_pdf.html`, **bilingue PT+EN no mesmo documento** (nao ha `?lang=`)
- `_folha_autofit` renderiza em varias escalas (`_FOLHA_ESCALAS`) e escolhe a que cabe na pagina —
  por isso o PDF e caro: ~4 renders por valvula

### PDF individual (`/valvulas/<pk>/pdf/`)
Gera PDF (xhtml2pdf) + Excel (openpyxl) e devolve um ZIP com os dois.

### Preview (`/api/valvulas/preview/`)
Renderiza o HTML da folha a partir do formulario, **sem salvar**. Usado no iframe de
pre-visualizacao do cadastro.

### Exportacao em lote (`/api/valvulas/exportar-lote/`)
- `_valvulas_para_export` faz prefetch de projetos/materiais/vedacoes/componentes/anexos (evita N+1)
- `_gerar_export_lote` roda ate `_EXPORT_MAX_WORKERS = 4` valvulas em `ThreadPoolExecutor`
  (sobrepoe render CPU-bound e download de anexos), ordem preservada
- ZIP unico com subpasta por codigo: `<codigo>/valvula_<codigo>.pdf`, `.xlsx`, `anexos/`

### Envio por email (`/api/valvulas/email/`)
Recebe IDs + destinatarios (separados por `;` ou `,`), valida cada email, anexa PDFs.

---

## Estatisticas (so ESPECIAL)

`/api/estatisticas/` agrega sobre `Valvula`, com filtros de querystring: `projeto`,
`tipo`, `data_inicio`, `data_fim`, `projeto_a`, `projeto_b` (comparacao entre projetos).
Retorna contadores (total, por mes/ano), rankings via `_top()`, serie temporal
(`TruncMonth`) e as `TentativaDuplicata` registradas.

---

## Configuracao e Deploy

### Variaveis de Ambiente (.env)
```
DEBUG=True/False
SECRET_KEY=...
DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
EMAIL_HOST_USER, EMAIL_HOST_PASSWORD
SITE_URL=https://seu-dominio.com/
SUPABASE_URL, SUPABASE_KEY, SUPABASE_BUCKET   # anexos; sem isso cai no StorageBlob
```

### Comandos
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python manage.py runserver

# Testes (SQLite em memoria)
python manage.py test --settings=config.settings_test

# Deploy: gunicorn
gunicorn config.wsgi --log-file -
```

### Timezone
`America/Sao_Paulo`. Views usam `zoneinfo.ZoneInfo('America/Sao_Paulo')` direto para os cortes de data.

### Email
SMTP Gmail com TLS, timeout 10s. Verificacao de cadastro em thread separada (async);
reset de senha sincrono. **Alguns provedores de hospedagem bloqueiam a porta 587
outbound — se o email nao sair em producao, confirmar que a porta esta liberada.**

---

## Observacoes Importantes

1. **`views.py` e um monolito de 5.3k linhas** sem camada de services. Antes de adicionar
   logica, ver o mapa de linhas na secao de estrutura.

2. **Regras compartilhadas**: `_aplicar_regras_automaticas`, `_validar_regras_valvula`,
   `_encontrar_duplicata`/`_resposta_duplicata`, `_limpar_campos_por_tipo`, `_salvar_relacionados`
   sao usados por criacao e edicao. `valvula_preview` duplica parte das regras automaticas
   a mao — manter em sincronia.

3. **Concorrencia**: criacao usa `pg_advisory_xact_lock`. So PostgreSQL.

4. **SPA server-side**: sem roteamento frontend. Tudo na mesma pagina via JS vanilla + modais Bootstrap.

5. **Testes existem**: ~200 testes em `core/tests.py`. Alguns pulam em Python 3.14+
   (`SKIP_TEMPLATE`: copia de contexto de template quebrada no Django 6.0).
   **A suite nao esta verde: ~53 falhas pre-existentes**, em dois grupos:
   (a) fixtures que nao mandam `funcao`, que o `ValvulaForm` exige; (b) testes de Borboleta
   cujo proprio payload base bate nas regras de classe/diametro. Medir a baseline antes de
   culpar uma mudanca sua.

6. **CSS/JS servido de `staticfiles/`, nao de `static/`**: WhiteNoise serve os arquivos coletados.
   Editar `static/css/*.css` **nao tem efeito** ate rodar `python manage.py collectstatic`.
   Templates sao servidos direto e nao precisam de collectstatic.

7. **Buracos conhecidos de seguranca** (nao corrigidos):
   - Endpoints de leitura **sem auth**: `valvula_lista_api`, `valvula_detalhe_api`,
     `pesquisa_avancada_api`, `projeto_lista_api`, `opcoes_por_tipo`, `materiais_por_tipo`,
     `material_lista_api`, `valvula_pdf`. Anonimo lista specs e baixa a folha de dados
     (o `anexo_download` tem guard; o PDF nao).
   - `material_criar` (views.py:4928): sem `@require_POST` e sem auth.
   - `ALLOWED_HOSTS = ["*"]` e `SECRET_KEY` com fallback `django-insecure-...` hardcoded.
   - `@csrf_exempt` em `cadastro_api` e `esqueci_senha_api`.

8. **`AGENTS.md` esta vazio.**
