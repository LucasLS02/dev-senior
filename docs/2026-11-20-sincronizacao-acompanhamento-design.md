# Sincronização com ferramentas de acompanhamento: desenho da skill `track`

Data: 2026-11-20 · Status: rascunho

Este documento descreve o que será construído e por quê. O plano de
implementação sai daqui, como nas etapas anteriores
(`docs/2026-11-10-fluxo-de-skills-design.md`).

## 1. Intenção

O fluxo `refine → spec → implement → smart-commit → open-pr` funciona, mas o
que ele planeja e executa só existe em `.agent_plans/<pasta>/`. O time
acompanha o trabalho num quadro (Jira, monday, GitHub Issues, Azure Boards) e
hoje alguém precisa copiar à mão o que foi planejado e o andamento.

O objetivo é que o planejamento aprovado vire o item certo no quadro e que esse
item acompanhe o progresso sozinho: status, critérios e checklist, comentários
sobre o que foi feito, limitações encontradas e travas que dependem de uma
decisão ou de outra pessoa.

## 2. Objetivos, não objetivos e antiobjetivos

**Objetivos**

- Spec aprovada vira um item no quadro (ou atualiza o card de onde o trabalho
  veio), com os critérios de aceite e as tarefas.
- O item reflete o andamento por eventos: começou, travou, destravou, entregou,
  PR aberta.
- Rodar a sincronização de novo nunca duplica nada.
- Funciona com qualquer ferramenta acessível por CLI ou MCP, escolhida pelo
  `AGENTS.md` do repositório.

**Não objetivos**

- Ler o quadro para decidir o que construir (a entrada continua sendo o
  `refine`).
- Mover o item para "concluído" no merge: nenhuma skill faz merge, e as
  ferramentas já têm integração com o GitHub para isso.
- Comentários a partir do `pr-feedback`.
- Subtarefa por tarefa da spec.
- Camada de adaptadores por ferramenta (decisão da §2 do design do fluxo).
- Instalar CLI ou configurar MCP.

**Antiobjetivos** (falhas mesmo que tudo funcione)

- Card duplicado por rodar duas vezes ou em outra máquina.
- Comentário a cada passo, que transforma o card em log.
- Texto publicado com caminho de máquina, credencial, `arquivo:linha` ou ID
  interno (`RV-003`, `G6`) que o leitor do quadro não entende.
- Sobrescrever o que uma pessoa escreveu no card.
- Publicar no quadro sem a confirmação do dono.
- Uma parada nova a cada evento, até a aprovação virar reflexo.

## 3. Restrições

- Texto da skill em português; comandos e identificadores como na ferramenta.
- A skill descreve capacidades (criar item, comentar, mudar status, marcar
  impedimento, ligar itens), nunca a API de uma ferramenta. Os comandos de cada
  ferramenta ficam em `references/<ferramenta>.md`.
- Pasta autocontida: `SKILL.md` curto, `references/`, `scripts/`. Validador em
  Python só com a biblioteca padrão.
- Publicar no quadro é ação para fora, da mesma classe que push e PR: nunca sem
  confirmação.
- `findings.md` e o campo `correção` nunca saem da máquina (§5.4 do design do
  fluxo).
- Sem `AGENTS.md` declarando acompanhamento, nenhuma skill do fluxo muda de
  comportamento.

## 4. Abordagens consideradas

| Abordagem | Prós | Contras | Veredito |
|---|---|---|---|
| **A. Skill `track` que reconcilia a partir dos arquivos.** Lê `brief`, `spec`, `progress`, `pr.md` e `tracker.md`, calcula como o item remoto deveria estar e publica só a diferença. As outras skills ganham uma linha condicional que a chama. | Idempotente por construção; uma execução perdida é recuperada na próxima; pode ser chamada à mão (`/track`) a qualquer momento; nenhuma outra skill conhece a ferramenta | Precisa ler `progress.md` e `pr.md` (formatos já fixos e validados) | **Escolhida pelo dono** |
| B. Skill `track` movida por eventos que as outras skills passam | Mais simples de escrever | Evento perdido deixa o card errado para sempre; deduplicação em cada chamada | Descartada |
| C. Instruções de sincronização dentro de cada skill | Sem skill nova | Mesmo texto em quatro skills, que se desencontram; mistura responsabilidades | Descartada |

