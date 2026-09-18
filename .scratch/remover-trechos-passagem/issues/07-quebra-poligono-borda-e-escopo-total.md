# 07: Quebra por polígono usa a borda, e roda sobre todo trecho em escopo

**What to build:** duas correções na mesma dupla de funções, encontradas testando
o `COD_LOGRADOURO 3115` com a camada de quebra `UP` (polígono):

1. Uma feição de quebra **poligonal** só deve contar como "encostando"/"cruzando"
   pela sua **borda** — hoje mede distância/interseção contra a área cheia, então
   qualquer nó ou vértice **dentro** do polígono (mesmo a dezenas de metros da
   borda) conta como tocado. Com uma camada como a `UP` (unidades de
   planejamento, cobrindo a cidade sem vãos), isso bloqueia quase todo nó da
   região — nenhum segmento de passagem se forma. É a causa de `IDPKTRLOGR 28761`
   (que atravessa a borda da UP "VILA UNIVERSAL" no seu próprio interior) não
   colapsar com `28384`: o nó que os dois compartilham está 8,77 m **dentro** da
   UP, e isso já bastava para bloquear.
2. A fase 2 (quebra) só rodava sobre os trechos que **colapsaram** na fase 1. Um
   trecho comum, que nunca foi trecho de passagem mas cruza uma camada de quebra
   no meio, nunca era verificado. A fase 2 passa a rodar sobre **todo trecho do
   escopo** — colapsado (geometria já estendida) ou não (geometria original).

**Blocked by:** 04, 06

**Status:** done

_`quebra.py`: nova `_fronteira(g)` (polígono → `convertToType(LineGeometry)`;
linha passa direto), usada em `nos_tocados_por_quebra` e `_distancias_de_quebra`.
`algoritmo.py`: fase 2 agora itera `por_codigo[cod]` de todo `cod` em
`codigos_escopo` (pulando `apagar_total`), com
`geom_nova_total.get(fid, coords_por_id.get(fid))`; só grava quando `quebrar`
devolve mais de um pedaço; o retorno antecipado "nada para colapsar" foi movido
para depois da fase 2. Testado com stub geométrico (interseção segmento-segmento,
distância ponto-segmento real): nó a 10 m da borda de um polígono de quebra →
não bloqueado; nó a 0,02 m → bloqueado; trecho reto atravessando um quadrado →
quebra exatamente nas 2 travessias da borda (não em cada vértice interno);
vértice de trecho caindo dentro do polígono não gera corte espúrio; camada de
quebra de linha continua igual._

## Comportamento

- Camada de quebra poligonal: para o teste de nó (fase 1) e para achar pontos de
  corte (fase 2), usa a **borda** do polígono (`QgsGeometry.convertToType` para
  linha — inclui buracos), nunca a área cheia. Camada de linha, sem mudança.
- Fase 2 itera todo `IDPKTRLOGR` dos `COD_LOGRADOURO` em escopo que não foi
  apagado na fase 1: usa a geometria já estendida se colapsou, ou a original se
  não. Só grava (`changeGeometry`/registro novo) quando há de fato um corte —
  trecho sem cruzamento fica intocado, mesmo `IDPKTRLOGR`.
- Fica restrito ao escopo do parâmetro "apenas selecionadas"/camada inteira —
  não passa a rodar sobre a vizinhança inteira nem sobre outros códigos.

## Acceptance criteria

- [x] `quebra.py`: nova função (ou helper) que devolve a borda de uma feição
      poligonal (`QgsWkbTypes.PolygonGeometry` → `convertToType(LineGeometry)`);
      feição de linha passa direto.
- [x] `nos_tocados_por_quebra` usa a borda (não a feição original) na distância
      contra cada nó.
- [x] `_distancias_de_quebra` intersecta a linha do trecho com a **borda** da
      feição de quebra (não a área), para não coletar vértices internos do trecho
      como falso ponto de corte.
- [x] `algoritmo.py`: a fase 2 (`quebrar`) passa a iterar todos os `IDPKTRLOGR` de
      `por_codigo[cod]` para `cod` em `codigos_escopo`, pulando os apagados na
      fase 1; usa `geom_nova_total.get(fid, coords_por_id.get(fid))` como
      geometria de entrada; só atualiza `geom_nova_total`/cria registro novo
      quando `quebrar(...)` devolve mais de um pedaço.
- [ ] `COD_LOGRADOURO 3115`, com `UP` como camada de quebra: `28384` e `28761`
      colapsam num trecho só (o nó que compartilham não é mais bloqueado); esse
      trecho colapsado é então quebrado no ponto onde `28761` cruzava a borda da
      UP — 2 registros finais. As outras 7 trechos avulsos de 3115 (que nunca
      formam segmento de passagem) são verificados individualmente contra a `UP`
      pela fase 2, mesmo sem ter colapsado.
- [x] Um trecho qualquer (fora de qualquer segmento de passagem) que cruza uma
      camada de quebra no meio é dividido, mesmo que nenhum segmento tenha
      colapsado naquele `COD_LOGRADOURO`.
- [x] Trecho que não cruza nenhuma quebra e não colapsou fica intocado — sem
      `changeGeometry`, mesmo `IDPKTRLOGR`.
- [x] `CONTEXT.md` atualizado (**Cruzamento**, **Nó de passagem**, **Remoção de
      trecho de passagem**, **Camada de quebra**) — já feito na modelagem.
- [x] `python -m py_compile` limpo; teste funcional cobrindo os cenários acima
      com um polígono simulado (ponto dentro vs perto da borda) e um trecho fora
      de qualquer segmento cruzando a quebra.
- [ ] Verificação do operador no QGIS 3.28 sobre o `3115` real com a camada `UP`.
      (pendente)
