# Fluxo de desenvolvimento com agentes: desenho das skills

Data: 2026-11-10 · Status: aprovado em 2026-11-10

Este documento descreve o que será construído e por quê. Cada skill terá
depois o seu próprio plano de implementação, escrito a partir daqui.

## 1. Intenção

Hoje existem três skills: `smart-commit`, `pr-review` e `pr-feedback`. As duas
de commit e de tratamento de review funcionam bem. A de review depende do
revisor embutido do Claude, o que impede o uso em outras ferramentas e limita a
quantidade de achados por execução; a versão portátil dela não tem método de
revisão próprio.

Faltam três etapas antes do review: refinar a necessidade, especificar frente
ao projeto e implementar de forma orquestrada. O objetivo é ter um conjunto
pequeno de skills, portáteis entre Claude Code, Codex e OpenCode, que cubra a
tarefa da ideia até o plano de commits e que sirva de base para uma ferramenta
própria no futuro.

Os problemas que o fluxo precisa atacar, nas palavras do dono:

| Causa | Como aparece |
|---|---|
| Não entendeu a necessidade | Entrega algo que funciona e não resolve o problema |
| Não entendeu o projeto | Ignora padrões, inventa caminho onde havia referência, recria função que existia |
| Construiu demais | Solução complicada para necessidade simples, pouco otimizada |
| Só testou o próprio caminho | Sem casos de borda nem caminhos alternativos |

As três primeiras causas se resolvem antes da implementação, não no review. Por
isso a `spec` é a peça de maior valor do fluxo.

## 2. Objetivos, não objetivos e antiobjetivos

**Objetivos**

- Review com método próprio, portátil, em que todo achado passa por uma
  verificação independente antes de ser apresentado.
- Spec que prova que o projeto foi investigado e em que cada critério de aceite
  tem uma forma de verificação.
- Orquestrador que corrige sozinho dentro de gatilhos objetivos e para o humano
  só quando há impacto grande ou decisão em aberto.
- Qualidade e desempenho apresentados como números calculados por ferramenta.
- Cada skill nova precisa mostrar ganho medido para continuar existindo.

**Não objetivos**

- Construir a ferramenta própria agora.
- Unificar ou corrigir skills de terceiros instaladas na máquina.
- Uma skill por lente de review (segurança, desempenho, dívida técnica).
- Vários agentes em paralelo como padrão.
- Integração com graphify (testada em 2026-11-10, sem ganho sobre busca
  simples; fica fora por enquanto).
- Camada de adaptadores por ferramenta ou bloco de capacidades em YAML.

**Antiobjetivos** (falhas mesmo que tudo funcione)

- Review que apresenta achado sem evidência.
- Agente que resolve um achado enfraquecendo teste ou adicionando supressão.
- Spec mais longa que o código que descreve.
- Paradas tão frequentes que a aprovação vira reflexo.

## 3. Restrições

- Texto das skills em português; identificadores, comandos e caminhos como
  aparecem no código.
- A skill descreve capacidades, nunca a API de uma ferramenta: "se houver
  delegação, um subagent por lente; se não, as lentes em sequência".
- Nenhuma skill instala ferramenta. Usa os comandos que o repositório já tem e
  ferramentas opcionais só se estiverem presentes.
- Commits sem atribuição de IA. Push e abertura de PR nunca acontecem sem ordem
  explícita.
- Comentário em PR de outra pessoa tem três partes, problema, evidência e
  impacto, sem sugestão de correção, num único review, no idioma da PR.
- GitHub é o alvo principal. Os comandos equivalentes do Azure DevOps ficam em
  arquivo de referência.
- Cada pasta de skill é autocontida: `SKILL.md` curto, detalhe em
  `references/`, `templates/` e `scripts/`.
- Este repositório é a fonte única; `install.sh` cria os links nas ferramentas.

## 4. Visão do fluxo

```text
Entrada ── classificação ─┬─ funcionalidade ─ refine ─ brief.md ─┐
                          ├─ bug ─ refine (modo diagnóstico) ────┤
                          └─ mudança rápida ─────────────────────┤
                                                                 ▼
                                        spec ─ spec.md ─ APROVAÇÃO
                                                                 ▼
implement: prontidão ─ tarefas ─ critérios ─ qualidade ─ review-diff
           ─ correções (gatilhos) ─ convergência ─ plano de commits ─ APROVAÇÃO
                                                                 ▼
                                   smart-commit ─ (push e PR só com ordem)
```

