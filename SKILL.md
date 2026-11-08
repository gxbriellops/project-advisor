---
name: project-advisor
description: >-
  Analyzes codebases (structure, code, and documentation) and delivers a
  prioritized impact/effort table of features and refactors for Flutter,
  Next.js, and Python. Starts with scripts/project_summary.py instead of
  reading the repo. Optionally prototypes top ideas in isolated Orca Git
  worktrees; when the agent cannot create them autonomously, recommends
  concrete clicks in the Orca app (Add Repo, +, agent, split, Diff, Annotate
  AI Diff, Commit). After the table, can propose and execute a GitHub
  shipping scheme (branches, commits, PRs, issues) via the GitHub MCP already
  in this CLI — never asks the user to log in or install gh. Use when the
  user asks to analyze a project, recommend features, prioritize refactors,
  produce a roadmap, inspect architecture health, review TODOs/duplication/docs/CI,
  manage PRs/commits from the roadmap, or mentions project-advisor, análise
  de projeto, recomendações priorizadas, Orca worktrees, or esquema de PR.
type: workflow
lifecycle: active
version: "1.2.0"
---

# Project Advisor

Analisar estrutura, código e docs com o **mínimo de tokens**. Entregar recomendações priorizadas (features e refatorações). Prototipar no Orca e shipar no GitHub só quando o usuário pedir ou confirmar.

## Economia de tokens

Não ler o codebase inteiro. Não fazer glob amplo de `**/*.{ts,tsx,dart,py}`. Não abrir `node_modules`, `.next`, `build`, `dist`, `.dart_tool` ou `__pycache__`.

- O mapa do projeto vem do script, não de dezenas de leituras.
- Depois do JSON, ler no máximo ~12 arquivos: `key_files` + 3–8 alvos em `hotspots` / `suggested_reads`.
- Abrir referências sob demanda: só a stack detectada em [references/analysis-patterns.md](references/analysis-patterns.md). Só [references/orca-integration.md](references/orca-integration.md) se for prototipar. Só [references/github-integration.md](references/github-integration.md) se for esquema/execução de PR, commit ou issue.
- Não colar arquivos inteiros na resposta. Citar evidência curta (caminho + sintoma).
- Parar de ler quando a tabela de recomendações já tiver 5–9 itens com evidência.

## Fluxo

Copiar e ir marcando:

```
- [ ] 1. Resumo estrutural (script)
- [ ] 2. Leitura seletiva
- [ ] 3. Recomendações priorizadas
- [ ] 4. Orca worktrees (opcional)
- [ ] 5. GitHub: PRs / commits (opcional)
```

### 1. Resumo estrutural (obrigatório, antes de ler código)

Resolver o diretório desta skill (pasta do `SKILL.md` carregado). Executar:

```bash
python3 <skill_dir>/scripts/project_summary.py [PROJECT_ROOT]
```

`PROJECT_ROOT` omite = cwd do workspace. Stdlib only, Python 3.9+. Se `python3` falhar, tentar `python`.

O JSON traz tipo (`flutter` | `nextjs` | `python` | `generic` ou misto), contagens, linhas aproximadas, arquivos-chave, hotspots, TODOs e `read_guidance`. **Obedecer `do_not_read_all`.** Não reimplementar o walker no agente.

Se o script falhar, relatar o erro e só então cair para uma amostragem mínima (README + manifesto: `pubspec.yaml` / `package.json` / `pyproject.toml`) — ainda sem varrer o repo.

### 2. Leitura seletiva

Ler nesta ordem, parando cedo:

1. Manifesto e README (`key_files`).
2. Entradas (`lib/main.dart`, `app/layout.tsx`, `app/page.tsx`, pacote Python).
3. 3–8 hotspots (arquivos grandes) e 1–2 testes/CI se existirem.
4. A seção da stack em [references/analysis-patterns.md](references/analysis-patterns.md), mais a seção geral.

