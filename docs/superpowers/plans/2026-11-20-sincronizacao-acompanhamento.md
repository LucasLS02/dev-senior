# Plano de implementação: sincronização de acompanhamento

> Execução: aplicar `superpowers:executing-plans` ou `superpowers:subagent-driven-development` após revisão deste plano.

**Objetivo:** transformar uma spec aprovada em acompanhamento remoto e reconciliar seu progresso sem duplicações.

**Arquitetura:** `track` calcula a diferença entre artefatos locais e estado remoto; o agente apresenta e executa as operações permitidas usando referências específicas de cada ferramenta. `tracker.md` é cache e log; o remoto é consultado a cada execução.

**Tecnologia:** skills em Markdown, Python padrão, testes `unittest` e avaliações shell.

**Desenho:** `docs/2026-11-20-sincronizacao-acompanhamento-design.md`, especialmente §§5–14, que prevalecem quanto ao comportamento pretendido.

## Restrições globais

- Português; nenhuma publicação de `findings.md`, campo correção, caminhos, credenciais ou IDs internos.
- Sem configuração na raiz, nenhuma alteração de comportamento; configuração incompleta ou acesso indisponível encerra sem fallback.
- Confirmação explícita para criação, vínculo, edição de descrição e `/track` manual; a primeira confirmação cobre apenas atualizações de rotina da mesma pasta.
- Não instalar ferramentas, criar adaptadores, subtarefas por tarefa, integração de merge ou sincronização de `pr-feedback`.
- Não executar commits, push ou escritas em serviços durante a implementação sem autorização específica.

## Focos de revisão

1. Estado local ausente ou desatualizado: busca remota antes de criar e deduplicação por marcador e rodapé.
2. Edição humana da seção sincronizada: apresentar diferença e pedir confirmação, inclusive sem hash anterior.
3. Falha parcial ou resposta remota ambígua: registrar somente operações confirmadas e consultar novamente antes de repetir; nunca presumir sucesso.
4. Aprovação ausente ou de outra pasta: nenhuma atualização de rotina; aprovações de descrição e criação continuam individuais.
5. Conteúdo sensível ou estado incompleto: bloquear publicação com vazamento; não declarar entrega antes de convergência e resolução das escaladas.

## Tarefa 1: contrato local e cálculo

**Arquivos:** criar `skills/track/references/modelo-tracker.md`, `skills/track/scripts/check_track.py`, `tests/check_track_test.py`.

- [x] Definir no modelo seções para configuração, marcador, URLs, confirmação por pasta, hash da seção, eventos e log cumulativo; definir IDs estáveis para escaladas e eventos. Registrar somente confirmações efetivamente obtidas.
- [x] Escrever testes de formato inválido, ausência de estado local, spec não aprovada, prontidão, tarefas concluídas, escalada pendente e decidida, AC manual e convergência. Fixar que S1, S3 e dependência declarada de terceiro são impedimentos; outros gatilhos não são automaticamente impedimentos.
- [x] Executar `python3 -m unittest discover -s tests -p 'check_track_test.py'` e observar falha antes da implementação.
- [x] Implementar interface CLI documentada no próprio script para validar estado, calcular eventos locais e verificar texto de saída usando a regex `LEAK` de `skills/open-pr/scripts/check_pr.py`; receber estado remoto explicitamente e não realizar chamadas de rede. Rejeitar entradas incompletas sem assumir sucesso.
- [x] Acrescentar testes de múltiplas escaladas, retomada, alterações manuais da seção com e sem hash e vazamentos; executar o comando acima até passar.

## Tarefa 2: skill e referências de ferramentas

**Arquivos:** criar `skills/track/SKILL.md`, `skills/track/references/github.md`, `jira.md`, `monday.md`, `azure-boards.md`, `tests/track_text_test.py`.

