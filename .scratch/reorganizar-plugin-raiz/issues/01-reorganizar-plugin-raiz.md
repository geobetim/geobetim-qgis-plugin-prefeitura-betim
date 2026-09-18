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

**Status:** ready-for-agent

- [ ] `F:/projetos/editor_trechologradouro` é, ele mesmo, o diretório do
      plugin — sem mais aninhamento em `plugin-qgis/prefeitura_betim/`
- [ ] O `.git` do plugin preserva histórico e remoto intactos (mesmos
      commits, mesmo `origin`) depois da mudança
- [ ] `CONTEXT.md` e `docs/adr/` estão na nova raiz, rastreados pelo git do
      plugin; `CONTEXT.md` não menciona mais conceitos exclusivos do
      front-end/back-end
- [ ] `.scratch/` na nova raiz contém só as pastas relacionadas ao plugin;
      as de front-end/back-end foram removidas
- [ ] Front-end, back-end e arquivos exclusivos deles não existem mais no
      projeto
- [ ] `.claude/launch.json` não referencia mais servidores de
      desenvolvimento do front-end/back-end (removido por completo, se não
      sobrar nenhuma configuração útil)
- [ ] `CLAUDE.md` descreve o projeto como o plugin QGIS "Prefeitura de
      Betim"
- [ ] `README.md` do plugin tem a instrução de `mklink` apontando para o
      caminho novo
- [ ] `py_compile` recursivo em todos os `.py` do projeto, sem erro de
      import
- [ ] A suíte de stub já usada nas rodadas anteriores continua encontrando
      os módulos do pacote `prefeitura_betim` no caminho novo
- [ ] `git status` limpo depois do commit da reorganização; nada da
      estrutura antiga sobrando fora do índice
- [ ] Remoto do GitHub confirmado acessível com o commit da reorganização,
      antes de qualquer push
