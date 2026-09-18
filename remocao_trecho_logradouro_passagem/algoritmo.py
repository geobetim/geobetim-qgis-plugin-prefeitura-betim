"""Algoritmo do Processing: Quebrar e remover trechos de passagem.

Para cada ``COD_LOGRADOURO`` em escopo, em três fases: fase 0 — a própria
camada de trechos é fonte obrigatória de cruzamento (sempre, sem parâmetro):
um trecho em escopo que cruza qualquer outro trecho da vizinhança, do mesmo
código ou não, é dividido ali; por padrão um código fora de escopo nunca é
tocado, só serve de candidato de cruzamento — a menos que o parâmetro de
também quebrar o de fora esteja ligado, em que ele também é dividido, sem
entrar nas fases seguintes; fase
1 — encontra os segmentos de passagem
(trechos ligados só por nós de passagem, já considerando os nós da fase 0) e
colapsa cada um de 2+ trechos num só (o maior; empate pela chave primária
configurada ou pelo menor id); fase 2 — divide nas interseções internas com
as camadas de quebra auxiliares **todo trecho em escopo**, colapsado ou não
(não depende de ter colapsado na fase 1). Feição de quebra poligonal conta
pela borda, não pela área cheia. Tudo no buffer de edição da camada, sem
``commitChanges()``.
"""

from qgis.core import (
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterDefinition,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorLayer,
    QgsRectangle,
    QgsWkbTypes,
)
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from ..numeracao_trecho_logradouro import (
    GrafoLogradouro,
    NumeracaoError,
    SequenciadorAutomatico,
    atribuir,
    parse_geometria,
)
from ..shared.camada import (
    avisar_sem_codigo,
    avisar_trechos_degenerados,
    exigir_crs_metrico,
    ler_camada,
)
from ..shared.edicao import edicao_sem_commit, exigir
from ..shared.topologia import IndiceDeNos
from .absorcao import colapsar
from .identificacao import (
    fundir_trecho_degenerado,
    segmentos_de_passagem,
    trecho_degenerado_fundivel,
    trechos_degenerados,
)
from .quebra import nos_tocados_por_quebra, quebrar
from .quebra_entre_logradouros import quebrar_cruzamentos_entre_logradouros
from .sequence_geomedia import resolver_chaves

_TIPOS_INTEIROS = (
    QVariant.Int,
    QVariant.LongLong,
    QVariant.UInt,
    QVariant.ULongLong,
    QVariant.Double,
)


class RemoverTrechosPassagemAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    APENAS_SELECIONADAS = "APENAS_SELECIONADAS"
    CAMPO_CODIGO = "CAMPO_CODIGO"
    TOL_VERTICE = "TOL_VERTICE"
    QUEBRAR_FORA_DE_ESCOPO = "QUEBRAR_FORA_DE_ESCOPO"
    CAMADA_QUEBRA_1 = "CAMADA_QUEBRA_1"
    CAMADA_QUEBRA_2 = "CAMADA_QUEBRA_2"
    CAMPO_CHAVE_PRIMARIA = "CAMPO_CHAVE_PRIMARIA"
    NUMERAR_APOS = "NUMERAR_APOS"
    CAMPO_SEQUENCIAL = "CAMPO_SEQUENCIAL"
    TOL_GAP = "TOL_GAP"

    # -- identidade --------------------------------------------------------

    def name(self):
        return "quebrar_remover_trechos_passagem"

    def displayName(self):
        return self.tr("Quebrar e remover trechos de passagem")

    def group(self):
        return self.tr("Trecho logradouro")

    def groupId(self):
        return "trechologradouro"

    def shortHelpString(self):
        return self.tr(
            "Colapsa cada segmento de passagem de um logradouro num trecho só.\n\n"
            "Um segmento de passagem é uma sequência de trechos do mesmo "
            "COD_LOGRADOURO ligados só por nós de passagem (grau 2, sem outro "
            "logradouro no nó, sem bifurcação), terminada em cruzamento, "
            "bifurcação ou extremidade nas duas pontas. Todo segmento com 2+ "
            "trechos colapsa: sobrevive o maior por comprimento (empate pelo "
            "menor valor da chave primária configurada, ou pelo id da feição "
            "sem ela), estendido para passar por todos os vértices dos demais; "
            "os outros são apagados. Um trecho já bem delimitado fica "
            "intacto.\n\n"
            "Por padrão ('apenas selecionadas' marcado) processa só os "
            "COD_LOGRADOURO das feições selecionadas; desmarque a opção para "
            "processar todos os COD_LOGRADOURO distintos da camada.\n\n"
            "A própria camada de trechos também é usada, sempre (sem "
            "parâmetro para desligar), para achar cruzamento: onde um "
            "trecho em escopo cruza — com ou sem nó compartilhado hoje, "
            "inclusive um X sem vértice em nenhum dos dois lados, ou um "
            "quase toque dentro da tolerância de encaixe — qualquer outro "
            "trecho na vizinhança, do mesmo COD_LOGRADOURO ou não, ele é "
            "dividido ali. Por padrão, um código fora de escopo nunca é "
            "alterado, só serve de candidato de cruzamento; marque 'Também "
            "quebrar o outro logradouro no cruzamento' para dividir também "
            "o trecho de fora nesse ponto — só a divisão, sem entrar em "
            "colapso de segmento de passagem nem quebra por camada de "
            "quebra do código de fora nesta execução.\n\n"
            "Camadas de quebra (opcionais, até duas; linha ou polígono — polígono "
            "conta pela borda, não pela área): uma feição de quebra que encosta "
            "num nó torna esse nó cruzamento — o segmento para ali e não colapsa "
            "através dele (preserva trechos já partidos no lugar certo). Onde uma "
            "feição de quebra cruza o meio de qualquer trecho em escopo — "
            "colapsado ou não — ele é dividido: o registro original fica com o "
            "primeiro pedaço; cada pedaço seguinte vira um registro novo, cópia "
            "dos atributos do original.\n\n"
            "Atributo da chave primária (opcional, só para camada Oracle; "
            "tipicamente IDPKTRLOGR, mas pode ter outro nome): usado para dar aos "
            "registros novos (da quebra pela própria camada ou pelas camadas de "
            "quebra) um valor pela sequência do Geomedia (dicionário "
            "GDOSYS.GFIELDMAPPING) e para desempatar o absorvedor em caso de "
            "trechos do mesmo comprimento. Sem isso, ou fora do Oracle, os "
            "registros novos ficam com esse campo nulo.\n\n"
            "As mudanças são aplicadas na edição da camada — ficam visíveis no "
            "mapa mas só são gravadas quando você clicar em 'Salvar edições da "
            "camada'. Antes disso dá para inspecionar e reverter tudo de uma "
            "vez.\n\n"
            "Trechos com o código do logradouro nulo são desconsiderados.\n\n"
            "A camada precisa estar em CRS projetado (unidade em metros).\n\n"
            "'Numerar os trechos após a remoção/quebra' (desmarcado por padrão): "
            "depois de aplicar a remoção/quebra, numera automaticamente os "
            "mesmos COD_LOGRADOURO processados (lendo a geometria já "
            "atualizada), sempre sobrescrevendo a numeração anterior — sem "
            "expor essa escolha como parâmetro. Os parâmetros 'Atributo do "
            "número sequencial' e 'Tolerância de gap' só são usados quando "
            "esta opção está marcada."
        )

    def createInstance(self):
        return RemoverTrechosPassagemAlgorithm()

    def flags(self):
        # Edita direto a camada do projeto — não roda fora da thread principal.
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def tr(self, texto):
        return QCoreApplication.translate("RemoverTrechosPassagemAlgorithm", texto)

    # -- parâmetros ------------------------------------------------------

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                self.tr("Camada de trechos-logradouros"),
                [QgsProcessing.TypeVectorLine],
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.APENAS_SELECIONADAS,
                self.tr(
                    "Processar apenas os logradouros das feições selecionadas "
                    "(desmarque para processar a camada inteira)"
                ),
                defaultValue=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPO_CODIGO,
                self.tr("Atributo de agrupamento (código do logradouro)"),
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Any,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOL_VERTICE,
                self.tr("Tolerância para encaixe de vértices (m)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.05,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.QUEBRAR_FORA_DE_ESCOPO,
                self.tr(
                    "Também quebrar o outro logradouro no cruzamento (o "
                    "trecho de fora do escopo é dividido, mas não colapsa "
                    "nem quebra por camada de quebra nesta execução)"
                ),
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.CAMADA_QUEBRA_1,
                self.tr("Camada de quebra 1 (opcional)"),
                [QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon],
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.CAMADA_QUEBRA_2,
                self.tr("Camada de quebra 2 (opcional)"),
                [QgsProcessing.TypeVectorLine, QgsProcessing.TypeVectorPolygon],
                optional=True,
            )
        )
        chave = QgsProcessingParameterField(
            self.CAMPO_CHAVE_PRIMARIA,
            self.tr(
                "Atributo da chave primária do Geomedia (ex.: IDPKTRLOGR) — só "
                "camada Oracle"
            ),
            parentLayerParameterName=self.INPUT,
            type=QgsProcessingParameterField.Any,
            optional=True,
        )
        chave.setFlags(
            chave.flags() | QgsProcessingParameterDefinition.FlagAdvanced
        )
        self.addParameter(chave)
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.NUMERAR_APOS,
                self.tr("Numerar os trechos após a remoção/quebra"),
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPO_SEQUENCIAL,
                self.tr(
                    "Numeração — atributo do número sequencial do trecho "
                    "(inteiro; só usado se 'Numerar os trechos após a "
                    "remoção/quebra' estiver marcado)"
                ),
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Numeric,
                optional=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOL_GAP,
                self.tr(
                    "Numeração — tolerância de gap entre trechos do mesmo "
                    "logradouro (m; só usado se 'Numerar os trechos após a "
                    "remoção/quebra' estiver marcado)"
                ),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=30.0,
                minValue=0.0,
            )
        )

    # -- execução ------------------------------------------------------

    def processAlgorithm(self, parameters, context, feedback):
        camada = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        if camada is None:
            raise QgsProcessingException(
                self.tr(
                    "A entrada precisa ser uma camada vetorial do projeto — o "
                    "resultado é gravado nela."
                )
            )
        apenas_selecionadas = self.parameterAsBool(
            parameters, self.APENAS_SELECIONADAS, context
        )
        exigir_crs_metrico(camada)

        nome_codigo = self.parameterAsString(parameters, self.CAMPO_CODIGO, context)
        tol = self.parameterAsDouble(parameters, self.TOL_VERTICE, context)
        quebrar_fora_de_escopo = self.parameterAsBool(
            parameters, self.QUEBRAR_FORA_DE_ESCOPO, context
        )
        nome_pk = self.parameterAsString(
            parameters, self.CAMPO_CHAVE_PRIMARIA, context
        )
        numerar_apos = self.parameterAsBool(parameters, self.NUMERAR_APOS, context)
        nome_sequencial = self.parameterAsString(
            parameters, self.CAMPO_SEQUENCIAL, context
        )
        tol_gap = self.parameterAsDouble(parameters, self.TOL_GAP, context)
        camadas_quebra = [
            c
            for c in (
                self.parameterAsVectorLayer(parameters, self.CAMADA_QUEBRA_1, context),
                self.parameterAsVectorLayer(parameters, self.CAMADA_QUEBRA_2, context),
            )
            if c is not None
        ]

        campos = camada.fields()
        if campos.indexFromName(nome_codigo) < 0:
            raise QgsProcessingException(
                self.tr("Atributo de agrupamento não encontrado na camada.")
            )
        if nome_pk and campos.indexFromName(nome_pk) < 0:
            nome_pk = ""  # parâmetro inválido: ignora, como se não tivesse sido informado
        idx_pk_campo = campos.indexFromName(nome_pk) if nome_pk else -1

        idx_sequencial = -1
        if numerar_apos:
            idx_sequencial = campos.indexFromName(nome_sequencial)
            if idx_sequencial < 0:
                raise QgsProcessingException(
                    self.tr(
                        "Numeração após a remoção/quebra: atributo do número "
                        "sequencial não encontrado."
                    )
                )
            if campos.at(idx_sequencial).type() not in _TIPOS_INTEIROS:
                raise QgsProcessingException(
                    self.tr(
                        "Numeração após a remoção/quebra: o atributo do número "
                        "sequencial precisa ser numérico (inteiro ou real)."
                    )
                )

        feedback.pushInfo(self.tr("Lendo a camada..."))
        campos_extra = (nome_pk,) if nome_pk else ()
        leitura = ler_camada(
            camada, nome_codigo, campos_extra=campos_extra, feedback=feedback
        )
        if feedback.isCanceled():
            return {}
        avisar_sem_codigo(leitura, feedback)
        geom_por_id = leitura.geom_por_id
        cod_por_id = leitura.cod_por_id
        por_codigo = leitura.por_codigo
        valor_pk_por_id = dict(leitura.valor_extra.get(nome_pk, {})) if nome_pk else {}

        # -- escopo ------------------------------------------------------
        if apenas_selecionadas:
            fids_sel = camada.selectedFeatureIds()
            if not fids_sel:
                raise QgsProcessingException(
                    self.tr(
                        "Nenhuma feição selecionada na camada — marque as feições "
                        "ou desligue a opção 'apenas selecionadas'."
                    )
                )
            codigos_escopo = {
                cod_por_id[fid] for fid in fids_sel if fid in cod_por_id
            }
        else:
            codigos_escopo = set(por_codigo.keys())

        # -- vizinhança ---------------------------------------------------
        bbox = QgsRectangle()
        for cod in codigos_escopo:
            for fid in por_codigo.get(cod, []):
                bbox.combineExtentWith(geom_por_id[fid].boundingBox())
        if bbox.isNull():
            feedback.pushInfo(self.tr("Nada em escopo."))
            return {}
        bbox.grow(tol)
        ids_vizinhanca = leitura.indice_espacial.intersects(bbox)

        coords_por_id = {}
        invalidos = set()
        for fid in ids_vizinhanca:
            coords = [QgsPointXY(v) for v in geom_por_id[fid].vertices()]
            if len(coords) < 2:
                invalidos.add(fid)
                continue
            coords_por_id[fid] = coords
        geom_por_id_viz = {fid: geom_por_id[fid] for fid in coords_por_id}
        cod_por_id_viz = {fid: cod_por_id[fid] for fid in coords_por_id}

        # -- fase 0: quebra pela própria camada (cruzamento entre logradouros) --
        # Sempre, sem parâmetro — a própria camada é fonte obrigatória de
        # cruzamento, além de qualquer camada de quebra auxiliar. Roda antes de
        # tudo, sobre a topologia original: um trecho em escopo que cruza — com
        # ou sem nó compartilhado, inclusive um X sem vértice em nenhum dos dois
        # lados, ou um quase toque dentro da tolerância de encaixe — qualquer
        # outro trecho na vizinhança, do mesmo COD_LOGRADOURO ou não, é dividido
        # ali; um código fora de escopo nunca é tocado, só serve de candidato.
        ids_escopo_fase0 = {
            fid
            for cod in codigos_escopo
            for fid in por_codigo.get(cod, [])
            if fid in coords_por_id
        }
        (
            coords_por_id,
            geom_por_id_viz,
            cod_por_id_fase0,
            novos_fase0,
            origem_real,
            pontos_de_corte,
            avisos_fase0,
        ) = quebrar_cruzamentos_entre_logradouros(
            ids_escopo_fase0,
            coords_por_id,
            geom_por_id_viz,
            cod_por_id_viz,
            tol,
            quebrar_fora_de_escopo=quebrar_fora_de_escopo,
        )
        for aviso in avisos_fase0:
            feedback.pushWarning(aviso)
        for temp_id in origem_real:
            por_codigo[cod_por_id_fase0[temp_id]].append(temp_id)

        # chave primária dos pedaços da fase 0, resolvida na hora (decisão do
        # operador): mesmo pipeline do Geomedia; o valor entra em
        # valor_pk_por_id para o desempate do absorvedor na fase 1 já usar a
        # chave real do pedaço, não um id temporário.
        atributos_por_origem = {}
        novos_fase0_com_chave = 0
        if novos_fase0:
            _, chaves0, motivo_pk0 = resolver_chaves(camada, nome_pk, len(novos_fase0))
            if motivo_pk0:
                feedback.pushWarning(motivo_pk0)
            for origem in {fid_origem for _, fid_origem, _ in novos_fase0}:
                atributos_por_origem[origem] = camada.getFeature(origem).attributes()
            if idx_pk_campo >= 0 and chaves0 is not None:
                for (temp_id, _, _), valor in zip(novos_fase0, chaves0):
                    if valor is not None:
                        valor_pk_por_id[temp_id] = valor
                        novos_fase0_com_chave += 1

        # -- índice de nós, já sobre a topologia pós-fase-0 -----------------
        indice = IndiceDeNos(tol)
        for fid, coords in coords_por_id.items():
            indice.indexar(fid, cod_por_id_fase0[fid], coords[0], coords[-1])

        # nós tocados por camada de quebra OU pela fase 0 viram cruzamento
        nos_bloqueados = nos_tocados_por_quebra(indice.nos, camadas_quebra, tol)
        for ponto in pontos_de_corte:
            nos_bloqueados.add(indice.achar_ou_criar_no(ponto))

        # -- fase 1: colapso por COD_LOGRADOURO ----------------------
        geom_nova_total = {}
        apagar_total = set()
        segmentos_colapsados = 0
        cods_com_segmento = 0
        cods_pulados = 0
        total = len(codigos_escopo)
        for i, cod in enumerate(sorted(codigos_escopo, key=str)):
            if feedback.isCanceled():
                break
            feedback.setProgress(int(100 * i / total) if total else 0)

            ids_cod = por_codigo.get(cod, [])
            if not ids_cod:
                continue
            if any(fid in invalidos or fid not in coords_por_id for fid in ids_cod):
                feedback.pushWarning(
                    self.tr(
                        "COD_LOGRADOURO {0}: trecho com geometria inválida "
                        "(menos de 2 vértices); logradouro pulado."
                    ).format(cod)
                )
                cods_pulados += 1
                continue

            degenerados_cod = trechos_degenerados(indice, ids_cod)
            avisar_trechos_degenerados(feedback, cod, degenerados_cod)

            segmentos = segmentos_de_passagem(
                indice, ids_cod, cod, nos_bloqueados, degenerados=degenerados_cod
            )
            geom_nova, apagar, avisos = {}, set(), []
            if segmentos:
                geom_nova, apagar, avisos = colapsar(
                    segmentos, indice, coords_por_id, geom_por_id_viz, tol, valor_pk_por_id
                )
                for aviso in avisos:
                    feedback.pushWarning(
                        "COD_LOGRADOURO {0}: {1}".format(cod, aviso)
                    )

            # Trecho degenerado (ADR-0009/0010): funde sempre com o maior
            # trecho real do mesmo código que tocar seu nó — mesmo num
            # cruzamento real (bifurcação, ou outro COD_LOGRADOURO), exceto
            # isolado ou bloqueado por camada de quebra. A fusão estende o
            # vizinho pelo vão real que o trecho degenerado preenchia — a
            # menos que esse vão já tenha sido coberto por um colapso normal
            # de segmento de passagem na mesma execução.
            if degenerados_cod:
                ids_cod_set = set(ids_cod)
                for did in sorted(degenerados_cod):
                    vizinho = trecho_degenerado_fundivel(
                        indice, did, ids_cod_set, nos_bloqueados, geom_por_id_viz, valor_pk_por_id
                    )
                    if vizinho is None:
                        continue
                    base_atual = geom_nova.get(vizinho, coords_por_id[vizinho])
                    nova_geom = fundir_trecho_degenerado(
                        indice, did, vizinho,
                        base_atual, coords_por_id[did],
                        geom_por_id_viz[vizinho], geom_por_id_viz[did],
                        tol, valor_pk_por_id,
                    )
                    if nova_geom is not None:
                        geom_nova[vizinho] = nova_geom
                    apagar.add(did)

            # Conta o que colapsou de fato (um absorvedor por segmento), não o
            # que foi identificado — segmento pulado por aviso fica de fora.
            if geom_nova:
                cods_com_segmento += 1
                segmentos_colapsados += len(geom_nova)
            geom_nova_total.update(geom_nova)
            apagar_total |= apagar

        # -- fase 2: quebra de todo trecho em escopo, colapsado ou não ------
        # Não depende de ter colapsado na fase 1: um trecho comum que nunca foi
        # trecho de passagem, mas cruza uma camada de quebra no meio, é
        # verificado do mesmo jeito. Só grava o que de fato precisa mudar.
        # novos: lista de (fid_origem, [QgsPointXY, ...]) para virar registro novo.
        novos = []
        if camadas_quebra:
            for cod in codigos_escopo:
                for fid in por_codigo.get(cod, []):
                    if fid in apagar_total:
                        continue
                    base = geom_nova_total.get(fid, coords_por_id.get(fid))
                    if base is None:
                        continue  # geometria inválida — já avisado ao pular o logradouro
                    pedacos = quebrar(base, camadas_quebra, tol)
                    if len(pedacos) <= 1:
                        continue
                    geom_nova_total[fid] = pedacos[0]
                    for extra in pedacos[1:]:
                        novos.append((fid, extra))

        if not geom_nova_total and not apagar_total and not novos_fase0:
            feedback.pushInfo(
                self.tr(
                    "Nenhum segmento de passagem para colapsar, trecho para "
                    "quebrar, nem cruzamento entre logradouros para dividir."
                )
            )
            if numerar_apos:
                feedback.pushInfo(self.tr("Numerando os trechos processados..."))
                numerados_apos, falhados_apos = self._numerar_codigos_afetados(
                    camada, codigos_escopo, nome_codigo, idx_sequencial, tol, tol_gap, feedback
                )
                feedback.pushInfo(
                    self.tr(
                        "Numeração: {0} logradouro(s) numerado(s) · {1} com falha."
                    ).format(numerados_apos, falhados_apos)
                )
            return {}

        # -- separa o que é id real do que é id temporário da fase 0 --------
        # Um id temporário nunca existiu na camada: se acabou apagado pela
        # fase 1 (absorvido num segmento de passagem), é só descartado — nunca
        # chama deleteFeature nele. Se sobreviveu, materializa como registro
        # novo (geometria final = a da fase 1, se ela o estendeu; senão a
        # própria da fase 0), com atributos da origem real e a chave já
        # resolvida.
        ids_temp_fase0 = set(origem_real)
        apagar_reais = apagar_total - ids_temp_fase0
        geom_nova_reais = {
            fid: c for fid, c in geom_nova_total.items() if fid not in ids_temp_fase0
        }
        # Um id real que a fase 0 truncou precisa ir para a EDIÇÃO com a
        # geometria truncada, mesmo que nem a fase 1 nem a fase 2 o toquem de
        # novo depois — senão a camada fica com a geometria ORIGINAL (inteira)
        # dele, duplicando o traçado que o pedaço novo agora cobre.
        for fid_origem_real in set(origem_real.values()) - apagar_reais:
            geom_nova_reais.setdefault(fid_origem_real, coords_por_id[fid_origem_real])
        temp_sobreviventes = sorted(ids_temp_fase0 - apagar_total)

        # -- chave primária dos registros novos da fase 2 (dicionário Geomedia) --
        chaves, motivo_pk = None, ""
        if novos:
            _, chaves, motivo_pk = resolver_chaves(camada, nome_pk, len(novos))
            if motivo_pk:
                feedback.pushWarning(motivo_pk)

        def _atributos_de(fid_origem):
            real = origem_real.get(fid_origem, fid_origem)
            if real in atributos_por_origem:
                return list(atributos_por_origem[real])
            return list(camada.getFeature(real).attributes())

        # -- aplica na EDIÇÃO da camada (sem commit) ------------------
        multi = QgsWkbTypes.isMultiType(camada.wkbType())
        novos_com_chave = 0
        with edicao_sem_commit(camada, self.tr("Quebrar e remover trechos de passagem")):
            for fid, coords in geom_nova_reais.items():
                exigir(
                    camada.changeGeometry(fid, self._geom(coords, multi)),
                    "changeGeometry, feição {0}".format(fid),
                )

            feicoes_novas = []

            for temp_id in temp_sobreviventes:
                coords = geom_nova_total.get(temp_id, coords_por_id[temp_id])
                atributos = _atributos_de(temp_id)
                if idx_pk_campo >= 0:
                    atributos[idx_pk_campo] = valor_pk_por_id.get(temp_id)
                nova = QgsFeature(camada.fields())
                nova.setAttributes(atributos)
                nova.setGeometry(self._geom(coords, multi))
                feicoes_novas.append(nova)

            for i, (fid_origem, coords) in enumerate(novos):
                atributos = _atributos_de(fid_origem)
                if idx_pk_campo >= 0:
                    valor = chaves[i] if chaves is not None else None
                    atributos[idx_pk_campo] = valor
                    if valor is not None:
                        novos_com_chave += 1
                nova = QgsFeature(camada.fields())
                nova.setAttributes(atributos)
                nova.setGeometry(self._geom(coords, multi))
                feicoes_novas.append(nova)

            if feicoes_novas:
                exigir(
                    camada.addFeatures(feicoes_novas),
                    "addFeatures, {0} registro(s) novo(s)".format(len(feicoes_novas)),
                )

            for fid in apagar_reais:
                exigir(
                    camada.deleteFeature(fid),
                    "deleteFeature, feição {0}".format(fid),
                )

        trechos_divididos_fase0 = len({o for o in origem_real.values()})
        feedback.pushInfo(
            self.tr(
                "Fase 0 (cruzamento entre logradouros): {0} trecho(s) "
                "dividido(s) · {1} registro(s) novo(s) ({2} com chave "
                "primária, {3} sem)."
            ).format(
                trechos_divididos_fase0,
                len(origem_real),
                novos_fase0_com_chave,
                len(origem_real) - novos_fase0_com_chave,
            )
        )
        codigos_fora_divididos = {
            cod_por_id_fase0[origem]
            for origem in set(origem_real.values())
            if cod_por_id_fase0[origem] not in codigos_escopo
        }
        if codigos_fora_divididos:
            feedback.pushWarning(
                self.tr(
                    "COD_LOGRADOURO fora de escopo dividido pelo cruzamento "
                    "('Também quebrar o outro logradouro no cruzamento'): {0}. "
                    "A geometria desses trechos mudou, mas o número sequencial "
                    "deles não é recalculado por esta execução (mesmo com "
                    "'Numerar os trechos após a remoção/quebra' marcado) — "
                    "rode a numeração separadamente para esses códigos."
                ).format(", ".join(str(c) for c in sorted(codigos_fora_divididos, key=str)))
            )
        feedback.pushInfo(
            self.tr(
                "Concluído: {0} segmento(s) de passagem colapsado(s) · {1} "
                "trecho(s) apagado(s) · {2} registro(s) novo(s) pela quebra "
                "({3} com chave primária, {4} sem) · {5} logradouro(s) com "
                "segmento de passagem · {6} logradouro(s) pulado(s)."
            ).format(
                segmentos_colapsados,
                len(apagar_reais),
                len(novos),
                novos_com_chave,
                len(novos) - novos_com_chave,
                cods_com_segmento,
                cods_pulados,
            )
        )
        if numerar_apos:
            feedback.pushInfo(self.tr("Numerando os trechos processados..."))
            numerados_apos, falhados_apos = self._numerar_codigos_afetados(
                camada, codigos_escopo, nome_codigo, idx_sequencial, tol, tol_gap, feedback
            )
            feedback.pushInfo(
                self.tr(
                    "Numeração: {0} logradouro(s) numerado(s) · {1} com falha."
                ).format(numerados_apos, falhados_apos)
            )

        feedback.pushInfo(
            self.tr(
                "As mudanças estão na EDIÇÃO da camada. Revise no mapa e use "
                "'Salvar edições da camada' para gravar em definitivo, ou "
                "'Reverter' para desfazer tudo."
            )
        )
        return {}

    @staticmethod
    def _geom(coords, multi):
        if multi:
            return QgsGeometry.fromMultiPolylineXY([coords])
        return QgsGeometry.fromPolylineXY(coords)

    def _numerar_codigos_afetados(
        self, camada, codigos, nome_codigo, idx_sequencial, tol_vertice, tol_gap, feedback
    ):
        """Numera ``codigos`` lendo a camada de novo — já com a geometria da
        remoção/quebra aplicada no buffer de edição — sempre sobrescrevendo
        (a geometria acabou de mudar, a numeração anterior está obsoleta).
        Reaproveita as mesmas funções puras do algoritmo de numeração
        standalone; não instancia o ``QgsProcessingAlgorithm`` dele.
        """
        leitura = ler_camada(camada, nome_codigo, feedback=feedback)
        if feedback.isCanceled():
            return 0, 0
        avisar_sem_codigo(leitura, feedback)
        geom_por_id = leitura.geom_por_id
        cod_por_id = leitura.cod_por_id
        por_codigo = leitura.por_codigo

        a_numerar = [cod for cod in codigos if por_codigo.get(cod)]
        if not a_numerar:
            return 0, 0

        bbox = QgsRectangle()
        for cod in a_numerar:
            for fid in por_codigo[cod]:
                bbox.combineExtentWith(geom_por_id[fid].boundingBox())
        bbox.grow(tol_vertice)
        ids_vizinhanca = leitura.indice_espacial.intersects(bbox)

        parseados = {}
        for fid in ids_vizinhanca:
            try:
                parseados[fid] = parse_geometria(fid, cod_por_id[fid], geom_por_id[fid])
            except NumeracaoError as ex:
                feedback.pushWarning(str(ex))
        grafo = GrafoLogradouro(parseados.values(), tol_vertice)

        resultado = {}
        numerados = 0
        falhados = 0
        for cod in a_numerar:
            ids = por_codigo[cod]
            if any(fid not in parseados for fid in ids):
                feedback.pushWarning(
                    self.tr(
                        "Numeração após remoção/quebra — COD_LOGRADOURO {0}: "
                        "algum trecho ficou fora do grafo; pulado."
                    ).format(cod)
                )
                falhados += 1
                continue
            alvo = [parseados[fid] for fid in ids]
            try:
                grafo.definir_alvo(alvo)
                ordem = SequenciadorAutomatico(cod, alvo, grafo, tol_gap).run()
                numeros = atribuir(ordem, grafo)
            except NumeracaoError as ex:
                feedback.pushWarning(
                    self.tr(
                        "Numeração após remoção/quebra — COD_LOGRADOURO {0}: {1}"
                    ).format(cod, ex)
                )
                falhados += 1
                continue
            avisar_trechos_degenerados(feedback, cod, grafo.degenerados)
            resultado.update(numeros)
            numerados += 1

        if resultado:
            with edicao_sem_commit(
                camada,
                self.tr("Numeração após quebrar e remover trechos de passagem"),
            ):
                for fid, n in resultado.items():
                    exigir(
                        camada.changeAttributeValue(fid, idx_sequencial, int(n)),
                        "changeAttributeValue, feição {0}".format(fid),
                    )

        return numerados, falhados
