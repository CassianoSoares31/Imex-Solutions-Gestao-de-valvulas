# Sistema de Gestão de Válvulas — Documentação Completa

---

## Sumário

1. [Requisitos Funcionais](#1-requisitos-funcionais)
2. [Requisitos Não Funcionais](#2-requisitos-não-funcionais)
3. [Estrutura do Banco de Dados](#3-estrutura-do-banco-de-dados)
4. [Opções por Tipo de Válvula](#4-opções-por-tipo-de-válvula)
   - [Esfera](#41-esfera)
   - [Gaveta](#42-gaveta)
   - [Globo](#43-globo)
   - [Retenção](#44-retenção)
   - [Borboleta](#45-borboleta)
   - [Globo Controle](#46-globo-controle)

---

## 1. Requisitos Funcionais

Os requisitos funcionais descrevem as funcionalidades que o sistema deve oferecer para atender às necessidades dos usuários.

### 1.1. Gestão de Válvulas

| ID | Nome | Descrição |
|----|------|-----------|
| RF001 | Cadastro de Válvulas | O sistema deve permitir o registro de novas válvulas, incluindo todos os atributos relevantes. |
| RF002 | Visualização de Cadastros | O sistema deve possibilitar a consulta e exibição detalhada dos registros de válvulas existentes. |
| RF003 | Identificação de Produto | O sistema deve permitir a inserção e validação do código de identificação de cada produto. |

### 1.2. Geração e Exportação de Dados

| ID | Nome | Descrição |
|----|------|-----------|
| RF004 | Geração de Arquivos de Cadastro | O sistema deve ser capaz de gerar um arquivo individual para cada registro de cadastro. |
| RF005 | Exportação para PDF | O sistema deve oferecer a funcionalidade de exportar os dados ou relatórios para o formato PDF. |

### 1.3. Pesquisa e Auditoria

| ID | Nome | Descrição |
|----|------|-----------|
| RF006 | Pesquisa por Código | O sistema deve permitir a pesquisa de cadastros utilizando o código do produto como critério. |
| RF007 | Geração de Logs de Auditoria | O sistema deve registrar logs de todas as operações de criação de dados para fins de auditoria. |

### 1.4. Integridade e Consistência de Dados

| ID | Nome | Descrição |
|----|------|-----------|
| RF008 | Prevenção de Entradas Duplicadas | O sistema deve impedir o registro de entradas idênticas para garantir a unicidade dos dados. |
| RF009 | Persistência de Dados | O sistema deve armazenar os dados em um banco de dados relacional. |
| RF010 | Validação de Entradas | O sistema deve validar as entradas para prevenir o registro de dados inconsistentes ou impossíveis. |

---

## 2. Requisitos Não Funcionais

Os requisitos não funcionais especificam critérios de qualidade e restrições sobre como o sistema deve operar.

### 2.1. Usabilidade

| ID | Nome | Descrição |
|----|------|-----------|
| RNF001 | Interface Intuitiva | O sistema deve apresentar uma interface de usuário intuitiva e de fácil compreensão. |
| RNF002 | Eficiência na Navegação | O sistema deve minimizar o número de interações (cliques) necessárias para acessar e pesquisar cadastros. |
| RNF003 | Otimização de Entrada de Dados | O sistema deve reduzir a quantidade de campos de texto para entrada de dados. |

### 2.2. Experiência do Usuário

| ID | Nome | Descrição |
|----|------|-----------|
| RNF004 | Clareza Visual | O sistema deve garantir uma visualização clara e organizada das informações. |
| RNF005 | Padronização de Dados | O sistema deve garantir a padronização das unidades de medição e tipos de dados em todos os campos de cadastro para assegurar a consistência das informações. |

### 2.3. Intercambialidade

| ID | Nome | Descrição |
|----|------|-----------|
| RNF006 | Intercambialidade de Sistemas | O sistema deve ser construído de forma a não ser restrito a uma única ferramenta, permitindo sua execução em múltiplos sistemas. |
| RNF007 | Intercambialidade de Pessoas | O sistema deve ser independente de desenvolvedores específicos, garantindo que sua manutenção e operação não sejam restritas a uma única pessoa. |

---

## 3. Estrutura do Banco de Dados

### Tabelas e Relacionamentos

#### Tabela: `VALVULA` (tabela central)

| Tipo | Coluna | Chave |
|------|--------|-------|
| int | id_valvula | PK |
| varchar | codigo | |
| varchar | tipo_valvula | |
| varchar | norma | |
| boolean | nbr | |
| varchar | diametro | |
| int | classe | |
| varchar | tipo_extremidade | |
| varchar | tipo_ranhura | |
| varchar | tipo_montagem | |
| varchar | tipo_acionamento | |
| varchar | construcao_corpo | |
| boolean | dbb | |
| varchar | dib | |
| boolean | valvula_alivio | |
| boolean | dispositivo_antiestatico | |

#### Tabela: `MATERIAL`

| Tipo | Coluna | Chave |
|------|--------|-------|
| int | id_material | PK |
| varchar | nome | |

#### Tabela: `VALVULA_MATERIAL` (relacionamento N:N entre VALVULA e MATERIAL)

| Tipo | Coluna | Chave |
|------|--------|-------|
| int | id | PK |
| int | valvula_id | FK → VALVULA |
| varchar | tipo_material | |
| int | material_id | FK → MATERIAL |

#### Tabela: `VEDACAO`

| Tipo | Coluna | Chave |
|------|--------|-------|
| int | id_vedacao | PK |
| int | valvula_id | FK → VALVULA |
| varchar | vedacao_corpo_tampa | |

#### Tabela: `COMPONENTES_INTERNOS`

| Tipo | Coluna | Chave |
|------|--------|-------|
| int | id | PK |
| int | valvula_id | FK → VALVULA |
| varchar | inserto_rede | |

### Relacionamentos

```
VALVULA ──possui──> VEDACAO
VALVULA ──possui──> COMPONENTES_INTERNOS
VALVULA ──possui──> VALVULA_MATERIAL <──compoe── MATERIAL
```

---

## 4. Opções por Tipo de Válvula

---

### 4.1. ESFERA

| Coluna | Opções |
|--------|--------|
| Norma de Construção | API 6D / ISO 14313 / API 608 / ASME B16.34 / ISO 17292 / MSS SP72 / NBR 14788 |
| NBR 15827 | SIM / NÃO |
| Diâmetro | 1/2" / 3/4" / 1" / 1 1/4" / 1 1/2" / 2" / 2 1/2" / 3" / 4" / 6" / 8" / 10" / 12" / 14" / 16" / 18" / 20" / 22" / 24" / 26" / 28" / 30" / 32" / 34" / 36" / 38" / 40" / 42" / 48" / 54" / 56" / 60" |
| Classe | 150 / 300 / 600 / 800 / 900 / 1500 / 2500 / 4500 / PN 10 / PN 16 / PN 20 / PN 25 / PN 40 / PN 50 / PN 100 / PN 150 / PN 250 / PN 420 |
| Tipo de Extremidade | FLANGE FACE PLANA / FLANGE RF / FLANGE RTJ (FJA) / BUTT-WELDING / SOCKET-WELDING / ROSCA NPT / ROSCA BSP / NIPLE 4" COMP. SCH 40 / NIPLE 4" COMP. SCH 80 / NIPLE 4" COMP. SCH 160 / NIPLE 4" COMP. SCH XS / NIPLE 4" COMP. SCH XXS |
| Tipo de Ranhura | 125-250 μin ESPIRAL / 125-250 μin CONCÊNTRICA / LISO (125 μin) |
| Material do Corpo / Tampa | ASTM A105 / ASTM A182 F11 CL1 / ASTM A182 F11 CL2 / ASTM A182 F6a / ASTM A182 F304 / ASTM A182 F304 L / ASTM A182 F316 / ASTM A182 F316 L / ASTM A182 F317 / ASTM A182 F321 / ASTM A182 F347 / ASTM A182 F51 / ASTM A182 F53 / ASTM A182 F54 / ASTM A182 F55 / ASTM A216 WCB / ASTM A216 WCC / ASTM A217 WC5 / WC6 / C5 / C12 / CA15 / ASTM A350 LF1 / LF2 / LF3 / ASTM A351 CF3 / CF8 / CF3M / CF8M / CF8C / CN7M / ASTM A352 LCA / LCB / LCC / CA6NM / ASTM A995 3A / 4A / 5A / 6A / ASTM B564 N04400 / ASTM B865 N05500 |
| Material do Obturador | AISI 304 / AISI 304L / AISI 316 / AISI 316L / AISI 321 / AISI 347 / AISI 410 (ASTM A182 F6A) / STELLITE 6 (ASTM A564 T630) / MONEL 400 (ASTM B564) / MONEL K500 (ASTM B865) |
| Material da Sede / Porta Sede | AISI 304 / AISI 304L / AISI 316 / AISI 316L / AISI 321 / AISI 347 / AISI 410 (ASTM A182 F6A) / STELLITE 6 (ASTM A564 T630) / MONEL 400 / MONEL K500 |
| Inserto da Sede | PEEK / PTFE / RPTFE (25% C) / DEVLON / DEVLON V-API / N/A |
| Material da Haste | AISI 304 / AISI 304L / AISI 316 / AISI 316L / AISI 321 / AISI 347 / AISI 410 / STELLITE 6 / MONEL 400 / MONEL K500 |
| Material das Molas | AISI 304 / AISI 316 / INCONEL 625 / INCONEL X750 / N/A |
| Vedação da Junção Corpo / Tampa | JUNTA ESPIRALADA / RTJ (FJA) / O'RING VITON |
| Material da Junta | AISI 304 + GRAFITE / AISI 316 + GRAFITE / N/A |
| Material da Gaxeta | GRAFITE / GRAFITE FLEXÍVEL + FIO DE INCONEL / GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR DE CORROSÃO / PTFE |
| Material dos Parafusos | ASTM A193 B7 / ASTM A193 B8 / ASTM A193 Gr B8M / ASTM A193 Gr B8M CL2 / ASTM A193 Gr B16 / ASTM A320 Gr L7 |
| Material das Porcas | ASTM A194 2H / ASTM A194 Gr 8 / ASTM A194 Gr 8M / ASTM A194 Gr7 / ASTM A194 Gr 7L / ASTM A194 Gr 4 / ASTM A194 Gr 4L |
| Tipo de Montagem (Esfera) | TRUNNION / FLUTUANTE |
| Tipo de Passagem | PLENA / REDUZIDA |
| Tipo de Acionamento | ALAVANCA / VOLANTE / VOLANTE COM ENGRENAGEM DE REDUÇÃO / ATUADOR ELÉTRICO / ATUADOR ELÉTRICO COM VOLANTE / ATUADOR PNEUMÁTICO RETORNO POR MOLA / ATUADOR PNEUMÁTICO RETORNO POR MOLA COM VOLANTE / ATUADOR PNEUMÁTICO DUPLA AÇÃO / ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA / ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA COM VOLANTE |
| Construção do Corpo (Esfera) | BI-PARTIDO / TRI-PARTIDO |
| DBB (Esfera) | SIM / NÃO |
| DIB (Esfera) | DIB-1 / DIB-2 / N/A |
| Válvula de Alívio / Dreno | SIM / NÃO |
| Dispositivo Antiestático | SIM / NÃO |
| Uso Geral / Testada a Fogo | USO GERAL / API 6FA / API 607 / ISO 10497 |
| Baixa Emissão Fugitiva | SIM / NÃO |
| Certificação SIL | SIL 1 / SIL 2 / SIL 3 / SIL 4 |
| NACE | MR0103 ISO 17495 / MR0175 ISO 15156 / N/A |

---

### 4.2. GAVETA

| Coluna | Opções |
|--------|--------|
| Norma de Construção | API 6D / ISO 14313 / API 600 / API 602 / ISO 15761 / ASME B16.34 |
| NBR 15827 | SIM / NÃO |
| Diâmetro | 1/2" / 3/4" / 1" / 1 1/4" / 1 1/2" / 2" / 2 1/2" / 3" / 4" / 6" / 8" / 10" / 12" / 14" / 16" / 18" / 20" / 22" / 24" / 26" / 28" / 30" / 32" / 34" / 36" / 38" / 40" / 42" / 48" / 54" / 56" / 60" |
| Classe | 150 / 300 / 600 / 800 / 900 / 1500 / 2500 / 4500 / PN 10 / PN 16 / PN 20 / PN 25 / PN 40 / PN 50 / PN 100 / PN 150 / PN 250 / PN 420 |
| Tipo de Extremidade | FLANGE FACE PLANA / FLANGE RF / FLANGE RTJ (FJA) / BUTT-WELDING / SOCKET-WELDING / ROSCA NPT / ROSCA BSP / NIPLE 4" COMP. SCH 40 / 80 / 160 / XS / XXS |
| Tipo de Ranhura | 125-250 μin ESPIRAL / 125-250 μin CONCÊNTRICA / LISO (125 μin) |
| Material do Corpo / Tampa | ASTM A105 / ASTM A182 F11 CL1 / ASTM A182 F11 CL2 / ASTM A182 F6a / ASTM A182 F304 / ASTM A182 F304 L / ASTM A182 F316 / ASTM A182 F316 L / ASTM A182 F317 / ASTM A182 F321 / ASTM A182 F347 / ASTM A182 F51 / ASTM A182 F53 / ASTM A182 F54 / ASTM A182 F55 / ASTM A216 WCB / ASTM A216 WCC / ASTM A217 WC5 / WC6 / C5 / C12 / CA15 / ASTM A350 LF1 / LF2 / LF3 / ASTM A351 CF3 / CF8 / CF3M / CF8M / CF8C / CN7M / ASTM A352 LCA / LCB / LCC / CA6NM / ASTM A995 3A / 4A / 5A / 6A / ASTM B564 N04400 / ASTM B865 N05500 |
| Material do Obturador | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 / STELLITE 6 / MONEL 400 / MONEL K500 |
| Material da Sede / Porta Sede | AISI 304 / AISI 304L / AISI 316 / AISI 316L / AISI 321 / AISI 347 / AISI 410 (ASTM A182 F6A) / STELLITE 6 (ASTM A564 T630) / MONEL 400 / MONEL K500 |
| Inserto da Sede | — |
| Material da Haste | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 / STELLITE 6 / MONEL 400 / MONEL K500 |
| Vedação da Junção Corpo / Tampa | JUNTA ESPIRALADA / RTJ (FJA) / PRESSURE SEAL / CASTELO SOLDADO |
| Material da Junta | AISI 304 + GRAFITE / AISI 316 + GRAFITE / N/A |
| Material da Gaxeta | GRAFITE / GRAFITE FLEXÍVEL + FIO DE INCONEL / GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR DE CORROSÃO / GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR (molibdato de bário e/ou fios de zinco) / PTFE |
| Material dos Parafusos | ASTM A193 B7 / B8 / Gr B8M / Gr B8M CL2 / Gr B16 / ASTM A320 Gr L7 / N/A |
| Material das Porcas | ASTM A194 2H / Gr 8 / Gr 8M / Gr7 / Gr 7L / Gr 4 / Gr 4L / N/A |
| Tipo de Passagem | PLENA / REDUZIDA |
| Tipo de Acionamento | VOLANTE / VOLANTE COM ENGRENAGEM DE REDUÇÃO / ATUADOR ELÉTRICO / ATUADOR ELÉTRICO COM VOLANTE / ATUADOR PNEUMÁTICO RETORNO POR MOLA / ATUADOR PNEUMÁTICO RETORNO POR MOLA COM VOLANTE / ATUADOR PNEUMÁTICO DUPLA AÇÃO / ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA / ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA COM VOLANTE |
| Tipo de Castelo | NORMAL / EXTENDIDO |
| Junção Corpo / Castelo | APARAFUSADO / SOLDADO / ROSCADO / ROSCADO E SOLDADO |
| Uso Geral / Testada a Fogo | USO GERAL / API 6FA / API 607 / ISO 10497 / N/A |
| Baixa Emissão Fugitiva | SIM / NÃO |
| Certificação SIL | SIL 1 / SIL 2 / SIL 3 / SIL 4 |
| NACE | MR0103 ISO 17495 / MR0175 ISO 15156 / N/A |

---

### 4.3. GLOBO

| Coluna | Opções |
|--------|--------|
| Norma de Construção | BS 1873 / API 602 / ISO 15761 / API 623 / ASME B16.34 |
| NBR 15827 | SIM / NÃO |
| Diâmetro | 1/2" / 3/4" / 1" / 1 1/4" / 1 1/2" / 2" / 2 1/2" / 3" / 4" / 6" / 8" / 10" / 12" / 14" / 16" / 18" / 20" / 22" / 24" / 26" / 28" / 30" / 32" / 34" / 36" / 38" / 40" / 42" / 48" / 54" / 56" / 60" |
| Classe | 150 / 300 / 600 / 800 / 900 / 1500 / 2500 / 4500 |
| Tipo de Extremidade | FLANGE FACE PLANA / FLANGE RF / FLANGE RTJ (FJA) / BUTT-WELDING / SOCKET-WELDING / ROSCA NPT / ROSCA BSP / NIPLE 4" COMP. SCH 40 / 80 / 160 / XS / XXS |
| Tipo de Ranhura | 125-250 μin ESPIRAL / 125-250 μin CONCÊNTRICA / LISO (125 μin) |
| Material do Corpo / Tampa | ASTM A105 / ASTM A182 F11 CL1 / ASTM A182 F11 CL2 / ASTM A182 F6a / ASTM A182 F304 / ASTM A182 F304 L / ASTM A182 F316 / ASTM A182 F316 L / ASTM A182 F317 / ASTM A182 F321 / ASTM A182 F347 / ASTM A182 F51 / ASTM A182 F53 / ASTM A182 F54 / ASTM A182 F55 / ASTM A216 WCB / ASTM A216 WCC / ASTM A217 WC5 / WC6 / C5 / C12 / CA15 / ASTM A350 LF1 / LF2 / LF3 / ASTM A351 CF3 / CF8 / CF3M / CF8M / CF8C / CN7M / ASTM A352 LCA / LCB / LCC / CA6NM / ASTM A995 3A / 4A / 5A / 6A / ASTM B564 N04400 / ASTM B865 N05500 |
| Material do Obturador | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 / STELLITE 6 / MONEL 400 / MONEL K500 |
| Material da Sede / Porta Sede | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 / STELLITE 6 / MONEL 400 / MONEL K500 |
| Inserto da Sede | — |
| Material da Haste | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 / STELLITE 6 / MONEL 400 / MONEL K500 |
| Vedação da Junção Corpo / Tampa | JUNTA ESPIRALADA / RTJ (FJA) / PRESSURE SEAL / CASTELO SOLDADO |
| Material da Junta | AISI 304 + GRAFITE / AISI 316 + GRAFITE / N/A |
| Material da Gaxeta | GRAFITE / GRAFITE FLEXÍVEL + FIO DE INCONEL / GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR DE CORROSÃO / PTFE / N/A |
| Material dos Parafusos | ASTM A193 B7 / B8 / Gr B8M / Gr B8M CL2 / Gr B16 / ASTM A320 Gr L7 / N/A |
| Material das Porcas | ASTM A194 2H / Gr 8 / Gr 8M / Gr7 / Gr 7L / Gr 4 / Gr 4L / N/A |
| Tipo de Passagem | PLENA / REDUZIDA |
| Tipo de Acionamento | VOLANTE / VOLANTE COM ENGRENAGEM DE REDUÇÃO / ATUADOR ELÉTRICO / ATUADOR ELÉTRICO COM VOLANTE / ATUADOR PNEUMÁTICO RETORNO POR MOLA / ATUADOR PNEUMÁTICO RETORNO POR MOLA COM VOLANTE / ATUADOR PNEUMÁTICO DUPLA AÇÃO / ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA / ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA COM VOLANTE |
| Tipo de Castelo | NORMAL / EXTENDIDO |
| Junção Corpo / Castelo | APARAFUSADO / SOLDADO / ROSCADO / ROSCADO E SOLDADO |
| Uso Geral / Testada a Fogo | USO GERAL / API 6FA / API 607 / ISO 10497 / N/A |
| Baixa Emissão Fugitiva | SIM / NÃO |
| Certificação SIL | SIL 1 / SIL 2 / SIL 3 / SIL 4 |
| NACE | MR0103 ISO 17495 / MR0175 ISO 15156 / N/A |

---

### 4.4. RETENÇÃO

| Coluna | Opções |
|--------|--------|
| Norma de Construção | BS 1868 / API 602 / ISO 15761 / API 6D / ASME B16.34 |
| NBR 15827 | SIM / NÃO |
| Diâmetro | 1/2" / 3/4" / 1" / 1 1/4" / 1 1/2" / 2" / 2 1/2" / 3" / 4" / 6" / 8" / 10" / 12" / 14" / 16" / 18" / 20" / 22" / 24" |
| Classe | 150 / 300 / 600 / 800 / 900 / 1500 / 2500 |
| Tipo de Extremidade | FLANGE FACE PLANA / FLANGE RF / FLANGE RTJ (FJA) / BUTT-WELDING / SOCKET-WELDING / ROSCA NPT / ROSCA BSP / NIPLE 4" COMP. SCH 40 / 80 / 160 / XS / XXS |
| Tipo de Ranhura | 125-250 μin ESPIRAL / 125-250 μin CONCÊNTRICA / LISO (125 μin) |
| Material do Corpo / Tampa | ASTM A105 / ASTM A182 F11 CL1 / ASTM A182 F11 CL2 / ASTM A182 F6a / ASTM A182 F304 / ASTM A182 F304 L / ASTM A182 F316 / ASTM A182 F316 L / ASTM A182 F317 / ASTM A182 F321 / ASTM A182 F347 / ASTM A182 F51 / ASTM A182 F53 / ASTM A182 F54 / ASTM A182 F55 / ASTM A216 WCB / ASTM A216 WCC / ASTM A217 WC5 / WC6 / C5 / C12 / CA15 / ASTM A350 LF1 / LF2 / LF3 / ASTM A351 CF3 / CF8 / CF3M / CF8M / CF8C / CN7M / ASTM A352 LCA / LCB / LCC / CA6NM / ASTM A995 3A / 4A / 5A / 6A / ASTM B564 N04400 / ASTM B865 N05500 |
| Material do Obturador | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 / STELLITE 6 / MONEL 400 / MONEL K500 |
| Material da Sede / Porta Sede | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 / STELLITE 6 / MONEL 400 / MONEL K500 |
| Material da Haste | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 |
| Material das Molas | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 / MONEL 400 / MONEL K500 |
| Vedação da Junção Corpo / Tampa | JUNTA ESPIRALADA / RTJ (FJA) |
| Material da Junta | AISI 304 + GRAFITE / AISI 316 + GRAFITE / N/A |
| Material da Gaxeta | — |
| Material dos Parafusos | ASTM A193 B7 / B8 / Gr B8M / Gr B8M CL2 / Gr B16 / ASTM A320 Gr L7 / N/A |
| Material das Porcas | ASTM A194 2H / Gr 8 / Gr 8M / Gr7 / Gr 7L / Gr 4 / Gr 4L / N/A |
| Tipo de Passagem | Plena / Passagem |
| Junção Corpo / Castelo | APARAFUSADO |
| NACE | MR0103 ISO 17495 / MR0175 ISO 15156 / N/A |

---

### 4.5. BORBOLETA

| Coluna | Opções |
|--------|--------|
| Norma de Construção | API 609 / ASME B16.34 / MSS SP67 |
| NBR 15827 | SIM / NÃO |
| Diâmetro | 1/2" / 3/4" / 1" / 1 1/4" / 1 1/2" / 2" / 2 1/2" / 3" / 4" / 6" / 8" / 10" / 12" / 14" / 16" / 18" / 20" / 22" / 24" / 26" / 28" / 30" / 32" / 34" / 36" / 38" / 40" / 42" / 48" / 54" / 56" / 60" |
| Classe | 150 / 300 / 600 / 800 / 900 / 1500 / 2500 / 4500 / PN 10 / PN 16 / PN 20 / PN 25 / PN 40 / PN 50 / PN 100 / PN 150 / PN 250 / PN 420 |
| Tipo de Ranhura | 125-250 μin ESPIRAL / 125-250 μin CONCÊNTRICA / LISO (125 μin) |
| Material do Corpo / Tampa | ASTM A536 65-45-12 / ASTM A105 / ASTM A216 GR WCB / ASTM A216 GR WCC |
| Material do Obturador | ASTM A536 65-45-12 / ASTM A106 / ASTM A216 GR WCB / ASTM A216 GR WCC |
| Material da Sede / Porta Sede | BUNA N / VITON / EPDM / PTFE / RPTFE (25% C) / N/A |
| Material da Haste | AISI 304 / AISI 304L / AISI 316 / AISI 316L / AISI 321 / AISI 347 / AISI 410 |
| Material da Gaxeta | GRAFITE / GRAFITE FLEXÍVEL + FIO DE INCONEL / GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR DE CORROSÃO / N/A |
| Tipo de Acionamento | ALAVANCA / VOLANTE / VOLANTE COM ENGRENAGEM DE REDUÇÃO / ATUADOR ELÉTRICO / ATUADOR ELÉTRICO COM VOLANTE / ATUADOR PNEUMÁTICO RETORNO POR MOLA / ATUADOR PNEUMÁTICO RETORNO POR MOLA COM VOLANTE / ATUADOR PNEUMÁTICO DUPLA AÇÃO / ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA / ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA COM VOLANTE |
| Dispositivo Antiestático | SIM / NÃO |
| Categoria (Borboleta) | CATEGORIA A / CATEGORIA B |
| Face a Face (Borboleta) | LUG / WAFER / FLANGEADA PADRÃO CURTO / FLANGEADA PADRÃO LONGO / N/A |
| Configuração do Disco (Borboleta) | CONCÊNTRICA / BI-EXCÊNTRICA / TRI-EXCÊNTRICA |
| Uso Geral / Testada a Fogo | USO GERAL / API 6FA / API 607 / ISO 10497 |
| Certificação SIL | SIL 1 / SIL 2 / SIL 3 / SIL 4 |
| NACE | MR0103 ISO 17495 / MR0175 ISO 15156 / N/A |

---

### 4.6. GLOBO CONTROLE

| Coluna | Opções |
|--------|--------|
| Norma de Construção | Conforme Fabricante |
| Diâmetro | 1/2" / 3/4" / 1" / 1 1/4" / 1 1/2" / 2" / 2 1/2" / 3" / 4" / 6" / 8" / 10" / 12" / 14" / 16" / 18" / 20" / 22" / 24" / 26" / 28" / 30" / 32" / 34" / 36" / 38" / 40" / 42" / 48" / 54" / 56" / 60" |
| Classe | 150 / 300 / 600 / 800 / 900 / 1500 / 2500 |
| Tipo de Extremidade | FLANGE FACE PLANA / FLANGE RF / FLANGE RTJ (FJA) / BUTT-WELDING / SOCKET-WELDING / ROSCA NPT / ROSCA BSP |
| Material do Corpo / Tampa | ASTM A105 / ASTM A182 F11 CL1 / ASTM A182 F11 CL2 / ASTM A182 F6a / ASTM A182 F304 / ASTM A182 F304 L / ASTM A182 F316 / ASTM A182 F316 L / ASTM A182 F317 / ASTM A182 F321 / ASTM A182 F347 / ASTM A182 F51 / ASTM A182 F53 / ASTM A182 F54 / ASTM A182 F55 / ASTM A216 WCB / ASTM A216 WCC / ASTM A217 WC5 / WC6 / C5 / C12 / CA15 / ASTM A350 LF1 / LF2 / LF3 / ASTM A351 CF3 / CF8 / CF3M / CF8M / CF8C / CN7M / ASTM A352 LCA / LCB / LCC / CA6NM / ASTM A995 3A / 4A / 5A / 6A / ASTM B564 N04400 / ASTM B865 N05500 |
| Material do Obturador | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 / STELLITE 6 / MONEL 400 / MONEL K500 |
| Material da Sede / Porta Sede | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 / STELLITE 6 / MONEL 400 / MONEL K500 |
| Material da Haste | AISI 304 / 304L / 316 / 316L / 321 / 347 / 410 / STELLITE 6 / MONEL 400 / MONEL K500 |
| Vedação da Junção Corpo / Tampa | JUNTA ESPIRALADA / RTJ (FJA) / PRESSURE SEAL / CASTELO SOLDADO |
| Material da Junta | AISI 304 + Grafite / AISI 316 + Grafite / N/A |
| Material da Gaxeta | Grafite / Grafite Flexível + Fio de Inconel / GRAFITE FLEXÍVEL + FIO DE INCONEL C/ INIBIDOR DE CORROSÃO / PTFE |
| Material dos Parafusos | ASTM A193 B7 / ASTM A193 B8 / ASTM A193 Gr B8M / ASTM A193 Gr B8M CL2 / ASTM A193 Gr B16 / ASTM A320 Gr L7 |
| Material das Porcas | ASTM A194 2H / ASTM A194 Gr 8 / ASTM A194 Gr 8M / ASTM A194 Gr 7 / ASTM A194 Gr 7L / ASTM A194 Gr 4 / ASTM A194 Gr 4L |
| Tipo de Passagem | PLENA / REDUZIDA |
| Tipo de Acionamento | VOLANTE / VOLANTE COM ENGRENAGEM DE REDUÇÃO / ATUADOR ELÉTRICO / ATUADOR ELÉTRICO COM VOLANTE / ATUADOR PNEUMÁTICO RETORNO POR MOLA / ATUADOR PNEUMÁTICO RETORNO POR MOLA COM VOLANTE / ATUADOR PNEUMÁTICO DUPLA AÇÃO / ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA / ATUADOR ELETROHIDRÁULICO RETORNO POR MOLA COM VOLANTE |
| Tipo de Castelo | APARAFUSADO / SOLDADO / ROSCADO / ROSCADO E SOLDADO |
| Uso Geral | USO GERAL / API 6FA / API 607 / ISO 10497 |
| Baixa Emissão Fugitiva | SIM / NÃO |
| Certificação SIL | SIL 1 / SIL 2 / SIL 3 / SIL 4 |
| NACE | MR0103 ISO 17495 / MR0175 ISO 15156 / N/A |
| Posicionador | ELETROPNEUMÁTICO 4–20 mA / ELETROPNEUMÁTICO 4–20 mA + HART / FIELDBUS / PROFIBUS |
| Filtro | SIM, COM MANÔMETROS / SIM, SEM MANÔMETROS / SIM, COM MAN. ELEMENTO FILTRANTE 5 µ / SIM, COM MAN. ELEMENTO FILTRANTE 5 µ CORPO ALUMÍNIO / SIM, COM MAN. ELEMENTO FILTRANTE 5 µ CORPO AÇO INOX |
| Indicador de Posição | SIM / NÃO |
| Tubing | INOX 316 / INOX 304 / COBRE / COBRE REVESTIDO |

---