Três portas de entrada, como modos e não como skills:

| Porta | Quando | O que muda |
|---|---|---|
| Funcionalidade | Necessidade aberta ou ambígua | `refine` completo, depois `spec` |
| Bug | Comportamento errado | `refine` em modo diagnóstico: reproduzir, causa raiz, comportamento atual, esperado e inalterado |
| Mudança rápida | Clara, pequena, fora das superfícies sensíveis | Spec mínima: objetivo, escopo, critérios, arquivos, verificação |

O modo (`rápido`, `padrão`, `profundo`) fica registrado no artefato com o
motivo. Modo rápido reduz cerimônia, não verificação.

## 5. Contratos entre as skills

Os artefatos de uma tarefa ficam em `.agent_plans/<slug>/` na raiz do projeto.
O review de uma PR de outra pessoa usa `.agent_plans/pr-<N>/`.

| Arquivo | Quem escreve | Quem lê |
|---|---|---|
| `brief.md` | `refine` | `spec` |
| `spec.md` | `spec` | `implement`, `review-diff` |
| `progress.md` | `implement` | `implement` (retomada), o humano |
| `findings.md` | `review-diff` | `pr-review`, `pr-feedback`, `implement` |

Regras comuns: IDs estáveis (`AC-001`, `T1`, `RV-001`), toda afirmação sobre o
código cita `arquivo:linha`, toda dúvida usa o marcador
`[PRECISA DECISÃO: …]`. Com isso a prontidão é conferida por script.

### 5.1 `brief.md`

```markdown
# Brief: <título>
Status: rascunho | aprovado | descartado · Origem: <card> · Modo: rápido | padrão | profundo

## Problema            <quem sofre, quando, evidência de que é real>
## Pedido vs. necessidade   <o que foi pedido · o que resolve de fato>
## Apetite             <quanto vale gastar>
## Referências de mercado   | Fonte | Como resolve | O que aproveitar |
## Opções consideradas | Opção | Prós | Contras | Veredito |
                       (sempre inclui "não fazer" e "resolver sem código")
## Recomendação
## Fora de escopo
## Riscos e armadilhas
## Perguntas em aberto - [PRECISA DECISÃO: …]
```

### 5.2 `spec.md`

```markdown
# Spec: <título>
Status · Brief: <path> · Modo

## Objetivo            <uma frase testável>
## Entendimento        <a necessidade reescrita · cenário de demonstração>
## Padrões aplicáveis  | Regra | Onde está escrita ou exemplificada `arquivo:linha` |
## Referências no código | Funcionalidade parecida | `arquivo:linha` | O que imitar |
## Reuso               | Termos buscados | Encontrado `arquivo:linha` | Reusar, adaptar ou criar · motivo |
## Decisões            | Decisão | Alternativa mais simples | Por que não serve |
## Escopo              Permitido · Proibido · Exige aprovação
                       Orçamento: arquivos novos, abstrações novas, dependências novas
## Matriz de casos     | Caso | Entrada ou estado | Resultado esperado | AC ou "fora de escopo" |
## Critérios de aceite
### AC-001 <nome>
- QUANDO <condição> ENTÃO <resultado observável>
- Verificação: `<comando ou teste>` → <sinal esperado>
- Tipo: teste | comando | inspeção | manual
### Critérios de qualidade
- AC-Q01 Usa `<símbolo>` de `<arquivo>` · Verificação: `<busca ou comando>`
## Tarefas
### T1 <nome> · [P]? · Depende de: — · Cobre: AC-001, AC-Q01
- Arquivos: criar / modificar / teste
- Interfaces: consome / produz
- Pronto quando: `<comando>` → <sinal>
## Rastreabilidade     | AC | Tarefas |
```

Regras da spec:

- A matriz de casos cobre no mínimo: entrada vazia, inválida, limite, erro de
  dependência, concorrência, permissão e estado anterior. Quem escreve é a
  `spec`, nunca quem implementa.
- Critério de qualidade que não nomeia arquivo ou comando é recusado.
- Critério de desempenho só é exigido quando a tarefa toca superfície quente
  (consulta, laço sobre coleção, listagem, bundle) e é sempre uma contagem:
  consultas com 1 e com 10 itens, chamadas externas, razão de operações entre n
  e 10n. Tempo de relógio é só informativo.
