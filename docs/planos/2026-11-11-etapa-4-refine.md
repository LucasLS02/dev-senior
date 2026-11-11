# Etapa 4: skill `refine` e validador de brief

> **Para agentes:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development
> (recomendado) ou superpowers:executing-plans para executar este plano tarefa a
> tarefa. Os passos usam checkbox (`- [ ]`) para acompanhamento.

**Objetivo:** a skill `refine` transforma um card, uma descrição ou uma conversa
em `.agent_plans/<pasta>/brief.md`: reescreve a necessidade, questiona se ela é
real e se o pedido a resolve, lista opções (sempre "não fazer" e "resolver sem
código"), recomenda uma e para para a aprovação do humano. Pode concluir que a
tarefa não vale a pena. Para bug, o mesmo brief ganha um diagnóstico.

**Arquitetura:** a skill é só instruções, mais `scripts/check_brief.py` (Python,
só biblioteca padrão) que lê o formato da seção 5.1 do design e imprime um erro
por linha, no molde do `check_spec.py`. `references/modelo.md` é o esqueleto;
`references/exemplo.md` é um brief completo e válido, que um teste passa pelo
validador. A prova de que funciona é uma avaliação no molde das etapas 2 e 3:
fixture com histórico, agente sem interação, checagens sobre o `brief.md`, em
quatro modos (`funcionalidade`, `vaga`, `bug`, `descartada`).

**Tecnologia:** Markdown no padrão Agent Skills, Python 3.9+ só com biblioteca
padrão, Bash, git, `claude -p` nas avaliações.

**Spec:** `docs/2026-11-10-fluxo-de-skills-design.md`, seções 3, 4 (portas e
modo), 5 e 5.1 (formato, IDs, `[PRECISA DECISÃO]`), 6.1 e 11 (ordem). O formato
que a `spec` lê está em `skills/spec/SKILL.md` e `tests/spec.eval.sh` (o brief
da avaliação `clara`).

## Restrições globais

- Texto das skills em português; identificadores, comandos e caminhos como
  aparecem no código.
- A skill descreve capacidades, nunca a API de uma ferramenta ("com pesquisa
  disponível, cruze com referências; sem ela, a tabela leva `—`").
- Nenhuma skill instala ferramenta; o script usa só a biblioteca padrão e roda no
  `python3` 3.9 do macOS (`from __future__ import annotations`, sem
  `str | None`).
- `SKILL.md` com no máximo 200 linhas.
- A skill só escreve `.agent_plans/<pasta>/brief.md`: nunca código, nunca spec,
  nunca commit.
- `Status: aprovado` e `Status: descartado` só depois da decisão do humano; a
  skill grava `rascunho`, mesmo quando recomenda não fazer.
- Dúvida que o código e o card não respondem vira `[PRECISA DECISÃO: …]`, nunca
  suposição. O rascunho com marcadores é gravado **antes** de perguntar (lição
  da etapa 3: sem isso o agente sem interação não entrega arquivo).
- Fonte de mercado só se o agente abriu a fonte; sem pesquisa, a linha é `—`.
- O texto da skill (SKILL.md, modelo, exemplo) não contém respostas da fixture
  de avaliação.
- Commits sem atribuição de IA, mensagens em en-US, com parada para aprovação.
  Push nunca.

## Lições da etapa 3 que este plano já aplica

1. O validador nasce endurecido: erro único para arquivo não UTF-8, erro para
   cerca de código aberta, citação resolvida dentro da raiz (nada de `..`,
   diretório ou intervalo de linhas inválido).
2. A RED roda **sem** a pasta da skill visível ao agente (na etapa 3 o agente leu
   o validador e contaminou a linha de base).
3. As checagens da avaliação não exigem "validador limpo" quando o card deixa
   brecha real; exigem "limpo ou só `marcador pendente`". A exigência estrita
   fica só onde o card é inteiramente claro (`descartada`).
4. Logs e artefatos da avaliação ficam em `.superpowers/` (git-ignorado), nunca em
   `/tmp`.
5. Codex fica **fora** das tarefas: a verificação cruzada das skills no Codex
   acontece uma vez, no fim, com limite de tempo (decisão do Lucas, 2026-11-11).

## Review Focus

Entradas que os testes talvez não exerçam e que o revisor final confere de
propósito, da mais provável para a menos:

1. Brief `aprovado` ou `descartado` gravado pela própria skill (o validador não
   sabe quem aprovou; o texto e a avaliação é que seguram).
2. Pedido de mudança rápida entrando pelo `refine` (a skill recusa e manda para a
   `spec`, em vez de produzir cerimônia).
3. Fonte de mercado inventada ou linha de referência que parece pesquisa sem ter
   havido.
4. Diagnóstico de bug com causa raiz afirmada sem reprodução, ou só parte das cinco
   linhas.
5. Brief que a `spec` não consegue ler: o brief da avaliação `clara` da etapa 3 e
   o exemplo deste plano precisam passar no mesmo validador.

## Decisões deste plano (o Lucas pode contestar)

| # | Decisão | Por quê | Custo se errada |
|---|---|---|---|
| D1 | Validador `check_brief.py`, como nas etapas 1 a 3 | Torna a avaliação determinística e protege o contrato `refine`→`spec` | ~150 linhas e 25 testes; cortável (Tarefa 1 sai e a avaliação perde o "limpo") |
| D2 | Bug ganha a seção `## Diagnóstico` com cinco linhas (Reprodução, Causa raiz, Comportamento atual, Comportamento esperado, Deve permanecer igual) | O design 4 pede o modo diagnóstico, mas o formato 5.1 não tem onde pôr | Muda o contrato 5.1; a `spec` ignora a seção (lê só `Problema` e `Recomendação`) |
| D3 | O modo e o motivo ficam na primeira linha de `## Apetite`: `Modo <modo>: <motivo>` | O design 4 diz "registrado no artefato com o motivo"; 5.1 só tem o modo no cabeçalho | Uma linha a mais por brief |
| D4 | Recomendar "não fazer" **não** muda o `Status` para `descartado`; só o humano faz | Mesma regra de aprovação da `spec` | O validador só exige: `descartado` ⇒ recomendada é "não fazer" |
| D5 | Mudança rápida não passa pelo `refine` | Design 4: é uma porta separada | A skill recusa em uma frase |
| D6 | Citação de arquivo é uma cópia do trecho do `check_spec.py`, não import | Pasta autocontida (design 3); onde ficam scripts compartilhados é item 14 do design | Duas cópias para manter; a dívida entra no ledger |
| D7 | Quatro modos de avaliação (e não três) | `bug` e `descartada` são as duas formas do `refine` que a `spec` não tem | Cada rodada gasta tokens: 4 agentes por rodada, no máximo 3 rodadas |

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `skills/refine/SKILL.md` | Instruções (≤200 linhas) |
| `skills/refine/references/modelo.md` | Esqueleto do brief e da seção Diagnóstico |
| `skills/refine/references/exemplo.md` | Brief completo e válido (domínio de reservas de sala) |
| `skills/refine/scripts/check_brief.py` | Validador: `check(brief, root) -> list[str]` e CLI |
| `tests/check_brief_test.py` | Testes do validador |
| `tests/refine_text_test.py` | Invariantes do texto da skill |
| `tests/refine.eval.sh` | Avaliação com agente, quatro modos |
| `tests/run-agent.sh` | Modificar: `SKILLS_DIR` opcional para a RED |
| `README.md` | Uma linha na seção Avaliações |
| `docs/medicoes/2026-11-etapa-4.md` | RED, GREEN e rodadas |

---

### Tarefa 1: validador `check_brief.py`

**Arquivos:**

- Criar: `skills/refine/scripts/check_brief.py`
- Testar: `tests/check_brief_test.py`

**Interfaces:**

- Produz, para as Tarefas 2 e 3: `check(brief: Path, root: Path) -> list[str]`
  (uma mensagem `"<nome>:<linha>: <problema>"` por erro; sem linha,
  `"<nome>: <problema>"`) e a CLI `check_brief.py <brief.md> [raiz]`: imprime os
  erros e sai 1, ou imprime `limpo` e sai 0; brief ausente sai 2 com a mensagem
  no stderr.
- O texto `VALID` do Anexo A é a base dos testes (domínio de reservas de sala,
  nenhuma relação com a fixture de avaliação).

O que o validador confere:

| Confere | Mensagem contém |
|---|---|
| Título `# Brief: <texto>` e cabeçalho `Status: rascunho\|aprovado\|descartado · Origem: <texto> · Modo: rápido\|padrão\|profundo` | `cabeçalho` |
| As nove seções do 5.1: Problema, Pedido vs. necessidade, Apetite, Referências de mercado, Opções consideradas, Recomendação, Fora de escopo, Riscos e armadilhas, Perguntas em aberto | `seção ausente: <nome>` |
| `Apetite` tem a linha `Modo <modo>: <motivo>` e o modo é o do cabeçalho | `Apetite` |
| `Pedido vs. necessidade` tem `Pedido:` e `Necessidade:` | `Pedido vs. necessidade` |
| `Referências de mercado`: tabela `Fonte \| Como resolve \| O que aproveitar` com ao menos uma linha; cada `Fonte` é `—`, uma URL `http(s)://` ou um caminho entre crases | `Referências` |
| `Opções consideradas`: tabela `Opção \| Prós \| Contras \| Veredito` com ao menos três linhas, uma `não fazer`, uma `sem código`; `Veredito` é `Recomendada` ou `Descartada`; exatamente uma `Recomendada` | `Opções` |
| `Status: descartado` ⇒ a recomendada é a linha `não fazer` | `descartado` |
| `Perguntas em aberto`: `Nenhuma.` ou linhas `- [PRECISA DECISÃO: …]`; mais de cinco marcadores no arquivo é erro | `mais de cinco` |
| Marcador pendente em qualquer parte, fora de cerca de código | `marcador pendente` |
| `Diagnóstico` (opcional): as cinco linhas; `Reprodução` com comando entre crases; `Causa raiz` com citação | `Diagnóstico` |
| Citação `arquivo:linha` entre crases aponta para arquivo que existe dentro da raiz, com linha válida (≥1, intervalo crescente, não além do fim) | `cita` |
| Arquivo não UTF-8: um único erro | `não é UTF-8` |
| Cerca de código aberta sem fechar | `cerca de código aberta` |

Só se confere o que começa num item real da raiz, como no `check_spec.py`: o brief
cita arquivo a criar sem que ele exista.

- [ ] **Passo 1: escrever `tests/check_brief_test.py` (RED).** Mesmo molde de
  `tests/check_spec_test.py` (setUp numa pasta temporária com `AGENTS.md` e
  `app/booking.py` de 3 linhas; helper `errors(text)` que grava e chama `check`;
  `assertError(errs, *palavras)`). Um teste por linha da tabela, mais:
  `test_valid_brief_is_clean`, `test_valid_bug_brief_is_clean` (o `VALID` mais a
  seção `Diagnóstico` do Anexo A), `test_discarded_brief_is_clean` (Status
  `descartado` e recomendada `não fazer`), `test_pipe_inside_backticks_is_not_a_cell_break`,
  `test_marker_inside_code_fence_is_ignored` e `test_cli_exit_codes` (0 limpo, 1 com
  erro, 2 sem arquivo). O teste do exemplo da skill fica na Tarefa 3. Rodar: `python3 -m unittest tests.check_brief_test` → falha (módulo inexistente).

- [ ] **Passo 2: implementar `check_brief.py`.** Reaproveitar a estrutura do
  `skills/spec/scripts/check_spec.py` (leitura de seções fora de cerca, divisão de
  células que respeita crases e `\|`, marcador, citação endurecida): copiar o
  trecho, não importar (D6), e registrar no ledger `Ruling: duas cópias do
  tratamento de citação`. Assinaturas: `check(brief: Path, root: Path) ->
  list[str]` e `main(argv: list[str]) -> int`.

- [ ] **Passo 3: rodar os testes e as checagens estáticas.**
  `python3 -m unittest discover -s tests -p '*_test.py'`, o mesmo com
  `/usr/bin/python3`, e `ruff check skills tests` → OK e limpo.

- [ ] **Passo 4: mutação.** Para cada teste de cerca, de célula e de citação,
  desligar a lógica correspondente e ver o teste falhar; restaurar. Registrar no
  ledger (lição das etapas 2 e 3: teste que não discrimina é o defeito mais comum).

---

### Tarefa 2: avaliação e RED

**Arquivos:**

- Modificar: `tests/run-agent.sh` (`--add-dir "${SKILLS_DIR:-$repo/skills}"`)
- Criar: `tests/refine.eval.sh`
- Modificar: `README.md` (uma linha na seção Avaliações)
- Criar: `docs/medicoes/2026-11-etapa-4.md`

**Interfaces:**

- Consome: `tests/make-docs-fixture.sh <destino> spec` (8 commits; `AGENTS.md`
  correto), `tests/run-agent.sh <diretório> <prompt>`, `check_brief.py` (Tarefa 1).
- Produz, para a Tarefa 3: `tests/refine.eval.sh funcionalidade|vaga|bug|descartada`
  (saída `ok:`/`FALHOU:` por checagem e `resultado: passou|falhou`; sai 0 só se
  passou; `SKILLS_DIR` repassado ao agente).

Os cartões **não citam** `slugify`, o registro de handlers nem as funções de
dinheiro: o agente acha tudo isso no código.

| Modo | Cartão no prompt | O que o agente tem de fazer |
|---|---|---|
| `funcionalidade` | "card-101: avisar a operação por SMS quando a exportação CSV de um cliente terminar" | Separar pedido (SMS) de necessidade (saber que o arquivo está pronto); achar o canal que já existe |
| `vaga` | "card-102: melhorar a exportação" | Gravar o rascunho com marcadores e não inventar o que "melhorar" quer dizer |
| `bug` | "card-103: a exportação de um cliente quebra com `ValueError: invalid literal for int()` quando o total é 1.234,50" | Reproduzir, achar a causa raiz no código e preencher o diagnóstico |
| `descartada` | "card-104: criar uma função que normalize o nome do cliente: sem acento, minúsculo, com hífens" | Achar que já existe e recomendar não fazer, sem marcar `descartado` |

Prompt comum: "Use a skill refine neste repositório. <cartão>. Grave o brief em
.agent_plans/<pasta>/brief.md." Nenhum modo dá o nome da pasta: o agente escolhe.

Checagens comuns: 8 commits; `git status --porcelain` igual a `?? .agent_plans/`;
agente com código de saída ≠ 0 reprova; existe um único `.agent_plans/*/brief.md`;
`Status: rascunho`; não existe `spec.md`.

| Modo | Checagens específicas |
|---|---|
| `funcionalidade` | saída do `check_brief.py` vazia de erros ou só `marcador pendente`; `Pedido vs. necessidade` com `Pedido:` e `Necessidade:` e os dois diferentes; `Opções consideradas` ou `Recomendação` cita `app/handlers/`; `Modo padrão` na linha de Apetite; no máximo 60 linhas |
| `vaga` | a saída do `check_brief.py` só tem `marcador pendente` (de 1 a 5 linhas); as `Opções` têm `não fazer` e `sem código` mesmo assim; nenhuma opção recomendada afirma o que "melhorar" significa (checado só pela contagem de marcadores, o resto é leitura humana da medição) |
| `bug` | `check_brief.py` limpo ou só marcadores; seção `Diagnóstico`; `Causa raiz` cita `app/money.py:` com linha de 1 a 3; `Reprodução` com comando entre crases e `ValueError`; só `.agent_plans/` novo (nenhuma correção feita) |
| `descartada` | `check_brief.py` limpo (sem marcador: o cartão é inteiramente claro); a recomendada é a linha `não fazer`; cita `app/text.py:`; `Status: rascunho` |

- [ ] **Passo 1: `tests/run-agent.sh` aceita `SKILLS_DIR`.** Trocar o
  `--add-dir "$repo/skills"` por `--add-dir "${SKILLS_DIR:-$repo/skills}"`. Rodar
  `bash -n tests/run-agent.sh`. Esperado: sintaxe OK; sem `SKILLS_DIR`, o
  comportamento das avaliações anteriores não muda.

- [ ] **Passo 2: escrever `tests/refine.eval.sh`** no molde de `tests/spec.eval.sh`
  (monta a fixture em modo `spec`, roda o agente, confere), com os quatro modos
  das tabelas acima. Nenhum modo escreve brief de entrada: o agente parte do
  cartão. `bash -n` → OK.

- [ ] **Passo 3: RED, sem a skill visível.** Criar o diretório de skills sem o
  `refine` (ainda não existe, mas o validador existe em `skills/refine/scripts/`
  desde a Tarefa 1, por isso o filtro):
  `d=$(mktemp -d); for s in skills/*; do [ "$(basename $s)" = refine ] || ln -s
  "$PWD/$s" "$d/$(basename $s)"; done; SKILLS_DIR=$d tests/refine.eval.sh
  funcionalidade` e idem para `vaga`, `bug` e `descartada`, em paralelo, com a saída em
  `.superpowers/sdd/<plano>/red/<modo>.log`. Esperado: os quatro saem 1 (sem
  `brief.md` no formato). Anotar em `docs/medicoes/2026-11-etapa-4.md`, por modo, o que
  o modelo sozinho fez: pesquisou o código? separou pedido e necessidade? perguntou
  em vez de gravar? implementou o bug? É a linha de base.

- [ ] **Passo 4: README.** Acrescentar `tests/refine.eval.sh funcionalidade  #
  funcionalidade | vaga | bug | descartada` à seção Avaliações.

---

### Tarefa 3: escrever a skill e rodar a GREEN

**Arquivos:**

- Criar: `skills/refine/SKILL.md`
- Criar: `skills/refine/references/modelo.md`
- Criar: `skills/refine/references/exemplo.md`
- Testar: `tests/refine_text_test.py`
- Modificar: `docs/medicoes/2026-11-etapa-4.md`

**Interfaces:**

- Consome: `check_brief.py` (Tarefa 1) e a avaliação (Tarefa 2).
- Produz, para o fluxo: `.agent_plans/<pasta>/brief.md` no formato 5.1, lido pela
  `spec`. A `spec` lê `Status`, `Modo`, `Problema`, `Recomendação` e
  `Fora de escopo`; o `Diagnóstico` é só do `refine`.

O `SKILL.md` (português, `metadata: opencode/slash: "true"`, até 200 linhas)
contém, nesta ordem:

1. **`description`** com os disparos: "refinar o pedido", "entender a
   necessidade", "criar o brief", "investigar o bug", "/refine".
1. **Entrada, porta e modo.** Card, descrição ou conversa. Classificar a porta:
   `funcionalidade` ou `bug`. Mudança clara, pequena e fora de migração e de
   caminho sensível **não passa por aqui**: dizer em uma frase que é caso da `spec`
   e parar. O `Modo` (`padrão` ou `profundo`) e o motivo vão na primeira linha de
   `Apetite`. Pasta em kebab-case ASCII; se o brief já existe, atualizar. Só grava
   `.agent_plans/<pasta>/brief.md`.
1. **Entender antes de propor.** Reescrever a necessidade e separar o que foi
   pedido do que resolve de fato; perguntar se o problema é real e qual a
   evidência, e se o pedido resolve a necessidade. Olhar o código o bastante para
   saber o que já existe (o `AGENTS.md`, o histórico dos arquivos tocados, uma
   busca por nome e sinônimo) e citar `arquivo:linha` só onde o brief afirma algo
   sobre o código.
1. **Referências de mercado.** Só com pesquisa disponível e só de fonte aberta; sem
   ela, a linha é `—`. Nunca inventar fonte.
1. **Opções.** Sempre "não fazer" e "resolver sem código", mais as que o problema
   pedir; cada uma com prós, contras e veredito; exatamente uma recomendada. Se a
   melhor opção é não fazer, recomendar "não fazer" e dizer o porquê; o `Status`
   continua `rascunho`.
1. **Bug (modo diagnóstico).** Acrescentar `## Diagnóstico` com Reprodução (comando
   que mostra a falha), Causa raiz (`arquivo:linha`), Comportamento atual,
   Comportamento esperado e Deve permanecer igual. Não afirmar causa sem
   reproduzir; se não reproduz, marcador.
1. **Dúvida.** Pergunta sem resposta no código, no card ou na conversa vira
   `[PRECISA DECISÃO: <pergunta, nomeando o termo>]` em `Perguntas em aberto` e no
   ponto onde entra. Marcador só para o que apenas o dono do pedido sabe; escolha
   que o código permite resolver, a skill decide e registra nas opções. **Grave o
   rascunho antes de perguntar**; depois, no máximo cinco perguntas por rodada.
1. **Validar e parar.** `python3 <pasta da skill>/scripts/check_brief.py <brief.md>
   .` na raiz do repositório, até `limpo` ou só `marcador pendente`. Parar e pedir a
   aprovação; só o humano muda o `Status` para `aprovado` ou `descartado`.
   Resposta final: caminho, marcadores abertos e a recomendação em uma linha.
1. **Regras de escrita.** Brief maior que o problema é transcrição: cortar; só fato
   com `arquivo:linha`; imperativo; sem "deveria".

`references/modelo.md` é o esqueleto da seção 5.1 mais a seção `Diagnóstico`.
`references/exemplo.md` é o brief do Anexo A, completo e válido.

- [ ] **Passo 1: escrever `tests/refine_text_test.py` (RED)**, mesmo molde de
  `tests/spec_text_test.py`:
  - `test_does_not_leak_fixture_answers`: `\b(?:slugify|slug|HANDLERS|dispatch|sms|
    centavos?|cents|to_cents|UTC|schema_gen|ValueError|money)\b` não casa (sem
    diferenciar maiúsculas) em `SKILL.md`, `modelo.md` nem `exemplo.md`.
  - `test_skill_stays_within_line_cap`: `SKILL.md` ≤ 200 linhas.
  - `test_example_brief_passes_validator`: lê `exemplo.md`, recria numa árvore
    temporária cada arquivo citado como `arquivo:N` (com N linhas), roda
    `check(...)` e espera `[]`.
  - `test_skill_runs_the_validator`: `SKILL.md` contém `check_brief.py` e
    `[PRECISA DECISÃO`.
  - `test_spec_eval_brief_is_still_a_valid_brief`: extrai o brief do heredoc de
    `tests/spec.eval.sh` (entre `cat > ".agent_plans/$slug/brief.md" <<EOF` e `EOF`,
    com `$title` e `$rule` substituídos), grava e espera `check(...) == []`: o que
    o `refine` produz é o que a `spec` lê.

  Rodar → falha (arquivos não existem).

- [ ] **Passo 2: escrever `SKILL.md`, `modelo.md` e `exemplo.md`.**
  `exemplo.md` usa o Anexo A. Se o brief da `spec.eval.sh` não passar no
  validador, o erro está num dos dois; decidir com o formato 5.1 do design e
  ledgerar.

- [ ] **Passo 3: checagens estáticas e testes.**
  `python3 -m unittest discover -s tests -p '*_test.py'` e o mesmo com
  `/usr/bin/python3` → OK. `ruff check skills tests` → limpo. `wc -l
  skills/refine/SKILL.md` → ≤ 200. `grep -rniE 'Task tool|Agent tool|subagent_type'
  skills/refine` → nada. Mutação: vazar uma palavra da fixture no `SKILL.md` e
  tirar `check_brief.py` do texto; os testes correspondentes têm de falhar.

- [ ] **Passo 4: rodar a GREEN.** `tests/refine.eval.sh` nos quatro modos, em
  paralelo, com o `wait` dentro do mesmo comando (a notificação de conclusão do
  lançador não é a do fim das avaliações) e logs em
  `.superpowers/sdd/<plano>/green/`. Registrar na medição, com o nº de linhas de
  cada brief, para recalibrar o limite de 60.

- [ ] **Passo 5: corrigir as falhas.** Ler o log do agente e o `brief.md` gerado
  antes de culpar a skill: se o card tem brecha real (como o brief da etapa 3), o erro
  é da fixture, e a correção vai nela, com ruling. Senão, corrigir o texto da
  skill. No máximo 3 rodadas; depois, parar e mostrar ao Lucas.

## Commit

Plano único de commits, separado por tarefa e por intenção, antes da revisão final:
plano; validador com testes; avaliação e `run-agent.sh` e README; skill com teste de
texto; medição. Parada para a aprovação do Lucas antes de commitar.

## Revisão final

Revisor de contexto novo, no modelo mais capaz, com o Review Focus acima e o
ledger. Uma passada de correção por TDD; menores vão ao ledger como `Final: minor
(deferred)`. Depois, o menu de integração (merge local, PR ou manter).

## Anexo A: brief-base dos testes e do exemplo (`VALID`)

Domínio de reservas de sala; nenhuma relação com a fixture de avaliação.

````markdown
# Brief: Cancelar reserva de sala
Status: rascunho · Origem: card-7 · Modo: padrão

## Problema
Quem reserva uma sala e desiste precisa chamar o suporte para liberar o horário;
o suporte registrou 14 pedidos assim no mês. Hoje só `app/booking.py:2` cria
reservas.

## Pedido vs. necessidade
Pedido: um botão de cancelar. Necessidade: o horário voltar a ficar livre sem
depender de uma pessoa do suporte.

## Apetite
Modo padrão: mexe em dado de reserva, mas em um arquivo só.
Pequeno: um dia.

## Referências de mercado
| Fonte | Como resolve | O que aproveitar |
| --- | --- | --- |
| — | — | — |

## Opções consideradas
| Opção | Prós | Contras | Veredito |
| --- | --- | --- | --- |
| Não fazer | Sem custo | O suporte segue cancelando à mão | Descartada |
| Resolver sem código | O suporte cancela por formulário | Não elimina a espera | Descartada |
| Cancelar pela própria pessoa | Libera na hora, sem suporte | Precisa tratar cancelamento repetido | Recomendada |

## Recomendação
Permitir que quem reservou cancele uma reserva futura, liberando o horário.

## Fora de escopo
Reembolso, aviso aos demais participantes, histórico de cancelamentos.

## Riscos e armadilhas
Cancelar duas vezes a mesma reserva não pode liberar o horário de outra pessoa.

## Perguntas em aberto
Nenhuma.
````

Seção que o modo bug acrescenta (entre `Pedido vs. necessidade` e `Apetite`):

````markdown
## Diagnóstico
- Reprodução: `python3 -c "from app.booking import reserve; reserve('', 10)"` → `KeyError`
- Causa raiz: `app/booking.py:2` indexa o dicionário antes de validar o id
- Comportamento atual: id vazio derruba a chamada com `KeyError`
- Comportamento esperado: erro de validação com mensagem legível
- Deve permanecer igual: reservas com id válido
````