## 5. Configuração no `AGENTS.md`

A skill só age se o `AGENTS.md` da raiz tiver esta seção:

```markdown
## Acompanhamento de projeto
- Ferramenta: Jira · Acesso: acli (ou MCP atlassian) · Projeto: ENG
- Tipos: spec → Story · brief → Epic (opcional)
- Status: em andamento = "In Progress" · em review = "Code Review"
```

- **Ferramenta e acesso** dizem qual `references/<ferramenta>.md` ler e se o
  caminho é CLI ou MCP.
- **Tipos** mapeiam os artefatos para os tipos de item do projeto. Sem a linha
  `brief → …`, não se cria épico.
- **Status** mapeia os estados do fluxo para os nomes do workflow do time, que
  variam de time para time.
- Seção ausente: a skill não faz nada e diz isso em uma linha. Seção incompleta
  ou acesso indisponível (CLI ausente, MCP sem autorização): para e diz o que
  falta, sem tentar outro caminho.
- A `codebase-agent-docs` passa a oferecer essa seção como candidata quando
  audita um repositório (`references/templates.md`).

## 6. Mapeamento dos artefatos

| Artefato | Vira | Regra |
|---|---|---|
| `brief.md` | Épico | Só com `brief → Epic` no `AGENTS.md`, ou quando o card de origem já é um épico: então a story nasce filha dele |
| `spec.md` | Uma story (1 spec = 1 PR = 1 item) | Descrição: `Objetivo` e `Entendimento`, os `AC-NNN` como critérios de aceite e as `T1..Tn` como checklist |
| Tarefas da spec | Checklist na story | Marcadas conforme `progress.md`; nunca subtarefas |
| Escalada | Impedimento + comentário (+ link "bloqueado por" quando a trava é outro item do quadro) | Comentário com efeito, alternativas e recomendação, em linguagem de resultado |
| Decisão registrada | Remove o impedimento + comentário com a decisão | — |
| `progress.md` | Status e checklist | Pendente → em andamento; checklist marcado na entrega |
| `pr.md` | Link da PR e status "em review" | — |
| `findings.md` | Nada | Nunca publicado |

## 7. Card existente ou novo

- **Com card de origem** (o `refine` recebeu um card): a skill se vincula a ele
  e grava a chave no `tracker.md`. Não reescreve a descrição de quem criou o
  card; acrescenta a seção sincronizada (abaixo) no fim.
- **Sem card:** cria a story a partir da spec, e o épico quando a regra da §6
  pedir.
- **Antes de criar, procura.** Todo item criado leva um marcador estável (o nome
  da pasta, em rótulo ou na descrição, conforme a ferramenta permitir). Antes de
  criar, a skill busca esse marcador no projeto: se o item existe, vincula em
  vez de criar. Isso evita duplicata mesmo quando o `tracker.md` não está na
  máquina (`.agent_plans/` não commitado, outra pessoa, outro agente).
- **O remoto é a verdade; o `tracker.md` é cache.** A cada execução a skill lê o
  item (descrição, comentários, status, impedimento) antes de calcular a
  diferença. Cada comentário de evento termina com um rodapé curto e legível
  (`— fluxo: início`, `— fluxo: impedimento 1`, `— fluxo: entrega`), que é como a
  skill sabe que ele já saiu. Assim, comentários, status e a seção sincronizada
  também não duplicam sem o `tracker.md`.

## 8. Conteúdo que a skill possui no item

- A skill só escreve numa seção delimitada da descrição, com título fixo
  ("Critérios e tarefas — sincronizado pelo fluxo"), mais os comentários,
  status, impedimento e links. O resto da descrição é das pessoas.
