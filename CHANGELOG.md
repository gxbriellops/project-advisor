# Changelog

## 1.2.0 — 2026-11-08

- Passo 5: esquema de ship no GitHub (branches, commits, PRs, issues) via MCP `github`.
- Não sugere login, `gh auth login`, install do GitHub CLI nem token; `get_me` e, se preciso, um único link OAuth.
- Review de PR alheio e “mensagem de commit do staging” continuam fora desta skill.

## 1.1.0 — 2026-11-08

- Alinha o passo Orca ao fluxo oficial *add → worktree → agent → split → diff → ship*.
- Sonda `status --json` e tenta o CLI; se não for autônomo, recomenda cliques no app (Add Repo, +, Needs You, Annotate AI Diff, Commit/Push).
- Não usa Computer Use na GUI do Orca nem finge worktree criado quando o runtime/repo/agente bloqueia.

## 1.0.0 — 2026-11-08

- Fluxo progressivo: `scripts/project_summary.py` → leitura seletiva → tabela impacto/esforço → Orca opcional.
- Detecção automática de Flutter, Next.js, Python (ou genérico) com JSON compacto, hotspots, TODOs e `do_not_read_all`.
- Padrões de análise por stack e guia de worktrees isolados (`orca-cli` + `orchestration`).
- Evals de qualidade e de trigger com prompts reais, sem placeholders.