- Uma spec maior que o código que ela descreve virou transcrição: cortar.

### 5.3 `progress.md`

```markdown
# Progresso · spec: <path>
## Prontidão           | Checagem | Resultado |
## Critérios de aceite | AC | Status | Evidência (comando + saída) | Estado da árvore |
## Tarefas             | T | Status | Arquivos alterados | Verificação |
## Qualidade           | Indicador | Antes | Depois | Limite | Origem |
## Achados             | ID | Severidade | Veredito | Gatilho | Ação | Resultado |
## Escaladas e decisões
## Log (só acrescenta)
```

É estado operacional, não transcrição. O relatório final e o plano de commits
saem dessas tabelas.

### 5.4 Achado (`findings.md`)

Um bloco por achado, o mesmo objeto em todas as etapas:

```yaml
id: RV-001
lente: requisito | correção | testes | conformidade | segurança | desempenho | manutenção
severidade: crítico | alto | médio | baixo
local: {arquivo: src/x.py, linhas: 81-94}
problema: <uma frase direta>
viola: AC-004 | `AGENTS.md` seção X | —
evidência: <`arquivo:linha`, trecho, comando e saída>
impacto: <cenário → consequência>
verificação: {veredito: confirmado | refutado | plausível, método: teste | reprodução | inspeção}
correção: {escopo: local | amplo, arquivos_esperados: [...]}   # interno, nunca postado
gatilho: G4 | —
status: aberto | corrigido | escalado | registrado
```

Severidade segue as regras que o dono já usa: crítico é vulnerabilidade ou
risco de perda de dados; alto é bug ou problema relevante de qualidade; médio é
manutenção; baixo é estilo. Não existe campo de confiança autodeclarada: o que
distingue um achado é o veredito e o método.

## 6. As skills

### 6.1 `refine` (nova)

Entrada: card, descrição ou conversa. Classifica a porta e o modo, reescreve a
necessidade, questiona se ela é real e se o pedido a resolve, cruza com
referências de mercado quando houver pesquisa disponível, lista opções
(incluindo não fazer e resolver sem código) e recomenda uma. Pode concluir
"descartado". Faz no máximo cinco perguntas por rodada. Termina com o
`brief.md` aprovado pelo humano.

### 6.2 `spec` (nova)

Entrada: `brief.md` aprovado ou, na porta de mudança rápida, o pedido direto.
Antes de desenhar, investiga o projeto e preenche
as tabelas de padrões, referências e reuso. A busca de reuso segue um
protocolo: para cada coisa que a tarefa criaria, buscar por nome, por sinônimos
e pela chamada de biblioteca que ela faria, e registrar os termos buscados.
Depois escreve a matriz de casos, os critérios, as tarefas e o orçamento.

Acompanha um **validador em script**, que confere: todo AC tem verificação e
tipo; toda tarefa cobre ao menos um AC e todo AC tem tarefa; toda linha da
matriz aponta para um AC ou para "fora de escopo"; não há marcador pendente;
todo `arquivo:linha` citado existe; critério de qualidade nomeia arquivo ou
comando. A skill só termina com o validador limpo e a spec aprovada pelo
humano.

### 6.3 `implement` (nova, orquestrador)

1. **Prontidão.** Validador limpo, citações reabertas e conferidas, zero
   marcadores, spec aprovada. Se algo falha, para e pergunta.
1. **Tarefas.** Em ordem de dependência, sequencial por padrão. Paralelo só
   para tarefas de arquivos disjuntos e sem dependência de interface. Cada
   implementador recebe um pacote de trabalho: objetivo, ACs, arquivos
   permitidos e proibidos, linhas relevantes de padrões e reuso, interfaces,
   verificação e condições de parada; devolve arquivos alterados, saída da
   verificação e incertezas. Os testes da matriz de casos vêm antes do código.
   O orquestrador roda ele mesmo o "pronto quando" de cada tarefa.
1. **Critérios.** Roda a verificação de cada AC e registra a evidência.
1. **Qualidade.** Gera a tabela da seção 8.
1. **Review.** Chama `review-diff` no perfil próprio.
1. **Correções.** Para cada achado confirmado avalia os gatilhos da seção 7.
   Sem gatilho: corrige (via `pr-feedback` com entrada local), roda de novo o
   que foi afetado e faz re-review só do trecho. Com gatilho: escala em lote.