- O `tracker.md` guarda o texto (ou um hash) da última versão publicada dessa
  seção. Se a versão remota mudou desde então, alguém editou à mão: a skill não
  sobrescreve, mostra a diferença e pergunta. Sem `tracker.md`, não há como
  saber quem editou: a skill compara a seção remota com a que geraria e, se
  diferem, pergunta antes de sobrescrever.

## 9. Eventos e onde a `track` é chamada

| Quem chama | Momento | O que a reconciliação publica | Confirmação |
|---|---|---|---|
| `refine` | Brief gravado com card de origem | Nada: grava o vínculo no `tracker.md` | Não precisa (nada sai) |
| `implement` | Prontidão aprovada (primeiro momento em que a spec está aprovada) | Cria ou vincula a story, escreve a seção sincronizada, status "em andamento", comentário de início | **Parada nova, uma vez por tarefa** |
| `implement` | Escalada | Impedimento + comentário | Coberta pela primeira; mostrada e registrada no log |
| `implement` | Decisão do humano registrada | Remove impedimento + comentário | Coberta pela primeira; mostrada e registrada no log |
| `implement` | Entrega | Checklist marcado + comentário de entrega (ACs que passaram, limitações, pendências) | Coberta pela primeira; mostrada e registrada no log |
| `open-pr` | PR criada | Link da PR + status "em review" | Coberta pela primeira; mostrada e registrada no log |
| Humano | `/track` | O que estiver diferente | Sempre |

A linha acrescentada em cada skill tem esta forma: "Se o `AGENTS.md` da raiz
tem `## Acompanhamento de projeto`, chame a skill `track` com a pasta." Nenhuma
skill passa evento: a `track` descobre o que mudou comparando os arquivos com o
item remoto.

**De onde sai cada estado** (os arquivos de hoje quase bastam):

| Estado | Fonte |
|---|---|
| Spec aprovada | `Status: aprovado` na `spec.md` |
| Em andamento | `progress.md` existe com a prontidão `ok` |
| Escalada aberta ou decidida | Bloco da escalada em `Escaladas e decisões` do `progress.md`. **Mudança pequena no `implement`:** o bloco passa a ser gravado inteiro (formato de `gatilhos.md`) com uma última linha `Decisão: pendente` ou `Decisão: <texto>`. Hoje o formato é livre e o exemplo só registra a decisão |
| Entrega | Todas as tarefas `concluída`, nenhuma escalada `pendente` e `converge` limpo; as limitações saem das escaladas decididas e dos AC `manual` pendentes |
| PR aberta | `gh pr view <branch> --json url` (leitura, já liberada; o `open-pr` só trabalha com GitHub). O `pr.md` existir não basta, porque ele é gravado antes da ordem |

**Quais escaladas viram impedimento no quadro:** só as que dependem de alguém
de fora do desenvolvimento: S1 (a correção contradiz a spec), S3 (regra de
negócio ausente) e qualquer escalada em que o humano disser que depende de
outra pessoa. As demais (G1–G9, S2, S4–S7, P1–P4) são decisões técnicas do dev
e só aparecem, resumidas, no comentário de entrega como limitação, se tiverem
mudado o resultado.

**Confirmação** segue o modelo da `smart-commit`: a skill monta o plano (cada
operação remota, o item, o texto exato que vai sair), apresenta e só executa com
o ok.

- **A primeira publicação da tarefa** (prontidão do `implement`) mostra o plano
  completo e os modelos dos comentários de impedimento, decisão e entrega. O ok
  dela vale também para as **atualizações de rotina daquela tarefa**: status,
  impedimento, decisão, entrega e link da PR. Assim o card aparece travado
  enquanto a trava existe, e não só depois da decisão.
- Cada atualização de rotina é mostrada ao humano quando sai e fica no log do
  `tracker.md`.
- **Sempre pedem confirmação:** criar item, vincular a um card existente e
  editar a descrição (inclusive a seção sincronizada), em qualquer momento, e
  qualquer publicação feita por `/track` chamado à mão.
- A confirmação vale para a tarefa (a pasta). Outra pasta exige outra.

## 10. Comentários

