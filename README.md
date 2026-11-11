# dev-senior

Skills pessoais para o fluxo de desenvolvimento com agentes: refinar a
necessidade, especificar, implementar, revisar, tratar o review e commitar.
Funcionam em qualquer ferramenta que leia `SKILL.md` (Claude Code, Codex,
OpenCode).

## Estrutura

```text
skills/<nome>/SKILL.md   uma pasta por skill, autocontida
docs/                    desenho do fluxo e decisões
install.sh               liga as skills nas pastas das ferramentas
tests/                   conferência do install.sh
```

## Instalação

```bash
./install.sh
```

Cria um link para cada skill em `~/.agents/skills`, `~/.claude/skills` e
`~/.claude-work/skills`, nas ferramentas que existirem na máquina. Uma pasta
real com o mesmo nome nunca é sobrescrita: o script avisa e segue.

Este repositório é a fonte única. Edite as skills aqui, nunca nas pastas das
ferramentas.

## Desenho

O fluxo completo, os contratos entre as skills e as decisões tomadas estão em
[docs/2026-11-10-fluxo-de-skills-design.md](docs/2026-11-10-fluxo-de-skills-design.md).
