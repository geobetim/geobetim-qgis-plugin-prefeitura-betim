# 02: Revogar o "cruzamento atípico" do mesmo COD_LOGRADOURO

**What to build:** `quebrar_cruzamentos_entre_logradouros`
(`remocao_trecho_logradouro_passagem/quebra_entre_logradouros.py`) deixa de
tratar cruzamento entre trechos do **mesmo** `COD_LOGRADOURO` sem nó
compartilhado como "atípico" (hoje: só gera aviso no log, nunca divide).
Passa a dividir esse cruzamento pelo mesmo caminho já usado para
`COD_LOGRADOURO` diferentes (`cortar`, ids temporários, ponto de corte
marcado cruzamento) — sem distinguir a forma do toque (ponta encostando no
meio, ou um X sem vértice em nenhum dos dois lados). O ramo que hoje só
acumula em `avisos` para esse caso é removido.

Combinado com o ticket 01 (que corrige a robustez numérica da detecção),
isto fecha de ponta a ponta o caso real que motivou o spec: no
`COD_LOGRADOURO 7640`, rodar a remoção de trecho de passagem deve dividir
`33725` no ponto onde `33729` o toca, e o colapso da fase 1 deve estender
`33722` (o absorvedor) até esse ponto — `33725` original apagado, um
registro novo criado para o pedaço remanescente (rumo à outra ponta de
`33725`), com `IDPKTRLOGR` da sequência do Geomedia.

**Blocked by:** 01 (Detectar quase toque na primitiva de interseção interna)

**Status:** done

_`quebrar_cruzamentos_entre_logradouros` (`quebra_entre_logradouros.py`) não
distingue mais `cand_cod == cod`: todo candidato da vizinhança (mesmo código
ou não) entra em `geoms_candidatas` e passa pela mesma
`distancias_de_intersecao_interna`/`cortar`. O ramo que só acumulava aviso
para o mesmo código foi removido, junto do `avisados`/`cod_por_id` como
parâmetro de decisão (o `cod` de cada `fid` ainda é lido, só não compara mais
contra o candidato). Docstrings do módulo e do `shortHelpString` do
algoritmo sincronizados. Testado com stub: `7640` real (WFS) ponta a ponta —
`33725` dividido, `33722` estendido até o ponto de corte via
`identificacao.segmentos_de_passagem` + `absorcao.colapsar` reais, pedaço
remanescente de `33725` não colapsado (nó de corte bloqueado) —, X puro
sintético no mesmo código (ambos os lados dividem) e controle sem toque
(nenhuma divisão)._

- [x] Reprodução do `COD_LOGRADOURO 7640` (`33722`/`33725`/`33729`) ponta a
      ponta: `33725` dividido no ponto de quase toque; `33722` estendido até
      esse ponto após o colapso da fase 1; `33725` (id original) apagado; um
      registro novo cobre o pedaço remanescente de `33725`
- [x] Caso sintético de dois trechos do mesmo `COD_LOGRADOURO` cruzando em X
      puro (sem nenhum vértice em nenhum dos dois lados, longe de qualquer
      ponta): ambos os lados são divididos no ponto de cruzamento
- [x] Caso de controle: dois trechos do mesmo `COD_LOGRADOURO` com pontos a
      mais de `tol` de distância um do outro — nenhuma divisão
- [x] Nenhuma mensagem de "atípico" é mais gerada para cruzamento no mesmo
      `COD_LOGRADOURO`
- [x] A assinatura de `quebrar_cruzamentos_entre_logradouros` não muda
      (continua devolvendo a mesma tupla de 7 posições)