- Por evento, nunca por passo. Quatro tipos: início, impedimento, decisão,
  entrega. O link da PR vai no campo próprio ou num comentário curto.
- Três partes: o que foi feito, o que vem a seguir, travas ou riscos.
- Leitor presumido: alguém de produto, que não abre o código. Sem caminho de
  arquivo, sem `arquivo:linha`, sem IDs internos de achado ou gatilho. Os IDs
  `AC-NNN` podem aparecer, porque estão nos critérios do próprio item.
- A escalada do `implement` (formato de `implement/references/gatilhos.md`)
  traduz-se assim: `Efeito`, `Alternativas` e `Recomendação` vão para o
  comentário; `Gatilho`, `Motivo` com `arquivo:linha` e `Arquivos` ficam de fora.
- Todo texto que sai passa pela verificação de vazamento (a mesma regex `LEAK`
  de `open-pr/scripts/check_pr.py:32`, copiada para o script da skill, porque
  cada pasta é autocontida).

## 11. Estado local: `tracker.md`

Fica em `.agent_plans/<pasta>/tracker.md`. Guarda:

- ferramenta, projeto e o marcador da pasta;
- a chave e a URL de cada item (épico, story);
- o que já foi publicado: status atual, impedimento ativo ou não, quais
  comentários de evento já saíram (por evento e por ID de escalada), link da PR,
  hash da seção sincronizada;
- um log que só acrescenta, com cada operação remota executada.

Um script (`scripts/check_track.py`) confere o formato do `tracker.md`, calcula
o que falta publicar a partir dos outros artefatos e aplica a verificação de
vazamento ao texto que vai sair. A ferramenta calcula; o agente executa os
comandos da referência e grava o resultado.

## 12. Referências por ferramenta

Uma por ferramenta em `references/`, cada uma com o comando ou a ferramenta MCP
de cada capacidade: buscar pelo marcador, ler o item (descrição, status,
impedimento), listar comentários, criar item (com pai), editar a descrição,
comentar, mudar status, marcar e desmarcar impedimento, ligar itens.

No GitHub Issues, status e impedimento são rótulos (`em andamento`,
`em review`, `bloqueado`), configurados pelo mapa de status do `AGENTS.md`.
Mover o card num GitHub Project (`gh project item-edit`) fica para depois:
exige outro escopo de token e outro `gh` falso na avaliação.

| Ferramenta | Acesso | Observação |
|---|---|---|
| GitHub Issues | `gh` | Instalado; é o que a avaliação usa, com `gh` falso como na do `open-pr` |
| Jira | `acli` ou MCP atlassian | `acli` não está instalado nesta máquina e o MCP precisa de autorização. A flag para definir o pai no `acli jira workitem create` não foi confirmada: conferir com `--help` antes de escrever |
| monday | MCP oficial (`mcp.monday.com`) ou GraphQL | Não tem CLI oficial. Checklist vira subitem ou lista no texto: decidir na referência |
| Azure Boards | `az boards` | Instalado |

Comando não conferido na ferramenta real não entra na referência, ou entra
marcado como não verificado.

## 13. Permissões

Escritas no quadro passam a pedir aprovação em `permissions/rules.py` (`ASK`):
`gh issue create`, `gh issue edit`, `gh issue comment`, os subcomandos de
escrita do `acli jira workitem` e `az boards work-item create`/`update`. Hoje já
pedem por não estarem na lista liberada; colocar em `ASK` torna isso explícito e
coberto pelo teste de permissões.

## 14. Medição

Pela regra da §10 do design do fluxo, a skill precisa mostrar ganho medido:

| Métrica | Meta |
|---|---|
| Itens duplicados ao rodar a `track` duas vezes seguidas, e com o `tracker.md` apagado | 0 |
| ACs e tarefas da spec presentes no item remoto | 100% |
| Texto publicado que reprova na verificação de vazamento | 0 |
| Criação, vínculo ou edição de descrição executados sem confirmação | 0 |
| Atualização de rotina antes da primeira confirmação da tarefa | 0 |
| Comentários por tarefa concluída sem escalada | ≤ 3 (início, entrega, PR) |