Para Next.js, não confiar na memória de APIs: se `node_modules/next/dist/docs/` existir, consultar o guia local antes de recomendar APIs. Para Flutter, cruzar `pubspec.yaml` (state, i18n, assets). Para Python, cruzar empacotamento, type hints e testes.

### 3. Recomendações priorizadas

Saída padrão — curta, em português, com evidência real do repo:

1. **Tipo e recorte** — uma linha: stack, escala (arquivos/linhas), o que foi lido vs ignorado.
2. **Achados** — 3–6 bullets (arquitetura, DX, riscos). Sem preâmbulo.
3. **Tabela** (5–9 linhas, ordenada por impacto↓ e esforço↑):

```markdown
| Pri | Tipo | Recomendação | Impacto | Esforço | Evidência |
| --- | --- | --- | --- | --- | --- |
| 1 | feature | … | alto | S | `path`: sintoma |
```

`Tipo`: `feature` | `refactor` | `perf` | `tests` | `docs` | `dx`. Impacto `alto|médio|baixo`. Esforço `S|M|L`.

4. **Não fazer agora** — 1–3 itens caros ou especulativos.
5. **Próximo passo** — uma ação concreta. Se o usuário quiser prototipar, oferecer Orca (passo 4). Se quiser shipar (PRs, commits, issues), oferecer o esquema GitHub (passo 5). Não criar worktrees, commits ou PRs sem pedido/confirmação. Não sugerir login no GitHub.

Não inventar features que o código já cobre. Não recomendar reescrita total se um refactor local resolve.

### 4. Orca (opcional)

Só com pedido explícito ou confirmação. Carregar [references/orca-integration.md](references/orca-integration.md) e as skills oficiais `orca-cli` e `orchestration`.

Orca é worktree-native: **uma ideia = um worktree = um agente**, em paralelo, sem pisar nos arquivos uns dos outros. Fluxo oficial: *add repo → worktree → agent → split → diff → ship*.

**Autonomia vs app**

1. Sondar `ORCA status --json`. Runtime pronto → tentar CLI (`worktree create --agent --prompt`).
2. Se o CLI criar os worktrees, relatar nomes/ids e o que o usuário ainda precisa fazer **no app** (split, Diff, Annotate AI Diff, Commit/Push). Review e ship **não** são autônomos.
3. Se o CLI falhar (Orca fechado, repo não cadastrado, agente sem login, `Needs You`, sandbox, repo ambíguo): **não fingir sucesso e não dirigir a GUI do Orca com Computer Use**. Entregar **Ações no app Orca** — cliques, nomes, prompts prontos para colar (ver o reference).
4. Linux desktop: nunca o binário `orca` (leitor de tela). Não usar `git worktree add` cru.

Máx. 3 worktrees em paralelo. O restante fica na tabela.

### 5. GitHub: PRs, commits, issues (opcional)

Só com pedido explícito ou confirmação para **shipar** as recomendações (esquema de branches/PRs, commits, issues). Carregar [references/github-integration.md](references/github-integration.md).

O namespace MCP `github` já está nesta CLI. **Não** sugerir login, `gh auth login`, instalar GitHub CLI, PAT ou token. `get_me` confirma a conta; se devolver URL OAuth, mostrar só esse link uma vez. `gh` ausente não é problema.

Não tratar “revisa este PR” ou “escreve a mensagem de commit do staging” como este passo — isso não é advisor. O passo 5 é o **esquema** pós-tabela: quais recomendações viram quais branches/PRs/issues, e executar no GitHub quando pedirem.

Uma recomendação independente = um PR (máx. 3 em voo). Commits locais seguem a user rule de git (só com pedido). Abrir PR via `create_pull_request` depois do push, sem duplicar PRs do mesmo head.

## Princípios

- Script primeiro, código depois, recomendações por último; Orca e GitHub só se couber.
- Preferir evidência do resumo (contagens, hotspots, TODOs, ausência de testes/CI) a adivinhar.
- Uma recomendação sem caminho de arquivo (ou motivo estrutural claro) não entra na tabela.
- Se o projeto for misto, uma tabela só, coluna/evidência dizendo a stack do item.
