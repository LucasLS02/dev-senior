---
name: track
description: >-
  Use quando for preciso vincular uma spec aprovada ao acompanhamento de projeto ou
  reconciliar andamento, impedimentos e PR: "sincronizar o card", "track", "/track".
metadata:
  opencode/slash: "true"
---

# Track

Reconcilie os artefatos da pasta `.agent_plans/<pasta>/` com o quadro configurado.
Leia `references/modelo-tracker.md` e a referência da ferramenta configurada.
O remoto é a fonte da verdade; `tracker.md` é cache e log. Não publique
`findings.md` nem o campo correção.

## Entrada e configuração

Receba a pasta e a origem da chamada (manual, refine, implement ou open-pr).
Leia `AGENTS.md` da raiz. Sem `## Acompanhamento de projeto`, diga que não há
acompanhamento e pare sem chamada remota. Exija ferramenta, acesso, projeto,
tipo da spec e mapeamento dos status em andamento e em review; se faltar algo
ou o acesso não estiver disponível, pare e explique, sem fallback. Leia somente
a referência correspondente. Se uma capacidade não estiver verificada ou não
existir, pare antes de precisar dela.

Antes de confirmar a presença da seção, não execute comandos da ferramenta,
nem mesmo `--help`, e não consulte MCP. A autorização para publicar não cria
configuração inexistente.

Na chamada de `refine`, se houver card de origem, registre somente seu vínculo
local como candidato no `tracker.md`; nenhuma escrita remota. O vínculo efetivo
exige confirmação na primeira publicação. Sem card de origem, não crie nada.

## Planejar

1. Leia `spec.md`, `brief.md`, `progress.md`, `pr.md` e `tracker.md` quando
   existirem. Se houver `tracker.md`, rode `python3 <pasta-da-skill>/scripts/check_track.py validate <tracker>`; erro impede publicação. Só publique com `Status: aprovado` na spec e prontidão concluída.
2. Identifique a tarefa pelo projeto remoto, identidade canônica do repositório
   e nome da pasta. Use o marcador definido na referência; nunca dependa só do
   nome da pasta. Procure-o no projeto antes de criar, inclusive sem cache. Se
   houver múltiplos resultados ou busca incompleta, pare e peça resolução. Uma
   busca vazia não prova que não existe item: antes de criar, peça que o humano
   verifique a ausência no quadro, inclusive em retomada sem estado local.
3. Leia o item, a descrição, status, impedimentos e todos os comentários. Uma
   resposta incerta de criação não autoriza outra criação: registre a incerteza,
   pesquise e peça verificação humana antes de repetir. Não confunda ausência em
   busca eventualmente consistente com prova de inexistência.
4. Card comum de origem é a própria story; confirme o vínculo antes de usar.
   Um épico de origem é o pai: procure a story filha pelo marcador e, se ausente
   após verificação humana, planeje sua criação sob esse pai. Para recuperação,
   acrescente o marcador no card de origem vinculado, com confirmação específica
   para editar a descrição; preserve os demais marcadores existentes. Se o
   marcador ainda não existir, guarde a URL e não crie outro item automaticamente.
   Mapeie `spec` a uma story: objetivo, entendimento, todos ACs e tarefas como
   checklist. Um brief só vira épico se o mapa o autorizar ou a origem já for
   épico. Nunca crie subtarefas para as tarefas. Preserve descrição humana e
   altere apenas a seção `Critérios e tarefas — sincronizado pelo fluxo`, cercada
   pelos delimitadores da referência. Se várias tarefas compartilham o card,
   mantenha um bloco delimitado pelo marcador para cada tarefa e preserve todos
   os demais blocos. Compare o hash anterior do próprio bloco com o remoto;
   se mudou, mostre diferença. Sem hash e seção diferente, trate como conflito.
5. Rode `python3 <pasta-da-skill>/scripts/check_track.py events <spec> <progress>`.
   Só passe `--converged` depois de `check_run.py converge <progress> <spec> .`
   sair limpo na árvore atual. Para deduplicar, passe `--comments` com JSON de
   textos completos lidos do remoto e `--marker <marcador>`. Não infira entrega
   de uma tabela incompleta.
   Para comparar os estados, use `check_track.py diff <json>`: o arquivo contém
   `desired` com `section`, `status`, `blocked` (booleano), `events` e `marker`;
   `remote` com `section`, `status`, `blocked` e `comments`; e `previous_hash`
   (texto ou null). `conflito` exige apresentação da diferença e confirmação.
   Para PR, confirme a URL por `gh pr view <branch> --json url`; `pr.md` não
   prova publicação. S1, S3 e dependência externa declarada viram impedimento;
   outras decisões só entram na entrega se mudaram o resultado.
6. Monte lista de operações com item, texto exato, status e links. Comentários
   são por evento: início, impedimento, decisão, entrega e, se necessário, PR;
   terminam em `— fluxo: <marcador> <evento>` para deduplicar por marcador e evento,
   mesmo com duas tarefas no mesmo card. Use linguagem de produto,
   sem caminhos, `arquivo:linha`, IDs internos, segredos ou campos internos.
   Traduza escaladas usando efeito, alternativas e recomendação. Rode
   `python3 <pasta-da-skill>/scripts/check_track.py leak <arquivo>` em cada
   texto enviado; rejeite vazamentos e confira também manualmente.

## Confirmação e execução

Apresente o plano completo e peça confirmação antes da primeira publicação,
incluindo modelos de comentários futuros. Registre a autorização de rotina para
esta pasta, projeto e repositório somente após o aceite explícito. Ela cobre
status, impedimento, decisão, entrega e link da PR; não cobre criação, vínculo
ou edição da descrição, que exigem confirmação específica sempre. Chamada
manual `/track` exige confirmação de todas as operações. Sem registro confiável
da autorização, peça novamente; recuperá-la do card não é permitido.

Depois de cada operação confirmada, releia o remoto, mostre o resultado e acrescente
uma entrada no log local. Grave hash e evento apenas após verificar o sucesso.
Em falha ou resultado incerto, pare; registre a incerteza e consulte o remoto
antes de retomar. Não invente resultado e não execute operações subsequentes
dependentes de uma escrita não confirmada.
