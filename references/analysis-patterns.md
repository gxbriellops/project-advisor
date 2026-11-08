# Padrões de análise

Ler **somente** a seção da stack detectada + [Recomendações gerais](#recomendacoes-gerais). Não copiar este arquivo na resposta; extrair 3–8 checagens aplicáveis.

Impacto/esforço da tabela final deve cruzar estes cheiros com evidência real (`key_files`, hotspots, TODOs, ausência de testes/CI).

## Flutter

### Arquitetura

- `lib/` só com `screens/`, `widgets/` e `services/` gigantes → feature-first (`lib/features/<nome>/{data,domain,ui}`) ou layer-first consistente. Não propor Clean Architecture completo em app pequeno.
- Regras de negócio e chamadas HTTP dentro de `State`/`build()` → extrair. Evidência: hotspots `.dart` + imports de `http`/`dio` no widget.
- `lib/main.dart` registrando tudo (rotas, DI, tema, Firebase) → bootstrap + `app.dart`. Esforço S–M, impacto alto em apps médios.

### State management

- Cruzar `pubspec.yaml`: `provider`, `flutter_riverpod`, `bloc`/`flutter_bloc`, `getx`, `mobx`, `redux`. Dois (ou mais) no app de produto = cheiro. Recomendar **um** e um plano de convergência, não um quarto pacote.
- `setState` em telas com async/lista/form + Riverpod/Bloc no mesmo módulo → estado local vazou. Impacto alto se houver race/loading duplicado.
- `ChangeNotifier` global para sessão + tema + features → fatiar. Não sugerir rewrite GetX↔Riverpod sem pedido.

### Widgets grandes

- Hotspot `.dart` ≥ 400 linhas, `build()` aninhado, métodos `_build*` demais → extrair widgets + const constructors. Esforço S, impacto médio–alto (jank, review).
- Listas sem `Key` estável, `ListView` + `Column` sem `shrinkWrap` consciente, `setState` no parent a cada keystroke → item de perf.
- Cores/text styles hardcoded (`Color(0xFF…)`, `TextStyle(fontSize:`) vs `Theme.of` → dx/theming. Agrupar num único item.

### Assets e i18n

- Strings de UI em português/inglês literais e **sem** `l10n.yaml` / `.arb` / `flutter_localizations` → feature de i18n só se o produto precisar; senão item `dx` “centralizar copy”.
- `pubspec.yaml` `assets:` ausente ou pastas em `assets/` não listadas → bug de runtime. Esforço S.
- Imagens grandes em `assets/` sem variantes / `cached_network_image` para rede → perf.

### Outros Flutter

- Sem `analysis_options.yaml` (ou sem `flutter_lints`) → dx barato.
- Testes: zero `*_test.dart` / `test/` → `tests` de alto impacto se houver lógica de domínio; não pedir golden de tudo.
- Plataformas: `minSdk`, permissões, flavors (`dev/prod`) só se `android/` `ios/` mostrarem um único ambiente.

## Next.js

Antes de recomendar API/convenção: se existir `node_modules/next/dist/docs/`, ler o guia local. Este Next pode divergir do treino.

### App Router vs Pages

- Só `app/` → App Router. Só `pages/` → Pages (item: migrar **por rota de valor**, não big-bang).
- **Os dois** com rotas equivalentes → cheiro de migração parada. Impacto alto, esforço L; priorizar paridade e depois apagar `pages/`.
- `pages/_app.tsx` + `app/layout.tsx` coexistindo → documentar o que ainda é Pages.

### Server Components

- `'use client'` no `layout.tsx` raiz ou em wrappers largos → todo o subárvore vira client. Impacto alto, esforço M: empurrar client para folhas (form, chart, listener).
- Fetch no client (`useEffect` + `fetch`) para dados de rota que poderiam ser server → waterfall + loading flash. Feature/refactor de data layer.
- Server Actions / Route Handlers misturados sem critério → um parágrafo de convenção, não os dois para o mesmo POST.

### Estrutura de pastas

- Tudo em `app/components` ou `components/` plano com 30+ arquivos → agrupar por rota/feature; colocation (`app/(rotas)/_components`) quando o componente é exclusivo.
- Barrel `index.ts` reexportando o design system inteiro → custo de bundle/tsc. Item perf/dx.
- `loading.tsx` / `error.tsx` / `not-found.tsx` ausentes em rotas com I/O → feature pequena, impacto médio em UX.

### Performance

- `<img>` em vez de `next/image` (ou Image sem `sizes` em grid) → perf S–M.
- Fontes via CSS externo vs `next/font` → layout shift.
- `NEXT_PUBLIC_` para segredo de servidor → risco, impacto alto, esforço S.
- Listas grandes sem paginação/`use cache`/streaming; client fetching em cascata. Cruzar hotspots `.tsx`.

### Outros Next.js

- Sem `metadata` / OG em `layout`/`page` → docs/seo se o produto for público.
- TypeScript frouxo (`any` espalhado, `ignoreBuildErrors`) → dx.
- Scripts `lint` / `test` ausentes no `package.json` → dx/tests.

## Python

### Type hints

- `def` públicas sem anotações em módulos de domínio → dx, esforço M. Não exigir 100% em scripts one-off.
- `typing.Dict`/`List` vs `dict`/`list` (3.9+) é nit; só mencionar se o arquivo já está aberto.
- `pyproject.toml` sem `mypy`/`pyright`/`ty` e sem CI de tipos → dx barato se o pacote for biblioteca.

### Estrutura de pacote

- Módulos soltos na raiz + `sys.path` hack → `src/<pkg>/` ou pacote plano declarado no `pyproject.toml`.
- `setup.py` só, sem `pyproject.toml` → modernizar empacotamento (esforço M).
- CLI, API e lib no mesmo módulo → fatiar. Evidência: `click`/`fastapi`/`flask` no mesmo arquivo que regras de negócio.

### Testes

- Zero `tests/` / `test_*.py` / `pytest.ini` → `tests` de alto impacto se houver lógica; para CLI/scripts, 2–3 casos de regressão bastam.
- Testes só de import (“smoke”) → item de qualidade, esforço S, impacto médio.
- Fixtures que batem em rede/prod → risco; marcar e recomendar fake/httpx mock.

### Config

- `os.environ[...]` espalhado sem defaults/validação → `pydantic-settings` ou módulo `config.py` único. Impacto alto se houver deploy.
- Segredos em `.env` commitado ou defaults reais no código → risco, esforço S.
- `settings.py` Django monolítico + flags mortas → limpeza, não rewrite.

### Outros Python

- `requirements.txt` pinado vs solto demais; duplicata poetry+pip+pipenv → dx.
- `print` em biblioteca, logging inconsistente → dx S.
- Scripts na raiz sem `python -m` → entry points no `pyproject.toml`.

## Recomendações gerais

Aplicar a qualquer tipo (`generic` incluso):

| Sinal | Tipo típico | Como priorizar |
| --- | --- | --- |
| README ausente, vazio ou divergente do manifesto | `docs` | S se o repo for compartilhado; senão baixo |
| `markers.TODO`/`FIXME` concentrados | `feature` ou `refactor` | Abrir 2–3 arquivos com mais hits; promover só os acionáveis |
| Duplicação (dois clientes HTTP, dois logins, copy-paste de validação) | `refactor` | Impacto alto se houver bug de paridade |
| Dependências não usadas / duas libs para o mesmo problema | `dx` | Esforço S–M; não “atualizar tudo” |
| Sem CI (`ci: []`) e há testes | `dx` | S: um workflow de lint+test |
| Sem testes e domínio não trivial | `tests` | M, impacto alto — 1º caminho feliz da regra de negócio |
| Hotspots ≫ restante (arquivo deus) | `refactor` | S–M se o arquivo estiver na evidência |
| `Dockerfile`/compose sem `.dockerignore` / secretos | `dx` | S |

Não transformar cada TODO em linha da tabela. Agrupar. Preferir 5–9 recomendações nítidas a 20 nits.

Ordem de prioridade na tabela: impacto alto + esforço S primeiro; em empate, risco de produção (auth, dados, money) > DX > estética.