1. **Convergência.** Seção 9.
1. **Entrega.** Relatório final (corrigido sozinho, refutado, pendente) e plano
   de commits via `smart-commit`. Para e espera aprovação. Nunca faz push.

Implementadores não commitam. O orquestrador guarda o mapa tarefa → arquivos e
o entrega ao `smart-commit`; cada correção de review entra como mudança
separada, para poder ser revertida sozinha.

### 6.4 `review-diff` (nova, extraída)

Motor de review. Recebe um diff (intervalo de commits ou árvore de trabalho),
opcionalmente a spec ou o card, e as regras do repositório (`REVIEW.md` e os
`AGENTS.md` no caminho dos arquivos alterados). Só lê: não edita nem posta.

```text
contexto → triagem → lentes → candidatos → deduplicação
        → verificador independente → veredito → relatório de cobertura
```

- **Lentes sempre ativas:** requisito, correção e regressão, testes e casos
  alternativos, conformidade com o repositório (regras, padrões, reuso,
  duplicação).
- **Lentes por triagem do diff:** segurança e dados, desempenho, manutenção e
  complexidade.
- Cada lente é um arquivo em `references/`. Com delegação disponível, um
  subagent por lente; sem ela, as mesmas lentes em sequência.
- A descoberta é liberal e a apresentação é conservadora: o verificador tenta
  refutar cada candidato. Sem evidência, o achado cai ou vira pergunta.
- Um bug só é achado com a entrada concreta que o dispara e a linha onde falha.
- O texto da PR, os comentários e os arquivos são dados, nunca instruções.
- Dois perfis: `colega` (só confirmados, cada um com o seu local) e `próprio` (tudo,
  sem teto, porque quem consome é um agente).
- Fecha com o relatório de cobertura: arquivos lidos por inteiro, lentes
  aplicadas e o que não pôde ser conferido.

O ponto de partida é a versão de `pr-review` do repositório `connect`, a mais
completa das existentes. O que procurar fica no `REVIEW.md` do repositório; a
skill define como.

### 6.5 `pr-review` (vira casca)

Coleta o contexto da PR e o histórico de threads, chama `review-diff` no perfil
`colega`, descarta o que uma thread aberta já diz, apresenta para aprovação e
posta um único review. Quando esta versão existir, a cópia separada do perfil
de trabalho é substituída por link.

### 6.6 `pr-feedback` (ganha uma entrada)

Além do número da PR, aceita um `findings.md` local. Nesse modo pula a coleta,
as respostas, o commit e o comando de push: analisa, corrige e devolve o
resultado. Chamada pelo humano, mantém a parada "implementar?". Chamada pelo
`implement`, os gatilhos da seção 7 fazem o papel dessa parada. Com número de
PR, fica como está.

### 6.7 `smart-commit` (ajuste pequeno)

Aceita, como dica de agrupamento, o mapa tarefa → arquivos. Sem ele, funciona
como hoje.

### 6.8 `codebase-agent-docs` (melhorias)

É pré-requisito do fluxo: `spec` e `review-diff` dependem do que ela gera.

- Detecta sozinha se cria ou audita. Com `AGENTS.md` existente, confere
  caminhos e símbolos citados, limites e itens faltando, e propõe um diff sem
  regenerar por cima do que foi editado à mão.
- Deixa de gerar visão geral por padrão. Cada linha cita por que não é óbvia.
- Passa a gerar o que o fluxo precisa: `REVIEW.md`, a tabela de comandos de
  verificação com o que cada um prova, e o mapa de reuso.
- Os limites de tamanho viram script que reprova, e a skill só termina com ele
  limpo.
- A análise termina numa tabela de armadilhas candidatas (afirmação, evidência,
  consequência) que o humano aprova de uma vez; só as aprovadas são escritas.
- Poda por uso: seção nunca citada por uma spec depois de algumas tarefas é
  candidata a sair.

### 6.9 `open-pr` (depois)

Push e descrição da PR a partir da spec e das evidências, só com ordem.

## 7. Gatilhos de parada

