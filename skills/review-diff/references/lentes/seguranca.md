# Lente: segurança e dados

## Quando roda

Pela triagem do `SKILL.md`.

## Como procurar

1. Siga cada entrada externa (parâmetro, corpo, cabeçalho, arquivo, variável de
   ambiente, retorno de serviço) até onde ela é usada.
1. Consultas: parâmetro em vez de interpolação; filtro de tenant ou de dono
   quando o dado é de um cliente.
1. Dado pessoal ou credencial que o diff adiciona: busque as saídas em todo o
   repositório (log, `repr` ou `str`, resposta de API, dump de objeto inteiro,
   mensagem de erro, arquivo exportado).
1. Autenticação e permissão: rota ou função nova sem a checagem que as
   vizinhas têm.
1. Caminho de arquivo vindo de fora (travessia com `..`); comando de shell
   montado com texto de fora.
1. Migração: busque no código e nos testes cada tabela ou coluna apagada ou
   renomeada.

## O que conta como evidência

A linha de origem e a linha de destino, com a entrada concreta que explora
(por exemplo, `status = "x' OR '1'='1"`).

## Não é desta lente

Regra de segurança violada sem caminho explorável: vai para conformidade.
