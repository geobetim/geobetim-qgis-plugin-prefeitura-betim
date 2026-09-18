# Trecho degenerado sempre funde com o maior vizinho real (revoga parte do ADR-0008)

Revoga a parte do [ADR-0008](0008-trecho-degenerado-como-no-de-passagem.md)
que limitava a remoção de um **trecho degenerado** a nós de passagem reais.
Na **remoção de trecho de passagem**, ele passa a fundir com o maior trecho
real do mesmo `COD_LOGRADOURO` que tocar seu nó, mesmo quando esse nó é um
**cruzamento** real — o cruzamento sobrevive, na ponta do trecho absorvedor
estendido; só o registro do trecho degenerado desaparece. A **numeração
automática** não muda: já tratava o trecho degenerado da mesma forma em
qualquer contexto (ADR-0008, mantido).

## Motivação

Ao verificar a correção do ADR-0008 contra dados reais, o `IDPKTRLOGR 33792`
(`COD_LOGRADOURO 7644`) continuou sem ser removido mesmo depois da correção.
Investigando: o nó onde `33792` cai — compartilhado com os trechos reais
`33791` e `33789` — também é tocado pelo trecho `33784`, do
`COD_LOGRADOURO 1078`, a menos de 5 cm. Pela definição de **Cruzamento** já
existente no glossário ("nó tocado por trecho de outro `COD_LOGRADOURO`"),
esse nó é um cruzamento real, não um nó de passagem — e o ADR-0008
deliberadamente não remove trecho degenerado fora de nó de passagem.

O operador (dono do domínio) revisou esse caso e decidiu que a distinção não
deveria valer para trecho degenerado: um trecho de ~0,03 m nunca representa
uma feição real, com cruzamento ao lado ou sem — o cruzamento em si (o ponto
onde `1078` encosta) não desaparece, só o registro redundante. A motivação
original do ADR-0008 para essa restrição (manter a remoção de trecho de
passagem dentro do que o nome do algoritmo promete) segue válida para
trechos degenerados **isolados** ou bloqueados por **camada de quebra** — só
deixa de valer para o caso de cruzamento, onde há sempre um vizinho real
concreto para absorver o registro.

## Escolha

- Na remoção de trecho de passagem, um trecho degenerado sempre funde com o
  **maior trecho real** (por comprimento; empate pela chave primária
  configurada ou pelo menor `IDPKTRLOGR`) do mesmo `COD_LOGRADOURO` que
  tocar o nó dele — mesmo critério de desempate do **trecho absorvedor**
  existente, para manter uma regra só.
- Isso vale mesmo que o nó seja um cruzamento real: por bifurcação de 3+
  trechos reais do mesmo logradouro, ou por outro `COD_LOGRADOURO` tocando
  ali. O cruzamento não desaparece — só o registro do trecho degenerado.
- **A fusão nunca precisa estender geometria.** O nó do trecho degenerado
  só existe porque, na indexação de nós (`IndiceDeNos`), uma das pontas do
  vizinho escolhido já caiu dentro da tolerância de encaixe desse mesmo nó
  — ou seja, o vizinho **já tem, por construção**, um vértice ali (na sua
  geometria original, ou herdado se ele mesmo foi absorvido por outro
  trecho maior num colapso de segmento de passagem — a extensão preserva
  todos os vértices do trecho absorvido). O trecho degenerado nunca
  contribui um ponto que já não estivesse coberto. A fusão é só apagar o
  registro do trecho degenerado — nenhuma chamada a `colapsar`/`_estender`
  é necessária para ele.
- Duas exceções continuam sem fusão automática, herdadas do ADR-0008: um nó
  **bloqueado por camada de quebra** (sinal explícito do operador, diferente
  de um cruzamento automático) continua impedindo; um trecho degenerado
  **isolado** (nenhum trecho real do mesmo `COD_LOGRADOURO` tocando o nó) não
  tem vizinho para absorver — nada muda, fica só o aviso.
- Sem alteração em `colapsar`/`_estender`/`_incorporar_lado` (`absorcao.py`)
  — a identificação do maior vizinho reaproveita o mesmo critério de
  desempate (`maior_por_comprimento`, tornado público), mas a fusão em si
  não passa por `colapsar`.

## Consequências

- `IDPKTRLOGR 33792` (`COD_LOGRADOURO 7644`) passa a apagar, com `33789`
  (o maior dos dois vizinhos reais, 190,28 m contra 8,15 m de `33791`)
  registrado como o vizinho que o absorve — mesmo com o cruzamento real com
  `1078` no mesmo nó. Nenhuma geometria muda.
- A remoção de trecho de passagem agora depende de conhecer, para cada
  trecho degenerado, o maior trecho real do mesmo `COD_LOGRADOURO` que toca
  seu nó (não só quando esse nó é nó de passagem) — `trechos_degenerados_absorviveis`
  foi substituída por `trecho_degenerado_fundivel`.
- Verificação por stub de `qgis.core`/`IndiceDeNos` com o cenário exato do
  `7644` (degenerado num nó também tocado por outro código), bifurcação real
  de 3+ ramos do mesmo código, e um cenário com dois trechos degenerados no
  mesmo `COD_LOGRADOURO` — um dentro de um segmento de passagem comum, outro
  num cruzamento com outro código — confirmando que a fusão funciona nos
  dois casos sem interferir uma na outra. Regressão dos cenários do
  ADR-0008 (isolado, bloqueado por camada de quebra) para confirmar que
  continuam sem fusão.