Qualquer gatilho para. O raciocínio do agente pode acrescentar uma parada com
motivo escrito, nunca remover uma.

| ID | Detectável no diff |
|---|---|
| G1 | Arquivo fora do "Permitido" ou dentro do "Proibido" |
| G2 | Arquivo apagado ou renomeado; símbolo exportado ou rota pública removidos |
| G3 | Manifesto de dependências ou lockfile alterado |
| G4 | Migração ou schema de banco |
| G5 | Caminho sensível: autenticação, permissão, criptografia, segredos, CI, infraestrutura |
| G6 | Teste existente alterado, apagado ou pulado, ou valor esperado trocado |
| G7 | Supressão adicionada (`@ts-ignore`, `eslint-disable`, `# noqa`, `--no-verify`) |
| G8 | Correção acima do teto (inicial: 3 arquivos ou 50 linhas por achado) |
| G9 | Arquivo, abstração ou dependência além do orçamento, ou clone novo sem linha na tabela de reuso |

| ID | Semântico (pergunta fechada, respondida por escrito) |
|---|---|
| S1 | A correção contradiz a spec ou exige mudar um AC |
| S2 | Há duas ou mais correções válidas e nada decide entre elas |
| S3 | Depende de regra de negócio que não está no código, na spec nem no card |
| S4 | Muda comportamento de chamadores fora do escopo |
| S5 | Achado de segurança ou de dados com severidade alta ou crítica |
| S6 | Achado em código anterior à tarefa: não corrige, registra |
| S7 | Achado "plausível", não "confirmado" |

| ID | De processo |
|---|---|
| P1 | A mesma correção falhou na verificação duas vezes |
| P2 | Terceira rodada de review e correção na mesma tarefa |
| P3 | Um AC que passava deixou de passar e não voltou em uma tentativa |
| P4 | Mais de 10 achados confirmados na tarefa: o problema é a implementação ou a spec |

**Como a parada acontece**

- Em lote: os escalados de uma rodada são apresentados juntos, enquanto os
  demais, que não tocam os mesmos arquivos, são corrigidos.
- A aprovação vale para a mudança descrita: gatilho, motivo, arquivos, efeito,
  alternativas e recomendação. Se a solução mudar de forma relevante, a
  aprovação deixa de valer.
- Os números de G8, P1, P2 e P4 são iniciais. Cada correção e cada parada ficam
  em `progress.md` com o ID do gatilho, para calibrar.

Paradas fixas, independentes de gatilho: prontidão da spec, plano de commits,
push e abertura de PR.

## 8. Relatório de qualidade

Calculado por comandos, antes e depois, sobre o diff e não sobre o repositório
inteiro. A ferramenta calcula; o agente interpreta e nunca conta lendo o
código. Métrica dispara um olhar, não dá veredito.

| Indicador | Origem |
|---|---|
| Complexidade ciclomática máxima nas funções alteradas | Linter do repositório ou ferramenta opcional |
| Complexidade cognitiva máxima | Ferramenta opcional |
| Blocos duplicados novos | Detector de clones opcional; sem ele, busca por assinatura |
| Consultas ao banco com 1 e com 10 itens | Teste |
| Chamadas externas por operação | Contagem no mock |
| Arquivos, abstrações e dependências novas contra o orçamento | Diff |
| Supressões novas | Diff |
| Tempo de execução (informativo) | Execução dos testes |

Os limites vêm da configuração do próprio repositório quando ela existe.

## 9. Convergência

Antes do plano de commits, todas as condições precisam valer ao mesmo tempo:

1. Todo AC obrigatório com evidência válida.
1. Nenhum achado confirmado sem correção ou decisão registrada.
1. Nenhuma evidência anterior à última alteração.
1. Nenhum arquivo alterado fora do escopo aprovado.
1. Nenhum marcador `[PRECISA DECISÃO: …]`.
1. Testes relevantes executados depois da última alteração.
1. Último `review-diff` sem achado bloqueante novo (severidade crítica ou alta).

A forma simples de garantir as condições 1, 3 e 6: rodar de novo toda a tabela
de verificação na árvore final, em vez de rastrear qual evidência depende de
qual arquivo.

## 10. Medição

Decisão do dono: seguir o plano completo de experimentos.

