# Lente: conformidade com o repositório

## Quando roda

Sempre.

## Como procurar

1. Para cada regra lida (`REVIEW.md`, `AGENTS.md` no caminho,
   `CONTRIBUTING.md`), confira as linhas alteradas que ela alcança.
1. Reuso: para cada função, classe, helper ou constante que o diff cria,
   busque no repositório inteiro, na versão do alvo:
   - pelo nome;
   - por sinônimos do que ela faz (por exemplo: slug, normalizar, formatar);
   - pelas chamadas de biblioteca que ela faz (`unicodedata.normalize`,
     `re.sub`, `datetime.strptime`…).

   Achou algo que já faz o mesmo: candidato, mesmo com nome e forma
   diferentes.
1. Duplicação: pegue a linha mais distinta de cada bloco novo e busque no
   repositório.
1. Padrão: compare com a funcionalidade parecida mais próxima no projeto
   (nome, camada, tratamento de erro, formato do teste).
1. Nome renomeado ou removido (classe, função, rota, variável de ambiente,
   comando): busque nos `.md` e em `docs/`. Texto que ficou errado é
   candidato.

## O que conta como evidência

A regra com `arquivo:linha` e a linha que a viola; ou o helper existente com
`arquivo:linha` e o equivalente novo; ou os termos buscados e o que voltou.

## Não é desta lente

Problema de segurança que uma regra também cobre: vai para segurança, com a
regra em `viola`.