A avaliação (`tests/track.eval.sh`) monta o repositório de teste, coloca um
`gh` falso no `PATH` que registra as chamadas e responde às buscas, e roda os
modos: `criar`, `vincular` (card de origem), `repetir` (segunda execução:
nenhuma criação), `sem-estado` (sem `tracker.md`: acha pelo marcador),
`escalada` e `sem-config` (sem a seção no `AGENTS.md`: nenhuma chamada).

## 15. O que muda em cada lugar

| Lugar | Mudança |
|---|---|
| `skills/track/` | Nova: `SKILL.md`, `references/` (formato do `tracker.md`, uma referência por ferramenta), `scripts/check_track.py` |
| `skills/refine/SKILL.md` | Uma linha: com card de origem, chamar `track` para gravar o vínculo |
| `skills/implement/SKILL.md` e `references/modelo-progress.md` | Uma linha na prontidão, na escalada, na decisão e na entrega; o bloco da escalada gravado inteiro com a linha `Decisão:` (§9) |
| `skills/open-pr/SKILL.md` | Uma linha depois de criar a PR |
| `skills/codebase-agent-docs/references/templates.md` | Seção `Acompanhamento de projeto` como candidata |
| `permissions/rules.py` | Escritas do quadro em `ASK` |
| `README.md` e `docs/2026-11-10-fluxo-de-skills-design.md` | Skill nova no fluxo e nos contratos |
| `tests/` | `track.eval.sh`, `check_track_test.py`, teste de texto da skill |

## 16. Quem decidiu o quê

**Decisões do dono**

- Abordagem A (reconciliação a partir dos arquivos, com `tracker.md`).
- Mapeamento da §6; tarefas como checklist, sem subtarefas.
- Com card de origem, vincula; sem card, cria pelo mesmo mapeamento.
- Criar só depois da spec aprovada.
- Comentários por evento, não por passo.
- Confirmação no modelo da `smart-commit`: preparar tudo e pedir o ok. O ok da
  primeira publicação cobre as atualizações de rotina da tarefa; criar,
  vincular e editar a descrição pedem sempre (§9).
- CLI ou MCP, conforme a ferramenta; qual usar vem do `AGENTS.md`.
- Sem adaptador por ferramenta; comandos em `references/`.
- Sem duplicata ao rodar de novo; medição da §14; reuso da regex de vazamento.

**Decisões de quem escreveu este documento** (conferir na leitura)

- O nome `track` e o arquivo `tracker.md`.
- O formato da seção no `AGENTS.md` (§5), incluindo o mapa de status.
- A primeira publicação acontece na prontidão do `implement`, com uma parada
  nova, uma vez por tarefa.
- Marcador estável no item e busca antes de criar (§7).
- Seção delimitada na descrição e detecção de edição manual (§8).
- Leitor presumido de produto; IDs internos e caminhos ficam de fora (§10).
- Épico só com regra explícita no `AGENTS.md` ou card de origem épico.
- GitHub Issues como ferramenta da avaliação, por ser testável com `gh` falso;
  status e impedimento por rótulo, GitHub Projects depois.
- `pr-feedback` fora por enquanto.
- O remoto é a verdade e o `tracker.md` é cache; rodapé `— fluxo: <evento>` nos
  comentários para não duplicar sem estado local (§7).
- De onde sai cada estado, incluindo a linha `Decisão:` no bloco de escalada
  do `implement` e a URL da PR lida pelo `gh` (§9).
- Só S1, S3 e dependência de outra pessoa viram impedimento no quadro (§9).

## 17. Deixado para quem construir

- O texto exato do `SKILL.md`, das referências e dos modelos de comentário.
- O formato concreto do `tracker.md` e o que o `check_track.py` calcula.
- Como cada ferramenta representa marcador, checklist e impedimento (rótulo,
  campo, flag, lista no texto), registrado na referência dela.
- A ordem de escrita das referências além da do GitHub.
