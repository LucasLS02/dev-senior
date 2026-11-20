# GitHub Issues com `gh`

Fonte: https://cli.github.com/manual/gh_issue e
https://cli.github.com/manual/gh_help_reference. Configure projeto como
`owner/repo`, rótulos de status e `bloqueado`; eles precisam existir.

- Marcador: `fluxo-` + SHA-256 hexadecimal dos bytes UTF-8 de
  `github.com/owner/repo` em minúsculas, `\n`, e nome da pasta exatamente como
  está no disco. Guarde como comentário HTML `<!-- fluxo: <marcador> -->` na
  descrição, fora da seção editável. Não publique o caminho local.
- Consulte `gh issue list -R owner/repo --state all --search '"<marcador>" in:body' --json number,url,body --limit 100` e confirme o marcador exato em cada corpo. Busca pode atrasar; uma criação incerta exige verificação humana, nunca repetição automática. Se houver 100 resultados, paginação incompleta ou erro, pare.
- Leia `gh issue view <n> -R owner/repo --json number,url,body,labels,comments` e verifique que todos os comentários foram obtidos; se não for possível, pare.
- Crie com `gh issue create -R owner/repo --title <título> --body-file <arquivo>`; pai, quando suportado, com `--parent <n>`. Leia novamente o item retornado.
- Delimite o bloco da tarefa com `<!-- fluxo:inicio <marcador> -->` e `<!-- fluxo:fim <marcador> -->`; preserve os blocos das demais tarefas. Envie o corpo inteiro preservando tudo fora dos limites com `gh issue edit <n> -R owner/repo --body-file <arquivo>` após confirmação específica. Acrescente marcadores de tarefas vinculadas ao card sem apagar os existentes.
- Comente com `gh issue comment <n> -R owner/repo --body-file <arquivo>`.
- Mude status e impedimento com `gh issue edit <n> -R owner/repo --add-label <rótulo> --remove-label <rótulo>`. Consulte rótulos antes; não remova rótulos humanos não pertencentes ao mapa configurado.
- Para relação de bloqueio entre issues use `gh issue edit <n> -R owner/repo --add-blocked-by <n>`, somente se disponível na versão instalada; confirme com `gh issue edit --help`. Projetos GitHub ficam fora desta versão.
