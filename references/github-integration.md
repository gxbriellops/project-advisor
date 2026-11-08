# Integração GitHub

Ler este arquivo **somente** quando o usuário pedir (ou confirmar) o esquema de ship: branches, commits, PRs, issues. Não substitui as user rules de git commit / pull request.

O MCP `github` já está nesta CLI. Fonte de verdade: tools do namespace `github`. Preferir MCP a `gh`. Não instalar GitHub CLI. Não pedir token, PAT, SSH key nem `gh auth login`.

## Não sugerir login

1. Chamar `get_me` (sem argumentos) para saber o usuário autenticado.
2. Se voltar perfil (`login`, `id`) → seguir. Nunca escrever “faça login no GitHub”, “autorize o MCP” ou “rode `gh auth login`” no passo de análise ou no próximo passo.
3. Se a tool devolver **URL OAuth** (`github.com/login/oauth/authorize…`): mostrar **só esse link uma vez**, pedir para autorizar no browser, e retry `get_me`. Sem tutorial, sem instalar nada, sem plano B de token.
4. Se `get_me` falhar por outro motivo: relatar o erro da tool. Não inventar login.

`gh` ausente no PATH é normal. Não é bloqueio e não vira sugestão de install.

## Identidade do repo

Do checkout local, uma vez:

```bash
git remote get-url origin
git branch --show-current
git status -sb
```

Extrair `owner` / `repo` do remote (`github.com/owner/repo.git`). Sem remote GitHub, o esquema fica local (branches/commits) e PRs não são criados — dizer isso em uma linha, sem pedir para o usuário “conectar o GitHub”.

## Esquema (obrigatório antes de executar)

Depois da tabela do passo 3, montar o plano. Uma recomendação = um PR, salvo dependência explícita (agrupar e dizer por quê). Máx. 3 PRs em voo; o resto fica backlog na tabela.

```markdown
### Esquema GitHub
| Rec | Branch | Commits (local) | PR | Issue |
| --- | --- | --- | --- | --- |
| P1 | feat/<slug> | 1, msg focada no porquê | título + body com evidência | só se o usuário quiser tracking |
```

- Branch: `feat/` | `fix/` | `refactor/` + slug curto da linha da tabela. Base = default do repo (`main`/`master` via `list_branches` ou `origin/HEAD`).
- Commits: só no worktree/checkout em que a mudança foi feita. Seguir a user rule de git commit (status + diff + log, HEREDOC, só quando o usuário pediu commit). Não usar `create_or_update_file` / `push_files` para commit do workspace local.
- PR: título no mesmo espírito do commit (porquê). Body: 1–3 bullets da evidência + Test plan. Head = branch da rec; base = default.
- Issue: opcional. Abrir só com pedido. Ligar ao PR no body (`Fixes #n` se for o caso).

Não abrir PR vazio. Não force-push. Não mergear sem pedido.

## O que o agente faz sozinho (MCP)

`--` abaixo são nomes de tools do namespace `github`. Resolver `owner`/`repo` antes.

| Intenção | Tool | Notas |
| --- | --- | --- |
| Quem está autenticado | `get_me` | Sempre primeiro neste passo |
| Branches remotas | `list_branches` | Default / existência do slug |
| Criar branch remota | `create_branch` | Só se o fluxo for 100% remoto; no workspace local preferir `git checkout -b` + push |
| PRs abertos | `list_pull_requests` | Evitar duplicata (mesmo head) |
| Abrir PR | `create_pull_request` | `title`, `head`, `base`, `body`; `draft: true` se o usuário não pediu review ainda |
| Ler PR | `pull_request_read` | `method`: `get` / `get_diff` / `get_files` / `get_commits` / `get_status` |
| Atualizar PR | `update_pull_request` | Título, body, draft, reviewers |
| Sync com a base | `update_pull_request_branch` | Sem force |
| Issues | `list_issues` / `issue_read` / `issue_write` | `create` só com pedido |
| Commits no remoto | `list_commits` | Auditoria; commits novos continuam no git local |

`search_pull_requests` / `search_issues` quando o filtro for autor/texto, não para listar o repo inteiro.

## Commits locais vs GitHub

| Fazer | Não fazer |
| --- | --- |
| `git status` / `git diff` / `git log` no checkout | Inventar histórico |
| Commit só com pedido explícito (user rule) | `git commit` no meio da análise |
| `git push -u origin HEAD` só com pedido de PR/push | Push `--force` em `main`/`master` |
| `create_pull_request` depois do push | Abrir PR antes da branch existir no remoto |
| Um PR por recomendação independente | Um PR gigante “todas as P1–P9” sem pedido |

Se o protótipo está num worktree Orca: commit/push **nesse** worktree. O passo GitHub não mistura diffs de worktrees diferentes no mesmo PR.

## Sequência no Project Advisor

1. Tabela pronta (passo 3). Pedido ou confirmação para o esquema.
2. `get_me` → remote `owner/repo` → `list_pull_requests` (duplicatas) → `list_branches`.
3. Publicar a tabela **Esquema GitHub**. Parar se o usuário só queria o plano.
4. Se pediu executar: branch local → commits (se pediu) → push → `create_pull_request`. Relatar URLs.
5. Sucesso parcial: o que já existe no GitHub + o que falta (push, review, merge). Sem “agora faça login”.

## Fora de escopo desta skill

- Review de um PR alheio (“olha o diff e acha bugs”) → não é project-advisor.
- Só mensagem de commit do staging → não é project-advisor.
- Esses pedidos não justificam carregar este arquivo.
