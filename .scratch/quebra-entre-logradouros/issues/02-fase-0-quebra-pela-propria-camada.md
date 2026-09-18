# 02: Fase 0 — quebra pela própria camada (cruzamento entre logradouros)

**What to build:** a **camada de trechos** passa a ser, ela mesma, fonte
obrigatória de cruzamento na **remoção de trecho de passagem** — sempre, sem
parâmetro para desligar, além de qualquer **camada de quebra** auxiliar
informada. Uma nova fase 0, antes do colapso (fase 1): para cada trecho em
escopo, acha os pontos onde ele cruza um trecho de **outro** `COD_LOGRADOURO`
na mesma camada — com ou sem nó compartilhado hoje, inclusive um X sem vértice
em nenhum dos dois lados — e o divide ali. O outro `COD_LOGRADOURO` nunca é
tocado, mesmo fora de escopo. O nó do corte é marcado cruzamento
explicitamente, para nunca ser colapsado de volta na fase 1. Um cruzamento
entre trechos do **mesmo** `COD_LOGRADOURO` sem nó compartilhado é atípico:
não quebra, só aparece no log.

Rodar "Remover trechos de passagem" no `COD_LOGRADOURO 7647` (apenas
selecionadas) divide o `IDPKTRLOGR 33748` em dois no ponto onde cruza o
`7643`, o pedaço novo com `IDPKTRLOGR` real da sequência do Geomedia, e o
`7643` sai idêntico.

**Blocked by:** 01

**Status:** done

_Novo módulo `quebra_entre_logradouros.py`: `quebrar_cruzamentos_entre_logradouros`
detecta e corta contra a topologia **original** (nunca o resultado já cortado
de outro trecho do próprio laço — evita dependência de ordem), usando a
primitiva do ticket 01; pedaço novo entra com id temporário (contador
negativo, próprio da chamada); nó de corte devolvido para o chamador marcar
como cruzamento; cruzamento mesmo-código só gera aviso (deduplicado por par).
`algoritmo.py`: fase 0 roda antes de montar o índice de nós; chave primária
dos pedaços resolvida na hora (decisão do operador) e mesclada em
`valor_pk_por_id` (o desempate do absorvedor já usa a chave real do pedaço);
na aplicação final, id temporário absorvido pela fase 1 é só descartado
(nunca `deleteFeature`), id temporário sobrevivente materializa como
registro novo — e, correção encontrada só nesta integração, um id **real**
truncado pela fase 0 recebe `changeGeometry` mesmo que nem a fase 1 nem a
fase 2 o toquem de novo depois (senão a camada ficaria com a geometria
original inteira, duplicando o traçado do pedaço novo). Testado com stub:
6 casos no módulo (incluindo `7647`/`7643` reais e uma integração direta com
`identificacao`/`absorcao`) + 4 cenários end-to-end via `algoritmo.py` inteiro
(pedaço absorvido, pedaço sobrevivente materializado, regressão sem
cruzamento, camada inteira com os dois lados de um X dividindo)._

- [x] Fase 0 roda sobre a união de todos os `COD_LOGRADOURO` em escopo, antes
      da identificação de segmentos de passagem — não dentro do laço por
      código da fase 1.
- [x] Fonte da quebra: trechos da vizinhança já carregada em memória (sem
      nova consulta) cujo `COD_LOGRADOURO` é diferente do trecho avaliado;
      usa a primitiva generalizada no ticket 01, sempre linha contra linha.
- [x] `COD_LOGRADOURO 7647`/`7643` reais (WFS): `33748` divide em dois pedaços
      no ponto do cruzamento (~585078.23, 7799018.59); `7643` sai sem nenhuma
      mudança de geometria; o nó do corte fica marcado cruzamento.
- [x] Trecho com duas ou mais interseções internas com códigos diferentes:
      divide em todos os pontos numa única passada (múltiplos pedaços).
- [x] Ao processar a camada inteira (sem "apenas selecionadas"), os dois
      lados de um mesmo cruzamento dividem — cada código, no seu turno, vê o
      outro como "trecho de outro código".
- [x] Dois trechos do **mesmo** `COD_LOGRADOURO` cruzando sem nó
      compartilhado: nenhuma divisão; aviso no log com os dois
      `IDPKTRLOGR`/ids e o ponto.
- [x] O nó de cada ponto de corte entra no mesmo conjunto de nós bloqueados
      que a fase 1 já usa para as camadas de quebra — nunca depende de o
      outro `COD_LOGRADOURO` ter, ele também, um nó real ali; um segmento de
      passagem não colapsa através desse nó.
- [x] Pedaço criado pela fase 0 recebe `IDPKTRLOGR` resolvido de imediato pela
      sequência do Geomedia (mesmo pipeline já existente), numa consulta
      batida por execução, separada da resolução da fase 2; nunca herda o
      `IDPKTRLOGR` do original.
- [x] Um pedaço da fase 0 que a fase 1 vier a absorver num segmento de
      passagem colapsado por outro motivo é apagado normalmente — o
      `IDPKTRLOGR` que recebeu fica como buraco aceitável na sequência.
- [x] Pedaço da fase 0 circula pelas estruturas em memória (coordenadas,
      geometria, índice de nós) por um identificador interno que nunca colide
      com um id real de feição; só se torna feição de verdade (`addFeatures`)
      na aplicação final, junto com os registros novos da fase 2, mantendo a
      ordem já estabelecida (alterar geometria → adicionar novos → apagar) e
      a atomicidade (tudo calculado em memória antes de qualquer escrita).
- [x] Resumo do log com contagem própria da fase 0 (trechos divididos,
      registros novos com/sem `IDPKTRLOGR`), distinta da contagem já
      existente da quebra por camada de quebra.
- [x] Regressão: `COD_LOGRADOURO` sem nenhum cruzamento com outro código —
      saída idêntica à de antes desta fase; comportamento de segmento de
      passagem (incluindo segmento fechado) e de camada de quebra (fase 2)
      intocados.
- [x] Um segmento de passagem que, depois da fase 0, tem um dos seus trechos
      recém-dividido: não colapsa através do nó marcado cruzamento; o
      restante do segmento colapsa normalmente.
- [x] `python -m py_compile` limpo; testes funcionais com stub de `qgis.core`
      cobrindo os casos acima (o do `7647`/`7643` com coordenadas reais do
      WFS), incluindo o algoritmo completo (`processAlgorithm`) ponta a ponta.
- [ ] Verificação do operador no QGIS 3.28: rodar no `7647` (apenas
      selecionadas) → `33748` sai como dois trechos, o novo com
      `IDPKTRLOGR` real, `7643` sem mudança; rodar sem "apenas selecionadas"
      numa área com mais de um cruzamento parecido → os dois lados dividem.
      (pendente)
