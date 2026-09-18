# 01: Colapso de segmento fechado começa/termina no nó de fechamento

**What to build:** rodar "Remover trechos de passagem" num logradouro em forma
de balão — um **segmento de passagem** cujas duas pontas caem no mesmo nó —
colapsa os trechos num único trecho fechado, sempre que as geometrias de fato
se encadeiam, independente da orientação em que a geometria do **trecho
absorvedor** foi digitalizada. O trecho fechado **começa e termina no nó de
fechamento** do segmento (o nó compartilhado pela primeira e pela última
ponta — no `COD_LOGRADOURO 7542`, o cruzamento onde encosta o toco `29810`),
para quem encostava ali continuar encostando numa ponta do trecho. Anel
isolado (sem cruzamento) colapsa pela mesma regra. Segmento aberto não muda.

**Blocked by:** None (can start immediately)

**Status:** done

_`absorcao.py`: `_encadear` recebe o ponto de início (nó de fechamento) e
orienta o primeiro trecho por ele — invertido se for a ponta final, falha se
nenhuma ponta tocar; `colapsar`, no ramo de anel, deixou de rotacionar a lista
para começar no absorvedor e emenda na ordem do segmento a partir de
`indice.nos[nó de fechamento]`; o absorvedor segue sendo só o registro que
sobrevive. Testado com stub sobre as coordenadas reais do 7542 e casos
sintéticos: todos os critérios abaixo._

- [x] No `7542` (coordenadas reais do WFS): sobrevive o `29807`, apagados
      `29806, 29808, 29809, 29811`, 318 vértices, primeiro = último vértice = nó
      de fechamento (≈ 588821.85, 7795236.02), zero avisos.
- [x] Mesmo resultado com a geometria do absorvedor invertida e com a ordem do
      segmento espelhada.
- [x] Anel isolado de 4 trechos sintéticos: colapsa num trecho fechado que
      começa/termina num nó do anel, zero avisos (também com ids embaralhados
      e absorvedor invertido).
- [x] Anel com um trecho de < 2 vértices: pulado com o aviso atual ("segmento
      fechado [...] não encadeia; não colapsado"), nada colapsado.
- [x] Regressão de segmento aberto `A—B—C—D` (e absorvedor no meio, invertido):
      geometria, apagados e avisos idênticos ao comportamento do ticket 06.
- [x] Docstring do módulo de absorção e o "Fluxo de execução" (fase 1) da spec
      da remoção descrevem o anel fechando no nó de fechamento.
- [x] `python -m py_compile` limpo; testes funcionais com stub de `qgis.core`
      cobrindo os cinco casos acima.
- [ ] Verificação do operador no QGIS 3.28: remoção no `7542` → 1 trecho
      fechado + toco `29810` encostado numa ponta; "Reverter" desfaz. (pendente)
