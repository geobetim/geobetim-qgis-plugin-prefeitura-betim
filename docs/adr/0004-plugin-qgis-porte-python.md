# Plugin do QGIS reimplementa a numeração em Python

O plugin do QGIS "Numeração de trechologradouro por logradouro" **porta as
regras da numeração automática para Python**, em vez de chamar o serviço C#
(ADR-0003) por HTTP a partir do QGIS. As duas implementações passam a coexistir:
a de C# continua sendo a fonte de verdade das regras; a de Python deve segui-la.

## Motivação

Quem trabalha o cadastro de trechos-logradouros faz isso dentro do QGIS, sobre
uma camada já carregada. Depender do serviço C# significaria: subir o host,
configurar a conexão ao Oracle, ter rede até o banco, e o QGIS mandar a geometria
de ida e volta por HTTP só para receber os números. Para uma operação que o
próprio QGIS já tem tudo para fazer localmente (geometria em memória, índice
espacial, cálculo planar), isso é peso morto.

## Escolha

- **Porte paralelo em Python**, como algoritmo do Processing num plugin
  instalável. Roda offline, sem servidor, sem Oracle — sobre a camada de linhas
  do projeto.
- **A solução em C# (`backend/`) é a fonte de verdade das regras.** O grafo de
  nós, o sequenciador multi-candidato, o `ContinuarDisjunto` e a atribuição por
  segmento são portados 1:1. Divergência entre as duas é bug do Python, não uma
  variação legítima.
- **O plugin usa os nativos do QGIS para as primitivas** (`QgsPointXY.distance`,
  `QgsVector`, `QgsSpatialIndex`, iteração de vértices do `QgsGeometry`) — só o
  algoritmo de grafo/sequenciamento, que é regra de domínio, é escrito à mão.
- **Sem máscara.** O plugin grava só o inteiro incremental por segmento (o `1` de
  `01052.0001`) num atributo da camada. A máscara `NNNNN.NNNN` fica para uma
  consulta futura.
- **Escopo "por logradouro" apenas** — numera todos os `COD_LOGRADOURO` distintos
  da camada, ou os dos trechos selecionados. Sem modo por área/MBR.
- **Um `COD_LOGRADOURO` com o atributo de número sequencial já preenchido em pelo
  menos um trecho é ignorado** — protege o que já foi numerado.
- **`docs/adr/0002` (numeração automática) e `docs/adr/0003` (serviço HTTP)
  permanecem válidos.** Este ADR não muda regra de numeração; muda só a
  plataforma onde ela roda.

## Consequências

- Duas implementações da mesma regra para manter em sincronia. Mitigação: a
  verificação do plugin compara a saída com o serviço C# para códigos conhecidos
  (1052 → segmentos 1, 2; 1171 → dois componentes disjuntos encadeados pelo vão).
- Sem suíte de testes no repositório para o plugin — o núcleo depende de tipos do
  `qgis.core` e não roda fora do QGIS. Verificação = `py_compile` + estrutura de
  plugin + o operador rodando no QGIS 3.28.
- Estrutura: `plugin-qgis/numeracao_trechologradouro/` (pacote instalável dentro
  de uma pasta contêiner na raiz do repo). _Renomeado depois para
  `plugin-qgis/prefeitura_betim/`, com o algoritmo de numeração no subpacote
  `numeracao_trecho_logradouro/`, quando o plugin passou a reunir mais de um
  algoritmo sob o provider "Prefeitura de Betim"._