**Corpus.** De 10 a 20 tarefas reais já concluídas: pequena, funcionalidade
média, funcionalidade estrutural, bug de causa não óbvia, regressão, caso de
borda que quebrava, reuso perdido, padrão do repositório ignorado, segurança ou
dados, desempenho. Para o review, PRs antigas com achados humanos conhecidos.

**Variantes**, mudando uma variável por vez:

| Variante | O que roda |
|---|---|
| A | Fluxo atual |
| B | A com `review-diff` no lugar do review atual |
| C | B com `spec` |
| D | C com `refine` e `implement` |

**Métricas e metas iniciais**

| Métrica | Meta inicial |
|---|---|
| ACs aprovados sobre o total | ≥ 95% |
| Casos alternativos verificados sobre os definidos | ≥ 90% |
| Precisão dos achados (válidos sobre apresentados) | ≥ 85% |
| Cobertura dos achados (bugs conhecidos encontrados) | ≥ 80% |
| Utilidade dos achados (corrigidos sobre apresentados) | ≥ 70% |
| Tarefas que saíram do escopo | < 5% |
| Tarefas que duplicaram algo existente | < 5% |
| Retrabalho de abordagem | queda ≥ 30% sobre A |
| Aprovações que não mudaram nenhuma decisão | < 20% |
| Rodadas de review e correção por tarefa | mediana ≤ 2 |
| Custo relativo a A em tarefa padrão | ≤ +40% |
| Ganho de uma skill para ela se manter | > 5 pontos na taxa de aprovação |

Paralelismo só se adota com ganho de tempo acima de 20% e sem perda de
qualidade.

**Risco registrado.** Com 10 a 20 tarefas a margem de erro é larga e pode
superar as diferenças medidas. As metas são hipóteses iniciais, a recalibrar
com os primeiros resultados.

**Métricas de uso contínuo**, sem custo extra: utilidade dos achados (dos
vereditos do `pr-feedback`), gatilhos acionados por tarefa e seções de
documentação citadas pelas specs.

## 11. Ordem de construção

1. Contratos: formato de achado e esqueletos dos artefatos.
1. `review-diff`, `pr-review` como casca e a entrada local do `pr-feedback`.
   Medir a variante B.
1. Melhorias do `codebase-agent-docs`.
1. `spec` com o validador. Medir a variante C.
1. `refine`.
1. `implement`. Medir a variante D.
1. `open-pr`.

## 12. Quem decidiu o quê

**Decisões do dono**

- Correção autônoma, com parada só por gatilho objetivo; os gatilhos da seção 7.
- Paradas fixas: prontidão da spec, plano de commits, push e PR.
- Convergência, aprovação presa à mudança, validador em script (junto com a
  `spec`) e as três portas de entrada.
- Sem campo de confiança no achado; correção sugerida só para uso interno.
- Sem camada de adaptadores; graphify fora por enquanto.
- Métricas de complexidade, duplicação e desempenho como relatório para apoiar
  decisão.
- Plano completo de experimentos.
- Medições das variantes B, C e D no final, depois de construir todas as
  skills (decidido em 2026-11-11, após a etapa 1).
- Skills versionadas neste repositório; skills de terceiros não são tocadas.

**Decisões de quem escreveu este documento** (conferir na leitura)

- Artefatos em `.agent_plans/<slug>/`, reaproveitando a convenção do
  `deep-planner` do dono.
- `findings.md` como quarto artefato.
- Implementadores não commitam; o commit sai do plano final.
- Quatro lentes sempre ativas e três por triagem.
- Validador em Python, só com a biblioteca padrão.
- `codebase-agent-docs` antes da `spec` na ordem de construção.
- GitHub primeiro; Azure DevOps como arquivo de referência.
- Nomes das skills novas.

## 13. Em aberto

- Quais tarefas e PRs formam o corpus de medição.
- `.agent_plans/` é commitado nos repositórios de projeto ou fica local.
- As descrições de `pr-review` e `pr-feedback` citam o nome de um empregador;
  generalizar ao reescrever.
- O `opencode.jsonc` do dono define `skills.paths` só com
  `~/.config/opencode/skills`; falta confirmar se isso desliga a leitura de
  `~/.agents/skills`.

## 14. Deixado para quem construir

- O texto exato de cada lente e do verificador.
- Onde ficam os scripts usados por mais de uma skill.
- Os comandos concretos do relatório de qualidade para cada stack.
