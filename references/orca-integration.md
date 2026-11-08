# Integração Orca

Ler este arquivo **somente** quando o usuário pedir (ou confirmar) prototipar recomendações. Não substitui as skills oficiais. Fonte: [Worktrees](https://www.onorca.dev/docs/model/worktrees), [first session](https://www.onorca.dev/docs/first-session), [Agents & sessions](https://www.onorca.dev/docs/model/agents-sessions), [CLI](https://www.onorca.dev/docs/cli/reference), [Orchestration](https://www.onorca.dev/docs/cli/orchestration), [Annotate AI Diff](https://www.onorca.dev/docs/review/annotate-ai-diff), [Commit & push](https://www.onorca.dev/docs/review/commit-push).

## Skills oficiais

1. **`orca-cli`** — worktrees, comentários, terminais, `agent launch`. Resolver o executável **como essa skill manda** (`ORCA skills get orca-cli`).
2. **`orchestration`** — workers com retorno ao coordenador. Só se o usuário quiser relatório unificado. Requer runtime (`ORCA status --json`) e, no app, Settings → Experimental → Orchestration se o CLI recusar.

Handoff sem retorno (“abre outro agente e segue”) = `orca-cli`. Supervisão / “me avisa quando terminar” = `orchestration`. Não reinventar os guias versionados.

## Melhor forma (docs)

Orca não é “mais um terminal”: cada tarefa ganha um git worktree isolado. Agentes em paralelo **nunca** compartilham working tree.

Fluxo canônico (*add → worktree → agent → split → diff → ship*):

1. Repo cadastrado no Orca (base ref, em geral `origin/main`).
2. Um worktree por ideia (nome curto, start-from = base ref, agente no launcher).
3. Até 3 agentes ao mesmo tempo; arrastar abas para split e acompanhar.
4. Quando idle: Diff contra o start-from → Annotate AI Diff → **Send to agent** em lote (não comentário a comentário).
5. Source Control: stage hunk → Commit → Push. Sem force-push silencioso. Perdedores: delete do worktree (confirmação no app).

Worktree = sandbox. O Orca já lança agentes em autonomia plena (equivalente a skip-permissions / yolo). Isolamento é o checkout, não o prompt de permissão.

Deps/secrets não vão no git: configurar **Worktree Shared Paths** (Settings → Repository) ou `worktree.sharedDirectories` no `orca.yaml` para `node_modules`; `.worktreeinclude` na raiz para copiar `.env` / `.env.local` (não symlink). Sem isso o protótipo quebra no `npm install` / Flutter pub.

## Resolver o CLI

Placeholder `ORCA` = binário escolhido uma vez:

- `ORCA_CLI_COMMAND` → esse valor.
- Linux **fora** de terminal gerenciado → `orca-ide`. **Nunca** `orca` no desktop (GNOME Orca / leitor de tela).
- Senão → `orca`.

Falha do binário: relatar e ir para [Ações no app](#acoes-no-app-orca). Não cair para outro executável. `runtime_access_denied`: repetir com permissão elevada; **não** `ORCA open` nem reiniciar o app.

## O que o agente pode fazer sozinho

Sondar, depois agir. `--json` em tudo.

```bash
ORCA status --json
ORCA repo list --json
ORCA worktree current --json
```

| Pronto | Ação autônoma |
| --- | --- |
| `runtime.reachable` | `worktree create` / `agent launch` |
| Repo do projeto na lista | omitir `--repo`; senão `--repo path:<abs>` ou `name:<nome>` |
| Agente conhecido (`cursor`, `codex`, `claude`, …) | `--agent` + `--prompt` no create |
| Worktree já existe | `agent launch --worktree name:<nome> --prompt "…" --json` |

Create (um por recomendação top, máx. 3):

```bash
ORCA worktree create --name proto-auth-session \
  --comment "project-advisor: P1 auth session (alto/S)" \
  --agent cursor \
  --prompt "Protótipo isolado da P1: … Não refatore outras áreas. Commits só neste worktree." \
  --json
```

- `--parent-worktree active` se a ideia deriva deste workspace; `--no-parent` se for experimento independente.
- `--activate` só se o usuário quiser focar a UI. Default: fundo.
- Launch perdido: `--retry-launch <operationId>` — nunca create duplicado.
- Status: `ORCA worktree set --worktree name:<nome> --comment "…" --workspace-status in-progress --json`
- Visão: `ORCA worktree ps --limit 20 --json`
- Abrir diff no Orca sem roubar foco: `ORCA file open-changed --worktree name:<nome> --json` (review humana continua no app).

Não usar `git worktree add` se o Orca estiver no fluxo.

## Quando NÃO dá para ser autônomo

Não fingir que o worktree existe. Não clicar na GUI do Orca via Computer Use (a skill `orca-cli` reserva Computer Use a janelas que o CLI não alcança; o Orca tem CLI). Entregar o bloco [Ações no app Orca](#acoes-no-app-orca) + prompts prontos.

| Bloqueio | O que pedir no app |
| --- | --- |
| App fechado / `runtime` inacessível | Abrir o Orca. Agente pode tentar `ORCA open --json` **uma vez**; se falhar, o usuário abre o app. |
| Repo ausente em `repo list` | Sidebar → **Add Repo** → pasta do checkout. Ou, se o runtime estiver up: `ORCA repo add --path <abs> --json`. |
| Host/SSH sem setup | Create Workspace → **Run on** → **Set project location** (pasta existente ou clone). Host desconectado → **Connect**. |
| Agente não aparece no picker | **Settings → Agents**: habilitar o CLI, conferir binário, **sign-in / account**. Permissões Manual/Auto/Yolo e Chat vs CLI também ficam aqui. |
| Card **Needs You** (âmbar / `?`) | Clicar o card (ou Agent Dashboard) e responder a permissão/pergunta. O agente **não** aprova isso no lugar do usuário. |
| Orchestration recusada | **Settings → Experimental** → Orchestration. Sem isso, só handoff `worktree create --agent`. |
| Usuário precisa **ver** os 3 agentes | Arrastar aba da worktree para a borda (split). **Settings → Experimental → Agent Dashboard** para o kanban Needs You / Working / Done. |
| Review / escolher vencedor | Diff do worktree → Annotate AI Diff (`+` na gutter ou `c`) → **Send to agent** em lote. |
| Ship | Source Control ao lado do Diff → stage hunk → Commit (`Ctrl-Enter`) → Push. Sem force-push. Perdedores: botão direito no card → delete (confirmação). |
| Agente morreu | Chip **Restart** no tab. |
| `.env` / `node_modules` faltando no worktree novo | Settings → Repository → Worktree Shared Paths; ou `.worktreeinclude` (`.env`) + `orca.yaml` `sharedDirectories` (`node_modules`). |
| Create CLI em voo / falhou | Sidebar: linha de progresso do worktree; painel in-tab **Retry** / cancel. Filtro **CLI-created workspaces** se o card não aparecer. |

## Ações no app Orca

Usar este bloco na resposta sempre que o passo 4 não fechar 100% no CLI. Preencher nomes e prompts da tabela de recomendações.

```markdown
### Ações no app Orca
1. Abrir o **Orca** (janela desktop).
2. Se o projeto não estiver na sidebar: **Add Repo** → `<PROJECT_ROOT>`.
3. Clicar **+** ao lado do repo. Nome: `<proto-p1>`. **Branch from**: base ref (`origin/main`). Agente: Cursor CLI / Codex / Claude (o que estiver signed-in em Settings → Agents).
4. Colar o prompt P1 (abaixo) e criar. Repetir **+** para P2 e P3 (máx. 3). Não reutilizar o mesmo worktree.
5. Arrastar as abas para split (direita/baixo) para ver os três. Opcional: Settings → Experimental → **Agent Dashboard**.
6. Se um card ficar **Needs You** (âmbar): abrir e aprovar/responder.
7. Quando idle (ponto verde / check): Diff de cada worktree → **Annotate AI Diff** → **Send to agent** (lote).
8. Escolher o vencedor → Source Control → Commit → Push. Apagar os outros worktrees no card (confirmação). Não mergear sem olhar o Diff.
```

Atalhos úteis no app: Jump Palette `Ctrl-J` (Linux) / `Cmd-J`; delete com confirmação `Ctrl-Shift-Backspace`.

### Prompts para colar no launcher

Um prompt **estreito** por worktree: linha da tabela, evidência, fora de escopo.

```text
Protótipo isolado da recomendação P1 (<título>).
Evidência: `<path>` — <sintoma>.
Faça só isso neste worktree. Não refatore outras áreas. Sem secrets no git.
Ao terminar: resumo do que mudou + como testar o caminho feliz.
```

## Paralelo e seguro

- Máx. 3 worktrees. Backlog fica na tabela.
- Prompt sem chaves; `.env` via `.worktreeinclude` / pedido ao usuário.
- Não merge / push `--force` / `worktree rm` sem pedido. CLI: `ORCA worktree rm --worktree name:<nome>` só com confirmação.
- Comentário curto no card a cada checkpoint (`worktree set --comment`).
- `--json` no create: guardar `id` (`<repoId>::<path>`) para `set` / `launch`.

## Sequência no Project Advisor

1. Tabela pronta (passo 3).
2. Confirmação para prototipar N itens.
3. `status --json` → CLI se reachable, senão bloco de ações no app.
4. Sucesso parcial: listar o que o CLI fez **e** os cliques que faltam (quase sempre: split, Diff, Annotate, Commit).
5. Relatar nomes dos worktrees, riscos, o que **não** mergear ainda.
