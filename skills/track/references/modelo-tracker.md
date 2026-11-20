# Estado local de acompanhamento

`tracker.md` vive ao lado da spec, é cache e log, nunca prova o estado remoto.
Não guarde segredos. Ausência ou perda do arquivo não concede autorização.

```markdown
# Acompanhamento
## Contexto
- Ferramenta: GitHub
- Projeto: owner/repo
- Repositório: github.com/owner/repo
- Pasta: exemplo
- Marcador: fluxo-<hash>
## Vínculos
- Origem candidata: —
- Épico: —
- Story: <chave e URL, ou —>
## Autorização
- Rotina: concedida | não concedida
- Escopo: <repositório, projeto e pasta>
- Evidência: <data e referência à confirmação explícita>
## Estado observado
- Hash da seção: <sha256 ou —>
- Status: <valor ou —>
- Impedimentos: <IDs ou —>
- Eventos: <rodapés observados ou —>
- PR: <URL ou —>
## Log
- <data>: <operação verificada ou resultado incerto, sem segredos>
```

Só acrescente ao log. Identifique escaladas por número estável alocado no
`progress.md`; não reutilize números. O hash é SHA-256 do texto completo da
seção, incluindo delimitadores. Atualize-o apenas depois de reler a escrita.
