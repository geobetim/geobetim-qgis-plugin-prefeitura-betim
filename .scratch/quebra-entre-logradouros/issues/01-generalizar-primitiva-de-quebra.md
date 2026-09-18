# 01: Generalizar a primitiva de quebra para geometrias em memória

**What to build:** a função que hoje acha interseções internas ao longo de uma
polilinha e a corta, contra uma lista de `QgsVectorLayer` (as **camadas de
quebra**), passa a aceitar também um iterável de geometrias já carregadas em
memória — sem exigir uma segunda camada do QGIS. É o prefactor que abre
caminho para a fase 0 (ticket 02) reaproveitar a mesma primitiva contra os
trechos de outro `COD_LOGRADOURO` já presentes na vizinhança, em vez de reler
uma camada.

Do ponto de vista do operador nada muda: a quebra por camada de quebra (fase
2) continua funcionando exatamente como hoje.

**Blocked by:** None (can start immediately)

**Status:** done

_`quebra.py`: nova primitiva pura `intersecao_interna(linha, geometria, tol)`
(uma geometria) e `distancias_de_intersecao_interna(linha, geometrias, tol)`
(iterável, agrega+dedup) — sem nenhuma leitura de camada. `cortar(coords,
distancias, tol)` extraído do corpo de `quebrar`. `quebrar(coords,
camadas_quebra, tol)` mantém a assinatura de sempre, agora montando o
iterável de geometrias (via `_geometrias_de_camadas`, com `_fronteira` e
filtro por bbox) e delegando para as duas primitivas novas. Testado com stub
geométrico completo (interseção segmento-a-segmento, `lineLocatePoint`,
`curveSubstring`): geometrias diretas (1 e 2, com e sem cruzamento) e
regressão completa de `quebrar` (sem camada, 1 e 2 camadas, interseção perto
da ponta, camada poligonal pela borda) — tudo verde._

- [x] A função de achar distâncias de interseção interna (`tol < d <
      comprimento − tol`) aceita um iterável de geometrias diretamente, além
      de continuar aceitando (ou sendo alimentada por) uma lista de camadas —
      a fase 2 continua montando o iterável a partir de `camada.getFeatures()`
      dentro do bbox da linha, como hoje.
- [x] A função de cortar a polilinha nesses pontos não muda de assinatura
      observável para quem já a chama hoje (fase 2); nenhuma regressão nos
      casos já cobertos (sem quebra, uma quebra, duas quebras, camada
      poligonal pela borda).
- [x] Novo teste funcional cobrindo a chamada com um iterável de geometrias
      passado diretamente (não vindo de `camada.getFeatures()`), incluindo o
      caso de zero interseções (passthrough) e de mais de uma.
- [x] `python -m py_compile` limpo; suíte de testes funcionais com stub de
      `qgis.core` (reaproveitando os cenários já existentes da quebra por
      camada de quebra) toda verde.
- [ ] Verificação do operador: nenhuma mudança de comportamento observável na
      quebra por camada de quebra (fase 2) — mesmo resultado de antes num
      cenário já validado. (pendente)
