# 01: Reorganizar o projeto (plugin como raiz)

**What to build:** o conteúdo de `plugin-qgis/prefeitura_betim/` (incluindo
o `.git/`) passa a ser a raiz do projeto (`F:/projetos/editor_trechologradouro`).
`CONTEXT.md` e `docs/adr/` migram para a nova raiz e passam a ser
rastreados pelo git do plugin; `CONTEXT.md` é revisado entrada por entrada,
removendo o que só descreve o front-end/back-end (`MBR`, `Logradouro
totalmente contido`, `Serviço de numeração`) e mantendo o que o plugin usa.
As pastas de `.scratch/` do front-end/back-end (`backend-api`,
`codigo-por-segmento`, `editor-trechos-logradouro`, `numeracao-em-lote`,
`numeracao-no-backend`, `repositorio-oracle`) são removidas; as do plugin
migram junto. Front-end (`src/`, `index.html`, `package.json`,
`package-lock.json`, `tsconfig.json`, `vite.config.ts`, `dist/`,
`run-frontend.bat`), back-end (`backend/`, `bin/`, `run-api.bat`) e
arquivos exclusivos deles (`.env.example`, `DESIGN.md`) são removidos.
`.claude/launch.json` perde as configurações de servidor de
desenvolvimento do front-end/back-end. `CLAUDE.md` passa a descrever o
plugin QGIS, não a "ferramenta web local". `README.md` do plugin (instrução
de `mklink`) é atualizado para o novo caminho.

**Blocked by:** 03 (Renomear o algoritmo, de `.scratch/cruzamento-fora-de-escopo/`)
e 01 (Numerar após quebrar e remover, de `.scratch/numeracao-apos-remocao/`)

**Status:** done

_O `README.md` já usava um placeholder genérico (`<caminho-deste-repositório>`)
na instrução de `mklink` — não precisou de edição. `.claude/launch.json` e o
`.gitignore` do front-end (raiz antiga) foram descartados por completo, sem
substituto (o `.gitignore` do próprio pacote do plugin já cobria
`__pycache__`/editor/backups do QGIS). A suíte de stub verifica a
importação pelo nome real da pasta do repositório
(`editor_trechologradouro`, já que não existe mais uma pasta literal
`prefeitura_betim` no disco) — os imports relativos internos do pacote
(`from ..shared...`) continuam funcionando de qualquer forma, independente
de como o pacote é nomeado por quem o importa; é a mesma razão pela qual o
`mklink` do README funciona (o nome do link, não o nome real da pasta, é o
que define o nome do pacote pra dentro do QGIS)._

- [x] `F:/projetos/editor_trechologradouro` é, ele mesmo, o diretório do
      plugin — sem mais aninhamento em `plugin-qgis/prefeitura_betim/`
- [x] O `.git` do plugin preserva histórico e remoto intactos (mesmos
      commits, mesmo `origin`) depois da mudança
- [x] `CONTEXT.md` e `docs/adr/` estão na nova raiz, rastreados pelo git do
      plugin; `CONTEXT.md` não menciona mais conceitos exclusivos do
      front-end/back-end
- [x] `.scratch/` na nova raiz contém só as pastas relacionadas ao plugin;
      as de front-end/back-end foram removidas
- [x] Front-end, back-end e arquivos exclusivos deles não existem mais no
      projeto
- [x] `.claude/launch.json` não referencia mais servidores de
      desenvolvimento do front-end/back-end (removido por completo, não
      sobrou nenhuma configuração útil)
- [x] `CLAUDE.md` descreve o projeto como o plugin QGIS "Prefeitura de
      Betim"
- [x] `README.md` do plugin tem a instrução de `mklink` apontando para o
      caminho novo (já era genérica; conteúdo dos algoritmos sincronizado)
- [x] `py_compile` recursivo em todos os `.py` do projeto, sem erro de
      import
- [x] A suíte de stub continua encontrando os módulos do pacote no caminho
      novo (verificado importando pelo nome real da pasta do repositório)
- [x] `git status` limpo depois do commit da reorganização; nada da
      estrutura antiga sobrando fora do índice
- [x] Remoto do GitHub confirmado acessível (`git fetch` bem-sucedido) com
      o commit da reorganização, antes de qualquer push