- [x] Escrever testes do contrato textual: configuração ausente ou incompleta, confirmação por operação, busca por marcador, leitura remota antes de comparar, preservação do conteúdo humano, deduplicação de comentários e retomada após falha parcial.
- [x] Executar `python3 -m unittest discover -s tests -p 'track_text_test.py'` e observar falha.
- [x] Documentar o procedimento de reconciliação, plano com texto exato, confirmação, execução, verificação e log. Especificar que a autorização inicial não dispensa confirmação de edição de checklist na descrição. Não registrar nem enviar texto reprovado por `LEAK`.
- [x] Documentar capacidades e comandos verificados para GitHub Issues; para Jira, monday e Azure Boards verificar comandos e recursos nas ferramentas ou documentação oficial, identificando explicitamente lacunas não verificadas e interrompendo operações sem suporte comprovado. Definir representação de marcador, checklist e impedimento por ferramenta.
- [x] Executar os testes textuais e do cálculo até passarem.

## Tarefa 3: integrar o fluxo existente

**Arquivos:** modificar `skills/refine/SKILL.md`, `skills/implement/SKILL.md`, `skills/implement/references/modelo-progress.md`, `skills/open-pr/SKILL.md`, `skills/codebase-agent-docs/references/templates.md`; testes correspondentes em `tests/`.

- [x] Adicionar testes para vínculo local de origem, chamada condicional em prontidão, escalada, decisão, entrega e após criação da PR, além da ausência de efeito sem configuração.
- [x] Adicionar testes do formato completo de escalada com `Decisão: pendente` ou texto decidido, preservando a compatibilidade de `check_run.py` com progressos existentes.
- [x] Executar os testes alterados e observar falhas; fazer as mudanças mínimas nas skills e no modelo, sem alterar as demais paradas do fluxo.
- [x] Executar `python3 -m unittest discover -s tests -p '*_test.py'`; corrigir regressões sem enfraquecer verificações existentes.

## Tarefa 4: permissões e documentação

**Arquivos:** modificar `permissions/rules.py`, `tests/permissions_test.py`, `README.md`, `docs/2026-11-10-fluxo-de-skills-design.md`.

- [x] Testar que os comandos de escrita indicados na §13 do desenho pedem aprovação, sem modificar a política de leitura; executar o teste e observar falha.
- [x] Acrescentar regras específicas de escrita e executar `python3 -m unittest discover -s tests -p 'permissions_test.py'` até passar.
- [x] Atualizar o fluxo, os contratos e a arquitetura documentada, incluindo os limites da aprovação e os provedores efetivamente verificados.

## Tarefa 5: avaliação integrada e revisão

**Arquivos:** criar `tests/track.eval.sh` e fixtures necessárias em `tests/`.

- [x] Criar avaliação com `gh` falso persistente que registra operações e simula leitura de itens e comentários. Cobrir `criar`, `vincular`, `repetir`, `sem-estado`, `escalada` e `sem-config`; acrescentar falha parcial, edição humana e recusa de confirmação.
- [x] Verificar as metas da §14: zero duplicatas, 100% de ACs e tarefas, zero vazamentos e escritas sem confirmação, e até três comentários sem escalada. A avaliação deve verificar estado remoto simulado, não apenas comandos emitidos.
- [x] Executar `python3 -m unittest discover -s tests -p '*_test.py'`, `bash tests/check-review-run.test.sh` e os modos da nova avaliação; registrar comandos, resultados e eventuais limitações de acesso real.
- [x] Revisar o diff contra o desenho e os cinco focos acima; corrigir achados e repetir verificações afetadas. Entregar evidências e plano de commits para aprovação.

## Pontos a resolver durante a implementação

- O marcador baseado apenas no nome da pasta pode colidir entre repositórios no mesmo projeto remoto: definir uma identidade estável com escopo do repositório, testando colisões e portabilidade entre máquinas antes de publicar.
- Confirmar como representar aprovação persistente e distingui-la de estado remoto recuperado; perda do `tracker.md` não deve recriar autorização.
- Um `gh` falso sozinho não executa instruções de uma skill: a avaliação integrada deve usar o mecanismo de agente das avaliações existentes e inspecionar o estado do falso, além dos testes determinísticos do script.
